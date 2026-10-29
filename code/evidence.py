"""Parse participant evidence once, preserving capture time, replica, and scope.

No case IDs or public answers enter this module. SQLite executes only an
allow-listed snapshot dialect inside an in-memory database.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from identity import identifiers
from policy import exposed
from schema import Observation, ResourceLink, Scope, UnresolvedCase, timestamp

COLLECTIONS = {
    "customer_profiles": ("account_service", "USER_PROFILE"),
    "profile_lookups": ("account_service", "USER_PROFILE"),
    "customer_search_documents": ("search_service", "SEARCH_INDEX_ENTRY"),
    "index_queries": ("search_service", "SEARCH_INDEX_ENTRY"),
    "customer_analytics_reports": ("analytics_platform", "ANALYTICS_PROFILE"),
    "customer_analytics_profiles": ("analytics_platform", "ANALYTICS_PROFILE"),
    "support_conversations": ("support_platform", "SUPPORT_MESSAGE"),
    "support_records": ("support_platform", "SUPPORT_MESSAGE"),
    "tickets": ("support_platform", "SUPPORT_MESSAGE"),
    "ticket_attachments": ("support_platform", "SUPPORT_ATTACHMENT"),
    "customer_export_jobs": ("export_service", "USER_EXPORT"),
    "customer_exports": ("export_service", "USER_EXPORT"),
    "exports": ("export_service", "USER_EXPORT"),
    "connector_configurations": ("integration_service", "DATA_FLOW"),
    "connector_subscriptions": ("integration_service", "DATA_FLOW"),
    "connectors": ("integration_service", "DATA_FLOW"),
    "backup_catalog": ("backup_service", "BACKUP_ARCHIVE"),
    "backup_restore_entries": ("backup_service", "BACKUP_ARCHIVE"),
    "restore_entries": ("backup_service", "BACKUP_ARCHIVE"),
    "security_audit_events": ("security_service", "SECURITY_AUDIT_LOG"),
    "security_audit_records": ("security_service", "SECURITY_AUDIT_LOG"),
    "audit_records": ("security_service", "SECURITY_AUDIT_LOG"),
    "retained_order_records": ("legal_service", "LEGAL_HOLD_RECORD"),
    "deleted_customer_references": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "marketing_profiles": ("marketing_platform", "MARKETING_PROFILE"),
    "email_delivery_logs": ("email_delivery_service", "EMAIL_DELIVERY_LOG"),
    "product_telemetry": ("analytics_platform", "PRODUCT_TELEMETRY"),
}
PREFIXES = {
    "account": ("account_service", "USER_PROFILE"),
    "search": ("search_service", "SEARCH_INDEX_ENTRY"),
    "analytics": ("analytics_platform", "ANALYTICS_PROFILE"),
    "support": ("support_platform", "SUPPORT_MESSAGE"),
    "export": ("export_service", "USER_EXPORT"),
    "data_flow": ("integration_service", "DATA_FLOW"),
    "backup": ("backup_service", "BACKUP_ARCHIVE"),
    "audit_record": ("security_service", "SECURITY_AUDIT_LOG"),
    "legal_hold": ("legal_service", "LEGAL_HOLD_RECORD"),
    "tombstone": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "marketing": ("marketing_platform", "MARKETING_PROFILE"),
    "email_delivery": ("email_delivery_service", "EMAIL_DELIVERY_LOG"),
    "cache": ("cache_service", "CACHE_ENTRY"),
}
RID_RE = re.compile(r"\b(?:account|search|analytics|support|export|data_flow|backup|audit_record|legal_hold|tombstone|marketing|email_delivery|cache)_\d+\b")
STATES = {"FOUND": "PRESENT", "NOT_FOUND": "ABSENT", "IDENTIFIABLE": "PRESENT",
          "REDACTED": "REDACTED", "ANONYMIZED": "ANONYMIZED", "ACTIVE": "ACTIVE",
          "DISABLED": "DISABLED", "BLOCKED": "BLOCKED", "PRESENT": "PRESENT"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"Invalid CSV header: {path.name}")
        rows = list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError(f"Malformed CSV rows: {path.name}")
        return rows


def boolean(value: object) -> bool:
    if value in (True, 1, "true", "1", "yes", "allow", "allowed"):
        return True
    if value in (False, 0, "false", "0", "no", "deny", "denied"):
        return False
    raise UnresolvedCase(f"Invalid boolean value: {value!r}")


def record_state(category: str, fields: dict) -> str:
    if fields.get("status_code") == 404 or str(fields.get("http_status")) == "404":
        return "ABSENT"
    if fields.get("result") in STATES:
        return STATES[fields["result"]]
    if category == "DATA_FLOW":
        return "ACTIVE" if boolean(fields["enabled"]) else "DISABLED"
    if category == "BACKUP_ARCHIVE":
        if fields.get("restore_allowed") is None:
            return "UNKNOWN"
        return "ACTIVE" if boolean(fields["restore_allowed"]) else "BLOCKED"
    if category in ("ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"):
        return "PRESENT" if exposed(fields, stable_allowed=False) else "ANONYMIZED"
    if category in ("SUPPORT_MESSAGE", "ACCOUNT_TOMBSTONE", "EMAIL_DELIVERY_LOG"):
        return "PRESENT" if exposed(fields, stable_allowed=True) else "REDACTED"
    return "PRESENT"


class EvidenceStore:
    def __init__(self, dataset: Path, cache: Path, *, use_ocr: bool = True, catalog=()):
        self.dataset = dataset.resolve()
        self.cache = cache
        self.use_ocr = use_ocr
        self.catalog = list(catalog)
        self.observations: list[Observation] = []
        self.scopes: list[Scope] = []
        self.coverage: list[dict] = []
        self.ocr_calls = 0
        self.ocr_cache_hits = 0
        self.ocr_engine = None
        self.sources = {r["file_id"]: r for r in read_csv(self.dataset / "evidence_files.csv")}
        self.model_hashes: dict[str, str] = {}
        for meta in self.sources.values():
            self.extract(meta)
        self.by_resource = defaultdict(list)
        self.by_identifier = defaultdict(set)
        for obs in self.observations:
            self.by_resource[(obs.system_id, obs.resource_id)].append(obs)
            for value in obs.identifiers:
                self.by_identifier[value].add((obs.system_id, obs.resource_id))
        self.links = []
        # Explicit ownership/derivation fields are grounded relationships. Nearby
        # IDs in a document, table order, and workflow timestamps are not joins.
        for obs in self.observations:
            for path, rid in resource_references(obs.fields):
                prefix=rid.rsplit("_",1)[0]
                if prefix not in PREFIXES or rid==obs.resource_id:
                    continue
                system,category=PREFIXES[prefix]
                self.links.append(ResourceLink(source_system=obs.system_id,source_resource=obs.resource_id,
                    target_system=system,target_resource=rid,target_category=category,
                    observed_at=obs.observed_at,available_at=obs.available_at,
                    evidence_id=obs.evidence_id,field_path=path))

    def add(self, meta: dict, system: str, rid: str, category: str, state: str,
            observed: str, fields: dict, *, replica="default", linked=()):
        timestamp(observed)
        if category=="BACKUP_ARCHIVE" and state=="UNKNOWN" and "restore_allowed" not in fields and not fields.get("restore_permission_observed"):
            fields=dict(fields,unknown_fields=["restore_allowed"])
        self.observations.append(Observation(
            system_id=system, resource_id=rid, category=category, state=state,
            observed_at=observed, available_at=meta["captured_at"], evidence_id=meta["file_id"],
            fields=fields, identifiers=tuple(sorted(identifiers(fields) | set(linked))), replica=replica))

    def scope(self, meta, system, category, observed, replica, rids, *, complete=False):
        self.scopes.append(Scope(system_id=system, category=category, observed_at=observed,
                                 available_at=meta["captured_at"], evidence_id=meta["file_id"],
                                 replica=replica, resource_ids=tuple(sorted(rids)), complete=complete))

    def extract(self, meta):
        path = (self.dataset / meta["file_path"]).resolve()
        if not path.is_relative_to(self.dataset / "evidence"):
            raise ValueError("Evidence path escapes participant evidence directory")
        before = len(self.observations)
        scopes_before = len(self.scopes)
        try:
            if path.suffix == ".json":
                self.json_file(meta, json.loads(path.read_text()))
            elif path.suffix == ".sql":
                self.sql_file(meta, path.read_text())
            elif path.suffix == ".log":
                self.log_file(meta, path.read_text())
            elif path.suffix == ".txt":
                self.text_file(meta, path.read_text())
            elif path.suffix == ".pdf":
                from pypdf import PdfReader
                text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
                if not text.strip():
                    raise ValueError("Scanned PDF requires vision; no text layer")
                self.document(meta, text)
            elif path.suffix == ".png":
                if not self.use_ocr:
                    raise ValueError("OCR explicitly disabled for ablation")
                self.image_file(meta, path)
            else:
                raise ValueError("Unsupported evidence format")
            self.coverage.append(dict(evidence_id=meta["file_id"], format=path.suffix,
                                      parsed=True, observations=len(self.observations)-before,
                                      content_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        except Exception as error:
            del self.observations[before:]
            del self.scopes[scopes_before:]
            self.coverage.append(dict(evidence_id=meta["file_id"], format=path.suffix,
                                      parsed=False, observations=0, error=type(error).__name__ + ": " + str(error)))

    def records(self, meta, collection, records, observed, *, system=None, replica="default"):
        if collection not in COLLECTIONS:
            raise ValueError(f"Unknown evidence collection {collection}")
        inferred_system, category = COLLECTIONS[collection]
        system = system or inferred_system
        for record in records:
            fields = record.get("profile") or record
            rid = record["resource_id"]
            if "hits" in record:
                documents = record["hits"].get("documents", [])
                fields = documents[0] if documents else record
            state = record_state(category, fields)
            if "hits" in record and record["hits"]["total"] == 0:
                state = "ABSENT"
            # User-supplied query keys link observations but are never PII fields.
            self.add(meta, system, rid, category, state, record.get("observed_at", observed), fields,
                     replica=replica, linked=identifiers(record))

    def json_file(self, meta, data):
        observed = data.get("captured_at", data.get("exported_at", meta["captured_at"]))
        if "snapshots" in data:
            for snapshot in data["snapshots"]:
                collection, system = snapshot["collection"], snapshot["data_store"]
                at = snapshot["captured_at"]
                if collection == "operational_record_history":
                    for r in snapshot["records"]:
                        self.add(meta, r["system"], r["resource_id"], r["record_type"], STATES[r["result"]],
                                 r["recorded_at"], r)
                    continue
                self.records(meta, collection, snapshot["records"], at, system=system)
                self.scope(meta, system, COLLECTIONS[collection][1], at, "default",
                           [r["resource_id"] for r in snapshot["records"]])
        elif "service_exports" in data:
            for system, collections in data["service_exports"].items():
                for collection, records in collections.items():
                    if collection == "profiles" and system == "analytics_platform":
                        collection = "customer_analytics_profiles"
                    self.records(meta, collection, records, observed, system=system)
        elif "collection" in data:
            self.records(meta, data["collection"], data["records"], observed)
        elif "records" in data:
            for r in data["records"]:
                self.add(meta, r["system"], r["resource_id"], r["record_type"], STATES[r["result"]],
                         r["recorded_at"], r)
        else:
            raise ValueError("Unrecognized JSON evidence structure")

    def sql_file(self, meta, text):
        connection = sqlite3.connect(":memory:")
        # Deny disk/network access and arbitrary SQL; only snapshot DDL/DML is needed.
        allowed = {sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_INSERT,
                   sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT, sqlite3.SQLITE_UPDATE,
                   sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_REINDEX}
        def authorize(action, arg1, arg2, database, trigger):
            if action in allowed:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and arg2 in {"json_valid"}:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_PRAGMA and arg1 == "foreign_keys":
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        connection.set_authorizer(authorize)
        try:
            connection.executescript(text)
            connection.set_authorizer(None)
            connection.row_factory = sqlite3.Row
            tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            scopes = {}
            if "snapshot_scope" in tables:
                scopes = {r["origin_system"]: r["captured_at"] for r in connection.execute("SELECT * FROM snapshot_scope")}
            # Empty replicas are still part of a snapshot. Infer their logical
            # collections from the declared schema and peer tables, never from
            # case IDs or the public answers.
            generic_collections=set()
            for name in tables:
                columns={r[1] for r in connection.execute('PRAGMA table_info("'+name.replace('"','""')+'")')}
                if "collection_name" in columns:
                    generic_collections.update(r[0] for r in connection.execute('SELECT DISTINCT collection_name FROM "'+name.replace('"','""')+'"'))
            for table in tables:
                if table == "snapshot_scope":
                    continue
                rows = [dict(r) for r in connection.execute('SELECT * FROM "'+table.replace('"','""')+'"')]
                replica = table if ("replica" in table or table.endswith("_primary")) else "default"
                groups = defaultdict(list)
                if table.startswith("customer_data_") and table not in COLLECTIONS:
                    for collection in generic_collections:
                        groups.setdefault(COLLECTIONS[collection],[])
                for row in rows:
                    if "record_json" in row:
                        collection = row["collection_name"]
                        system, category = COLLECTIONS[collection]
                        fields = json.loads(row["record_json"])
                    else:
                        collection = table
                        for suffix in ("_failover_replica", "_primary"):
                            collection = collection.removesuffix(suffix)
                        if collection == "search_documents":
                            collection = "customer_search_documents"
                        system, category = COLLECTIONS[collection]
                        fields = row
                    observed = scopes.get(system, meta["captured_at"])
                    self.add(meta, system, row["resource_id"], category, record_state(category, fields),
                             observed, fields, replica=replica)
                    groups[(system, category)].append(row["resource_id"])
                # Table names describe a collection/replica, not its coverage.
                # Only a declared snapshot scope authorizes negative inference.
                if table in COLLECTIONS:
                    system, category = COLLECTIONS[table]
                    if system in scopes:
                        groups.setdefault((system, category), [])
                if table.startswith("customer_profiles_"):
                    groups.setdefault(("account_service","USER_PROFILE"),[])
                for (system, category), rids in groups.items():
                    self.scope(meta, system, category, scopes.get(system, meta["captured_at"]), replica, rids,
                               complete=system in scopes)
        finally:
            connection.close()

    def text_file(self, meta, text):
        for line in text.splitlines():
            parts = [part.strip() for part in line.removeprefix("- ").split("|")]
            if len(parts) == 6 and re.match(r"\d{4}-", parts[0]):
                at, system, rid, category, state, subject = parts
                self.add(meta, system, rid, category, STATES[state], at, {"subject_reference": subject})

    def log_file(self, meta, text):
        frames = {}
        for line_no, line in enumerate(text.splitlines()):
            if not re.match(r"\d{4}-\d\d-\d\dT", line):
                continue
            at, body = line.split(" ", 1)
            fields = parse_log_fields(body)
            event = str(fields.get("event", ""))
            trace = fields.get("trace_id") or fields.get("requestId")
            rid = fields.get("resource_id")
            key = str(trace or rid or line_no)
            frame = frames.setdefault(key, {})
            frame.update(fields)
            rid = frame.get("resource_id")
            if not rid:
                continue
            if event == "record_lookup":
                self.add(meta, frame["system"], str(rid), frame["record_type"], STATES[frame["result"]], at, frame)
                continue
            if event not in READ_EVENTS:
                continue
            system, category = READ_EVENTS[event]
            state = "PRESENT"
            if category == "USER_PROFILE" and str(frame.get("rows")) == "0":
                state = "ABSENT"
            elif category == "DATA_FLOW":
                state = "ACTIVE" if boolean(frame["enabled"]) else "DISABLED"
            elif category == "BACKUP_ARCHIVE":
                restore = frame.get("restore_allowed", frame.get("eligible", frame.get("decision")))
                state = "ACTIVE" if boolean(restore) else "BLOCKED"
            elif category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"}:
                if str(frame.get("direct_identifiers")) == "0":
                    state = "ANONYMIZED"
                else:
                    state = record_state(category, frame)
            elif category in {"SUPPORT_MESSAGE", "EMAIL_DELIVERY_LOG", "ACCOUNT_TOMBSTONE"}:
                state = record_state(category, frame)
            if event == "contact_lookup_completed":
                category = "SECONDARY_IDENTIFIER"
            self.add(meta, system, str(rid), category, state, at, dict(frame))

    def document(self, meta, text):
        # Business documents prove only the resources actually identified in their text.
        rids = set(RID_RE.findall(text))
        for rid in sorted(rids):
            prefix = rid.rsplit("_", 1)[0]
            system, category = PREFIXES[prefix]
            if prefix == "support" and ("attachment" in text.casefold() or "uploader customer" in text.casefold()):
                category = "SUPPORT_ATTACHMENT"
            self.add(meta, system, rid, category, "PRESENT", meta["captured_at"], {"text": text})
        self.artifact_links(meta, text)

    def artifact_links(self, meta, text):
        """A catalog alias can identify an object in a business artifact.

        The combined fact becomes available only when BOTH sources exist.
        A link is identity evidence, never proof of the object's state.
        """
        for event in self.catalog:
            if event["event_type"] != "LINK_RESOURCE_IDENTITY":
                continue
            match = re.search(r'\(([^)]+)\)', event["details"])
            if not match or match[1] not in text:
                continue
            rid = event["resource_id"]
            allowed_origins = {"object": {"object_storage"}, "tombstone": {"identity_service"},
                               "export": {"account_history_service", "export_service"}}
            prefix = rid.rsplit("_", 1)[0]
            if meta["origin"] not in allowed_origins.get(prefix, set()):
                continue
            if any(o.resource_id == rid and o.evidence_id == meta["file_id"] for o in self.observations):
                continue
            if rid.startswith("object_"):
                system, category, state = event["target_system"], "SUPPORT_ATTACHMENT", "PRESENT"
            elif rid.startswith("tombstone_"):
                system, category = "identity_service", "ACCOUNT_TOMBSTONE"
                state = "PRESENT" if any("@" in value for value in identifiers(text)) else "REDACTED"
            elif rid.startswith("export_"):
                system, category, state = "export_service", "USER_EXPORT", "PRESENT"
            else:
                continue
            linked_meta = dict(meta)
            linked_meta["captured_at"] = max((meta["captured_at"], event["event_time"]), key=timestamp)
            self.add(linked_meta, system, rid, category, state, meta["captured_at"],
                     {"text": text, "catalog_evidence_id": event["activity_id"]}, linked=identifiers(event["details"]))

    def image_file(self, meta, path):
        version = "rapidocr-onnxruntime-1.4.4-layout-v1"
        digest = hashlib.sha256(path.read_bytes()+version.encode()).hexdigest()
        cached = self.cache / "ocr" / (digest+".json")
        if cached.exists():
            boxes = json.loads(cached.read_text())
            self.ocr_cache_hits += 1
        else:
            if self.ocr_engine is None:
                from rapidocr_onnxruntime import RapidOCR
                self.ocr_engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=2)
            result, _ = self.ocr_engine(str(path))
            if not result:
                raise ValueError("OCR found no text")
            boxes = [{"box": box, "text": text, "confidence": float(conf)} for box, text, conf in result]
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps(boxes), encoding="utf-8")
            self.ocr_calls += 1
        text = "\n".join(b["text"] for b in boxes)
        self.artifact_links(meta, text)
        main = "\n".join(b["text"] for b in boxes if sum(p[1] for p in b["box"])/4 < 310)
        rids = set(RID_RE.findall(main))
        # The main resource is identified in the page header or a labelled detail card.
        if not rids:
            rids = set(RID_RE.findall(text))
        origin = meta["origin"]
        expected = {"account_admin_portal": "account", "search_index_admin": "search",
                    "integration_admin": "data_flow", "analytics_platform": "analytics",
                    "export_service": "export", "support_platform": "support", "backup_service": "backup",
                    "security_service": "audit_record", "identity_service": "tombstone",
                    "object_storage": "export", "marketing_platform": "marketing"}.get(origin)
        if expected:
            rids = {r for r in rids if r.rsplit("_", 1)[0] == expected}
        if not rids:
            if any(o.evidence_id == meta["file_id"] for o in self.observations):
                return
            raise ValueError("OCR cannot ground the primary resource ID")
        selected = set()
        for b in boxes:
            center_x = sum(p[0] for p in b["box"])/4
            center_y = sum(p[1] for p in b["box"])/4
            if center_x > 1420 and center_y < 365:
                selected.update(RID_RE.findall(b["text"]))
        if selected.intersection(rids):
            rids = selected.intersection(rids)
        elif expected == "audit_record":
            # OCR sometimes reads zero as 'o' in a selected event's header.
            headers = [b["text"] for b in boxes if sum(p[0] for p in b["box"])/4 > 1420
                       and sum(p[1] for p in b["box"])/4 < 365]
            corrected = set(RID_RE.findall("\n".join(headers).replace("_oo", "_00")))
            if corrected.intersection(rids):
                rids = corrected.intersection(rids)
        for rid in sorted(rids):
            matching = [b for b in boxes if rid in b["text"]]
            if not matching or max(b["confidence"] for b in matching) < 0.85:
                raise ValueError("Low confidence OCR resource ID")
            system, category = PREFIXES[rid.rsplit("_", 1)[0]]
            state = "PRESENT"
            # Isolate the selected resource's header, row and detail pane.
            # Unrelated table rows must not contribute their owners' identifiers.
            selected_boxes = []
            row_y = [sum(p[1] for p in b["box"])/4 for b in matching
                     if sum(p[0] for p in b["box"])/4 < 1420]
            for b in boxes:
                x = sum(p[0] for p in b["box"])/4
                y = sum(p[1] for p in b["box"])/4
                if x > 1420 or y < 310 or any(abs(y-at) < 13 for at in row_y):
                    selected_boxes.append(b)
            resource_text = "\n".join(b["text"] for b in selected_boxes)
            lower = resource_text.casefold()
            if category == "DATA_FLOW":
                state = "DISABLED" if "disabled" in lower or "paused" in lower else "ACTIVE"
            elif category == "BACKUP_ARCHIVE":
                state = restore_permission_from_text(resource_text)
            elif category == "ACCOUNT_TOMBSTONE":
                state = "PRESENT" if identifiers(resource_text)-{x for x in identifiers(resource_text) if x.startswith("user_")} else "REDACTED"
            fields={"text":resource_text}
            if category=="BACKUP_ARCHIVE":
                fields["archive_present"]=True
                fields["restore_permission_observed"]=bool(re.search(r"\brestore[ _-]+(?:allowed|access|authorization|permission|policy)\b",resource_text,re.I))
            self.add(meta, system, rid, category, state, meta["captured_at"], fields)


def restore_permission_from_text(text: str) -> str:
    """Require a displayed restore control, not archive presence or UI health."""
    flags=re.findall(r"\brestore[ _-]+allowed\s*[:=]?\s*(true|false|yes|no)\b",text,re.I)
    controls=re.findall(r"\brestore[ _-]+(?:access|authorization|permission|policy)\s*[:=]?\s*(allowed|permitted|enabled|blocked|denied|disabled)\b",text,re.I)
    states={"ACTIVE" if value.casefold() in {"true","yes","allowed","permitted","enabled"} else "BLOCKED"
            for value in flags+controls}
    return states.pop() if len(states)==1 else "UNKNOWN"


READ_EVENTS = {
    "profile_lookup_completed": ("account_service", "USER_PROFILE"),
    "index_query_completed": ("search_service", "SEARCH_INDEX_ENTRY"),
    "analytics_identity_scan": ("analytics_platform", "ANALYTICS_PROFILE"),
    "analytics_profile_read": ("analytics_platform", "ANALYTICS_PROFILE"),
    "analytics_profile_read_completed": ("analytics_platform", "ANALYTICS_PROFILE"),
    "contact_lookup_completed": ("analytics_platform", "SECONDARY_IDENTIFIER"),
    "message_pii_scan": ("support_platform", "SUPPORT_MESSAGE"),
    "message_read": ("support_platform", "SUPPORT_MESSAGE"),
    "support_ticket_read_completed": ("support_platform", "SUPPORT_MESSAGE"),
    "attachment_pii_scan": ("support_platform", "SUPPORT_ATTACHMENT"),
    "contact_query_completed": ("support_platform", "SECONDARY_IDENTIFIER"),
    "export_download_check_completed": ("export_service", "USER_EXPORT"),
    "export_metadata_read_completed": ("export_service", "USER_EXPORT"),
    "connector_heartbeat": ("integration_service", "DATA_FLOW"),
    "connector_config_loaded": ("integration_service", "DATA_FLOW"),
    "connector_config_read_completed": ("integration_service", "DATA_FLOW"),
    "restore_candidate_evaluated": ("backup_service", "BACKUP_ARCHIVE"),
    "restore_authorization_completed": ("backup_service", "BACKUP_ARCHIVE"),
    "restore_policy_read_completed": ("backup_service", "BACKUP_ARCHIVE"),
    "audit_record_read_completed": ("security_service", "SECURITY_AUDIT_LOG"),
    "retained_order_loaded": ("legal_service", "LEGAL_HOLD_RECORD"),
}


def resource_references(value: object, path: str=""):
    fields={"source_resource_id","owner_resource_id","subject_resource_id","account_resource_id"}
    if isinstance(value,dict):
        for key,item in value.items():
            location=f"{path}.{key}" if path else key
            if key in fields and isinstance(item,str) and RID_RE.fullmatch(item):
                yield location,item
            elif isinstance(item,(dict,list)):
                yield from resource_references(item,location)
    elif isinstance(value,list):
        for index,item in enumerate(value):
            yield from resource_references(item,f"{path}[{index}]")


def parse_log_fields(body: str) -> dict:
    if body.startswith("{"):
        fields = json.loads(body)
        return {k: None if v == "null" else v for k, v in fields.items()}
    pattern = r'(\w+)=(?:"((?:\\.|[^"\\])*)"|([^\s]+))'
    fields = {}
    for match in re.finditer(pattern, body):
        key, quoted, bare = match.groups()
        fields[key] = json.loads('"'+quoted+'"') if bare is None else bare
    # Cloud-runtime exports carry the real log line inside an escaped message.
    if "message" in fields and isinstance(fields["message"], str):
        fields.update(parse_log_fields(fields.pop("message")))
    if "event" not in fields:
        match = re.search(r'\]\s+(\w+):', body)
        if match:
            fields["event"] = match[1]
            brackets = re.findall(r'\[([^\]]+)\]', body)
            if len(brackets) >= 3:
                fields.update(service=brackets[1], trace_id=brackets[2])
        elif " | " in body:
            parts = body.split(" | ")
            if len(parts) >= 5:
                fields.update(service=parts[1], trace_id=parts[2], event=parts[3])
    if "trace_id" not in fields:
        match = re.search(r'<\d+>1 \S+ (\S+) (\S+) - -', body)
        if match:
            fields.update(service=match[1], trace_id=match[2])
    return {k: None if v == "null" else v for k, v in fields.items()}
