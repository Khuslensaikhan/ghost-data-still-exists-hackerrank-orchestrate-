# Output status: explicit competition export

Root output.csv is the requested 518-row best-effort competition export. Root code.zip contains the current executable solution and both required evaluation reports. This replaces the retired baseline artifacts.

- 416 strict predictions are preserved unchanged.
- 102 authorized unresolved cases use unverified INCOMPLETE fallbacks, with only supported future verification checks and no invented findings, actions, ownership links or current-state citations.
- Status counts: 456 INCOMPLETE (354 strict + 102 fallbacks), 52 COMPLETE (strict only), 10 NOT_APPLICABLE.
- Strict mode remains the default: it still withholds those 102 cases and leaves existing output untouched.
- Competition export satisfies all 518 required rows and format/order checks under the explicitly documented fallback exception. It does not establish canonical step completeness or verified deletion for fallback rows.
- No live OpenAI calls occurred. No external submission or push was performed.

See README.md, code/evaluation/evaluation_report.md, code/evaluation/usage_report.md and code/evaluation/competition_fallbacks.md. Machine-readable fallback provenance: runs/competition/full/fallbacks.json.
