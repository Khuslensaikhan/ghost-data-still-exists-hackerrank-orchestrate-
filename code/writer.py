"""Validate before atomic replacement; failed runs leave previous output intact."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

from schema import COLUMNS


def write_atomic(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in sorted(rows, key=lambda row: row["case_id"]):
                writer.writerow(dict(case_id=row["case_id"], deletion_status=row["deletion_status"],
                                     steps_json=json.dumps(row["steps"], ensure_ascii=False, separators=(",", ":"))))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
