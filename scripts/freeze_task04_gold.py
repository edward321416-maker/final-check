"""Materialize manually authored annotations and freeze hashes before extraction."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/task04"


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    manifest_path = BASE / "gold_manifest.json"
    if manifest_path.exists() or (BASE / "extracted").exists():
        raise RuntimeError("Refusing Gold rewrite after freeze or extraction")
    cases = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    texts = {c["case_id"]: (ROOT / c["input_path"]).read_text(encoding="utf-8").splitlines() for c in cases}
    gold: dict[str, list] = {cid: [] for cid in texts}
    with (BASE / "gold/annotations.tsv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            cid = row["case_id"]
            first, last = int(row["start_line"]), int(row["end_line"])
            assert 1 <= first <= last <= len(texts[cid]), row
            assert row["modality"] in {"MUST", "MUST_NOT", "SHOULD", "MAY", "INFO"}
            gold[cid].append({"gold_id": f"{cid}-R{len(gold[cid])+1:03}", "rule": row["rule"],
                              "modality": row["modality"], "condition": row["condition"],
                              "evidence": {"start_line": first, "end_line": last,
                                           "quote": "\n".join(texts[cid][first-1:last])}})
    for cid, requirements in gold.items():
        save(BASE / "gold" / f"{cid}.json", requirements)
    paths = [BASE / "PROTOCOL.md", BASE / "manifest.json", *sorted((BASE / "gold").iterdir())]
    paths += [ROOT / c[key] for c in cases for key in ("snapshot_path", "input_path")]
    records = [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    save(manifest_path, {"frozen_at": datetime.now(timezone.utc).isoformat(), "extractor_executed": False,
                        "baseline_commit": "81bf2551c5967836d3e54869de2e86261428c78e",
                        "gold_counts": {cid: len(rows) for cid, rows in gold.items()},
                        "modality_counts": dict(Counter(r["modality"] for rows in gold.values() for r in rows)),
                        "files": records})
    print(f"Gold frozen: {sum(map(len, gold.values()))} requirements / {len(cases)} cases")
    print(f"Manifest SHA-256: {hashlib.sha256(manifest_path.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
