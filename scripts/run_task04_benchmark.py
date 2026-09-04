"""Run the frozen baseline once, then aggregate explicit manual scoring tables."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/task04"
# Initial capture failed to serialize Pydantic objects. Preserve that attempt in
# extracted/*.json; successful unchanged-baseline capture uses this subdirectory.
RUN = BASE / "extracted/baseline"
sys.path.insert(0, str(ROOT / "backend"))


def read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> dict:
    freeze = read(BASE / "gold_manifest.json")
    for entry in freeze["files"] + read(ROOT / "artifacts/task04/source-before.json")["files"]:
        if sha(ROOT / entry["path"]) != entry["sha256"]:
            raise RuntimeError(f"Frozen hash changed: {entry['path']}")
    return freeze


def execute(freeze: dict) -> None:
    # Imports deliberately occur only after the persisted freeze was verified.
    from app.services.announcement_input import source_from_bytes
    from app.services.extractors import LocalRuleExtractor
    from app.services.profiles import extract, new_profile

    class Capture:
        name = LocalRuleExtractor.name
        execution_kind = LocalRuleExtractor.execution_kind

        def __init__(self) -> None:
            self.raw: list[dict] = []

        def extract(self, source: object) -> list:
            result = LocalRuleExtractor().extract(source)
            self.raw = [item.model_dump(mode="json") for item in result]
            return result

    invoked_at = datetime.now(timezone.utc).isoformat()
    assert datetime.fromisoformat(invoked_at) > datetime.fromisoformat(freeze["frozen_at"])
    execution = {"invoked_at": invoked_at, "gold_manifest_sha256": sha(BASE / "gold_manifest.json"),
                 "freeze_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                 "classification": "ACTUAL TEST against INDEPENDENT BENCHMARK", "cases": []}
    # Persist start before the first provider invocation, including failed attempts.
    save(RUN / "execution.json", execution)
    for case in read(BASE / "manifest.json"):
        cid = case["case_id"]
        input_path = ROOT / case["input_path"]
        original = ROOT / case["snapshot_path"]
        source = source_from_bytes(original.name if case["source_type"] == "PDF" else input_path.name,
                                   original.read_bytes() if case["source_type"] == "PDF" else input_path.read_bytes(),
                                   "PDF" if case["source_type"] == "PDF" else "TEXT", original)
        if source.text != input_path.read_text(encoding="utf-8"):
            raise RuntimeError(f"Actual ingestion differs from frozen input: {cid}")
        capture = Capture()
        result = {"case_id": cid, "invoked_at": datetime.now(timezone.utc).isoformat(),
                  "source_sha256": source.sha256, "input_sha256": source.text_sha256}
        try:
            profile = extract(new_profile(source), capture)
            result["profile"] = profile.model_dump(mode="json", exclude={"announcement", "history"})
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        result["raw"] = capture.raw
        save(RUN / f"{cid}.json", result)
        execution["cases"].append({"case_id": cid, "raw_count": len(capture.raw),
                                   "output_sha256": sha(RUN / f"{cid}.json")})
        save(RUN / "execution.json", execution)
        print(f"{cid}: {len(capture.raw)} raw candidates; {result.get('error', result.get('profile', {}).get('status'))}")
    execution["completed_at"] = datetime.now(timezone.utc).isoformat()
    save(RUN / "execution.json", execution)


def aggregate() -> None:
    assessment_path = BASE / "scoring/candidates.tsv"
    if not assessment_path.exists():
        print("Manual scoring pending; no scores inferred automatically.")
        return
    with assessment_path.open(encoding="utf-8", newline="") as stream:
        candidates = list(csv.DictReader(stream, delimiter="\t"))
    with (BASE / "scoring/misses.tsv").open(encoding="utf-8", newline="") as stream:
        misses = list(csv.DictReader(stream, delimiter="\t"))
    gold = {r["gold_id"]: r for path in sorted((BASE / "gold").glob("C*.json")) for r in read(path)}
    raw = {(c["case_id"], r["requirement_id"]): r for path in sorted(RUN.glob("C*.json")) for c in [read(path)] for r in c["raw"]}
    assert {(r["case_id"], r["extracted_id"]) for r in candidates} == set(raw)
    assert len(candidates) == len(raw), "Duplicate candidate assessment"
    pairs, covered, matched = [], set(), set()
    metrics = Counter(gold_total=len(gold), extracted_total=len(raw))
    categories = Counter()
    for row in candidates:
        cid, rid = row["case_id"], row["extracted_id"]
        item = raw[cid, rid]
        ids = [] if row["gold_ids"] == "-" else row["gold_ids"].split(",")
        ids = [f"{cid}-R{int(g):03}" for g in ids]
        assert row["match_type"] in {"MATCH", "PARTIAL", "NO_MATCH"}
        if row["match_type"] == "MATCH":
            assert len(ids) == 1 and ids[0] not in matched
            assert row["atomicity"] == "0"
            matched.update(ids)
            metrics["matched"] += 1
            metrics["modality_correct"] += item["modality"] == gold[ids[0]]["modality"]
        for gid in ids:
            assert gid in gold
        covered.update(ids)
        categories.update(c for c in row["failure_categories"].split(",") if c != "-")
        for flag, key in (("semantic_support", "semantic_supported"), ("atomicity", "atomicity_violations"), ("hallucinated", "hallucinated_rules")):
            assert row[flag] in {"0", "1"}
            metrics[key] += int(row[flag])
        text = (BASE / "sources" / f"{cid}.txt").read_text(encoding="utf-8")
        quote = item["evidence"]["quote"]
        metrics["exact_quotes"] += bool(quote) and quote in text
        metrics["blockers"] += item["severity"] == "BLOCKER"
        metrics["unsupported_blockers"] += item["severity"] == "BLOCKER" and row["semantic_support"] == "0"
        for gid in ids or [""]:
            pairs.append({"case_id": cid, "gold_id": gid, "extracted_id": rid, "match_type": row["match_type"],
                          "reason": row["reason"], "failure_category": row["failure_categories"]})
    missed_categories = Counter()
    missing_ids = set()
    for row in misses:
        cid = row["case_id"]
        for n in row["gold_ids"].split(","):
            gid = f"{cid}-R{int(n):03}"
            assert gid in gold and gid not in covered and gid not in missing_ids
            missing_ids.add(gid)
            missed_categories[row["failure_category"]] += 1
            pairs.append({"case_id": cid, "gold_id": gid, "extracted_id": "", "match_type": "NO_MATCH",
                          "reason": row["reason"], "failure_category": row["failure_category"]})
    assert covered | missing_ids == set(gold), sorted(set(gold) - covered - missing_ids)
    result = dict(metrics)
    for key, numerator, denominator in [
        ("recall", "matched", "gold_total"), ("precision", "matched", "extracted_total"),
        ("modality_accuracy", "modality_correct", "matched"), ("evidence_exactness", "exact_quotes", "extracted_total"),
        ("evidence_semantic_support", "semantic_supported", "extracted_total"), ("atomicity_rate", "atomicity_violations", "extracted_total")]:
        result[key] = metrics[numerator] / metrics[denominator] if metrics[denominator] else None
    result["candidate_failure_counts"] = dict(categories.most_common())
    result["uncovered_gold_failure_counts"] = dict(missed_categories.most_common())
    result["fully_uncovered_gold"] = len(missing_ids)
    result["partial_only_gold"] = len(covered - matched)
    result["per_case"] = [{"case_id": cid, "gold": sum(g.startswith(cid) for g in gold),
                            "extracted": sum(c == cid for c, _ in raw), "matched": sum(g.startswith(cid) for g in matched)}
                           for cid in sorted({c for c, _ in raw})]
    save(BASE / "report/metrics.json", result)
    with (BASE / "scoring/pairs.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    lines = ["# TASK 04 — frozen independent baseline", "",
             "Eight actual announcements; Gold frozen before execution; unchanged local-rules-v1.",
             "Manual, one-to-one scoring; PARTIAL receives no credit. Same agent authored Gold and scored.", "",
             "| Metric | Actual result |", "|---|---:|",
             f"| Gold / raw extracted | {len(gold)} / {len(raw)} |",
             f"| Recall | {metrics['matched']}/{len(gold)} = {result['recall']:.2%} |",
             f"| Precision | {metrics['matched']}/{len(raw)} = {result['precision']:.2%} |",
             f"| Modality accuracy on MATCH | {metrics['modality_correct']}/{metrics['matched']} = {result['modality_accuracy']:.2%} |",
             f"| Evidence exactness | {metrics['exact_quotes']}/{len(raw)} = {result['evidence_exactness']:.2%} |",
             f"| Evidence semantic support | {metrics['semantic_supported']}/{len(raw)} = {result['evidence_semantic_support']:.2%} |",
             f"| Atomicity violations | {metrics['atomicity_violations']}/{len(raw)} = {result['atomicity_rate']:.2%} |",
             f"| Hallucinated constraints | {metrics['hallucinated_rules']} |",
             f"| Unsupported BLOCKER / total BLOCKER | {metrics['unsupported_blockers']} / {metrics['blockers']} |", "",
             "| Case | Gold | Extracted | MATCH | Recall | Precision |", "|---|---:|---:|---:|---:|---:|"]
    for c in result["per_case"]:
        lines.append(f"| {c['case_id']} | {c['gold']} | {c['extracted']} | {c['matched']} | {c['matched']/c['gold']:.2%} | {c['matched']/c['extracted']:.2%} |")
    lines += ["", f"{len(covered - matched)} Gold have only partial coverage; {len(missing_ids)} have no candidate coverage.", "",
              "Read [analysis and decision](analysis.md), [failure taxonomy](failure-taxonomy.md),",
              "[manual pairs](../scoring/pairs.csv), [candidate audit](../scoring/candidates.tsv),",
              "[source manifest](../manifest.json), and [Gold freeze](../gold_manifest.json).",
              "Task completion and regression evidence are recorded in [RESULT_CODEX](../../../RESULT_CODEX.md).", ""]
    (BASE / "report/report.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def audit_saved_execution() -> None:
    execution = read(RUN / "execution.json")
    frozen_entries = read(BASE / "gold_manifest.json")["files"]
    for entry in frozen_entries:
        data = subprocess.check_output(["git", "show", f"{execution['freeze_commit']}:{entry['path']}"], cwd=ROOT)
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]
    repeated, gates = [], []
    for path in sorted(RUN.glob("C*.json")):
        case = read(path)
        cid = case["case_id"]
        source = (BASE / "sources" / f"{cid}.txt").read_text(encoding="utf-8")
        lines = source.splitlines(keepends=True)
        accepted = {r["requirement_id"]: r for r in case["profile"]["requirements"]}
        gates.append({"case_id": cid, "raw": len(case["raw"]), "accepted": len(accepted),
                      "profile_status": case["profile"]["status"],
                      "needs_review": sum(r["extraction_status"] == "NEEDS_REVIEW" for r in accepted.values())})
        for row in case["raw"]:
            quote = row["evidence"]["quote"]
            match = re.search(r"줄 (\d+)", row["evidence"]["source_section"])
            if match and source.count(quote) > 1:
                line = int(match[1])
                intended = sum(map(len, lines[:line-1])) + lines[line-1].index(quote)
                anchored = accepted[row["requirement_id"]]["evidence_start"]
                if anchored != intended:
                    repeated.append({"case_id": cid, "extracted_id": row["requirement_id"], "quote": quote,
                                     "declared_line": line, "intended_start": intended, "actual_start": anchored,
                                     "source_find_start": source.find(quote)})
    integrity = read(ROOT / "artifacts/task04/source-before.json")
    integrity["recorded_at"] = datetime.now(timezone.utc).isoformat()
    integrity["freeze_commit_byte_verification"] = "PASS"
    for entry in integrity["files"]:
        actual = sha(ROOT / entry["path"])
        assert actual == entry["sha256"]
        entry["after_sha256"] = actual
    save(ROOT / "artifacts/task04/source-after.json", integrity)
    save(BASE / "report/gate-and-anchor-audit.json", {"gates": gates, "misanchored_repeated_quotes": repeated})
    print(f"Audit: Git freeze bytes verified; {len(repeated)} repeated quotes anchored to a different source occurrence.")


def main() -> None:
    freeze = verify()
    execution_path = RUN / "execution.json"
    if execution_path.exists():
        execution = read(execution_path)
        assert "completed_at" in execution, "Incomplete baseline attempt; inspect recorded state"
        assert execution["gold_manifest_sha256"] == sha(BASE / "gold_manifest.json")
        for case in execution["cases"]:
            assert sha(RUN / f"{case['case_id']}.json") == case["output_sha256"]
        print("Verified frozen inputs and saved actual outputs; baseline not re-executed.")
    else:
        execute(freeze)
    aggregate()
    audit_saved_execution()


if __name__ == "__main__":
    main()
