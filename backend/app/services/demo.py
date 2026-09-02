"""Serve actual synthetic TASK 02 files. No canned findings are loaded."""
from pathlib import Path
from app.models.schemas import SubmissionFile
from app.validators.v15_adapter import metadata

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures/v15"


def fixture_path(case: str, filename: str | None = None) -> Path:
    if case not in {"demo-broken", "demo-fixed"}:
        raise ValueError("Unknown demo fixture")
    directory = FIXTURES / case
    if filename is None:
        return directory
    allowed = {path.name for path in directory.iterdir() if path.suffix.lower() in {".pdf", ".mp4"}}
    if filename not in allowed:
        raise ValueError("Unknown demo file")
    return directory / filename


def fixture_files(case: str) -> list[SubmissionFile]:
    return [metadata(path) for path in sorted(fixture_path(case).iterdir()) if path.suffix.lower() in {".pdf", ".mp4"}]


def identify_fixture(files: list[SubmissionFile]) -> str | None:
    values = {(file.name, file.sha256) for file in files}
    for case in ("demo-broken", "demo-fixed"):
        if values == {(file.name, file.sha256) for file in fixture_files(case)}:
            return case
    return None
