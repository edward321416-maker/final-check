from pathlib import Path
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app
from app.models.schemas import Evidence, FindingStatus, SubmissionStatus, ValidationResult
from app.services import demo, sessions
from app.services.policy import summarize

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    sessions.SESSIONS.clear()
    with TestClient(app) as test_client:
        yield test_client
    sessions.SESSIONS.clear()


def start(client, mode="demo"):
    response = client.post("/api/sessions", json={"mode": mode})
    assert response.status_code == 201
    session_id = response.json()["id"]
    if mode == "demo":
        assert client.post(f"/api/sessions/{session_id}/demo-announcement").status_code == 200
    return session_id


def test_health_and_openapi(client):
    assert client.get("/api/health").json()["validator"] == "unavailable"
    schema = client.get("/openapi.json").json()["components"]["schemas"]
    assert set(schema["FindingStatus"]["enum"]) == {"BLOCKER", "REVIEW", "PASS", "EXTERNAL"}
    for name in ("CheckSession", "Requirement", "ValidationResult", "SubmissionStatus"):
        assert name in schema
    assert client.get("/docs").status_code == 200


def test_broken_to_fixed_golden_path(client):
    sid = start(client)
    assert client.post(f"/api/sessions/{sid}/validate").status_code == 409
    selected = client.post(f"/api/sessions/{sid}/fixture", json={"fixture": "demo-broken"}).json()
    assert {f["name"] for f in selected["files"]} == {"proposal.pdf", "clip.mp4"}
    broken = client.post(f"/api/sessions/{sid}/validate").json()
    assert broken["status"] == "BLOCKED"
    blockers = [r for r in broken["results"] if r["status"] == "BLOCKER"]
    assert len(blockers) == 2
    assert all(r["announcement_evidence"] and r["submission_evidence"] for r in blockers)
    selected = client.post(f"/api/sessions/{sid}/fixture", json={"fixture": "demo-fixed"}).json()
    assert selected["results"] == []
    assert selected["status"] == "NOT_CHECKED"
    fixed = client.post(f"/api/sessions/{sid}/validate").json()
    assert fixed["status"] == "NEEDS_REVIEW"
    assert fixed["revision"] == 2
    assert len(fixed["previous_results"]) == 5
    assert all(r["status"] != "BLOCKER" for r in fixed["results"])
    assert next(r["status"] for r in fixed["results"] if r["requirement_id"] == "R19") == "REVIEW"
    assert client.get(f"/api/sessions/{sid}").json() == fixed


@pytest.mark.parametrize("missing", ["announcement_evidence", "submission_evidence"])
def test_blocker_requires_both_evidence_sources(missing):
    result = demo.fixture_results("demo-broken")[0].model_dump()
    result[missing] = None
    with pytest.raises(ValidationError):
        ValidationResult.model_validate(result)


def test_r19_cannot_be_blocker_even_with_evidence():
    result = demo.fixture_results("demo-broken")[3].model_dump()
    result["status"] = "BLOCKER"
    with pytest.raises(ValidationError, match="R19"):
        ValidationResult.model_validate(result)


def test_empty_evidence_rejected():
    with pytest.raises(ValidationError):
        Evidence(source="", locator="", excerpt="")
    with pytest.raises(ValidationError):
        Evidence(source="doc.pdf", locator="page 1", excerpt="   ")


def test_ready_requires_complete_pass_only():
    rules = demo.load_requirements()
    passed = [ValidationResult.model_validate({**r.model_dump(), "status": "PASS"}) for r in demo.fixture_results("demo-fixed")]
    assert summarize(rules, passed) == SubmissionStatus.READY
    assert summarize(rules, passed[:-1]) == SubmissionStatus.NEEDS_REVIEW
    assert summarize(rules, passed + [passed[0]]) == SubmissionStatus.NEEDS_REVIEW
    assert summarize(rules, []) == SubmissionStatus.NOT_CHECKED
    passed[-1].status = FindingStatus.EXTERNAL
    assert summarize(rules, passed) == SubmissionStatus.NEEDS_REVIEW
    passed[-1].status = FindingStatus.REVIEW
    assert summarize(rules, passed) == SubmissionStatus.NEEDS_REVIEW


def test_custom_upload_cannot_inherit_demo_results(client):
    sid = start(client)
    client.post(f"/api/sessions/{sid}/fixture", json={"fixture": "demo-broken"})
    client.post(f"/api/sessions/{sid}/validate")
    response = client.post(f"/api/sessions/{sid}/files", files=[("files", ("custom.pdf", b"%PDF-1.4 custom", "application/pdf"))])
    assert response.status_code == 200
    data = response.json()
    assert data["source_mode"] == "unavailable"
    assert data["results"] == data["requirements"] == data["previous_results"] == []
    assert data["status"] == "NOT_CHECKED"
    assert client.post(f"/api/sessions/{sid}/validate").status_code == 503
    assert client.post(f"/api/sessions/{sid}/fixture", json={"fixture": "demo-fixed"}).status_code == 409
    assert client.post(f"/api/sessions/{sid}/demo-announcement").status_code == 409


@pytest.mark.parametrize(("name", "content", "status"), [("bad.exe", b"X", 415), ("empty.pdf", b"", 422), ("large.pdf", b"x" * (20 * 1024 * 1024 + 1), 413)], ids=["unsupported", "empty", "oversize"])
def test_upload_boundaries(client, name, content, status):
    sid = start(client)
    response = client.post(f"/api/sessions/{sid}/files", files=[("files", (name, content, "application/octet-stream"))])
    assert response.status_code == status
    assert client.get(f"/api/sessions/{sid}").json()["files"] == []


def test_duplicate_names_and_package_limits(client):
    sid = start(client)
    response = client.post(f"/api/sessions/{sid}/files", files=[("files", ("a.pdf", b"x")), ("files", ("A.pdf", b"y"))])
    assert response.status_code == 422
    files = [("files", (f"{i}.pdf", b"x")) for i in range(9)]
    assert client.post(f"/api/sessions/{sid}/files", files=files).status_code == 422


def test_custom_announcement_no_fabricated_requirements(client):
    sid = start(client, "custom")
    response = client.post(f"/api/sessions/{sid}/announcement", files={"file": ("announcement.txt", b"custom announcement", "text/plain")})
    assert response.status_code == 200
    assert response.json()["requirements"] == []
    assert response.json()["source_mode"] == "unavailable"


def test_expired_and_unknown_sessions(client):
    assert client.get("/api/sessions/missing").status_code == 404
    sid = start(client)
    sessions.SESSIONS[sid].updated_at -= timedelta(hours=2)
    assert client.get(f"/api/sessions/{sid}").status_code == 404


def test_isolated_sessions_and_fixture_path_validation(client):
    a, b = start(client), start(client)
    client.post(f"/api/sessions/{a}/fixture", json={"fixture": "demo-broken"})
    assert client.get(f"/api/sessions/{b}").json()["files"] == []
    assert client.post(f"/api/sessions/{a}/fixture", json={"fixture": "../../elsewhere"}).status_code == 422


def test_original_validator_adapter_is_explicitly_unavailable():
    from app.validators.v15_adapter import ValidatorInput, ValidatorUnavailable, validator_v15
    assert validator_v15.available is False
    package = ValidatorInput(announcement=ROOT / "fixtures/demo-announcement.txt",
                             submissions=(), requirements=tuple(demo.load_requirements()))
    with pytest.raises(ValidatorUnavailable, match="Original frozen"):
        validator_v15.validate(package)
