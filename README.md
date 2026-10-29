# Ghost Data Still Exists — deletion audit pipeline

This submission contains an explicitly requested **competition export**, not a fully verified deletion audit. `output.csv` covers all 518 requests: 416 strict predictions are retained and 102 authorized unresolved cases receive **unverified INCOMPLETE fallbacks**. No fallback is declared COMPLETE. The export may differ from canonical answers and is not evidence that all 456 INCOMPLETE cases have observed violations.

## Setup

Python 3.12 was used. Extract `code.zip`, place the official participant dataset at `dataset/` beside `code/`, and run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
```

On Windows activate with `.venv\Scripts\Activate.ps1`. All paths default relative to this checkout. No server or system OCR executable is needed. Offline mode requires no API key. The first local RapidOCR pass takes several minutes on CPU; content-addressed image caches avoid repeat inference. The archive intentionally excludes the dataset, caches, environments and credentials.

## Competition export: all required rows

```sh
python code/main.py --mode offline --publication competition-export --run-dir runs/competition/full --output output.csv
python code/validate_output.py --output output.csv --fallback-ledger runs/competition/full/fallbacks.json
```

The output has exactly `case_id,deletion_status,steps_json`, sorted lexicographically by case_id. Steps use canonical phase/operation/system/resource order and consecutive numbering. All resource joins and state decisions check both observation and availability timestamps against audit_at. Predictions use only participant-facing inputs; public labels are read only after sample predictions finish.

Competition export first runs the unchanged strict audit. Its 416 resolved rows remain identical. The 102 unresolved cases map to INCOMPLETE only after deletion authorization is confirmed. Unknown intent still blocks export; NOT_APPLICABLE is reserved for confident non-deletion requests.

For fallback cases, INCOMPLETE means **completion could not be established**, not a confirmed remaining record. Only policy-required future checks for admissibly linked resources are retained. Their evidence_id is blank, as required for future verification on INCOMPLETE rows. They assert no current absence, redaction, anonymization, disabled flow or blocked restore. No unknown account ID, ownership link, finding or destructive action is invented. When no supported resource is available, steps_json may be empty. Known violations already produce strict INCOMPLETE plans and are preserved unchanged.

`runs/competition/full/fallbacks.json` records every fallback, original strict reason and actual source observations. [competition_fallbacks.md](code/evaluation/competition_fallbacks.md) lists all 102 cases in the package. The CSV's three columns cannot encode uncertainty, so keep these disclosures with it. Competition validation explicitly permits missing finding/remediation phases or empty arrays for ledger-listed fallback cases; it does not certify complete remediation coverage or canonical semantic correctness. Other rows retain strict validation. No external submission is performed.

## Strict mode: default and unchanged

```sh
python code/main.py --mode offline --run-dir runs/strict/full --output runs/strict/output.csv
```

With this dataset strict mode resolves 416/518, writes resolved_only.csv plus traces, and exits 2 without replacing the requested output. It withholds 102 unresolved cases. A retained security record or redacted tombstone alone cannot prove account deletion. The legacy --best-effort flag does not bypass strict gates; competition export requires the separate explicit --publication option.

## Evaluation, reports and packaging

```sh
python -m pytest code/tests -q --junitxml=runs/competition/tests.xml
python code/evaluation/main.py --mode offline --run-dir runs/competition/strict-samples
python code/evaluation/main.py --mode offline --publication competition-export --run-dir runs/competition/samples
python code/evaluation/competition_report.py
python code/package_submission.py
```

Run the full competition export first, then these commands in order. Reports compare strict and competition metrics, count fallbacks separately and include custom synthetic evaluation scenarios. The 32 public cases are a development benchmark, not a held-out estimate. The 518 requests have no public ground-truth labels. Full coverage and structural validation do not establish accuracy.

The required reports are [evaluation_report.md](code/evaluation/evaluation_report.md) and [usage_report.md](code/evaluation/usage_report.md). The archive also includes [architecture.md](code/evaluation/architecture.md), [correctness_review.md](code/evaluation/correctness_review.md) and the fallback ledger, under both `code/evaluation/` and the contract's `evaluation/` paths. [code/README.md](code/README.md) points to this root setup/run guide. The final full run uses deterministic processing and local neural OCR, with zero live OpenAI API calls. Local OCR work is not counted as LLM tokens. Historical benchmark/reconnaissance Markdown is excluded from the archive.

## Optional OpenAI interpretation

Set OPENAI_API_KEY securely in the environment and AUDIT_MODEL to an explicitly chosen supported model identifier. No default model or embedded credentials are supplied.

```sh
python code/evaluation/main.py --mode model --publication competition-export --run-dir runs/model/samples
```

The adapter is connected to intent assessment and bounded support/tombstone text cross-checks, with typed responses and ID/quotation validation. Model output cannot invent ownership, evidence or final steps. Provider attempts, tokens, errors and cache hits are recorded. AUDIT_TIMEOUT defaults to 90 seconds and AUDIT_ATTEMPTS to 3. SDK retries are disabled in favor of counted retries. Injected adapter tests prove wiring, not live inference. Credentials were unavailable for this submission; no live-model accuracy is claimed. Model interpretation cannot recover absent source mappings or restore permissions.

## Source map

- code/main.py: CLI, strict audit and explicit publication choice.
- code/competition_export.py: authorized uncertainty fallback and provenance ledger.
- code/identity.py, evidence.py, state_resolver.py: history, extraction, cutoff-qualified joins and replica resolution.
- code/assessor.py, model_client.py: consent and optional structured interpretation.
- code/policy.py, planner.py: policy treatment and ordered plans.
- code/schema.py, validate_output.py, writer.py: vocabulary, validation and atomic CSV writing.
- code/evaluation/: public scoring, reporting and diagnostic source.
- code/tests/: independent synthetic regressions.

SQL executes only in memory, with external access denied. No source system is modified. code.zip contains executable Python source, tests, pinned requirements, README and current reports. output.csv and the append-only log.txt transcript are separate submission artifacts.

Official challenge/submission: [Ghost Data Still Exists](https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists).
