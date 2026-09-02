"""Run only after independent audit. Save raw engine output separately from adapted results."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.models.schemas import CheckSession
from app.services.policy import summarize
from app.services.sessions import now
from app.validators.v15_adapter import EXPECTED_SHA256, metadata, profile_requirements, validator_v15


def main() -> None:
    audit = json.loads((ROOT / "artifacts/demo-fixture-audit.json").read_text(encoding="utf-8"))
    for case in ("broken", "fixed"):
        directory = ROOT / "fixtures/v15" / f"demo-{case}"
        proof = audit["cases"][f"demo-{case}"]
        assert proof["audit_pass"]
        files = [metadata(p) for p in sorted(directory.iterdir()) if p.suffix.lower() in {".pdf", ".mp4"}]
        for file in files:
            expected = proof["pdf" if file.name.endswith(".pdf") else "video"]["sha256"]
            assert file.sha256 == expected, "Fixture changed since independent audit"
        session = CheckSession(id=f"acceptance-{case}", created_at=now(), updated_at=now(), mode="demo",
                               validation_profile="frozen_v15", source_mode="validator",
                               requirements=profile_requirements(), files=files)
        result = validator_v15.validate(session, directory)
        adapted = {"engine_sha256": EXPECTED_SHA256, "validation_complete": result.complete,
                   "status": summarize(session.requirements, result.results, validation_complete=result.complete),
                   "results": [item.model_dump(mode="json") for item in result.results]}
        for suffix, output in (("raw", result.raw), ("adapted", adapted)):
            (ROOT / f"artifacts/v15-{case}-{suffix}.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        findings = {(f["requirement_id"], f["status"]) for f in result.raw["findings"]}
        if case == "broken":
            assert {("R09", "BLOCKER"), ("R13", "BLOCKER"), ("R19", "REVIEW"), ("R21", "REVIEW")} <= findings
            assert set(result.raw["blocker_rule_ids"]) == {"R09", "R13"}
            assert adapted["status"] == "BLOCKED"
        else:
            assert not result.raw["blocker_rule_ids"]
            assert adapted["status"] == "REVIEW_REQUIRED"
        print(f"PASS: {case}: {adapted['status']}; {len(result.results)} adapted requirements; raw findings={len(findings)}")


if __name__ == "__main__":
    main()
