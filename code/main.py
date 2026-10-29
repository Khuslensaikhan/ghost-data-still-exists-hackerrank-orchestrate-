"""Deletion audit CLI. The prediction path never reads public reference answers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from assessor import account_audit_required, authorized
from evidence import EvidenceStore, read_csv
from identity import IdentityIndex
from planner import plan
from policy import Policy
from schema import UnresolvedCase
from state_resolver import resolve
from validate_output import validate
from writer import write_atomic

ROOT = Path(__file__).resolve().parents[1]


class AuditPipeline:
    def __init__(self, dataset: Path, cache: Path, *, model=None, use_ocr=True, best_effort=False):
        self.dataset, self.model = dataset, model
        self.best_effort = best_effort
        self.review_required: list[dict] = []
        self.users = read_csv(dataset/"user_identities.csv")
        self.audits = read_csv(dataset/"user_audit_log.csv")
        self.activity = read_csv(dataset/"system_activity.csv")
        self.identity = IdentityIndex(self.users, self.audits)
        self.policy = Policy(read_csv(dataset/"deletion_rules.csv"))
        self.store = EvidenceStore(dataset, cache, use_ocr=use_ocr, catalog=self.activity)
        self.traces: list[dict] = []

    def process(self, request: dict) -> dict:
        if not authorized(request["request_text"], self.model):
            self.traces.append(dict(case_id=request["case_id"],status="NOT_APPLICABLE",
                                    assessment="NOT_APPLICABLE",resources=[]))
            return dict(case_id=request["case_id"], deletion_status="NOT_APPLICABLE", steps=[])
        user, values = self.identity.resolve(request["email"], request["audit_at"])
        observations = resolve(self.store, values, request["audit_at"], self.activity)
        trace=dict(case_id=request["case_id"],subject_hash=hashlib.sha256(user.encode()).hexdigest()[:12],
                   status=None,assessment="UNRESOLVED",resources=[
                       dict(system_id=o.system_id,resource_id=o.resource_id,category=o.category,state=o.state,
                            evidence_id=o.evidence_id,observed_at=o.observed_at,available_at=o.available_at,
                            replica=o.replica) for o in observations])
        self.traces.append(trace)
        if self.model:
            candidates = [dict(system_id=o.system_id, resource_id=o.resource_id, evidence_id=o.evidence_id,
                               text=str(o.fields["text"])) for o in observations
                          if "text" in o.fields and o.category in {"SUPPORT_MESSAGE", "ACCOUNT_TOMBSTONE"}]
            if candidates:
                facts = self.model.assess_evidence(candidates)
                updates = {(f.system_id, f.resource_id, f.evidence_id): f for f in facts.facts}
                for observation in observations:
                    key = observation.system_id, observation.resource_id, observation.evidence_id
                    if key in updates and updates[key].pii_exposed != (observation.state=="PRESENT"):
                        raise UnresolvedCase("Semantic interpretation disagrees with extracted PII state; review required")
        status, steps = plan(observations, self.policy, request["audit_at"])
        if status == "COMPLETE" and any(not r["parsed"] for r in self.store.coverage):
            raise UnresolvedCase("Evidence extraction incomplete; completion cannot be established")
        # Compliance of a security ledger alone cannot prove account deletion.
        if status == "COMPLETE" and account_audit_required(request["request_text"]) and not any(o.category=="USER_PROFILE" and o.state=="ABSENT" for o in observations):
            reason = "No subject-linked account absence proof; compliant downstream records or tombstones alone do not establish account deletion"
            raise UnresolvedCase(reason)
        trace.update(status=status,assessment="CONFIRMED_"+status)
        return dict(case_id=request["case_id"], deletion_status=status, steps=steps)

    def run(self, requests: list[dict]) -> tuple[list[dict], list[dict]]:
        rows, unresolved = [], []
        self.traces=[]
        for request in requests:
            try:
                rows.append(self.process(request))
            except UnresolvedCase as error:
                unresolved.append(dict(case_id=request["case_id"], reason=str(error)))
                if not self.traces or self.traces[-1]["case_id"]!=request["case_id"]:
                    self.traces.append(dict(case_id=request["case_id"],status=None,assessment="UNRESOLVED",resources=[]))
                self.traces[-1]["reason"]=str(error)
        return sorted(rows, key=lambda r: r["case_id"]), unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT/"dataset")
    parser.add_argument("--requests", default="deletion_requests.csv")
    parser.add_argument("--output", type=Path, default=ROOT/"output.csv")
    parser.add_argument("--mode", choices=["offline", "model"], default="offline")
    parser.add_argument("--publication", choices=["strict", "competition-export"], default="strict",
                        help="Competition export labels authorized unresolved cases INCOMPLETE, explicitly unverified")
    parser.add_argument("--run-dir", type=Path, default=ROOT/"runs"/"full")
    parser.add_argument("--cache", type=Path, default=ROOT/".cache")
    parser.add_argument("--case", help="One case for a vertical slice")
    parser.add_argument("--without-ocr", action="store_true", help="Coverage ablation only")
    parser.add_argument("--best-effort", action="store_true", help="Legacy inspection flag; never bypasses completion evidence requirements")
    args = parser.parse_args()
    started = time.monotonic()
    model = None
    if args.mode == "model":
        from model_client import ModelClient
        model = ModelClient(args.cache, model=os.environ.get("AUDIT_MODEL", ""),
                            timeout=float(os.environ.get("AUDIT_TIMEOUT", "90")),
                            attempts=int(os.environ.get("AUDIT_ATTEMPTS", "3")))
    pipeline = AuditPipeline(args.dataset, args.cache, model=model, use_ocr=not args.without_ocr, best_effort=args.best_effort)
    requests_path=(args.dataset/args.requests).resolve()
    if not requests_path.is_relative_to(args.dataset.resolve()):
        raise ValueError("Request file must remain inside the participant dataset")
    requests = read_csv(requests_path)
    if args.case:
        requests = [r for r in requests if r["case_id"] == args.case]
        if not requests:
            raise ValueError("Requested case does not exist")
    rows, unresolved = pipeline.run(requests)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    strict_rows = rows
    fallbacks = []
    if unresolved:
        write_atomic(args.run_dir/"resolved_only.csv", strict_rows)
    if args.publication == "competition-export":
        from competition_export import build_export
        rows, fallbacks = build_export(pipeline, requests, strict_rows, unresolved)
        (args.run_dir/"fallbacks.json").write_text(json.dumps(fallbacks, indent=2), encoding="utf-8")
    stats = dict(mode=args.mode, requests=len(requests), resolved=len(rows), unresolved=unresolved,
                 publication=args.publication, strict_resolved=len(strict_rows), exported=len(rows) if args.publication=="competition-export" else 0,
                 fallback_count=len(fallbacks), fallback_case_ids=[f["case_id"] for f in fallbacks],
                 status_counts=dict(Counter(r["deletion_status"] for r in rows)),
                 extraction=pipeline.store.coverage, model_events=model.events if model else [],
                 ocr_calls=pipeline.store.ocr_calls, ocr_cache_hits=pipeline.store.ocr_cache_hits,
                 best_effort=args.best_effort, review_required=pipeline.review_required,
                 plan_coverage_gaps=[dict(case_id=t["case_id"],status=t["status"],
                                         reason="No subject-linked primary account resource ID; verification plan may be incomplete")
                                     for t in pipeline.traces if t["status"]!="NOT_APPLICABLE" and not any(o["category"]=="USER_PROFILE" for o in t["resources"])],
                 output_written=False,
                 duration_seconds=round(time.monotonic()-started, 3))
    (args.run_dir/"run.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    (args.run_dir/"traces.jsonl").write_text("".join(json.dumps(t)+"\n" for t in pipeline.traces), encoding="utf-8")
    if unresolved and args.publication == "strict":
        # This file is explicitly partial and must never replace the submission.
        print(f"{len(rows)}/{len(requests)} resolved; {len(unresolved)} unresolved. Submission not replaced.")
        print(f"Review {args.run_dir/'run.json'}")
        return 2
    validate(rows, requests, pipeline.store.sources, pipeline.activity, pipeline.audits,
             pipeline.store.observations, pipeline.store.scopes,
             fallback_case_ids={f["case_id"] for f in fallbacks}, resource_links=pipeline.store.links)
    write_atomic(args.output, rows)
    stats.update(output_written=True, duration_seconds=round(time.monotonic()-started, 3))
    (args.run_dir/"run.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    if fallbacks:
        print(f"COMPETITION EXPORT: {len(fallbacks)} unverified INCOMPLETE fallbacks; see {args.run_dir/'fallbacks.json'}")
    if pipeline.review_required:
        print(f"BEST-EFFORT INSPECTION OUTPUT: {len(pipeline.review_required)} provisional cases lack account proof.")
    print(f"Wrote and validated {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f"Audit failed: {error}", file=sys.stderr)
        raise SystemExit(2)
