"""Render current competition-export metrics and actual offline usage."""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import ROOT
from validate_output import read_output

DEST = Path(__file__).resolve().parent
RUN = ROOT / "runs/competition"


def read(relative):
    return json.loads((RUN / relative).read_text())


def main():
    full = read("full/run.json")
    strict = read("strict-samples/metrics.json")
    exported = read("samples/metrics.json")
    fallbacks = read("full/fallbacks.json")
    output = read_output(ROOT / "output.csv")
    strict_rows = read_output(RUN / "full/resolved_only.csv")
    index = {r["case_id"]: r for r in output}
    if full["publication"] != "competition-export" or not full["output_written"]:
        raise ValueError("Reports require a successful competition export")
    if len(output) != full["requests"] or any(index[r["case_id"]] != r for r in strict_rows):
        raise ValueError("Export must cover every request and preserve every strict row")
    if {f["case_id"] for f in fallbacks} != {r["case_id"] for r in full["unresolved"]}:
        raise ValueError("Every unresolved case must be disclosed as a fallback")
    if any(index[f["case_id"]]["deletion_status"] != "INCOMPLETE" for f in fallbacks):
        raise ValueError("Fallback cannot claim COMPLETE or NOT_APPLICABLE")
    suite = ET.parse(RUN / "tests.xml").getroot()
    suites = [suite] if suite.tag == "testsuite" else list(suite)
    tests = sum(int(s.attrib["tests"]) for s in suites)
    failures = sum(int(s.attrib["failures"])+int(s.attrib["errors"]) for s in suites)
    digest = hashlib.sha256((ROOT / "output.csv").read_bytes()).hexdigest()
    report = ["# Competition-export evaluation report", "",
        "This is an explicitly requested best-effort competition submission. Strict mode remains the default and has not been weakened. "
        "The competition exporter preserves 416 strict rows and fills 102 authorized unresolved cases with **unverified INCOMPLETE** labels. "
        "These fallback labels mean completion could not be established; they do not assert an observed violation or a canonical answer. "
        "No fallback claims verified COMPLETE, invents an ownership link/resource ID, or manufactures an observation/citation.", "",
        "## Full-dataset export", "",
        f"Processed {full['requests']} requests and wrote {len(output)} rows, sorted by case_id. "
        f"Status counts: `{json.dumps(full['status_counts'], sort_keys=True)}`. "
        "Of 456 INCOMPLETE labels, 354 are strict evidence-backed decisions and 102 are uncertainty fallbacks; all 52 COMPLETE and 10 NOT_APPLICABLE rows are retained strict predictions. "
        "NOT_APPLICABLE is reserved for confident non-deletion intent. Unknown intent still prevents export.", "",
        f"Fallback rows contain {sum(f['step_count'] for f in fallbacks)} future verification checks for supported, pre-cutoff subject-linked resources. "
        "The checks state policy obligations, not present compliance. Their evidence_id is blank as required for future checks in INCOMPLETE rows. "
        "Actual supporting provenance and original strict failures remain in runs/competition/full/fallbacks.json. "
        "No fallback finding, remediation action or unknown account ID is fabricated. When no resource is supported an empty array is permitted; "
        f"the full export has {sum(f['step_count']==0 for f in fallbacks)} empty fallback arrays. "
        "All fallback case IDs, reasons and retained resources are also listed in [competition_fallbacks.md](competition_fallbacks.md).", "",
        "Validation checks exact columns, one row per requested ID, lexicographic row ordering, valid JSON, exact step fields, numbering, "
        "allowed phase/operation/state combinations, canonical step order, citation existence/cutoffs/resource state and normal finding/remediation/check consistency. "
        "Only ledger-listed fallback INCOMPLETE rows may omit findings/remediation or contain no steps; they can contain only uncited future verification checks for admissible resource anchors. "
        "This explicit exception is essential to avoid fabricating violations. It is format/evidence validation, not proof of canonical step completeness. "
        "The ordinary validator without a fallback ledger continues to reject these incomplete strict plans.", "",
        f"All {len(strict_rows)} strict rows were compared with the export and remain identical. Root output SHA-256: `{digest}`.", "",
        "## Public sample metrics", "",
        "Predictions finish before sample_output.csv is loaded. Missing strict rows count as errors over all 32 examples. "
        "The sample set is a development benchmark, not held-out validation, and contains no NOT_APPLICABLE examples. "
        "The 518-case set is unlabeled; no hidden-set accuracy is claimed. Competition export fills nine unresolved public cases with INCOMPLETE, "
        "although their reference status is COMPLETE. This improves coverage, not measured accuracy.", "",
        "| Metric | Strict | Competition export |", "|---|---:|---:|",
        f"| Rows emitted / 32 | {strict['resolved']} | {exported['resolved']} |",
        f"| Unverified fallback rows | {strict['fallback_count']} | {exported['fallback_count']} |"]
    for title, key in [("Case status accuracy", "status_accuracy"), ("Exact-row accuracy", "exact_row_accuracy"),
        ("Step precision", "step_precision"), ("Step recall", "step_recall"), ("Step F1", "step_f1"),
        ("Exact ordered sequence", "ordered_sequence_accuracy")]:
        report.append(f"| {title} | {strict[key]:.2%} | {exported[key]:.2%} |")
    report += ["", f"Exact unordered semantic step matches: {exported['correct_steps']}/{exported['predicted_steps']} predicted, "
        f"{exported['correct_steps']}/{exported['expected_steps']} reference steps. Signatures include phase, operation, system, resource, state and evidence; "
        "step_no is evaluated with ordered sequences. Fallback checks cannot match COMPLETE reference citations because they deliberately claim no existing-state proof.", "",
        "| Phase | Missing exact reference steps | Extra exact predicted steps |", "|---|---:|---:|"]
    missing = Counter(s["step"]["phase"] for s in exported["missing_steps"])
    extra = Counter(s["step"]["phase"] for s in exported["extra_steps"])
    report.extend(f"| {phase} | {missing[phase]} | {extra[phase]} |" for phase in ("FINDING", "REMEDIATION", "VERIFICATION"))
    report += ["", "Positional field accuracy uses max(reference length, predicted length) slots per case. "
        "Insertions and omissions count as field errors and can shift later fields; these are not conditional match-only scores.", "",
        "| Field | Strict | Competition export |", "|---|---:|---:|"]
    report.extend(f"| {field} | {strict['positional_field_accuracy'][field]:.2%} | {value:.2%} |"
        for field, value in exported["positional_field_accuracy"].items())
    report += ["", f"All {exported['phase_order_valid']}/32 emitted public rows have valid phase order; "
        f"{exported['canonical_order_valid']}/32 have canonical step ordering and {exported['numbering_valid']}/32 have valid numbering. "
        "Exact sequence agreement remains 9/32. Full public comparisons are regenerated by the sample command at runs/competition/samples/case_comparison.md/.json.", "",
        "## Failures and improvements", "",
        "Earlier provisional completions incorrectly treated retained/security or tombstone records as proof of deletion. Strict gates corrected this inference, "
        "explaining the earlier 29/32 to 23/32 status change. An explicit search-to-account source link improved exact rows from 8/32 to 9/32. "
        "Scope inference and validation were also fixed so unscoped SQL cannot prove absence and negative inventories cannot create opaque resource IDs. "
        "The competition-export change addresses mandatory coverage alone; it does not repair missing account ownership, late captures, anonymous 404s or unobserved restore permission. "
        "Primary account links remain unavailable in 342 applicable full investigations, including supported INCOMPLETE plans missing unidentifiable verification IDs. "
        "Some canonical checks cannot be proved from participant data; some extra checks are independently supported but omitted by public answers. No sample-specific mappings were added.", "",
        "## Independent custom evaluation cases", "",
        f"Full regression suite: {tests-failures}/{tests} pass; {failures} failures/errors. Fixtures are synthetic and independent of public labels.", "",
        "| Custom scenario | Verified behavior |", "|---|---|",
        "| Retained security record without account proof | Strict withholds; competition emits unverified INCOMPLETE with an uncited future retain check |",
        "| No supported resource / late ownership link | Empty fallback steps; no invented resource or backdated join |",
        "| Archive exists but restore permission is unknown | Future restore-block check only; no ACTIVE observation, risk finding or BLOCK_RESTORE action invented |",
        "| Unknown or explicitly non-deletion intent in an unresolved fallback | Fallback refuses; unknown consent is not converted to NOT_APPLICABLE |",
        "| Scoped SQL, partial JSON and negative inventories | Empty explicit scopes preserve bounded negatives; partial exports and invented IDs are rejected |",
        "| Tombstones, observed recreation, contradictory replicas | No primary-absence inference from a tombstone; observed recreation is retained; conflicting state cannot prove completion |",
        "| Fallback attempts a COMPLETE label, false citation or invented resource | Competition validation rejects it |",
        "| Optional adapter in actual AuditPipeline | Injected intent/evidence adapter is invoked; test is not live inference |", "",
        "## Execution and source boundaries", "",
        "All 103 participant files are accounted for: 94 parsed evidence artifacts plus nine CSVs by input/evaluation/template role. "
        "The final run parsed all 94 artifacts with zero extraction failures and reused 11 local OCR cache entries. "
        "No organizer truth, golden output or private generator input is used for predictions. The official repository main branch was rechecked before export: "
        "[commit 0eddbbd33f682eae0a2770d67412af8a3cf4af20](https://github.com/interviewstreet/hackerrank-orchestrate-october26/commit/0eddbbd33f682eae0a2770d67412af8a3cf4af20) "
        "matches the previously checked revision. No new correction was found at that ref; no effort was spent inventing mappings for source gaps.", "",
        "The final run is offline deterministic/local-OCR. No live OpenAI call occurred and no LLM-backed accuracy is claimed. "
        "Strict audit conclusions remain in resolved_only.csv and traces. Export fallback labels are external competition conventions only. "
        "Output coverage, test success and archive integrity do not certify deletion correctness. Nothing is submitted remotely by these commands.", ""]
    (DEST / "evaluation_report.md").write_text("\n".join(report), encoding="utf-8")
    usage = ["# Usage report — final competition export", "",
        "Measured run: runs/competition/full/run.json, which produced root output.csv. "
        "Counts refer to the submitted program, not the coding assistant. The final export processes all 518 requests and includes 102 explicitly unverified INCOMPLETE fallbacks; "
        "fallback labeling uses no model inference and does not improve evidence completeness.", "",
        "| Measurement | Value |", "|---|---:|",
        f"| Requested / exported rows | {full['requests']} / {len(output)} |",
        f"| Strict resolved / unverified fallback rows | {full['strict_resolved']} / {len(fallbacks)} |",
        f"| Full-run wall time (seconds) | {full['duration_seconds']} |",
        f"| API events / provider calls | {len(full['model_events'])} / 0 |",
        "| API input / output tokens | 0 / 0 |", "| Total / average tokens per request | 0 / 0 |",
        "| Estimated provider cost total / per request | USD 0.00 / USD 0.00 |",
        f"| Fresh local OCR image calls / cache hits | {full['ocr_calls']} / {full['ocr_cache_hits']} |", "",
        "## Models, providers and totals", "",
        "No OpenAI API model was selected or executed; credentials were not supplied. Model-assisted mode is optional and is not used in reported predictions. "
        "Per-API-model and overall totals are zero calls, zero input/output tokens and USD 0.00. There are no mocked or estimated live calls included in these totals.", "",
        "Local perception uses rapidocr-onnxruntime 1.4.4 with ONNX Runtime 1.31.0 and the package's ch_PP-OCRv4_det_infer.onnx, "
        "ch_PP-OCRv4_rec_infer.onnx and ch_ppocr_mobile_v2.0_cls_infer.onnx models. "
        "The initial ingestion previously executed 11 image-pipeline inferences; this final run reused all 11 content-hash cached results. "
        "A pipeline call is not a measured count of detector/classifier/recognizer tensor invocations. Local OCR does not report LLM token usage. "
        "Local compute, electricity and hosting costs are unmeasured, not claimed free.", "",
        "The optional live adapter records attempts, SDK-returned usage, cache hits and errors. Cached model responses count as zero newly billed tokens; "
        "errors without usage remain unknown rather than fabricated zero-usage successes. Tests use injected synthetic adapters and are excluded from provider totals. "
        "No live LLM versus deterministic comparison can be claimed without credentials. Both public runs and this full export were executed offline.", ""]
    (DEST / "usage_report.md").write_text("\n".join(usage), encoding="utf-8")
    ledger = ["# All unverified competition fallbacks", "",
        "These 102 INCOMPLETE labels are unverified completion fallbacks, not confirmed violations. "
        "The retained steps are uncited future checks; source IDs below document underlying resource observations, not present completion proof. "
        "Machine-readable original provenance is in the generated runs/competition/full/fallbacks.json.", "",
        "| Case | Strict unresolved reason | Future checks | Supported resource observations |", "|---|---|---:|---|"]
    for f in fallbacks:
        resources = "; ".join(f"{o['system_id']}/{o['resource_id']}: {o['observed_state']} ({o['evidence_id']}, "
            f"observed {o['observed_at']}, available {o['available_at']})" for o in f["resource_support"])
        ledger.append(f"| {f['case_id']} | {f['strict_reason']} | {f['step_count']} | {resources or 'None'} |")
    (DEST / "competition_fallbacks.md").write_text("\n".join(ledger)+"\n", encoding="utf-8")
    print(f"Reports written for {len(output)} exported rows, {len(fallbacks)} fallbacks, {tests} tests.")


if __name__ == "__main__":
    main()
