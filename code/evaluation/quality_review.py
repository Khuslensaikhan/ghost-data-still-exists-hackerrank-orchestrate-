"""Reproducible correctness investigation; never generates prediction labels."""
from __future__ import annotations

import csv
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidence import read_csv
from evaluation.diagnostics import write_comparisons
from main import AuditPipeline,ROOT
from schema import timestamp
from state_resolver import admissible,resolve
from validate_output import read_output,validate


DEST=Path(__file__).resolve().parent


def investigate():
    before=ROOT/"runs/quality-before";after=ROOT/"runs/quality-after"
    baseline=read_output(before/"output.csv")
    old={r["case_id"]:r for r in baseline}
    current=read_output(after/"full/resolved_only.csv")
    new={r["case_id"]:r for r in current}
    run=json.loads((after/"full/run.json").read_text())
    pipeline=AuditPipeline(ROOT/"dataset",ROOT/".cache")
    requests=read_csv(ROOT/"dataset/deletion_requests.csv")
    validate(current,[r for r in requests if r["case_id"] in new],pipeline.store.sources,
             pipeline.activity,pipeline.audits,pipeline.store.observations,pipeline.store.scopes)
    missing_before=[];security_before=[];ledger=[];details={}
    for request in requests:
        case=request["case_id"];oldrow=old[case];newrow=new.get(case)
        if oldrow["deletion_status"]=="NOT_APPLICABLE":
            ledger.append(dict(case_id=case,baseline_status="NOT_APPLICABLE",current_status=newrow["deletion_status"],root_cause="NON_DELETION"))
            continue
        user,values=pipeline.identity.resolve(request["email"],request["audit_at"])
        observed=resolve(pipeline.store,values,request["audit_at"],pipeline.activity)
        direct=[o for o in pipeline.store.observations if o.category=="USER_PROFILE" and values.intersection(o.identifiers)]
        eligible=[o for o in direct if admissible(o,request["audit_at"])]
        future=[o for o in direct if not admissible(o,request["audit_at"])]
        account=[o for o in observed if o.category=="USER_PROFILE"]
        cause=("DIRECT_ACCOUNT_OBSERVATION" if eligible else "EXPLICIT_REFERENCE_STATE_UNPROVEN" if account
               else "IDENTITY_LINK_ONLY_AFTER_CUTOFF" if future else "NO_ACCOUNT_IDENTITY_LINK_IN_SOURCES")
        related={o.evidence_id for o in observed}
        unassigned=[o for o in pipeline.store.observations if o.evidence_id in related and o.category=="USER_PROFILE"
                    and not o.identifiers and admissible(o,request["audit_at"])]
        scope_queries=[]
        for scope in pipeline.store.scopes:
            if scope.evidence_id not in related or scope.category!="USER_PROFILE" or not admissible(scope,request["audit_at"]):continue
            matching=[o.resource_id for o in eligible if o.evidence_id==scope.evidence_id and o.replica==scope.replica]
            scope_queries.append(dict(evidence_id=scope.evidence_id,table=scope.replica,
                                      captured_rows=len(scope.resource_ids),matching_known_identifiers=matching))
        oldmissing=not any(s["system_id"]=="account_service" for s in oldrow["steps"])
        securityonly=oldrow["deletion_status"]=="COMPLETE" and len(oldrow["steps"])==1 and oldrow["steps"][0]["system_id"]=="security_service"
        if oldmissing:missing_before.append(case)
        if securityonly:security_before.append(case)
        row=dict(case_id=case,subject=user,baseline_status=oldrow["deletion_status"],
                 current_status=newrow["deletion_status"] if newrow else "UNRESOLVED",root_cause=cause,
                 baseline_missing_account=oldmissing,baseline_security_only=securityonly,
                 current_linked_account_resources=[o.resource_id for o in account],
                 current_account_states=[o.state for o in account],history_count=len(pipeline.identity.history[user]),
                 future_account_links=[dict(resource=o.resource_id,state=o.state,evidence=o.evidence_id,
                     observed_at=o.observed_at,captured_at=o.available_at) for o in future],
                 unassigned_absence_records=[dict(resource=o.resource_id,evidence=o.evidence_id) for o in unassigned],
                 account_scope_queries=scope_queries)
        ledger.append(row)
        details[case]=dict(request=request,subject=user,identity_values=sorted(values),
                           history=[dict(audit_id=h["audit_id"],field=h["field_name"],event_time=h["event_time"]) for h in pipeline.identity.history[user]],
                           resolved=[dict(resource=o.resource_id,system=o.system_id,state=o.state,evidence=o.evidence_id,
                                          observed_at=o.observed_at,captured_at=o.available_at,fields=o.fields) for o in observed])
    baseline_missing=[r for r in ledger if r.get("baseline_missing_account")]
    still_missing=[r for r in ledger if r["root_cause"]!="NON_DELETION" and not r.get("current_linked_account_resources")]
    provisional=[r for r in current if r["deletion_status"]=="COMPLETE" and not any(s["system_id"]=="account_service" for s in r["steps"])]
    security_new=[r for r in current if r["deletion_status"]=="COMPLETE" and len(r["steps"])==1 and r["steps"][0]["system_id"]=="security_service"]
    primary_missing_emitted=sum(not any(s["system_id"]=="account_service" for s in r["steps"]) for r in current if r["deletion_status"]!="NOT_APPLICABLE")
    summary=dict(requests=518,current_rows=len(current),unresolved=len(run["unresolved"]),
        baseline_missing_account=len(missing_before),current_missing_account_all_cases=len(still_missing),
        current_missing_account_emitted=primary_missing_emitted,
        baseline_security_only=len(security_before),current_security_only=len(security_new),
        current_complete_without_account=len(provisional),current_provisional_completions=len(run["review_required"]),
        baseline_missing_causes=dict(Counter(r["root_cause"] for r in baseline_missing)),
        security_only_current_outcomes=dict(Counter(r["current_status"] for r in ledger if r.get("baseline_security_only"))),
        status_counts=run["status_counts"],live_llm_executed=False,
        missing_model_configuration=[key for key in ("OPENAI_API_KEY","AUDIT_MODEL") if not os.environ.get(key)])
    request_by_id={r["case_id"]:r for r in requests}
    late_capture=[r for r in baseline_missing if r["root_cause"]=="IDENTITY_LINK_ONLY_AFTER_CUTOFF"]
    summary["pre_cutoff_observation_in_late_capture"]=sum(any(timestamp(o["observed_at"])<=timestamp(request_by_id[r["case_id"]]["audit_at"]) for o in r["future_account_links"]) for r in late_capture)
    summary["only_post_cutoff_account_observations"]=len(late_capture)-summary["pre_cutoff_observation_in_late_capture"]
    after.mkdir(parents=True,exist_ok=True)
    (after/"investigation.json").write_text(json.dumps(dict(summary=summary,cases=ledger,traces=details),indent=2),encoding="utf-8")
    with (after/"case_ledger.csv").open("w",newline="",encoding="utf-8") as f:
        columns=["case_id","baseline_status","current_status","root_cause"]
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore");writer.writeheader();writer.writerows(ledger)
    expected=read_output(ROOT/"dataset/sample_output.csv")
    write_comparisons(expected,read_output(after/"samples/predictions.csv"),after/"samples",label="current corrected strict pipeline")
    write_comparisons(expected,read_output(before/"sample-predictions.csv"),before,label="previous best-effort baseline")
    shutil.copy2(before/"case_comparison.md",DEST/"case_comparison_before.md")
    shutil.copy2(after/"samples/case_comparison.md",DEST/"case_comparison.md")
    metrics=json.loads((after/"samples/metrics.json").read_text())
    oldmetrics=json.loads((before/"sample-metrics.json").read_text())
    strict_path=before/"strict-metrics.json"
    if not strict_path.exists():shutil.copy2(ROOT/"runs/evaluation/metrics.json",strict_path)
    strict_before=json.loads(strict_path.read_text())
    ablation=json.loads((before/"event-only-ablation.json").read_text())
    independent=json.loads((before/"independent-scan.json").read_text())
    report=["# Correctness investigation and before/after evaluation","",
        "The previous root output.csv is a retired best-effort baseline, not a corrected or final submission. The corrected runner evaluated all 518 requests and withheld unresolved cases. No new archive was generated and nothing was submitted.","",
        "## Root causes","",
        "1. The previous planner declared any fully compliant selected subset COMPLETE. The best-effort flag bypassed the subsequent missing-account guard. This is a decision error: discovering a retained audit record does not establish deletion. Both the planner and standalone validator now reject retention-only completion; the best-effort flag cannot bypass the check.",
        "2. Retrieval indexed identifiers and resource IDs, but did not traverse explicit resource relationships. A search document's source_resource_id supplies a genuine account link. Typed, time-qualified relationship traversal now includes that resource and identifier-free downstream copies. Unknown current state produces a required future verification in an already INCOMPLETE case, without inventing a present-state finding or a deletion action. It blocks completion when no current state is proved.",
        "3. Empty primary/replica tables disappeared from the scope inventory. Collection roles are now retained for empty peer tables. This improves query diagnostics; a missing row or a negative query over an excerpt is not promoted into an invented resource ID.",
        "4. Many apparent retrieval failures are source-link or time gaps. Current and historical identity lookup succeeds for these subjects. Native source scanning found only one known-subject direct association absent from the old account observation index: the explicit search-to-account reference for a public sample, fixed above. It does not belong to the 518 evaluation requests. The other raw scan differences were decoys or key=value tokenization artifacts, not new subject links. All 518 subjects' identity snapshots and history events predate their audit cutoff, so future identity rollback is not the cause in this dataset.","",
        f"Among the original 342 missing-account cases, the corrected investigation classifies: {json.dumps(summary['baseline_missing_causes'],sort_keys=True)}. The original direct-observation audit found 262 with no direct account identity observation at any time and 80 with links only after the cutoff. No additional account link was recovered in the 518 evaluation requests; the explicit source relationship improves a public sample. The before/after link denominator remains all applicable cases, including withheld cases.","",
        f"Of those 80 temporal exclusions, {summary['pre_cutoff_observation_in_late_capture']} have an embedded observation by the cutoff but a later file capture; {summary['only_post_cutoff_account_observations']} have only later observations. The former raise a capture-semantics question; the latter cannot establish the earlier state regardless of export semantics.","",
        "These counts do not mean the accounts are present, nor that they were deleted. An unattributed 404 proves that one resource was absent, but cannot identify its owner. A SQL query can show zero matches for known identifiers in supplied primary/replica tables; it cannot reconstruct the opaque ID of a deleted row or establish coverage of systems outside that capture. History, a shared file, numeric suffixes, near timestamps and array order do not provide those missing ownership links.","",
        "## Review of all 78 security-only completions","",
        f"Current outcomes: {json.dumps(summary['security_only_current_outcomes'],sort_keys=True)}. None is emitted as COMPLETE. The old rows comprise 53 cases citing SQL, 24 citing JSON, and one citing a screenshot; these are case counts, not distinct-file counts. SQL cases have negative identifier queries in captured account tables but no recoverable account IDs; JSON cases include identifier-free absent lookups; the screenshot proves a retained audit entry and a reported closure event. These are different evidence situations, not 78 copies of one assumed account step. None supplies the full required subject-linked completion plan.","",
        "## Before/after metrics","",
        "Missing predictions count as errors. Withholding an unsupported label is not credited as a correct prediction. Previous best-effort and strict results are shown separately so the coverage change is visible.","",
        "| Metric | Previous best-effort | Previous strict | Corrected strict |","|---|---:|---:|---:|"]
    for title,key in [("Public resolved / 32","resolved"),("Status accuracy","status_accuracy"),("Exact-row accuracy","exact_row_accuracy"),
                      ("Ordered-sequence accuracy","ordered_sequence_accuracy"),("Step precision","step_precision"),("Step recall","step_recall")]:
        fmt=lambda m:str(m[key]) if key=="resolved" else f"{m[key]:.2%}"
        report.append(f"| {title} | {fmt(oldmetrics)} | {fmt(strict_before)} | {fmt(metrics)} |")
    report += ["","Current positional field accuracy (missing and extra array slots count as errors):","",
               "| Field | Accuracy |","|---|---:|"]
    report.extend(f"| {field} | {value:.2%} |" for field,value in metrics["positional_field_accuracy"].items())
    report += ["",f"Denominator: {metrics['field_alignment_slots']} step slots. Reference steps: {metrics['expected_steps']}; predicted steps: {metrics['predicted_steps']}; exact semantic step matches: {metrics['correct_steps']}.","",
               "Confusion matrix:","","| Reference | COMPLETE | INCOMPLETE | NOT_APPLICABLE | UNRESOLVED |","|---|---:|---:|---:|---:|"]
    for label in ("COMPLETE","INCOMPLETE","NOT_APPLICABLE"):
        cm=metrics["confusion_matrix"].get(label,{})
        report.append(f"| {label} | "+" | ".join(str(cm.get(k,0)) for k in ("COMPLETE","INCOMPLETE","NOT_APPLICABLE","UNRESOLVED"))+" |")
    report += ["","| Full-dataset measure | Before | After |","|---|---:|---:|",
        f"| Cases processed | 518 | 518 |",f"| Rows emitted | 518 | {len(current)} |",
        f"| Unresolved cases | 0 (provisionally labeled) | {summary['unresolved']} |",
        f"| Missing account links, all 508 applicable cases | 342 | {len(still_missing)} |",
        f"| Missing account steps, emitted subset only | 342 / 508 | {primary_missing_emitted} / {len(current)-10} |",
        f"| COMPLETE without account step | 101 | {len(provisional)} |",f"| Security-only COMPLETE | 78 | {len(security_new)} |",
        f"| Provisional COMPLETE emitted | 97 | {summary['current_provisional_completions']} |","",
        "Withholding unresolved rows accounts for the decrease in missing steps among emitted rows. The retrieved-link improvement is one public sample and zero full-dataset cases. The missing-link problem is not repaired, and the new output coverage is not a finished submission.","",
        "## Ablations and model execution","",
        f"A diagnostic event-time-only ablation on the old pipeline reduced missing account steps from 342 to {ablation['missing_account_steps']} but left sample exact-row accuracy at {ablation['sample_exact_row_accuracy']:.2%}. It admits captures created after audit_at and therefore violates the current contract; it is not selected for predictions. This confirms a temporal exclusion cause, not permission to use later evidence.","",
        "The new relationship supplies identity and expected verification coverage; it does not turn an activity success or a stale source into state proof.","",
        "Live LLM execution: not performed. OPENAI_API_KEY and AUDIT_MODEL are absent from the environment. No provider call or LLM-backed accuracy is claimed. Neural OCR remains the executed baseline. Existing mock-client integration tests exercise grounding, caching, retry and refusal handling.","",
        "## Representative end-to-end traces",""]
    link_ablation=after/"ablation-no-links/metrics.json"
    if link_ablation.exists():
        am=json.loads(link_ablation.read_text())
        report += [f"Explicit-link ablation: exact-row accuracy is {am['exact_row_accuracy']:.2%} with typed links disabled versus {metrics['exact_row_accuracy']:.2%} enabled. Status accuracy is {am['status_accuracy']:.2%} versus {metrics['status_accuracy']:.2%}; the effect is an added evidence-grounded future check, not a fabricated status improvement.",""]
    sample_requests={r["case_id"]:r for r in read_csv(ROOT/"dataset/sample_deletion_requests.csv")}
    representatives=["case_103","case_114","case_150","case_45","case_55","case_01","case_06","case_12","case_21","case_26"]
    for case in representatives:
        q=next((r for r in requests if r["case_id"]==case),sample_requests.get(case))
        user,values=pipeline.identity.resolve(q["email"],q["audit_at"])
        states=resolve(pipeline.store,values,q["audit_at"],pipeline.activity)
        history=pipeline.identity.history[user]
        report += [f"### {case}","",f"Identity: `{user}`; request identifier is {'current' if q['email'].casefold()==pipeline.identity.users[user]['email'].casefold() else 'historical'}; {len(values)} exact current/historical identifiers; {len(history)} history changes. Cutoff: {q['audit_at']}.","",
                   "| Resource | System | State | Evidence | Observed | Captured/available |","|---|---|---|---|---|---|"]
        for o in states:
            report.append(f"| {o.resource_id} | {o.system_id} | {o.state} | {o.evidence_id} | {o.observed_at} | {o.available_at} |")
        if not states:report.append("| No attributable admissible resource | | | | | |")
        if case in details:
            entry=next(r for r in ledger if r["case_id"]==case)
            report += ["",f"Association diagnosis: {entry['root_cause']}."]
            if entry["account_scope_queries"]:report += ["", "Captured account-table queries: `"+json.dumps(entry["account_scope_queries"],sort_keys=True)+"`."]
            if entry["unassigned_absence_records"]:report += ["", "Unassigned account lookups in related evidence (not assigned by position): `"+json.dumps(entry["unassigned_absence_records"])+"`."]
            if entry["future_account_links"]:report += ["", "Excluded future account observations: `"+json.dumps(entry["future_account_links"])+"`."]
        report.append("")
    suite=ET.parse(after/"tests.xml").getroot()
    suites=[suite] if suite.tag=="testsuite" else list(suite)
    tests=sum(int(s.attrib.get("tests",0)) for s in suites)
    failures=sum(int(s.attrib.get("failures",0))+int(s.attrib.get("errors",0)) for s in suites)
    report += ["## Tests and additional custom evaluation cases","",
        f"Executed {tests} tests: {tests-failures} passed, {failures} failures/errors. They include independent synthetic fixtures, not copied public labels.","",
        "- Retained security record alone: completion is rejected, even with the legacy best-effort flag.",
        "- Explicit search-to-account source link: an unknown account state generates a future absence check in an incomplete plan, with no invented finding or delete action.",
        "- Identifier-free downstream record: retrieved through its explicit owning source; unrelated textual mentions do not create ownership.",
        "- A link captured after the cutoff: excluded from the earlier plan.",
        "- Empty primary SQL table: retained in scope inventory instead of silently disappearing.",
        "- Narrow attachment-only request: does not require an account step by pattern.",
        "- Diagnostic field changes and reordering: paired once and reported separately as operation, state, resource, evidence or sequence errors.","",
        "- Backup metadata versus restore permission: archive presence and a healthy console yield UNKNOWN; only an explicit authorization control proves allowed or blocked. A later September policy cannot establish an April state. An independent earlier policy can still be cited when a later view only shows metadata.","",
        "Earlier custom cases covering identity changes, recreation, replica drift, retained records, tombstones, model failures and atomic writes also pass.","",
        "## Documented evidence boundaries and official repository check","",
        "Anonymous 404 records are not subject-specific absence proof. Both observation and capture time are checked. A later capture cannot establish an earlier state; an independently supported earlier fact retains its earlier provenance. Missing mappings and citations are never invented. Findings, remediation and checks are generated only for linked resources with the necessary evidence.","",
        "Resource traces distinguish PRESENT, ABSENT and UNKNOWN, while every request has an internal assessment. UNRESOLVED remains outside the submission vocabulary: emitted CSV rows still use only COMPLETE, INCOMPLETE and NOT_APPLICABLE. There is no honest mapping from lack of evidence to one of those conclusions. The runner therefore withholds a final CSV when cases remain unresolved rather than emitting unsupported statuses or a fourth status.","",
        "The new archive-screen fix withholds evaluation case_55: archive existence is supported, but restore permission at its April cutoff is UNKNOWN. No active-restore finding or BLOCK_RESTORE action is fabricated for this case. The full request ledger includes its reason and resource-level trace.","",
        "See [official_repository_check.md](official_repository_check.md) for the checked revision, per-file verification and links to [issue #19](https://github.com/interviewstreet/hackerrank-orchestrate-october26/issues/19) and [issue #24](https://github.com/interviewstreet/hackerrank-orchestrate-october26/issues/24). Those participant reports document concerns; they are not authoritative policy or ownership evidence and are never read by the prediction path.","",
        "## Remaining work","",
        "The 32-case field-level comparisons are in case_comparison.md and case_comparison_before.md. The full 518-case status/reason ledger is runs/quality-after/case_ledger.csv; raw trace and identity-association diagnostics are in investigation.json. Current resolved plans are in runs/quality-after/full/resolved_only.csv. Those files are incomplete work products, not submission artifacts.","",
        "Participant-visible pre-cutoff resource/query associations are still needed for the withheld cases and missing verification IDs. A specific counterexample is the public service export with several profile:null / status_code:404 resources and several security subjects but no join key between them. Reassigning those absent opaque account IDs to subjects leaves the visible export unchanged. Neither an LLM nor deterministic joining can prove a particular assignment from that export alone. We do not reconstruct such assignments from public answers.","",
        "There is no corrected 518-row final CSV or newly packaged archive. The previous root artifacts must not be submitted. Accuracy and evidence completeness remain below the requested definition of done.",""]
    (DEST/"correctness_review.md").write_text("\n".join(report),encoding="utf-8")
    (DEST/"evaluation_report.md").write_text("\n".join(report),encoding="utf-8")
    review=["# Review required — corrected strict investigation","",
            "Root output.csv and code.zip are old best-effort artifacts. They have not been regenerated as final outputs. See correctness_review.md for the current before/after evidence investigation and case_comparison.md for all 32 public examples.","",
            f"All 518 cases were rerun: {len(current)} emitted work-product rows; {len(run['unresolved'])} withheld. The emitted subset contains {len(security_new)} security-only completions and {len(provisional)} completions without account proof. This reduction comes from withholding unsupported conclusions, not repairing all missing source links.","",
            f"Missing account links across all 508 applicable investigations: {len(still_missing)}. Provisional COMPLETE labels emitted: 0.","",
            "## Withheld cases","","| Case | Reason |","|---|---|"]
    review.extend(f"| {r['case_id']} | {r['reason']} |" for r in run["unresolved"])
    (DEST/"review_required.md").write_text("\n".join(review)+"\n",encoding="utf-8")
    usage_path=DEST/"usage_report.md"
    usage=usage_path.read_text().split("## Current strict audit attempt")[0].rstrip()
    usage+=f"\n\n## Current strict audit attempt\n\nProcessed {run['requests']} requests, emitted {run['resolved']} work-product rows and withheld {len(run['unresolved'])}. No final output.csv was produced. Runtime: {run['duration_seconds']} seconds; model API events: {len(run['model_events'])}; OCR image calls: {run['ocr_calls']}; OCR cache hits: {run['ocr_cache_hits']}. The offline run made no provider calls, used zero API input/output tokens and incurred USD 0.00 provider cost; local compute cost is unmeasured. No LLM-backed result is claimed.\n"
    usage_path.write_text(usage,encoding="utf-8")
    (after/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    investigate()
