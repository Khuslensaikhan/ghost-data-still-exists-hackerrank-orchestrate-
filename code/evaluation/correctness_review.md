# Correctness review and evidentiary limitations

The current root output.csv is the explicitly requested 518-row competition export. It preserves 416 strict predictions and adds 102 unverified INCOMPLETE fallbacks. Those fallback labels mean completion could not be established; they do not prove a remaining record, an active restore path or a canonical answer. Strict mode still withholds the same 102 cases.

## Current measurements

| Measure | Strict | Competition export |
|---|---:|---:|
| Full-dataset rows | 416/518 | 518/518 |
| Unverified fallback labels emitted | 0 | 102 |
| Public status matches | 23/32 | 23/32 |
| Public exact rows | 9/32 | 9/32 |
| Step precision | 96.62% | 87.20% |
| Step recall | 74.09% | 74.09% |
| Step F1 | 83.87% | 80.11% |

All 82 regression tests pass. The 32 public examples are a development benchmark; the full 518 requests have no public ground truth. Coverage, tests and structural validation do not certify prediction accuracy. [evaluation_report.md](evaluation_report.md) contains field/sequence metrics, custom cases and failure analysis. [usage_report.md](usage_report.md) records the executed offline run and zero live API calls.

## Why records remain unresolved

The 102 strict abstentions have this primary partition:

- 60 lack admissible ownership and sufficiently scoped account coverage.
- 25 primarily depend on account evidence available after audit_at.
- 16 have bounded negative inventory queries without a recoverable opaque account ID.
- One has unknown restore authorization, despite evidence that the archive exists.

Categories overlap beyond that partition. All 102 lack demonstrated subject-linked primary-account absence; 26 have later account evidence, including the restore-uncertainty case. No missing IDs are reconstructed from array positions, numeric suffixes, shared files or temporal proximity.

Across all applicable full-dataset investigations, 342 still lack account-resource links. Current and historical identity lookup succeeds; absent ownership/state evidence is distinct from failed identity lookup. Parsed evidence is also distinct from successfully attributed evidence.

## Evidence boundaries

- An identifier-free 404 can establish an absent resource, but cannot identify whose resource it was. Anonymous anonymized records have the same attribution limitation.
- Both observed_at and availability/capture time must be at or before audit_at. Later ownership evidence cannot backdate an earlier anonymous lookup. An independently supported earlier fact retains its own earlier provenance.
- SQL negatives are bounded to explicitly declared snapshot scope and the known identifiers queried. Partial JSON arrays, unscoped tables and missing rows do not establish universal account absence or manufacture a deleted account ID.
- Security records retained by policy prove retention only. A correctly redacted tombstone proves its own treatment, not primary-account deletion. The 78 previous security-only completions are now unverified fallback INCOMPLETE rows, never verified COMPLETE.
- An archive screen showing existence, checksum or unrelated restore history does not show that this subject's restore permission is allowed or blocked. case_55 retains a future restore-block verification obligation; it has no invented active-risk finding or BLOCK_RESTORE action.
- Worker success, reported workflow status and synchronization claims are not observed resource-state proof. Direct readback and independently observed recreation take precedence when admissible. Conflicting simultaneous state blocks a strict conclusion; unknown replica state cannot be hidden by a clean read.

## Fixes versus benchmark shortcuts

Explicit source_resource_id traversal recovered a supported account verification obligation and improved public exact rows from 8/32 to 9/32. Empty SQL peer-table scopes are retained. Unscoped SQL is no longer assumed exhaustive, and the validator cannot accept an invented resource ID simply because it is absent from a table.

The earlier 29/32 to 23/32 status decrease reflects rejection of unsupported completions, including downstream-only compliance and a tombstone-only inference. Some canonical checks require missing or late mappings; some independently supported extra checks are omitted by public answers. No sample-specific identifiers or answer labels enter predictions.

## Competition convention and disclosures

All 416 strict rows are unchanged. The 102 fallback rows contain 163 future policy verification checks for admissibly linked resources; their citations are blank because they describe future work, not verified current state. No fallback finding, remediation action or current compliance observation is invented. A fallback with no supported resource may have an empty array; none of the current 102 full-run fallbacks is empty.

The export has 456 INCOMPLETE labels: 354 strict decisions plus 102 uncertainty fallbacks. All 52 COMPLETE and 10 NOT_APPLICABLE rows are retained strict predictions. NOT_APPLICABLE requires confident non-deletion intent. Unknown intent cannot be relabeled to fill coverage.

[competition_fallbacks.md](competition_fallbacks.md) preserves every affected case ID, strict reason and supporting resource facts. This consolidates the relevant review-required information; a separate review_required.md is unnecessary. The generated machine-readable ledger is runs/competition/full/fallbacks.json. Keep these disclosures with the three-column output because it has no uncertainty field.

Validation explicitly permits future-check-only or empty plans for ledger-listed fallback INCOMPLETE rows. This format exception is not a claim of complete remediation or canonical correctness. Missing mappings and restore facts still require source correction or clarification. No live LLM evaluation was performed, and no external submission was made.
