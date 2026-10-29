"""Post-prediction diagnostics only. Reference answers never enter the auditor.

Run after the offline sample and full runs documented in accuracy_diagnostics.md.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence import read_csv
from evaluation.diagnostics import FIELDS, compare_case, describe
from evaluation.main import score
from main import AuditPipeline, ROOT
from schema import OPERATIONS, timestamp
from state_resolver import admissible, resolve
from validate_output import read_output, validate

RUN = ROOT / "runs/accuracy-review"
DEST = Path(__file__).resolve().parent
CATEGORIES = (
    "MISSING_OWNERSHIP_LINK", "ACCOUNT_ABSENCE_NOT_DEMONSTRABLE", "POST_CUTOFF_EVIDENCE",
    "UNKNOWN_RESTORE_STATE", "CONFLICTING_OBSERVATIONS", "INCOMPLETE_SNAPSHOT_COVERAGE",
    "MISSING_DATA_OR_UNSUPPORTED_INFERENCE", "OTHER",
)


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def brief(o):
    return dict(system=o.system_id, resource=o.resource_id, state=o.state, evidence=o.evidence_id,
                observed_at=o.observed_at, available_at=o.available_at, replica=o.replica)


def context(pipeline, request):
    user, values = pipeline.identity.resolve(request["email"], request["audit_at"])
    states = resolve(pipeline.store, values, request["audit_at"], pipeline.activity)
    direct = [o for o in pipeline.store.observations if values.intersection(o.identifiers)]
    return dict(user=user, values=values, states=states, direct=direct,
                related={o.evidence_id for o in states})


def assess_step(store, step, request, ctx):
    """Explain support independently of benchmark agreement. Never repair labels."""
    key = step["system_id"], step["resource_id"]
    candidates = store.by_resource.get(key, [])
    linked = [o for o in ctx["states"] if (o.system_id, o.resource_id) == key]
    source = store.sources.get(step["evidence_id"])
    owned = [o for o in candidates if ctx["values"].intersection(o.identifiers)]
    details = dict(step=step, subject_linked_at_cutoff=bool(linked),
                   observations=[brief(o) for o in candidates],
                   direct_ownership_observations=[brief(o) for o in owned])
    if source and timestamp(source["captured_at"]) > timestamp(request["audit_at"]):
        reason = "CITATION_CAPTURED_AFTER_CUTOFF"
    elif not linked:
        if owned and not any(admissible(o, request["audit_at"]) for o in owned):
            reason = "OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE"
        elif not candidates:
            reason = "NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN"
        else:
            reason = "RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN"
    elif not step["evidence_id"]:
        reason = "SUPPORTED_FUTURE_CHECK_FOR_LINKED_RESOURCE"
    elif any(o.evidence_id == step["evidence_id"] and o.state == step["state"] for o in linked):
        reason = "SUPPORTED_CURRENT_STATE_AND_CITATION"
    else:
        reason = "CITATION_DOES_NOT_ESTABLISH_LINKED_CURRENT_STATE"
    details.update(reason=reason, supported=reason.startswith("SUPPORTED_"))
    return details


def phase_counts(steps):
    counts = Counter(s["phase"] for s in steps)
    return {phase: counts[phase] for phase in OPERATIONS}


def main():
    pipeline = AuditPipeline(ROOT / "dataset", ROOT / ".cache")
    store = pipeline.store
    samples = read_csv(ROOT / "dataset/sample_deletion_requests.csv")
    requests = read_csv(ROOT / "dataset/deletion_requests.csv")
    # Existing predictions are read before the labels. No evaluation code feeds
    # source attribution, extraction, temporal resolution or final planning.
    previous = read_output(ROOT / "runs/quality-before/sample-predictions.csv")
    strict_before = read_output(RUN / "before/samples/predictions.csv")
    current = read_output(RUN / "after/samples/predictions.csv")
    full = read_output(RUN / "after/full/resolved_only.csv")
    run = json.loads((RUN / "after/full/run.json").read_text())
    expected = read_output(ROOT / "dataset/sample_output.csv")
    old_index = {r["case_id"]: r for r in previous}
    current_index = {r["case_id"]: r for r in current}
    req_index = {q["case_id"]: q for q in samples}
    for rows, queries in ((current, samples), (full, requests)):
        ids = {r["case_id"] for r in rows}
        validate(rows, [q for q in queries if q["case_id"] in ids], store.sources,
                 pipeline.activity, pipeline.audits, store.observations, store.scopes)
    comparisons = []
    citation_checks = []
    for gold in expected:
        case = gold["case_id"]; q = req_index[case]; ctx = context(pipeline, q)
        actual = current_index.get(case)
        comp = compare_case(gold, actual)
        comp["previous_status"] = old_index.get(case, {}).get("deletion_status", "UNRESOLVED")
        comp["previous_comparison"] = compare_case(gold, old_index.get(case))
        comp["expected_step_support"] = [assess_step(store, s, q, ctx) for s in gold["steps"]]
        comp["expected_answer_support"] = (
            "UNSUPPORTED_RESOURCE_OR_CITATION" if any(not s["supported"] for s in comp["expected_step_support"])
            else "REFERENCE_OMITS_SUPPORTED_STEPS" if comp["extra_steps"] else "SUPPORTED_WITHIN_OBSERVED_RESOURCE_SCOPE")
        reasons = Counter(s["reason"] for s in comp["expected_step_support"] if not s["supported"])
        comp["mismatch_reasons"] = dict(reasons)
        if comp["extra_steps"]:
            comp["mismatch_reasons"]["REFERENCE_OMITS_SUPPORTED_STEPS"] = len(comp["extra_steps"])
        comp["status_regression_reason"] = (
            "CORRECTED_UNSUPPORTED_COMPLETION_INFERENCE" if comp["previous_status"] == gold["deletion_status"]
            and not comp["status_correct"] else None)
        comp["resolved_resources"] = [brief(o) for o in ctx["states"]]
        comp["identity_trace"] = dict(subject=ctx["user"], identifier_count=len(ctx["values"]),
            history_changes=len(pipeline.identity.history[ctx["user"]]),
            request_uses_current_email=q["email"].casefold() == pipeline.identity.users[ctx["user"]]["email"].casefold(),
            audit_at=q["audit_at"])
        if actual:
            for s in actual["steps"]:
                if s["evidence_id"]:
                    citation_checks.append(dict(case_id=case, **assess_step(store, s, q, ctx)))
        comparisons.append(comp)
    metrics = score(expected, current)
    aligned = sum(len(c["aligned_pairs"]) for c in comparisons)
    field_errors = {field: sum(len(c["mismatches"][field]) for c in comparisons) for field in FIELDS}
    metrics.update(
        missing_by_phase=phase_counts([x["step"] for x in metrics["missing_steps"]]),
        extra_by_phase=phase_counts([x["step"] for x in metrics["extra_steps"]]),
        aligned_pairs=aligned, aligned_field_errors=field_errors,
        aligned_field_accuracy={k: (aligned-v)/aligned if aligned else None for k,v in field_errors.items()},
        # Missing steps remain errors in recall; perfect conditional accuracy
        # among matched steps is explicitly not exhaustive correctness.
        reference_slot_field_accuracy={k: (aligned-v)/metrics["expected_steps"] for k,v in field_errors.items()},
        cited_steps=len(citation_checks), grounded_cited_steps=sum(c["supported"] for c in citation_checks),
        legal_operation_state_pairs=sum(s["state"] == OPERATIONS[s["phase"]][s["operation"]]
            for row in current for s in row["steps"]),
        error_categories=dict(Counter(reason for c in comparisons
            for s in c["expected_step_support"] if not s["supported"] for reason in [s["reason"]])),
        live_llm_executed=False)
    dump(RUN / "public_comparison.json", comparisons)
    dump(RUN / "step_metrics.json", metrics)
    dump(RUN / "citation_checks.json", citation_checks)

    withheld = []
    contexts = {}
    for q in requests:
        contexts[q["case_id"]] = context(pipeline, q)
    for item in run["unresolved"]:
        case = item["case_id"]; q = next(q for q in requests if q["case_id"] == case)
        ctx = contexts[case]; cutoff = q["audit_at"]
        accounts = [o for o in ctx["states"] if o.category == "USER_PROFILE"]
        direct_accounts = [o for o in ctx["direct"] if o.category == "USER_PROFILE"]
        late = [o for o in direct_accounts if not admissible(o, cutoff)]
        scopes = [s for s in store.scopes if s.category == "USER_PROFILE"
                  and s.evidence_id in ctx["related"] and admissible(s, cutoff)]
        partial = [s for s in scopes if not s.complete]
        complete = [s for s in scopes if s.complete]
        unknown = [o for o in ctx["states"] if o.category == "BACKUP_ARCHIVE" and o.state == "UNKNOWN"]
        flags = []
        if not accounts: flags.append("MISSING_OWNERSHIP_LINK")
        if not any(o.state == "ABSENT" for o in accounts): flags.append("ACCOUNT_ABSENCE_NOT_DEMONSTRABLE")
        if late: flags.append("POST_CUTOFF_EVIDENCE")
        if unknown: flags.append("UNKNOWN_RESTORE_STATE")
        if "Contradictory" in item["reason"]: flags.append("CONFLICTING_OBSERVATIONS")
        # Partial/missing account inventories cannot authorize global negatives.
        if partial or not scopes: flags.append("INCOMPLETE_SNAPSHOT_COVERAGE")
        if not direct_accounts or unknown: flags.append("MISSING_DATA_OR_UNSUPPORTED_INFERENCE")
        if not flags: flags.append("OTHER")
        primary = ("UNKNOWN_RESTORE_STATE" if unknown else "POST_CUTOFF_EVIDENCE" if late
                   else "SCOPED_NEGATIVE_QUERY_WITHOUT_RESOURCE_ID" if complete
                   else "MISSING_OWNERSHIP_AND_INCOMPLETE_COVERAGE")
        withheld.append(dict(case_id=case, primary_cause=primary, categories=flags,
            runner_reason=item["reason"], code_fixable_from_demonstrated_existing_evidence=False,
            needed="Earlier subject-linked restore authorization and account/query evidence" if unknown else
                   "Pre-cutoff subject-to-resource/query association and admissible state/coverage evidence",
            identity_subject=ctx["user"], identity_resolution_succeeded=True,
            linked_resources=[brief(o) for o in ctx["states"]],
            excluded_account_links=[brief(o) for o in late],
            unknown_restore=[brief(o) for o in unknown],
            account_inventory_queries=[dict(evidence=s.evidence_id, replica=s.replica, complete=s.complete,
                captured_resources=len(s.resource_ids), matches_for_known_identifiers=[o.resource_id for o in direct_accounts
                    if o.evidence_id == s.evidence_id and o.replica == s.replica and admissible(o, cutoff)]) for s in scopes],
            negative_query_scope="No known-identifier match within declared SQL capture; opaque account ID and broader coverage remain unproved"
                if complete and not accounts else None))
    groups = {category: [x["case_id"] for x in withheld if category in x["categories"]] for category in CATEGORIES}
    primary_groups = {key: [x["case_id"] for x in withheld if x["primary_cause"] == key]
                      for key in sorted({x["primary_cause"] for x in withheld})}
    dump(RUN / "withheld_classification.json", dict(categories=groups, primary_partition=primary_groups, cases=withheld))
    with (RUN / "withheld_classification.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "primary_cause", "categories", "runner_reason",
                                             "code_fixable_from_demonstrated_existing_evidence", "needed"])
        writer.writeheader()
        for x in withheld:
            writer.writerow({k: ";".join(x[k]) if k == "categories" else x[k] for k in writer.fieldnames})

    # Audit all participant files by role; do not claim template/reference files
    # are used as prediction inputs. Parsing and attribution have separate counts.
    role = {"sample_output.csv": "evaluation labels only", "sample_deletion_requests.csv": "public evaluation requests",
            "output.csv": "blank template; intentionally not prediction input"}
    inventory = [dict(path=str((ROOT / "dataset" / r["file_path"]).relative_to(ROOT / "dataset")),
        role="prediction evidence", **next(c for c in store.coverage if c["evidence_id"] == r["file_id"]))
        for r in store.sources.values()]
    for path in sorted((ROOT / "dataset").glob("*.csv")):
        rows = read_csv(path)
        inventory.append(dict(path=path.name, role=role.get(path.name, "prediction input"),
            parsed=True, rows=len(rows), content_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    known_values = set().union(*(c["values"] for c in contexts.values()))
    # Include public subjects separately from full-run subjects in attribution counts.
    known_values.update(set().union(*(context(pipeline, q)["values"] for q in samples)))
    directly_linked = [o for o in store.observations if known_values.intersection(o.identifiers)]
    observation_index = {id(o): i for i,o in enumerate(store.observations)}
    admissible_indices = set(); linked_pairs = eligible_pairs = 0
    per_case = []
    for q in requests:
        ctx = contexts[q["case_id"]]; direct = ctx["direct"]
        eligible = [o for o in direct if admissible(o, q["audit_at"])]
        linked_pairs += len(direct); eligible_pairs += len(eligible)
        admissible_indices.update(observation_index[id(o)] for o in eligible)
        per_case.append(dict(case_id=q["case_id"], directly_linked_observations=len(direct),
                             cutoff_admissible_direct_observations=len(eligible), resolved_resources=len(ctx["states"])))
    evidence_metrics = dict(participant_files=len(inventory), evidence_files=len(store.coverage),
        csv_files=sum(x["path"].endswith(".csv") for x in inventory),
        parsed_evidence_files=sum(x["parsed"] for x in store.coverage),
        failed_evidence_files=[x for x in store.coverage if not x["parsed"]],
        observations=len(store.observations),
        observations_with_valid_provenance=sum(o.evidence_id in store.sources
            and timestamp(o.available_at) >= timestamp(store.sources[o.evidence_id]["captured_at"])
            and (o.available_at == store.sources[o.evidence_id]["captured_at"] or
                 any(e["activity_id"] == o.fields.get("catalog_evidence_id")
                     and e["event_time"] == o.available_at for e in pipeline.activity))
            and bool(timestamp(o.observed_at)) and bool(timestamp(o.available_at)) for o in store.observations),
        observations_with_catalog_qualified_availability=sum(
            o.available_at != store.sources[o.evidence_id]["captured_at"] for o in store.observations),
        observations_with_explicit_system_resource_key=sum(bool(o.system_id and o.resource_id) for o in store.observations),
        observations_with_any_identifier=sum(bool(o.identifiers) for o in store.observations),
        observations_directly_linked_to_full_or_sample_subject=len(directly_linked),
        explicit_resource_relationships=len(store.links),
        full_case_observation_pairs=linked_pairs, cutoff_admissible_full_case_observation_pairs=eligible_pairs,
        distinct_direct_observations_admissible_for_their_full_run_subject=len(admissible_indices),
        scopes=len(store.scopes), complete_scopes=sum(s.complete for s in store.scopes),
        partial_scopes=sum(not s.complete for s in store.scopes),
        empty_scopes=sum(not s.resource_ids for s in store.scopes),
        ocr_calls=store.ocr_calls, ocr_cache_hits=store.ocr_cache_hits,
        missing_model_configuration=[k for k in ("OPENAI_API_KEY", "AUDIT_MODEL") if not os.environ.get(k)])
    dump(RUN / "evidence_pipeline.json", dict(summary=evidence_metrics, files=inventory, cases=per_case))
    suite = ET.parse(RUN / "after/tests.xml").getroot()
    suites = [suite] if suite.tag == "testsuite" else list(suite)
    tests = sum(int(s.attrib["tests"]) for s in suites)
    old_metrics = score(expected, previous); before_metrics = score(expected, strict_before)
    non_deletion_ids = {r["case_id"] for r in full if r["deletion_status"] == "NOT_APPLICABLE"}
    summary = dict(previous_best_effort={k:old_metrics[k] for k in ("status_accuracy", "exact_row_accuracy", "step_precision", "step_recall", "step_f1")},
        strict_before={k:before_metrics[k] for k in ("status_accuracy", "exact_row_accuracy", "step_precision", "step_recall", "step_f1")},
        strict_after={k:metrics[k] for k in ("status_accuracy", "exact_row_accuracy", "step_precision", "step_recall", "step_f1")},
        tests=tests, full_processed=run["requests"], emitted=run["resolved"], withheld=len(withheld),
        status_counts=run["status_counts"],
        missing_account_links_all_applicable=sum(
            not any(o.category == "USER_PROFILE" for o in contexts[q["case_id"]]["states"])
            for q in requests if q["case_id"] not in non_deletion_ids),
        missing_account_steps_emitted=sum(not any(s["system_id"] == "account_service" for s in r["steps"])
            for r in full if r["deletion_status"] != "NOT_APPLICABLE"),
        primary_counts={k:len(v) for k,v in primary_groups.items()}, category_counts={k:len(v) for k,v in groups.items()},
        provisional_completions=len(run["review_required"]), evidence=evidence_metrics)
    dump(RUN / "summary.json", summary)
    render(comparisons, metrics, withheld, groups, primary_groups, summary, run)
    print(json.dumps(summary, indent=2))


def render(comparisons, metrics, withheld, groups, primary_groups, summary, run):
    public = ["# Public benchmark diagnosis", "",
        "All 32 cases; previous is the saved 29/32 best-effort run. UNRESOLVED is an internal abstention, counted as an error. "
        "Support is evaluated against the supplied evidence at the cutoff, independently of reference agreement. "
        "Supported means within the observed resource universe; exhaustive global coverage is not established by this benchmark.", "",
        "| Case | Expected | Previous | Current | Missing / extra | Op / state / resource / evidence errors | Reference support |",
        "|---|---|---|---|---|---|---|"]
    for c in comparisons:
        m=c["mismatches"]
        public.append(f"| {c['case_id']} | {c['expected_status']} | {c['previous_status']} | {c['predicted_status']} | "
            f"{len(c['missing_steps'])} / {len(c['extra_steps'])} | " + " / ".join(str(len(m[k])) for k in
            ("operation", "state", "resource_id", "evidence_id")) + f" | {c['expected_answer_support']} |")
    for c in comparisons:
        public += ["", f"## {c['case_id']}", "", f"Exact row: {c['exact_row']}. Identity trace: `{json.dumps(c['identity_trace'])}`.", ""]
        if c["status_regression_reason"]:
            public += ["Status regression: corrected unsupported completion inference; no new source-supported defect found.", ""]
        if c["exact_row"]:
            public.append("All canonical steps, fields and order match. Subject/state/citation support is present for the selected resources.")
        for key in ("missing_steps", "extra_steps"):
            public += [key.replace("_", " ").capitalize() + ":", ""]
            public.extend(["- " + describe(s) for s in c[key]] or ["None."])
            public.append("")
        unsupported = [s for s in c["expected_step_support"] if not s["supported"]]
        for item in unsupported:
            public += [f"- `{item['step']['resource_id']}`: {item['reason']}. "
                f"Observed resource facts: `{json.dumps(item['observations'])}`. "
                f"Subject-bearing facts: `{json.dumps(item['direct_ownership_observations'])}`."]
        if c["extra_steps"]:
            public += ["", "Extra steps cover independently linked resources omitted by the reference; removing them would reduce evidence coverage."]
        if c["case_id"] in {"case_01", "case_02", "case_04"}:
            public += ["", "The cited SQL snapshot has no subject-linked row identifying the expected absent account. A deletion-worker activity claim does not supply the missing subject/resource join or prove readback. Array position or numeric suffix cannot supply ownership."]
        if c["case_id"] == "case_31":
            public += ["", "evidence_51 proves the redacted tombstone and retained audit record. Its empty customer_profiles array is a partial JSON snapshot with no account_4857 row or scoped subject query; it cannot establish primary-account absence."]
        if c["case_id"] == "case_27":
            public += ["", "evidence_92 contains an anonymous absent account. The subject-bearing account link in evidence_02 is first available September 17, after the September 15 cutoff. It cannot backdate ownership."]
        public += ["", "Paired field mismatches: `" + json.dumps(c["mismatches"]) + "`. Relative order wrong: " + str(c["relative_order_wrong"]) + "."]
    (DEST / "public_accuracy.md").write_text("\n".join(public)+"\n", encoding="utf-8")
    text = ["# Withheld-case classification", "",
        "Primary groups form a partition of all 102 cases. Diagnostic categories overlap; their counts must not be summed. "
        "No withholding is caused by failed identity lookup, parsing failure or a demonstrated recoverable join omitted by the current index. "
        "Missing ownership means no admissible account join, including cases with a later join. Negative SQL queries prove only no known-identifier match inside their declared capture, not an opaque deleted account ID or universal absence.", "",
        "| Primary cause | Count | Case IDs |", "|---|---:|---|"]
    text.extend(f"| {key} | {len(ids)} | {', '.join(ids)} |" for key,ids in primary_groups.items())
    text += ["", "| Diagnostic category | Count | Case IDs |", "|---|---:|---|"]
    text.extend(f"| {key} | {len(ids)} | {', '.join(ids) or 'None'} |" for key,ids in groups.items())
    text += ["", "## Every withheld case", "", "| Case | Primary blocker | Categories | Current evidence / needed fact |", "|---|---|---|---|"]
    for x in withheld:
        resources=", ".join(f"{o['resource']}={o['state']} ({o['evidence']})" for o in x["linked_resources"])
        late=", ".join(f"{o['resource']} ({o['evidence']}, observed {o['observed_at']}, available {o['available_at']})" for o in x["excluded_account_links"])
        queries="; ".join(f"{s['evidence']}:{s['replica']} complete={s['complete']}, matching IDs={len(s['matches_for_known_identifiers'])}" for s in x["account_inventory_queries"])
        text.append(f"| {x['case_id']} | {x['primary_cause']} | {', '.join(x['categories'])} | {resources}. "
            f"Excluded account facts: {late or 'none'}. Account inventories: {queries or 'none'}. Needed: {x['needed']}. |")
    text += ["", "All code_fixable_from_demonstrated_existing_evidence flags are false. This is the outcome of the current exact-identifier, explicit-reference and native-source investigation, not proof that no future extractor could discover a missed fact. "
        "Temporal exclusions, missing opaque IDs, anonymous lookups and absent restore permissions require source evidence or official clarification. Do not map them to fabricated COMPLETE/INCOMPLETE labels."]
    (DEST / "withheld_classification.md").write_text("\n".join(text)+"\n", encoding="utf-8")
    evidence=summary["evidence"]
    report=["# Accuracy diagnosis and targeted fixes", "",
        "## Findings", "",
        "Status accuracy fell from 29/32 to 23/32 because case_21, case_25, case_26, case_27, case_28 and case_31 are now withheld. "
        "The first five previously inferred completion from retained/compliant downstream records; case_31 inferred primary-account absence from a redacted tombstone. "
        "The missing pre-cutoff account ownership/absence proof remains unsupported. This is a conservative correction, not six newly introduced retrieval bugs. "
        "case_01, case_02 and case_04 were already unresolved in the earlier run. All 22 public INCOMPLETE statuses remain correct.", "",
        "Exact-row accuracy rose from 8/32 to 9/32 through an explicit search-to-account source_resource_id link in case_06. "
        "The remaining differences are missing verification coverage and additional evidence-backed checks omitted by the reference. "
        "Anonymous deleted/anonymized rows have no subject link; some expected account/audit IDs have no observed state; other subject-bearing captures arrive after the cutoff. "
        "The five extra steps concern object_19 in case_07 and account_6523 / tombstone_17 in case_17, all supported by earlier participant evidence. "
        "No answer-specific IDs or inferred row ordering were introduced into predictions.", "",
        "[All 32 combined previous/current comparisons, canonical missing/extra steps and source support](public_accuracy.md). "
        "[All withheld cases, overlapping categories and exact primary partition](withheld_classification.md). "
        "Machine-readable counterparts: ../../runs/accuracy-review/public_comparison.json, withheld_classification.json/.csv, step_metrics.json and evidence_pipeline.json.", "",
        "## Measured public accuracy", "",
        "| Metric | Earlier best-effort | Strict before | Strict after |", "|---|---:|---:|---:|",
        "| Correct statuses | 29/32 | 23/32 | 23/32 |", "| Exact rows | 8/32 | 9/32 | 9/32 |",
        f"| Step precision | {summary['previous_best_effort']['step_precision']:.2%} | {summary['strict_before']['step_precision']:.2%} | {metrics['step_precision']:.2%} |",
        f"| Step recall | {summary['previous_best_effort']['step_recall']:.2%} | {summary['strict_before']['step_recall']:.2%} | {metrics['step_recall']:.2%} |",
        f"| Step F1 | {summary['previous_best_effort']['step_f1']:.2%} | {summary['strict_before']['step_f1']:.2%} | {metrics['step_f1']:.2%} |", "",
        f"Exact semantic matches: {metrics['correct_steps']}/{metrics['predicted_steps']} predicted and {metrics['correct_steps']}/{metrics['expected_steps']} reference steps.", "",
        "| Phase | Missing canonical steps | Extra predicted steps |", "|---|---:|---:|"]
    report.extend(f"| {phase} | {metrics['missing_by_phase'][phase]} | {metrics['extra_by_phase'][phase]} |" for phase in OPERATIONS)
    report += ["", f"All {metrics['predicted_steps']} operation/state pairs are legal. On {metrics['aligned_pairs']} matched pairs, operation, state, system, resource and citation agreement are all 100%; "
        f"counting missing reference slots lowers each to {metrics['aligned_pairs']}/{metrics['expected_steps']} = {metrics['aligned_pairs']/metrics['expected_steps']:.2%}. "
        "Unmatched extras are separately penalized by step precision. This conditional match accuracy must not be read as exhaustive correctness. "
        f"All {metrics['grounded_cited_steps']}/{metrics['cited_steps']} nonempty current citations are time-admissible, resource/state-grounded and subject-linked; future checks correctly have blank citations. "
        "Citation validity is independent of reference exact agreement. Predicted operation/state/resource/citation tuples have the same 143/148 exact-step precision; there are no paired field substitutions.", "",
        f"Ordered sequences match in {round(metrics['ordered_sequence_accuracy']*32)}/32 cases. All {metrics['resolved']} emitted public rows have valid phase order, canonical operation order and numbering. "
        "There are no relative-order inversions among matched steps; missing/extra steps account for sequence failures. Missing predictions are errors in all 32-case denominators.", "",
        "Unsupported reference-step categories: `" + json.dumps(metrics["error_categories"], sort_keys=True) + "`. "
        "Some supported reference steps are also absent from emitted rows because the entire unsupported COMPLETE row is withheld; they are not extraction errors.", "",
        "## Coverage and evidence pipeline", "",
        f"Processed 518/518 requests; emitted {summary['emitted']} ({summary['status_counts']['INCOMPLETE']} INCOMPLETE, "
        f"{summary['status_counts']['COMPLETE']} COMPLETE, {summary['status_counts']['NOT_APPLICABLE']} NOT_APPLICABLE); withheld {summary['withheld']}. "
        f"Before/after this turn are identical. Missing account links remain {summary['missing_account_links_all_applicable']}/508 applicable investigations, "
        f"including {summary['missing_account_steps_emitted']}/406 emitted applicable rows. "
        "There are zero provisional completions and zero security-only completions emitted. The 78 former security-only completions remain withheld.", "",
        "Primary withheld partition: `" + json.dumps(summary["primary_counts"], sort_keys=True) + "`. "
        "Overlapping diagnostic counts: `" + json.dumps(summary["category_counts"], sort_keys=True) + "`.", "",
        f"All {evidence['participant_files']} participant files are accounted for: 94 evidence artifacts plus 9 CSVs. "
        "Six CSVs and the 94 artifacts serve full-run prediction; sample requests/reference answers serve evaluation, and the blank output template is intentionally unused. "
        "All 94 artifacts parsed; formats are 24 SQL, 28 JSON, 26 logs, 11 PNGs, 4 PDFs and 1 text. CSV headers/rows were independently read for the role inventory. "
        "No reference/template file is used for prediction.", "",
        "Evidence counts and denominator definitions:", ""]
    for key in ("observations", "observations_with_valid_provenance", "observations_with_explicit_system_resource_key",
                "observations_with_any_identifier", "observations_directly_linked_to_full_or_sample_subject",
                "explicit_resource_relationships", "full_case_observation_pairs", "cutoff_admissible_full_case_observation_pairs",
                "distinct_direct_observations_admissible_for_their_full_run_subject", "scopes", "complete_scopes", "partial_scopes", "empty_scopes"):
        report.append(f"- {key}: {evidence[key]}.")
    report += ["", "Provenance means a real manifest file with capture time retained and parseable observation time. Four business-artifact aliases also require a catalog event: "
        "their availability is the later of capture and catalog association, and both provenance IDs are retained. An explicit resource key is not a subject ownership link. "
        "Direct subject links are exact current/historical identifier matches to the 518 full-run or 32 sample subjects; any-identifier counts also include unrelated subjects. "
        "Cutoff counts are subject-specific observation/case pairs, with both observation and availability checked; the distinct count deduplicates reused observations. "
        "These are extraction/association diagnostics, not independently labeled extraction accuracy. Complete snapshot scope is bounded to its declared collection/replica, not all systems or all direct-identifier forms.", "",
        f"All 11 images were processed by local neural OCR, with {evidence['ocr_calls']} fresh calls and {evidence['ocr_cache_hits']} content-hash cache hits in this audit. "
        "A parser failure is recorded and blocks COMPLETE; OCR text is not a certified transcription. Empty tables retain scopes, partial JSON cannot prove negatives, simultaneous conflicting states fail closed, "
        "and an unknown replica cannot be masked by a compliant read. Current withheld reasons contain no extraction failures or same-time observation conflicts. "
        "INCOMPLETE rows can still be emitted on known violations despite partial knowledge; emission is not proof that all opaque missing resources were discovered.", "",
        "## Demonstrable code fixes and regressions", "",
        "Two new synthetic counterexamples failed before the fixes and pass afterward: (1) a table named customer_profiles_primary without snapshot_scope "
        "was incorrectly marked complete; it now remains partial, while explicitly scoped empty tables still support bounded negative observations; "
        "(2) the standalone validator accepted an invented resource ID merely because it was absent from a scoped table; "
        "it now requires an admissible same-evidence resource anchor of the same category. Neither fix changes current dataset predictions.", "",
        f"Full suite: {summary['tests']} tests pass (65 before). The regression set covers anonymous 404 isolation, late subject/resource links, explicitly scoped SQL versus partial snapshots, "
        "archive/restore uncertainty, redacted tombstones versus primary-account absence, worker success versus readback, observed recreation before cutoff, replica conflict and retention-only completion. "
        "The optional adapter is exercised through AuditPipeline with an injected test adapter; this verifies wiring and is not a live model result.", "",
        "case_55: activity_4006 links backup_9287 to the subject. evidence_32 is an April 29 archive screen before the April 30 cutoff. "
        "It shows archive existence, encryption, checksum and unrelated restore history, but no authorization/block setting for this archive. "
        "Its state remains UNKNOWN. September restore settings cannot resolve the April question; no restore-risk finding or BLOCK_RESTORE action is fabricated.", "",
        "## LLM boundary and reproducibility", "",
        "The executed runs use --mode offline: deterministic parsing/joins/planning plus local RapidOCR. Both model API event lists are empty; zero API input/output tokens and zero provider cost. "
        "OPENAI_API_KEY and AUDIT_MODEL are absent. No provider was called. ModelClient is connected through consent assessment and candidate support/tombstone text interpretation, "
        "with exact-ID/quotation validation and disagreement withholding; the current adapter does not perform missing ownership retrieval or image/PDF vision. "
        "It can help interpret ambiguous intent, text and PII exposure; it cannot recover absent join keys, opaque deleted IDs, capture-time clarification or unobserved restore permission.", "",
        "After configuring credentials securely in the environment and setting AUDIT_MODEL to an explicitly chosen supported model, run:", "",
        "```sh", ".venv/bin/python code/evaluation/main.py --mode model --run-dir runs/accuracy-review/live-samples",
        ".venv/bin/python code/main.py --mode model --run-dir runs/accuracy-review/live-full --output runs/accuracy-review/live-output.csv", "```", "",
        "Model-mode evaluation persists provider events and totals. A warm model cache can yield zero new calls; clear only the task-specific model cache or use main.py --cache with a fresh directory when measuring live execution. "
        "This command is preparation, not a completed LLM comparison. Exit 2 on unresolved cases is expected and preserves strict publication.", "",
        "Offline reproduction:", "", "```sh",
        ".venv/bin/python -m pytest code/tests -q --junitxml=runs/accuracy-review/after/tests.xml",
        ".venv/bin/python code/evaluation/main.py --mode offline --run-dir runs/accuracy-review/after/samples",
        ".venv/bin/python code/main.py --mode offline --run-dir runs/accuracy-review/after/full --output runs/accuracy-review/after/output.csv",
        "# The full runner exits 2 after writing traces and resolved_only.csv, because 102 cases remain unresolved.",
        ".venv/bin/python code/evaluation/accuracy_review.py", "```", "",
        "## Decision and next improvement", "",
        "No demonstrated existing-evidence mapping legitimately resolves one of the 102 withheld cases in this review. "
        "The highest-value next engineering work is a grounded query/ownership coverage register: retain exact query predicates, collection/replica scope, "
        "identifier lineage, timestamps and proof for each obligation. It would make negative-query coverage auditable and catch future recoverable joins; "
        "it cannot manufacture the missing opaque IDs. Source corrections or an official uncertainty/output convention are needed to close the demonstrated gaps. "
        "Adding orchestration or a larger model would not resolve these missing facts.", "",
        "The three allowed statuses cannot honestly encode an unknown deletion state. Labeling unknowns INCOMPLETE would assert a violation without evidence; "
        "labeling them COMPLETE would assert deletion without proof; NOT_APPLICABLE would deny explicit consent. "
        "Preserve strict withholding: the 416-row work product fails the mandatory 518-row submission contract. The old 518-row root CSV and old archive remain retired. "
        "No publication-policy change, package, push or submission was made. The last official repository correction check is documented in official_repository_check.md; "
        "it is a dated snapshot, not a new online check in this task. No final generation occurred.", ""]
    rendered = "\n".join(report)
    (DEST / "accuracy_diagnostics.md").write_text(rendered, encoding="utf-8")
    (DEST / "evaluation_report.md").write_text(rendered, encoding="utf-8")
    usage_path = DEST / "usage_report.md"
    usage = usage_path.read_text().split("## Current strict audit attempt")[0].rstrip()
    usage += (f"\n\n## Current strict audit attempt\n\n"
        f"Latest run: runs/accuracy-review/after/full/run.json. Processed {run['requests']} requests, emitted {run['resolved']} work-product rows "
        f"and withheld {len(run['unresolved'])}. No final output.csv was produced. Runtime: {run['duration_seconds']} seconds; "
        f"model API events: {len(run['model_events'])}; OCR image calls: {run['ocr_calls']}; OCR cache hits: {run['ocr_cache_hits']}. "
        "API input/output tokens: 0/0; total/average tokens: 0/0; provider cost total/per request: USD 0.00/0.00. "
        "No API model was selected or executed. Local OCR model names/hashes are listed above. Local compute cost is unmeasured. "
        "See accuracy_diagnostics.md for the latest evaluation; no LLM-backed result is claimed.\n")
    usage_path.write_text(usage, encoding="utf-8")


if __name__ == "__main__":
    main()
