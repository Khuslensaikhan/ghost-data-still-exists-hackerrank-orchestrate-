"""Render measured run artifacts directly into submission-visible Markdown."""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEST=Path(__file__).resolve().parent


def read(relative):
    return json.loads((ROOT/relative).read_text())


def percent(value):
    return "n/a" if value is None else f"{value:.2%}"


def write_reports():
    if (ROOT/"runs/competition/full/run.json").exists():
        sys.path.insert(0,str(ROOT/"code"))
        from evaluation.competition_report import main
        main()
        return
    if (ROOT/"runs/accuracy-review/after/full/run.json").exists():
        sys.path.insert(0,str(ROOT/"code"))
        from evaluation.accuracy_review import main
        main()
        return
    if (ROOT/"runs/quality-after/full/run.json").exists():
        sys.path.insert(0,str(ROOT/"code"))
        from evaluation.quality_review import investigate
        investigate()
        return
    strict=read("runs/evaluation/metrics.json")
    best=read("runs/evaluation-best-effort/metrics.json")
    ablation=read("runs/ablation-no-ocr/metrics.json")
    full=read("runs/best-effort/run.json")
    suites=ET.parse(ROOT/"runs/tests.xml").getroot()
    suites=[suites] if suites.tag=="testsuite" else list(suites)
    tests=sum(int(s.attrib.get("tests",0)) for s in suites)
    failures=sum(int(s.attrib.get("failures",0))+int(s.attrib.get("errors",0)) for s in suites)
    report=["# Evaluation report", "",
            "The current 518-row output is an explicitly authorized **best-effort inspection artifact**, not a verified final submission. The default strict run withholds unsupported completions. All figures below come from executed runs; no hidden evaluation answers were accessed.", "",
            "## Methodology", "",
            "Predictions are generated from participant-facing sources before loading the public sample answers. Missing/unresolved predictions count as errors in status and exact-row accuracy. Exact row match requires both status and the complete ordered step array. Unordered step precision/recall compare multisets of all six semantic fields (excluding numbering); array order is scored separately. Positional field accuracy aligns each ordered array by index and counts missing/extra slots as incorrect. These strict metrics expose omitted verification resources; label accuracy alone does not.", "",
            "The 32 samples are a development benchmark used during implementation, not a held-out test. They contain no NOT_APPLICABLE labels. Custom consent tests cover that gap. No accuracy is claimed on the unlabeled 518 requests.", "",
            "## Executed configurations", "", "| Metric | Strict + neural OCR | Best-effort + neural OCR | Strict, OCR disabled |", "|---|---:|---:|---:|"]
    for title,key in [("Resolved cases","resolved"),("Status accuracy","status_accuracy"),("Exact row accuracy","exact_row_accuracy"),
                      ("Exact ordered-array accuracy","ordered_sequence_accuracy"),("Step precision","step_precision"),("Step recall","step_recall")]:
        values=[str(m[key]) if key=="resolved" else percent(m[key]) for m in (strict,best,ablation)]
        report.append(f"| {title} | {' | '.join(values)} |")
    report += ["",f"Best-effort matched {best['correct_steps']}/{best['expected_steps']} reference steps and emitted {best['predicted_steps']} steps. Missing steps: {len(best['missing_steps'])}; extra steps: {len(best['extra_steps'])}.", "",
               "OCR ablation disables all 11 images, so it changes extraction coverage and can trigger the conservative completeness gate. Its status delta is not evidence that every additional OCR interpretation is correct. No secondary auditor, autonomous-loop, live LLM or VLM ablation was run. Missing subject/resource links cannot be supplied by model interpretation alone.", "",
               "## Per-label results: best-effort", "", "| Label | Support | Precision | Recall | F1 |", "|---|---:|---:|---:|---:|"]
    for label,row in best["per_label"].items():
        report.append(f"| {label} | {row['support']} | {percent(row['precision'])} | {percent(row['recall'])} | {percent(row['f1'])} |")
    supported=[r["f1"] for r in best["per_label"].values() if r["support"]]
    report += ["",f"Macro F1 over labels with sample support: {percent(sum(supported)/len(supported))}.", "",
               "Confusion matrix (unresolved is an evaluator diagnostic, not a submission status):", "",
               "| Reference | COMPLETE | INCOMPLETE | NOT_APPLICABLE | UNRESOLVED |", "|---|---:|---:|---:|---:|"]
    for label in ("COMPLETE","INCOMPLETE","NOT_APPLICABLE"):
        row=best["confusion_matrix"].get(label,{})
        report.append(f"| {label} | {' | '.join(str(row.get(k,0)) for k in ('COMPLETE','INCOMPLETE','NOT_APPLICABLE','UNRESOLVED'))} |")
    report += ["", "## Field and sequence results", "", "| Positional field | Accuracy |", "|---|---:|"]
    for field,value in best["positional_field_accuracy"].items():
        report.append(f"| {field} | {percent(value)} |")
    report += ["",f"Field denominator: {best['field_alignment_slots']} aligned step slots. Among {best['resolved']} emitted sample rows, phase order, operation/system/resource order, and consecutive numbering each passed on {best['phase_order_valid']}, {best['canonical_order_valid']}, and {best['numbering_valid']} rows respectively. These structural checks do not establish semantic correctness.", "",
               "## Diagnostic groups", "", "Groups can overlap. Numeric subgroups require at least three labeled cases; even these counts are too small for reliable generalization.", "",
               "| Group | Cases | Resolved | Status accuracy | Exact row accuracy |", "|---|---:|---:|---:|---:|"]
    for group,row in (best["modality_subgroups"]|best.get("diagnostic_subgroups",{})).items():
        report.append(f"| {group} | {row['cases']} | {row['resolved']} | {percent(row['status_accuracy'])} | {percent(row['exact_row_accuracy'])} |")
    report += ["", "Insufficiently populated groups: "+", ".join(f"{k} (n={v})" for k,v in sorted(best.get("small_subgroup_counts",{}).items()))+". No standalone tombstone accuracy is inferred from two examples.", "",
               "## Independent synthetic tests", "",f"Executed pytest result: **{tests-failures}/{tests} passing**, {failures} failures/errors. These are custom cases encoded in Python, not copied sample labels.", "",
               "| Custom scenario | Expected result |", "|---|---|",
               "| Non-deletion, correction, access and marketing-only consent | NOT_APPLICABLE; no destructive plan |",
               "| Historical email plus similar unrelated email and future phone change | Exact historical subject; decoy/future value excluded |",
               "| Deletion followed by synchronization readback before cutoff | INCOMPLETE; latest present state wins |",
               "| Primary absent, regional replica present | Replica remains a finding |",
               "| Tombstone retains stable user reference only | REDACTED; hash/name/email/phone exposure fails compliance |",
               "| Active connector and unsafe backup alongside profile | Disable flow and block restore before record changes |",
               "| Security and legal records under retention | Preserve; verify presence |",
               "| Later capture, later event or later catalog association | Excluded from earlier audit |",
               "| Partial snapshot omission | Does not prove record absence |",
               "| Model invents ID, omits grounding, refuses or retries | Reject invalid output; record attempts and known/unknown usage |",
               "| Atomic write fails | Preserve existing output |",
               "| Temporary full dataset integration | COMPLETE, INCOMPLETE and NOT_APPLICABLE round-trip through CSV and validation |", "",
               "## Observed failures and improvements", "",
               "An initial identifier parser scanned Python dictionary representations and admitted an apostrophe into email tokens. Structured recursive extraction fixed the association loss; a regression test covers it. Operational-history JSON collections needed a dedicated decoder. Cloud message escaping, bracketed logs, pipe logs, syslog and trace-correlated lookups are covered by synthetic format tests.", "",
               "OCR initially associated all visible table rows with a selected customer. Extraction now restricts content to the selected header/detail/row and permits catalog aliases only for the relevant artifact origin. Catalog-derived observations use the later source availability time. Regression guards cover future links and exact identities. These corrections increased the measured strict benchmark from an early 6/32 resolvable rows to the strict result above; no complete metrics were retained for that initial six-row pass, so no invented before/after accuracy is supplied.", "",
               "case_05 was run as a real vertical slice and matched its three-step public reference. Its failover profile remains present despite the successful workflow claim. The final best-effort output does not read or reuse sample answers.", "",
               "Remaining errors are dominated by missing subject links for absent accounts and anonymized analytics records. The code does not pair unlabeled records by array position, numeric suffix, case family or golden answers. Some older participant-supported records create extra steps relative to the public reference (for example an object-store attachment and a stable retained reference). These disagreements are documented rather than hidden by case-specific exclusions.", "",
               "## Full-dataset run and limitations", "",
               f"The final executed offline best-effort run processed {full['requests']} requests and wrote {full['resolved']} rows. Status counts: "+", ".join(f"{k}={v}" for k,v in sorted(full["status_counts"].items()))+".", "",
               f"{len(full['review_required'])} COMPLETE labels are provisional because account-state proof is missing. {len(full.get('plan_coverage_gaps',[]))} plans have no linked primary-account resource ID, including cases whose INCOMPLETE status is supported but whose verification plan can be incomplete. All are listed in review_required.md. No hidden-set status, step or sequence accuracy can be measured.", "",
               f"Extraction coverage: {sum(r['parsed'] for r in full['extraction'])}/{len(full['extraction'])} files parsed; parse failures: {sum(not r['parsed'] for r in full['extraction'])}. Parsing an artifact is not exhaustive semantic understanding. OCR ID confidence is checked, but some PII/state interpretation remains heuristic. Names, addresses, indirect identifiers, conditional policy variants outside the supplied corpus, and noisy/scanned PDFs need further semantic validation. Unknown or expired policy conditions fail closed rather than inventing a treatment.", "",
               "Optional OpenAI integration passed injected-client contract tests only. Credentials were unavailable, so no live provider, live multilingual semantic ablation, provider cost benchmark or model reproducibility claim is made. The publication decision is explicitly best-effort; the production-quality definition of done has not been met.", ""]
    package_check=ROOT/"runs/package_verification.json"
    if package_check.exists():
        check=json.loads(package_check.read_text())
        report += ["## Packaged-source replay", "",
                   f"Extracted the archive to an isolated temporary directory and ran its source against the participant dataset. It produced {check['rows']} rows, byte-identical to root output.csv (SHA-256 {check['output_sha256']}). The run reused the warm OCR cache and existing Python environment; this is not a cold dependency installation or live-provider test. Archive exclusions and required report paths were also checked.", ""]
    (DEST/"evaluation_report.md").write_text("\n".join(report),encoding="utf-8")

    rows=["# Review required — inspection output", "",
          "`output.csv` contains 518 structurally valid best-effort rows. It is not a verified submission. No absent/anonymized resource was assigned to a subject using numeric patterns or public answers.", "",
          "## Provisional COMPLETE labels", "",
          f"{len(full['review_required'])} cases contain only observed-resource compliance; account proof is missing:", "",
          ", ".join(r["case_id"] for r in full["review_required"]), "",
          "## Missing primary-account resource links in plans", "",
          "These are verification-plan coverage warnings, not proof that the account still exists. Some cases have a permitted tombstone instead. INCOMPLETE cases can have correct findings and still omit unidentifiable account verification IDs.", ""]
    for status in ("COMPLETE","INCOMPLETE"):
        group=[r["case_id"] for r in full.get("plan_coverage_gaps",[]) if r["status"]==status]
        rows += [f"{status}: {len(group)} cases", "", ", ".join(group), ""]
    rows += ["## Concrete source gaps", "",
             "Public sample case_01 asks for an absence verification on account_001, but the SQL capture evidence_54 contains no row associating that resource with the request's subject. Its activity is a deletion claim without a subject identifier. The pipeline does not derive an account ID from a case/user number.", "",
             "Public case_26 requires account_5684 and analytics_4566. In evidence_92 the absent profile and anonymized analytics records have no subject identifiers. The historical account link appears in evidence_02, whose manifest capture is 2026-09-17, after the case's 2026-09-15 cutoff. The strict pipeline excludes that later capture. Similar gaps affect other absent and anonymized resources. A person-to-resource catalog or query provenance captured by the cutoff would resolve the association without exposing PII in a retained record.", "",
             "The current problem statement was fetched from the official repository and matches the local Git blob hash 31a6bc69ff0b22a211710d0e5b4cbc23577a9e6a. The code follows both observation-time and manifest-availability cutoffs. An official clarification of capture semantics or corrected participant-visible mappings would be needed before relaxing that rule.", "",
             "Next improvement: obtain participant-visible, pre-cutoff resource/query associations and run the configured live intent/semantic model with credentials. Re-run the strict benchmark and complete-flow checks before treating a best-effort CSV as submission-ready.", ""]
    (DEST/"review_required.md").write_text("\n".join(rows),encoding="utf-8")

    events=full["model_events"]
    calls=[e for e in events if not e["cache_hit"]]
    inputs=sum(e["input_tokens"] for e in events);outputs=sum(e["output_tokens"] for e in events)
    usage=["# Usage report — final full-dataset run", "",
           "This report describes the executed offline best-effort run that wrote root output.csv, not the development assistant's token usage. Runtime data comes from runs/best-effort/run.json. The output remains an inspection artifact with the limitations in review_required.md.", "",
           "| Measurement | Observed value |", "|---|---:|",
           f"| Requests / rows written | {full['requests']} / {full['resolved']} |",
           f"| Provisional COMPLETE labels | {len(full['review_required'])} |",
           f"| Wall time, seconds | {full['duration_seconds']} |",
           f"| Provider API attempts | {len(calls)} |",
           f"| Model-response cache hits | {sum(e['cache_hit'] for e in events)} |",
           f"| API input / output tokens | {inputs} / {outputs} |",
           f"| Total API tokens | {inputs+outputs} |",
           f"| Average API tokens per requested case | {(inputs+outputs)/full['requests']:.6f} |",
           f"| Neural OCR image pipeline calls in final run | {full['ocr_calls']} |",
           f"| Neural OCR image cache hits in final run | {full['ocr_cache_hits']} |",
           "| API retries / failures | 0 / 0 |", "| Case execution | Sequential, one case at a time |", "",
           "## Model providers and exact models", "",
           "The final run used cached local RapidOCR perception; all 11 images had been inferred during development and were cache hits in the final run. The first ingestion executed 11 image-pipeline inferences. This count is per image pipeline, not an invented count of detector/classifier/recognizer tensor batches. There were no API calls in development or the final audit run.", "",
           "Local provider/runtime: RapidOCR 1.4.4 with ONNX Runtime 1.31.0. Models installed with the package:", "",
           "| Model | SHA-256 |", "|---|---|"]
    import importlib.util
    package=Path(importlib.util.find_spec("rapidocr_onnxruntime").origin).parent
    for model in sorted(package.rglob("*.onnx")):
        usage.append(f"| {model.name} | {hashlib.sha256(model.read_bytes()).hexdigest()} |")
    usage += ["", "Neural OCR operates on image tensors and does not report LLM input/output tokens. API input/output totals are zero; local tensor work is not falsely converted to tokens. Per-stage ONNX execution counts were not instrumented. No exact OpenAI runtime model was selected or called: optional model mode requires AUDIT_MODEL and OPENAI_API_KEY. Mock-client tests use an explicitly synthetic model label and are excluded from all usage totals.", "",
              "## Cost and accounting", "",
              "Estimated provider API cost: **USD 0.00 total; USD 0.00 per request**, because zero provider requests occurred. No token-price assumption is needed for zero requests. CPU time, electricity and environment hosting cost were not measured and are not claimed to be free. No live-model cost estimate or per-provider price is fabricated.", "",
              "The optional model client records every explicit attempt, SDK-returned input/output/cache tokens, retry and cache hit. Calls with no returned usage remain marked unknown. Cache reads count as zero new API tokens. A future live run must regenerate this report with provider-specific prices and cached-token rates; the current renderer intentionally reports only this measured offline configuration.", "",
              "Overall totals for this run: zero API calls, zero API tokens, zero newly executed OCR image calls, 11 OCR cache hits. Across initial extraction: 11 local image-pipeline calls. No autonomous loop or secondary auditor ran.", ""]
    if calls:
        raise ValueError("Live model calls require a per-model pricing/accounting renderer; do not reuse the offline cost statements")
    (DEST/"usage_report.md").write_text("\n".join(usage),encoding="utf-8")
    print(f"Wrote measured reports to {DEST}")


if __name__=="__main__":
    write_reports()
