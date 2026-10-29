"""Standalone structural, temporal, and resource-level citation validator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence import read_csv
from schema import COLUMNS, OPERATIONS, step_key, timestamp


def validate(rows: list[dict], requests: list[dict], sources: dict[str, dict],
             activity: list[dict], audits: list[dict], observations=(), scopes=(), *,
             fallback_case_ids=frozenset(), resource_links=()) -> None:
    ids = [r["case_id"] for r in rows]
    expected = [r["case_id"] for r in requests]
    if len(set(expected)) != len(expected):
        raise ValueError("Input contains duplicate cases")
    if len(set(ids)) != len(ids) or set(ids) != set(expected) or ids != sorted(ids):
        raise ValueError("Output must contain every requested case exactly once in sorted order")
    if not set(fallback_case_ids).issubset(ids):
        raise ValueError("Fallback ledger contains unknown cases")
    request_index = {r["case_id"]: r for r in requests}
    references = {key: r["captured_at"] for key, r in sources.items()}
    references.update({r["activity_id"]: r["event_time"] for r in activity})
    references.update({r["audit_id"]: r["event_time"] for r in audits})
    evidence_resources = {}
    for obs in observations:
        evidence_resources.setdefault(obs.evidence_id, set()).add((obs.system_id, obs.resource_id))
    for event in activity:
        evidence_resources.setdefault(event["activity_id"], set()).add((event["target_system"], event["resource_id"]))
    fields = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
    for row in rows:
        status, steps = row["deletion_status"], row["steps"]
        fallback = row["case_id"] in fallback_case_ids
        if fallback and status != "INCOMPLETE":
            raise ValueError("Unverified fallback must be INCOMPLETE")
        if status not in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}:
            raise ValueError("Unknown deletion status")
        if not isinstance(steps, list) or (status == "NOT_APPLICABLE" and steps):
            raise ValueError("NOT_APPLICABLE requires []")
        if any(not isinstance(step,dict) for step in steps):
            raise ValueError("Every step must be a JSON object")
        if status != "NOT_APPLICABLE" and not steps and not fallback:
            raise ValueError("Applicable cases need grounded steps")
        if status=="COMPLETE" and not any(s.get("operation") in {
                "VERIFY_RECORD_ABSENT","VERIFY_RECORD_REDACTED","VERIFY_RECORD_ANONYMIZED"} for s in steps):
            raise ValueError("COMPLETE needs deletion-state evidence; retained records alone cannot prove deletion")
        seen = set()
        for i, step in enumerate(steps, 1):
            if set(step) != fields or type(step["step_no"]) is not int or step["step_no"] != i:
                raise ValueError("Invalid step fields or numbering")
            if any(not isinstance(step[k], str) for k in fields - {"step_no"}):
                raise ValueError("Step fields must be strings")
            phase, operation = step["phase"], step["operation"]
            if phase not in OPERATIONS or operation not in OPERATIONS[phase] or step["state"] != OPERATIONS[phase][operation]:
                raise ValueError("Invalid phase/operation/state")
            if not step["system_id"] or not step["resource_id"]:
                raise ValueError("Missing resource identity")
            key = phase, operation, step["system_id"], step["resource_id"]
            if key in seen:
                raise ValueError("Duplicate step")
            seen.add(key)
            if fallback:
                cutoff = timestamp(request_index[row["case_id"]]["audit_at"])
                if phase != "VERIFICATION" or step["evidence_id"]:
                    raise ValueError("Fallback may contain only uncited future verification obligations")
                linked = any(o.system_id==step["system_id"] and o.resource_id==step["resource_id"]
                    and timestamp(o.observed_at)<=cutoff and timestamp(o.available_at)<=cutoff for o in observations)
                linked |= any(link.target_system==step["system_id"] and link.target_resource==step["resource_id"]
                    and timestamp(link.observed_at)<=cutoff and timestamp(link.available_at)<=cutoff for link in resource_links)
                if not linked:
                    raise ValueError("Fallback verification lacks an admissible resource anchor")
            required_evidence = phase == "FINDING" or status == "COMPLETE"
            evidence = step["evidence_id"]
            if required_evidence:
                cutoff = timestamp(request_index[row["case_id"]]["audit_at"])
                if evidence not in references or timestamp(references[evidence]) > cutoff:
                    raise ValueError("Unknown or post-cutoff evidence citation")
                # A negative inventory can establish the state of an already
                # identified resource, never manufacture its opaque identity.
                anchors = [o for o in observations if o.system_id==step["system_id"]
                           and o.resource_id==step["resource_id"]
                           and timestamp(o.observed_at)<=cutoff and timestamp(o.available_at)<=cutoff]
                absent_scope = step["state"]=="ABSENT" and any(
                    s.complete and s.evidence_id==evidence and s.system_id==step["system_id"]
                    and step["resource_id"] not in s.resource_ids
                    and timestamp(s.observed_at)<=cutoff and timestamp(s.available_at)<=cutoff
                    and any(o.category==s.category and o.evidence_id==s.evidence_id for o in anchors)
                    for s in scopes)
                if observations and (step["system_id"], step["resource_id"]) not in evidence_resources.get(evidence, set()):
                    if not absent_scope:
                        raise ValueError("Citation does not identify this resource")
                if observations and evidence in sources:
                    supporting = [o for o in observations if o.evidence_id==evidence
                                  and o.system_id==step["system_id"] and o.resource_id==step["resource_id"]
                                  and timestamp(o.observed_at)<=cutoff and timestamp(o.available_at)<=cutoff
                                  and o.state==step["state"]]
                    if not supporting and not absent_scope:
                        raise ValueError("Citation does not prove this state before the cutoff")
            elif evidence:
                raise ValueError("Future remediation/verification must not cite existing evidence")
            if status == "COMPLETE" and phase != "VERIFICATION":
                raise ValueError("COMPLETE may contain only verification")
        if steps != sorted(steps, key=step_key):
            raise ValueError("Steps are not canonically ordered")
        if status == "INCOMPLETE" and not fallback and not all(any(s["phase"] == p for s in steps) for p in OPERATIONS):
            raise ValueError("INCOMPLETE needs findings, remediation, and verification")
        followups = {
            "REPORT_REMAINING_RECORD": ({"DELETE_RECORD"}, "VERIFY_RECORD_ABSENT"),
            "REPORT_EXPOSED_PII": ({"REDACT_RECORD", "ANONYMIZE_RECORD"}, None),
            "REPORT_ACTIVE_DATA_FLOW": ({"DISABLE_DATA_FLOW"}, "VERIFY_DATA_FLOW_DISABLED"),
            "REPORT_RESTORE_RISK": ({"BLOCK_RESTORE"}, "VERIFY_RESTORE_BLOCKED"),
        }
        if status == "INCOMPLETE":
            for finding in (s for s in steps if s["phase"]=="FINDING"):
                actions, check = followups[finding["operation"]]
                matching = [s for s in steps if s["system_id"]==finding["system_id"] and s["resource_id"]==finding["resource_id"]]
                remedies = [s for s in matching if s["phase"]=="REMEDIATION" and s["operation"] in actions]
                if len(remedies)!=1:
                    raise ValueError("Finding requires exactly one corresponding remediation")
                if check is None:
                    check = "VERIFY_RECORD_REDACTED" if remedies[0]["operation"]=="REDACT_RECORD" else "VERIFY_RECORD_ANONYMIZED"
                if not any(s["phase"]=="VERIFICATION" and s["operation"]==check for s in matching):
                    raise ValueError("Remediation lacks its final verification")
            for action in (s for s in steps if s["phase"]=="REMEDIATION"):
                if not any(s["phase"]=="FINDING" and s["system_id"]==action["system_id"]
                           and s["resource_id"]==action["resource_id"] for s in steps):
                    raise ValueError("Remediation has no grounded finding")


def read_output(path: Path) -> list[dict]:
    rows = read_csv(path)
    if rows and tuple(rows[0]) != COLUMNS:
        raise ValueError("Output columns must be case_id,deletion_status,steps_json")
    return [dict(case_id=r["case_id"], deletion_status=r["deletion_status"], steps=json.loads(r["steps_json"])) for r in rows]


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root/"output.csv")
    parser.add_argument("--dataset", type=Path, default=root/"dataset")
    parser.add_argument("--requests", default="deletion_requests.csv")
    parser.add_argument("--fallback-ledger", type=Path, help="Explicit competition-export fallbacks.json; strict validation is the default")
    args = parser.parse_args()
    data = args.dataset
    sources = {r["file_id"]: r for r in read_csv(data/"evidence_files.csv")}
    from evidence import EvidenceStore
    store = EvidenceStore(data, root/".cache", catalog=read_csv(data/"system_activity.csv"))
    validate(read_output(args.output), read_csv(data/args.requests), sources,
             read_csv(data/"system_activity.csv"), read_csv(data/"user_audit_log.csv"), store.observations, store.scopes,
             fallback_case_ids={f["case_id"] for f in json.loads(args.fallback_ledger.read_text())} if args.fallback_ledger else set(),
             resource_links=store.links)
    print(f"Validated {len(read_output(args.output))} rows")


if __name__ == "__main__":
    main()
