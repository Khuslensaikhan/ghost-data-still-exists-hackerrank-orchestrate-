# Accuracy diagnosis and targeted fixes

## Findings

Status accuracy fell from 29/32 to 23/32 because case_21, case_25, case_26, case_27, case_28 and case_31 are now withheld. The first five previously inferred completion from retained/compliant downstream records; case_31 inferred primary-account absence from a redacted tombstone. The missing pre-cutoff account ownership/absence proof remains unsupported. This is a conservative correction, not six newly introduced retrieval bugs. case_01, case_02 and case_04 were already unresolved in the earlier run. All 22 public INCOMPLETE statuses remain correct.

Exact-row accuracy rose from 8/32 to 9/32 through an explicit search-to-account source_resource_id link in case_06. The remaining differences are missing verification coverage and additional evidence-backed checks omitted by the reference. Anonymous deleted/anonymized rows have no subject link; some expected account/audit IDs have no observed state; other subject-bearing captures arrive after the cutoff. The five extra steps concern object_19 in case_07 and account_6523 / tombstone_17 in case_17, all supported by earlier participant evidence. No answer-specific IDs or inferred row ordering were introduced into predictions.

[All 32 combined previous/current comparisons, canonical missing/extra steps and source support](public_accuracy.md). [All withheld cases, overlapping categories and exact primary partition](withheld_classification.md). Machine-readable counterparts: ../../runs/accuracy-review/public_comparison.json, withheld_classification.json/.csv, step_metrics.json and evidence_pipeline.json.

## Measured public accuracy

| Metric | Earlier best-effort | Strict before | Strict after |
|---|---:|---:|---:|
| Correct statuses | 29/32 | 23/32 | 23/32 |
| Exact rows | 8/32 | 9/32 | 9/32 |
| Step precision | 96.93% | 96.62% | 96.62% |
| Step recall | 81.87% | 74.09% | 74.09% |
| Step F1 | 88.76% | 83.87% | 83.87% |

Exact semantic matches: 143/148 predicted and 143/193 reference steps.

| Phase | Missing canonical steps | Extra predicted steps |
|---|---:|---:|
| FINDING | 0 | 1 |
| REMEDIATION | 0 | 1 |
| VERIFICATION | 50 | 3 |

All 148 operation/state pairs are legal. On 143 matched pairs, operation, state, system, resource and citation agreement are all 100%; counting missing reference slots lowers each to 143/193 = 74.09%. Unmatched extras are separately penalized by step precision. This conditional match accuracy must not be read as exhaustive correctness. All 44/44 nonempty current citations are time-admissible, resource/state-grounded and subject-linked; future checks correctly have blank citations. Citation validity is independent of reference exact agreement. Predicted operation/state/resource/citation tuples have the same 143/148 exact-step precision; there are no paired field substitutions.

Ordered sequences match in 9/32 cases. All 23 emitted public rows have valid phase order, canonical operation order and numbering. There are no relative-order inversions among matched steps; missing/extra steps account for sequence failures. Missing predictions are errors in all 32-case denominators.

Unsupported reference-step categories: `{"NO_RESOURCE_STATE_OBSERVATION_OR_SUBJECT_JOIN": 16, "OWNERSHIP_OR_STATE_ONLY_IN_POST_CUTOFF_CAPTURE": 8, "RESOURCE_OBSERVED_BUT_SUBJECT_OWNERSHIP_UNPROVEN": 10}`. Some supported reference steps are also absent from emitted rows because the entire unsupported COMPLETE row is withheld; they are not extraction errors.

## Coverage and evidence pipeline

Processed 518/518 requests; emitted 416 (354 INCOMPLETE, 52 COMPLETE, 10 NOT_APPLICABLE); withheld 102. Before/after this turn are identical. Missing account links remain 342/508 applicable investigations, including 240/406 emitted applicable rows. There are zero provisional completions and zero security-only completions emitted. The 78 former security-only completions remain withheld.

Primary withheld partition: `{"MISSING_OWNERSHIP_AND_INCOMPLETE_COVERAGE": 60, "POST_CUTOFF_EVIDENCE": 25, "SCOPED_NEGATIVE_QUERY_WITHOUT_RESOURCE_ID": 16, "UNKNOWN_RESTORE_STATE": 1}`. Overlapping diagnostic counts: `{"ACCOUNT_ABSENCE_NOT_DEMONSTRABLE": 102, "CONFLICTING_OBSERVATIONS": 0, "INCOMPLETE_SNAPSHOT_COVERAGE": 72, "MISSING_DATA_OR_UNSUPPORTED_INFERENCE": 77, "MISSING_OWNERSHIP_LINK": 102, "OTHER": 0, "POST_CUTOFF_EVIDENCE": 26, "UNKNOWN_RESTORE_STATE": 1}`.

All 103 participant files are accounted for: 94 evidence artifacts plus 9 CSVs. Six CSVs and the 94 artifacts serve full-run prediction; sample requests/reference answers serve evaluation, and the blank output template is intentionally unused. All 94 artifacts parsed; formats are 24 SQL, 28 JSON, 26 logs, 11 PNGs, 4 PDFs and 1 text. CSV headers/rows were independently read for the role inventory. No reference/template file is used for prediction.

Evidence counts and denominator definitions:

