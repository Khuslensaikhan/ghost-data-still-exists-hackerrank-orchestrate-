"""Public benchmark: labels are loaded only after the prediction run finishes."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evidence import read_csv
from main import AuditPipeline, ROOT
from schema import OPERATIONS, step_key
from validate_output import read_output
from writer import write_atomic
from evaluation.diagnostics import write_comparisons


def signature(step: dict) -> tuple:
    return tuple((k, step[k]) for k in sorted(step) if k != "step_no")


def score(expected: list[dict], predicted: list[dict]) -> dict:
    pred = {r["case_id"]: r for r in predicted}
    confusion = defaultdict(Counter)
    status_correct = exact = sequence = true_steps = pred_steps = gold_steps = 0
    fields = Counter()
    aligned_total = 0
    missing, extra, mismatches = [], [], []
    for gold in expected:
        actual = pred.get(gold["case_id"])
        status = actual["deletion_status"] if actual else "UNRESOLVED"
        confusion[gold["deletion_status"]][status] += 1
        status_correct += status == gold["deletion_status"]
        gs, ps = gold["steps"], actual["steps"] if actual else []
        ordered = bool(actual) and gs == ps
        sequence += ordered
        exact += ordered and status == gold["deletion_status"]
        gc, pc = Counter(map(signature, gs)), Counter(map(signature, ps))
        true_steps += sum((gc & pc).values())
        pred_steps += len(ps)
        gold_steps += len(gs)
        missing.extend([dict(case_id=gold["case_id"], step=dict(s)) for s in (gc-pc).elements()])
        extra.extend([dict(case_id=gold["case_id"], step=dict(s)) for s in (pc-gc).elements()])
        for i in range(max(len(gs), len(ps))):
            aligned_total += 1
            for field in ("phase", "operation", "system_id", "resource_id", "state", "evidence_id", "step_no"):
                if i < len(gs) and i < len(ps) and gs[i][field] == ps[i][field]:
                    fields[field] += 1
        if not ordered or status != gold["deletion_status"]:
            mismatches.append(dict(case_id=gold["case_id"], expected_status=gold["deletion_status"],
                                   predicted_status=status, expected_steps=len(gs), predicted_steps=len(ps),
                                   missing_steps=sum((gc-pc).values()), extra_steps=sum((pc-gc).values())))
    per_label = {}
    for label in ("COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"):
        tp = confusion[label][label]
        support = sum(confusion[label].values())
        predicted_count = sum(row[label] for row in confusion.values())
        precision = tp/predicted_count if predicted_count else 0
        recall = tp/support if support else None
        per_label[label] = dict(support=support, precision=precision if predicted_count else None,
                               recall=recall, f1=2*precision*recall/(precision+recall) if recall is not None and precision+recall else (0 if support else None))
    def invariant_count(check):
        return sum(check(r["steps"]) for r in predicted)
    count = len(expected)
    return dict(cases=count, resolved=len(predicted), status_accuracy=status_correct/count,
                exact_row_accuracy=exact/count, ordered_sequence_accuracy=sequence/count,
                step_precision=true_steps/pred_steps if pred_steps else 0,
                step_recall=true_steps/gold_steps if gold_steps else 0,
                step_f1=2*true_steps/(pred_steps+gold_steps) if pred_steps+gold_steps else 0,
                correct_steps=true_steps, predicted_steps=pred_steps, expected_steps=gold_steps,
                positional_field_accuracy={k:fields[k]/aligned_total if aligned_total else 0 for k in
                                           ("phase", "operation", "system_id", "resource_id", "state", "evidence_id", "step_no")},
                field_alignment_slots=aligned_total, per_label=per_label,
                confusion_matrix={k:dict(v) for k,v in confusion.items()},
                phase_order_valid=invariant_count(lambda s: [list(OPERATIONS).index(x["phase"]) for x in s] == sorted(list(OPERATIONS).index(x["phase"]) for x in s)),
                canonical_order_valid=invariant_count(lambda s:s == sorted(s,key=step_key)),
                numbering_valid=invariant_count(lambda s:[x["step_no"] for x in s] == list(range(1,len(s)+1))),
                missing_steps=missing, extra_steps=extra, mismatches=mismatches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT/"dataset")
    parser.add_argument("--run-dir", type=Path, default=ROOT/"runs"/"evaluation")
    parser.add_argument("--without-ocr", action="store_true")
    parser.add_argument("--mode", choices=["offline", "model"], default="offline")
    parser.add_argument("--publication", choices=["strict", "competition-export"], default="strict")
    parser.add_argument("--best-effort", action="store_true")
    args = parser.parse_args()
    model = None
    if args.mode == "model":
        import os
        from model_client import ModelClient
        model = ModelClient(ROOT/".cache", model=os.environ.get("AUDIT_MODEL", ""))
    pipeline = AuditPipeline(args.dataset, ROOT/".cache", use_ocr=not args.without_ocr, model=model, best_effort=args.best_effort)
    requests = read_csv(args.dataset/"sample_deletion_requests.csv")
    predictions, unresolved = pipeline.run(requests)
    strict_resolved = len(predictions)
    fallbacks = []
    if args.publication == "competition-export":
        from competition_export import build_export
        predictions, fallbacks = build_export(pipeline, requests, predictions, unresolved)
    expected = read_output(args.dataset/"sample_output.csv")
    metrics = score(expected, predictions)
    metrics["unresolved"] = unresolved
    metrics["publication"] = args.publication
    metrics["strict_resolved"] = strict_resolved
    metrics["fallback_count"] = len(fallbacks)
    metrics["fallback_case_ids"] = [f["case_id"] for f in fallbacks]
    metrics["review_required"] = pipeline.review_required
    metrics["mode"] = args.mode
    metrics["model_events"] = model.events if model else []
    metrics["model_usage"] = {
        "provider_attempts": sum(not e.get("cache_hit", False) for e in metrics["model_events"]),
        "cache_hits": sum(e.get("cache_hit", False) for e in metrics["model_events"]),
        "input_tokens": sum(e.get("input_tokens", 0) for e in metrics["model_events"]),
        "output_tokens": sum(e.get("output_tokens", 0) for e in metrics["model_events"]),
    }
    metrics["extraction_failures"] = [r for r in pipeline.store.coverage if not r["parsed"]]
    manifest = pipeline.store.sources
    subgroups = {}
    for suffix in (".sql", ".json", ".log", ".pdf", ".txt", ".png"):
        cases = [g for g in expected if any(Path(manifest[s["evidence_id"]]["file_path"]).suffix == suffix
                                           for s in g["steps"] if s["evidence_id"] in manifest)]
        if len(cases) >= 3:
            ids = {g["case_id"] for g in cases}
            subgroup = score(cases, [p for p in predictions if p["case_id"] in ids])
            subgroups[suffix] = {k:subgroup[k] for k in ("cases", "resolved", "status_accuracy", "exact_row_accuracy")}
    metrics["modality_subgroups"] = subgroups
    diagnostic_groups = {}
    request_index={r["case_id"]:r for r in requests}
    for gold in expected:
        request=request_index[gold["case_id"]]
        user,_=pipeline.identity.resolve(request["email"],request["audit_at"])
        groups=set()
        if pipeline.identity.history[user]:
            groups.add("historical_identity")
        if any(s["operation"]=="VERIFY_RECORD_PRESENT" for s in gold["steps"]):
            groups.add("retention")
        if any(s["system_id"]=="identity_service" for s in gold["steps"]):
            groups.add("tombstone")
        if any("replica" in manifest.get(s["evidence_id"],{}).get("file_path","") for s in gold["steps"]):
            groups.add("replica_capture")
        for step in gold["steps"]:
            candidates=pipeline.store.by_resource.get((step["system_id"],step["resource_id"]),[])
            groups.update("category:"+o.category for o in candidates)
        for group in groups:
            diagnostic_groups.setdefault(group,[]).append(gold)
    metrics["diagnostic_subgroups"]={}
    metrics["small_subgroup_counts"]={}
    for group,cases in diagnostic_groups.items():
        if len(cases)<3:
            metrics["small_subgroup_counts"][group]=len(cases)
            continue
        ids={g["case_id"] for g in cases}
        group_metrics=score(cases,[r for r in predictions if r["case_id"] in ids])
        metrics["diagnostic_subgroups"][group]={k:group_metrics[k] for k in ("cases","resolved","status_accuracy","exact_row_accuracy")}
    args.run_dir.mkdir(parents=True, exist_ok=True)
    (args.run_dir/"fallbacks.json").write_text(json.dumps(fallbacks, indent=2), encoding="utf-8")
    write_comparisons(expected,predictions,args.run_dir,label="current pipeline")
    write_atomic(args.run_dir/"predictions.csv", predictions)
    (args.run_dir/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in metrics.items() if k not in {"missing_steps","extra_steps","mismatches","unresolved","extraction_failures"}}, indent=2))


if __name__ == "__main__":
    main()
