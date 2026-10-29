"""One-to-one step diagnostics, independent of prediction and policy logic."""
from __future__ import annotations

import json
from pathlib import Path


FIELDS=("phase","operation","system_id","resource_id","state","evidence_id")


def compare_case(expected: dict, actual: dict | None) -> dict:
    gold=expected["steps"];pred=actual["steps"] if actual else []
    remaining_gold=set(range(len(gold)));remaining_pred=set(range(len(pred)))
    pairs=[]
    # Match semantic equals first so an insertion or a reorder is not mislabeled
    # as an operation/resource mismatch. Then pair shared resources, followed by
    # shared operations, with deterministic minimum field difference.
    stages=[FIELDS,("phase","system_id","resource_id"),("phase","operation","system_id"),
            ("phase","operation","resource_id")]
    for keys in stages:
        options=[]
        for g in remaining_gold:
            for p in remaining_pred:
                if all(gold[g][k]==pred[p][k] for k in keys):
                    cost=sum(gold[g][k]!=pred[p][k] for k in FIELDS)
                    options.append((cost,abs(g-p),g,p))
        for _,__,g,p in sorted(options):
            if g in remaining_gold and p in remaining_pred:
                pairs.append((g,p));remaining_gold.remove(g);remaining_pred.remove(p)
    mismatches={field:[] for field in FIELDS}
    for g,p in sorted(pairs):
        for field in FIELDS:
            if gold[g][field]!=pred[p][field]:
                mismatches[field].append(dict(expected_step=g+1,predicted_step=p+1,
                                              expected=gold[g][field],predicted=pred[p][field]))
    indices=[p for g,p in sorted(pairs)]
    return dict(case_id=expected["case_id"],expected_status=expected["deletion_status"],
                predicted_status=actual["deletion_status"] if actual else "UNRESOLVED",
                status_correct=bool(actual) and expected["deletion_status"]==actual["deletion_status"],
                exact_row=bool(actual) and expected==actual,
                missing_steps=[gold[g] for g in sorted(remaining_gold)],
                extra_steps=[pred[p] for p in sorted(remaining_pred)],mismatches=mismatches,
                aligned_pairs=[dict(expected_step=g+1,predicted_step=p+1) for g,p in sorted(pairs)],
                relative_order_wrong=indices!=sorted(indices),
                numbering_wrong=[s["step_no"] for s in pred]!=list(range(1,len(pred)+1)))


def describe(step: dict) -> str:
    return f"{step['phase']} / {step['operation']} / {step['system_id']} / {step['resource_id']} / {step['state']} / {step['evidence_id'] or '(future)'}"


def write_comparisons(expected: list[dict],predictions: list[dict],destination: Path,*,label: str):
    index={r["case_id"]:r for r in predictions}
    comparisons=[compare_case(g,index.get(g["case_id"])) for g in expected]
    text=[f"# Public case-by-case comparison — {label}","",
          "All 32 examples are included. Step alignment matches exact semantic steps before pairing a shared resource or operation. Missing/extra counts below exclude paired field mismatches; the benchmark's raw multiset missing/extra counts include them. This diagnostic alignment does not affect predictions or scores.","",
          "| Case | Reference → prediction | Exact row | Missing | Extra | Wrong operation | Resource ID | State | Evidence ID | Order |",
          "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for c in comparisons:
        m=c["mismatches"]
        ordering="n/a" if c["predicted_status"]=="UNRESOLVED" else "wrong" if c["relative_order_wrong"] else "valid"
        text.append(f"| {c['case_id']} | {c['expected_status']} → {c['predicted_status']} | {'yes' if c['exact_row'] else 'no'} | {len(c['missing_steps'])} | {len(c['extra_steps'])} | {len(m['operation'])} | {len(m['resource_id'])} | {len(m['state'])} | {len(m['evidence_id'])} | {ordering} |")
    for c in comparisons:
        text += ["",f"## {c['case_id']}","",f"Status: {c['expected_status']} → {c['predicted_status']}; exact row: {c['exact_row']}.",""]
        for key,title in (("missing_steps","Missing steps"),("extra_steps","Extra steps")):
            text.append(title+":")
            text.append("")
            text.extend("- "+describe(s) for s in c[key])
            if not c[key]:text.append("None.")
            text.append("")
        changes=[f"{field}: expected step {m['expected_step']} / predicted step {m['predicted_step']}: `{m['expected']}` → `{m['predicted']}`"
                 for field,items in c["mismatches"].items() for m in items]
        text += ["Paired field mismatches:",""]+(["- "+change for change in changes] if changes else ["None."])
    destination.mkdir(parents=True,exist_ok=True)
    (destination/"case_comparison.md").write_text("\n".join(text)+"\n",encoding="utf-8")
    (destination/"case_comparison.json").write_text(json.dumps(comparisons,indent=2),encoding="utf-8")
    return comparisons