- observations: 2907.
- observations_with_valid_provenance: 2907.
- observations_with_explicit_system_resource_key: 2907.
- observations_with_any_identifier: 2655.
- observations_directly_linked_to_full_or_sample_subject: 2312.
- explicit_resource_relationships: 3.
- full_case_observation_pairs: 2207.
- cutoff_admissible_full_case_observation_pairs: 1576.
- distinct_direct_observations_admissible_for_their_full_run_subject: 1574.
- scopes: 384.
- complete_scopes: 78.
- partial_scopes: 306.
- empty_scopes: 21.

Provenance means a real manifest file with capture time retained and parseable observation time. Four business-artifact aliases also require a catalog event: their availability is the later of capture and catalog association, and both provenance IDs are retained. An explicit resource key is not a subject ownership link. Direct subject links are exact current/historical identifier matches to the 518 full-run or 32 sample subjects; any-identifier counts also include unrelated subjects. Cutoff counts are subject-specific observation/case pairs, with both observation and availability checked; the distinct count deduplicates reused observations. These are extraction/association diagnostics, not independently labeled extraction accuracy. Complete snapshot scope is bounded to its declared collection/replica, not all systems or all direct-identifier forms.

All 11 images were processed by local neural OCR, with 0 fresh calls and 11 content-hash cache hits in this audit. A parser failure is recorded and blocks COMPLETE; OCR text is not a certified transcription. Empty tables retain scopes, partial JSON cannot prove negatives, simultaneous conflicting states fail closed, and an unknown replica cannot be masked by a compliant read. Current withheld reasons contain no extraction failures or same-time observation conflicts. INCOMPLETE rows can still be emitted on known violations despite partial knowledge; emission is not proof that all opaque missing resources were discovered.

## Demonstrable code fixes and regressions

Two new synthetic counterexamples failed before the fixes and pass afterward: (1) a table named customer_profiles_primary without snapshot_scope was incorrectly marked complete; it now remains partial, while explicitly scoped empty tables still support bounded negative observations; (2) the standalone validator accepted an invented resource ID merely because it was absent from a scoped table; it now requires an admissible same-evidence resource anchor of the same category. Neither fix changes current dataset predictions.

Full suite: 73 tests pass (65 before). The regression set covers anonymous 404 isolation, late subject/resource links, explicitly scoped SQL versus partial snapshots, archive/restore uncertainty, redacted tombstones versus primary-account absence, worker success versus readback, observed recreation before cutoff, replica conflict and retention-only completion. The optional adapter is exercised through AuditPipeline with an injected test adapter; this verifies wiring and is not a live model result.

case_55: activity_4006 links backup_9287 to the subject. evidence_32 is an April 29 archive screen before the April 30 cutoff. It shows archive existence, encryption, checksum and unrelated restore history, but no authorization/block setting for this archive. Its state remains UNKNOWN. September restore settings cannot resolve the April question; no restore-risk finding or BLOCK_RESTORE action is fabricated.

## LLM boundary and reproducibility

The executed runs use --mode offline: deterministic parsing/joins/planning plus local RapidOCR. Both model API event lists are empty; zero API input/output tokens and zero provider cost. OPENAI_API_KEY and AUDIT_MODEL are absent. No provider was called. ModelClient is connected through consent assessment and candidate support/tombstone text interpretation, with exact-ID/quotation validation and disagreement withholding; the current adapter does not perform missing ownership retrieval or image/PDF vision. It can help interpret ambiguous intent, text and PII exposure; it cannot recover absent join keys, opaque deleted IDs, capture-time clarification or unobserved restore permission.

After configuring credentials securely in the environment and setting AUDIT_MODEL to an explicitly chosen supported model, run:

```sh
.venv/bin/python code/evaluation/main.py --mode model --run-dir runs/accuracy-review/live-samples
.venv/bin/python code/main.py --mode model --run-dir runs/accuracy-review/live-full --output runs/accuracy-review/live-output.csv
```

Model-mode evaluation persists provider events and totals. A warm model cache can yield zero new calls; clear only the task-specific model cache or use main.py --cache with a fresh directory when measuring live execution. This command is preparation, not a completed LLM comparison. Exit 2 on unresolved cases is expected and preserves strict publication.

Offline reproduction:

```sh
.venv/bin/python -m pytest code/tests -q --junitxml=runs/accuracy-review/after/tests.xml
.venv/bin/python code/evaluation/main.py --mode offline --run-dir runs/accuracy-review/after/samples
.venv/bin/python code/main.py --mode offline --run-dir runs/accuracy-review/after/full --output runs/accuracy-review/after/output.csv
# The full runner exits 2 after writing traces and resolved_only.csv, because 102 cases remain unresolved.
.venv/bin/python code/evaluation/accuracy_review.py
```

## Decision and next improvement

No demonstrated existing-evidence mapping legitimately resolves one of the 102 withheld cases in this review. The highest-value next engineering work is a grounded query/ownership coverage register: retain exact query predicates, collection/replica scope, identifier lineage, timestamps and proof for each obligation. It would make negative-query coverage auditable and catch future recoverable joins; it cannot manufacture the missing opaque IDs. Source corrections or an official uncertainty/output convention are needed to close the demonstrated gaps. Adding orchestration or a larger model would not resolve these missing facts.

The three allowed statuses cannot honestly encode an unknown deletion state. Labeling unknowns INCOMPLETE would assert a violation without evidence; labeling them COMPLETE would assert deletion without proof; NOT_APPLICABLE would deny explicit consent. Preserve strict withholding: the 416-row work product fails the mandatory 518-row submission contract. The old 518-row root CSV and old archive remain retired. No publication-policy change, package, push or submission was made. The last official repository correction check is documented in official_repository_check.md; it is a dated snapshot, not a new online check in this task. No final generation occurred.
