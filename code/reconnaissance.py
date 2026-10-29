"""Write dataset structure and extraction coverage without exporting identities."""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
from pathlib import Path

from evidence import EvidenceStore, read_csv


def report(dataset: Path, cache: Path) -> str:
    rows = ["# Participant-data reconnaissance", "", "Only files under `dataset/` were inspected. No organizer truth or generator files were read.", "",
            "| CSV | Rows | Columns | Missing cells | Timestamp range |", "|---|---:|---|---:|---|"]
    for path in sorted(dataset.glob("*.csv")):
        data = read_csv(path)
        header = list(data[0]) if data else path.read_text().strip().split(",")
        missing = sum(value=="" for r in data for value in r.values())
        times = [value for r in data for key,value in r.items() if key.endswith("_at") or key=="event_time"]
        interval = f"{min(times)} to {max(times)}" if times else "n/a"
        rows.append(f"| {path.name} | {len(data)} | {', '.join(header)} | {missing} | {interval} |")
    sources = read_csv(dataset/"evidence_files.csv")
    counts = collections.Counter(Path(r["file_path"]).suffix for r in sources)
    rows += ["", "## Evidence distribution", "", ", ".join(f"`{k}`: {v}" for k,v in sorted(counts.items()))+".", "",
             "The 11 images require pixel-to-text inference. All four PDFs have extractable text layers (eight pages total); no PDF page rendering was necessary. Native parsers cover JSON, SQL, text and six logging encodings. OCR remains fallible; selected-resource IDs must be grounded and pass confidence checks.", "",
             "## Database topology", "", "| SQL file | Tables and row counts |", "|---|---|"]
    replica_names = set()
    for source in sources:
        path=dataset/source["file_path"]
        if path.suffix!=".sql":
            continue
        connection=sqlite3.connect(":memory:")
        # The ingestion layer's SQL allow-list is reused for all executable input.
        text=path.read_text()
        inspector=EvidenceStore.__new__(EvidenceStore);inspector.observations=[];inspector.scopes=[]
        inspector.sql_file(source,text)
        # Read-only schema/count inventory uses the already checked statement stream.
        connection.executescript(text)
        names=[r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        counts=[f"{n}: {connection.execute('SELECT COUNT(*) FROM '+n).fetchone()[0]}" for n in names]
        replica_names.update(n for n in names if "replica" in n)
        rows.append(f"| {path.name} | {'; '.join(counts)} |")
        connection.close()
    rows += ["", f"Distinct replica-table names: {len(replica_names)} ({', '.join(sorted(replica_names))}). These are table roles across captures, not a claim about the number of deployed hosts.", "",
             "Generic replica tables contain `resource_id`, `origin_system`, `collection_name`, `record_json`, and `updated_at`. Inventory captures use eight typed tables plus `snapshot_scope`. Primary, failover, reporting, read and regional tables must be compared independently. A primary miss does not establish absence in a replica.", "",
             "## Associations and time", "",
             "Current and historical emails, phone numbers, email hashes and stable subject references associate content with people. Query keys associate observations; they are not stored PII. The manifest supplies paths and capture time, never case membership. Resource IDs propagate links only after an admissible identifier association exists.", "",
             "Logs correlate query-start identifiers with readback results by trace ID. JSON includes business records, service lookups and operational histories. Catalog activity can link an image filename or business reference to a resource, but cannot establish its state. Every combined observation becomes available no earlier than either source.", "",
             "Overlapping snapshots and readbacks describe the same resources. Some bundles contain older and later observations. A capture made after `audit_at` is excluded even if it embeds an older observation. No workflow success result establishes absence, redaction or disabled status.", "",
             "## Measured coverage", ""]
    activity=read_csv(dataset/"system_activity.csv")
    store=EvidenceStore(dataset,cache,catalog=activity)
    parsed=sum(r["parsed"] for r in store.coverage)
    rows += [f"Parsed {parsed}/{len(store.coverage)} files into {len(store.observations)} observations and {len(store.scopes)} scope declarations. A parsed artifact can contain zero safely identifiable resources; this is distinct from parse failure.", ""]
    for failure in (r for r in store.coverage if not r["parsed"]):
        rows.append(f"- {failure['evidence_id']}: {failure['error']}")
    rows += ["## Public benchmark coverage", "",
             "The 32 public answers cover 10 COMPLETE and 22 INCOMPLETE cases, with no NOT_APPLICABLE examples. They include replica drift, historical hashes, backup risk, synchronization, support redaction, exports, tombstones, stale observations and similar-address decoys. Non-deletion behavior therefore needs independent custom tests.", "",
             "Difficult examples include case_05 (primary deletion versus failover presence), case_12 (historical hash and secondary identifier), case_26 (post-cutoff bundle and identifier-free compliant readbacks), case_28 (similar email decoy), and cases_31/32 (stable tombstone reference versus direct PII). The public benchmark has no hidden-label claim.", ""]
    return "\n".join(rows)


if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset",type=Path,default=root/"dataset")
    parser.add_argument("--output",type=Path,default=Path(__file__).parent/"evaluation"/"reconnaissance.md")
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(report(args.dataset,root/".cache"),encoding="utf-8")
    print(args.output)
