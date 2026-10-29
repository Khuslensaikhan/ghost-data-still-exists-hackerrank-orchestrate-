# Architecture

The solution is a terminal Python pipeline with local neural OCR and an optional structured OpenAI adapter. Resource discovery, time resolution, policy decisions and serialization run in explicit Python modules. No hosted runtime, database service or development server is required.

## Processing flow

1. `main.py` reads participant-facing requests, identities, identity history, activity, policy and the evidence manifest.
2. `assessor.py` determines deletion authorization. The executed offline configuration uses conservative lexical rules; optional model mode uses a typed intent assessment. Unknown intent withholds a decision.
3. `identity.py` reconstructs exact current and historical subject identifiers. No fuzzy identifier matching is used.
4. `evidence.py` parses SQLite-compatible SQL in memory, JSON, logs, PDF text and local RapidOCR image results. Observations retain resource/system IDs, category, state, replica, source ID, observation time and availability time. Content-hash caching avoids repeated OCR.
5. `state_resolver.py` retrieves identifier matches and explicit resource relationships, requires admissible ownership and timestamps, and resolves each replica before selecting resource state. Activity success claims alone do not prove deletion. Partial snapshots cannot prove negative observations.
6. `policy.py` applies supplied category/condition rules. `planner.py` constructs findings, ordered remediation and verification using fixed enums and deterministic ordering. Stop data flows and unsafe restores before dependent record changes.
7. `validate_output.py` checks coverage, schema, states, ordering, provenance and consistency. `writer.py` replaces the output atomically after validation.

## AI interpretation boundary

Local RapidOCR is the executed AI perception component. Native structured parsing preserves SQL/JSON/log relationships without sending full inventories to a model. OCR layout selection reduces cross-customer contamination, but OCR is not a certified transcription or a policy decision engine.

`model_client.py` is connected to the prediction pipeline for structured consent and bounded support/tombstone text cross-checks. Pydantic schemas, exact candidate IDs and exact supporting quotations constrain intermediate results. Model disagreement or uncertainty cannot produce a verified completion. API configuration is explicit through environment variables; prompts, model IDs and input/schema content qualify cache keys. Attempts, retries, tokens and cache hits are recorded.

No live OpenAI calls occurred in the reported runs. Injected adapter tests establish wiring and contract behavior only. Missing subject/resource mappings, unavailable historical state and absent restore permissions cannot be supplied by a model.

## Two publication modes

**Strict mode is the default.** It emits only resolved decisions. With this dataset it resolves 416/518, records 102 unresolved cases, writes `resolved_only.csv`, exits 2 and leaves the requested output unchanged. Security retention and tombstone redaction alone cannot prove primary-account deletion.

**Competition export is explicit:** `--publication competition-export`. `competition_export.py` preserves all 416 strict rows and maps the 102 authorized unresolved cases to unverified INCOMPLETE fallbacks. It retains only supported future verification obligations, with blank citations, and writes a separate provenance/reason ledger. No fabricated findings, destructive actions, resource IDs, ownership links or verified COMPLETE conclusions are introduced. Unknown intent still prevents export.

The CSV cannot express uncertainty in a separate field. The fallback convention is disclosed in README, evaluation and usage reports, and the full fallback ledger. Ledger-listed rows have a narrow validation exception allowing future-check-only or empty plans; strict validation remains unchanged for other rows. This is competition coverage, not a proof of complete canonical remediation.

## Reference design lessons

The previously inspected August reference separates model perception from deterministic final decisions and validates evidence selections against candidates. The June reference separates typed model assessments from model-independent business rules through adapters. This implementation uses those boundaries, typed observations, explicit provider accounting and testable pure planning. Task-specific routing/insurance rules were not transferred. Additional orchestration, concurrency or a second auditor was not introduced without measured benefit.

## Reproduction and artifacts

Run commands from the repository root using its README.md. Tests cover consent, identity history, temporal exclusions, replicas, recreation, retention, tombstones, snapshot scope, fallback safety and model contracts. Benchmark labels are read only after predictions finish.

`code.zip` includes executable Python modules, tests, pinned requirements, root and code-level README files, the required evaluation/usage reports, this architecture note, the correctness review and fallback disclosures. `output.csv` and `log.txt` are separate artifacts. Dataset files, caches, environments, credentials and nested archives are excluded.
