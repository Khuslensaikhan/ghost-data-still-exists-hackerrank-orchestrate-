# Usage report — final competition export

Measured run: runs/competition/full/run.json, which produced root output.csv. Counts refer to the submitted program, not the coding assistant. The final export processes all 518 requests and includes 102 explicitly unverified INCOMPLETE fallbacks; fallback labeling uses no model inference and does not improve evidence completeness.

| Measurement | Value |
|---|---:|
| Requested / exported rows | 518 / 518 |
| Strict resolved / unverified fallback rows | 416 / 102 |
| Full-run wall time (seconds) | 1.188 |
| API events / provider calls | 0 / 0 |
| API input / output tokens | 0 / 0 |
| Total / average tokens per request | 0 / 0 |
| Estimated provider cost total / per request | USD 0.00 / USD 0.00 |
| Fresh local OCR image calls / cache hits | 0 / 11 |

## Models, providers and totals

No OpenAI API model was selected or executed; credentials were not supplied. Model-assisted mode is optional and is not used in reported predictions. Per-API-model and overall totals are zero calls, zero input/output tokens and USD 0.00. There are no mocked or estimated live calls included in these totals.

Local perception uses rapidocr-onnxruntime 1.4.4 with ONNX Runtime 1.31.0 and the package's ch_PP-OCRv4_det_infer.onnx, ch_PP-OCRv4_rec_infer.onnx and ch_ppocr_mobile_v2.0_cls_infer.onnx models. The initial ingestion previously executed 11 image-pipeline inferences; this final run reused all 11 content-hash cached results. A pipeline call is not a measured count of detector/classifier/recognizer tensor invocations. Local OCR does not report LLM token usage. Local compute, electricity and hosting costs are unmeasured, not claimed free.

The optional live adapter records attempts, SDK-returned usage, cache hits and errors. Cached model responses count as zero newly billed tokens; errors without usage remain unknown rather than fabricated zero-usage successes. Tests use injected synthetic adapters and are excluded from provider totals. No live LLM versus deterministic comparison can be claimed without credentials. Both public runs and this full export were executed offline.
