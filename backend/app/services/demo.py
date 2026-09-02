import hashlib
import json
from pathlib import Path
from app.models.schemas import Requirement, SubmissionFile, ValidationResult

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"

def load_requirements() -> list[Requirement]:
    return [Requirement.model_validate(item) for item in json.loads((FIXTURES / "requirements.json").read_text(encoding="utf-8"))]


def fixture_files(case: str) -> list[SubmissionFile]:
    if case not in {"demo-broken", "demo-fixed"}:
        raise ValueError("Unknown demo fixture")
    return [
        SubmissionFile(name=path.name, size_bytes=path.stat().st_size,
                       media_type="application/pdf" if path.suffix == ".pdf" else "video/mp4",
                       sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted((FIXTURES / case).iterdir())
        if path.suffix in {".pdf", ".mp4"}
    ]


def fixture_results(case: str) -> list[ValidationResult]:
    if case not in {"demo-broken", "demo-fixed"}:
        raise ValueError("Unknown demo fixture")
    return [ValidationResult.model_validate(item) for item in json.loads((FIXTURES / case / "results.json").read_text(encoding="utf-8"))]
