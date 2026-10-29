# Running the Python solution

Use the [repository README](../README.md) for installation, publication modes, validation and reproduction. Run its commands from the parent directory containing `code/` and `dataset/`.

```sh
python code/main.py --mode offline --publication competition-export --run-dir runs/competition/full --output output.csv
python code/validate_output.py --output output.csv --fallback-ledger runs/competition/full/fallbacks.json
```

The competition export preserves 416 strict rows and adds 102 explicitly unverified INCOMPLETE fallbacks. Strict mode remains the default without `--publication competition-export`.

See [architecture.md](evaluation/architecture.md), [correctness_review.md](evaluation/correctness_review.md), [evaluation_report.md](evaluation/evaluation_report.md), [usage_report.md](evaluation/usage_report.md), and [competition_fallbacks.md](evaluation/competition_fallbacks.md).
