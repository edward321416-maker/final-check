from pathlib import Path
from datetime import timedelta
import hashlib
import json
import re
import shutil
import sys
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app
from app.api import routes
from app.models.schemas import Evidence, FindingStatus, SubmissionStatus, ValidationResult, CheckSession
from app.services import demo, sessions
from app.services.policy import summarize
from app.validators.v15_adapter import EXPECTED_SHA256, FROZEN, ValidatorRuntimeError, profile_requirements, metadata, validator_v15

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.generate_v15_fixtures import make_pdf


@pytest.fixture
def client():
    sessions.close_all()
    with TestClient(app) as test_client:
        yield test_client
    sessions.close_all()


def start(client, mode="demo"):
    response = client.post("/api/sessions", json={"mode": mode})
    assert response.status_code == 201
    assert response.json()["status"] is None
    assert response.json()["run_state"] == "NOT_STARTED"
    sid = response.json()["id"]
    if mode == "demo":
        assert client.post(f"/api/sessions/{sid}/demo-announcement").status_code == 200
    return sid


def upload(client, sid, case):
    files = [("files", (p.name, p.read_bytes(), "application/pdf" if p.suffix == ".pdf" else "video/mp4"))
             for p in sorted(demo.fixture_path(case).iterdir()) if p.suffix.lower() in {".pdf", ".mp4"}]
    response = client.post(f"/api/sessions/{sid}/files", files=files)
    assert response.status_code == 200, response.text
    return response.json()


def real_session(directory):
    return CheckSession(id="test", created_at=sessions.now(), updated_at=sessions.now(), mode="demo",
                        validation_profile="frozen_v15", requirements=profile_requirements(),
                        files=[metadata(p) for p in sorted(directory.iterdir()) if p.is_file()])


def test_source_hash_and_runtime_dependencies():
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == EXPECTED_SHA256
    assert validator_v15.available
    assert shutil.which("ffprobe")


def test_health_and_cross_language_status_contract(client):
    health = client.get("/api/health").json()
    assert health["validator"] == "available"
    assert health["vision_provider"] == "unavailable"
    schema = client.get("/openapi.json").json()["components"]["schemas"]
    assert set(schema["FindingStatus"]["enum"]) == {"BLOCKER", "REVIEW", "PASS", "EXTERNAL"}
    expected = {"BLOCKED", "REVIEW_REQUIRED", "READY"}
    assert set(schema["SubmissionStatus"]["enum"]) == expected
    text = (ROOT / "frontend/types/check.ts").read_text(encoding="utf-8")
    declaration = next(line for line in text.splitlines() if line.startswith("export type SubmissionStatus"))
    assert set(re.findall(r'"([A-Z_]+)"', declaration)) == expected
    assert client.get("/docs").status_code == 200


def test_actual_upload_broken_to_fixed_golden_path(client):
    sid = start(client)
    assert client.post(f"/api/sessions/{sid}/validate").status_code == 409
    upload(client, sid, "demo-broken")
    broken = client.post(f"/api/sessions/{sid}/validate")
    assert broken.status_code == 200, broken.text
    body = broken.json()
    assert body["status"] == "BLOCKED"
    assert body["source_mode"] == "validator"
    assert body["engine_sha256"] == EXPECTED_SHA256
    assert {r["requirement_id"] for r in body["results"] if r["status"] == "BLOCKER"} == {"R09", "R13"}
    for result in body["results"]:
        if result["status"] == "BLOCKER":
            assert result["announcement_evidence"]["excerpt"].strip()
            assert result["submission_evidence"]["excerpt"].strip()
    selected = upload(client, sid, "demo-fixed")
    assert selected["results"] == [] and selected["status"] is None
    fixed = client.post(f"/api/sessions/{sid}/validate").json()
    assert fixed["status"] == "REVIEW_REQUIRED"
    assert fixed["revision"] == 2 and fixed["run_state"] == "COMPLETE"
    assert len(fixed["previous_results"]) == 16
    assert all(r["status"] != "BLOCKER" for r in fixed["results"])
    statuses = {r["requirement_id"]: r["status"] for r in fixed["results"]}
    assert statuses["R09"] == statuses["R13"] == "PASS"
    assert statuses["R19"] == statuses["R20"] == statuses["R21"] == "REVIEW"
    assert client.get(f"/api/sessions/{sid}").json() == fixed


@pytest.mark.parametrize("missing", ["announcement_evidence", "submission_evidence"])
def test_blocker_requires_both_evidence_sources(missing):
    evidence = Evidence(source="test", locator="test", excerpt="test")
    result = dict(id="test", requirement_id="R13", status="BLOCKER", title="test", explanation="test",
                  action="test", announcement_evidence=evidence, submission_evidence=evidence)
    result[missing] = None
    with pytest.raises(ValidationError):
        ValidationResult.model_validate(result)


@pytest.mark.parametrize(("rid", "status"), [("R19", "BLOCKER"), ("R20", "BLOCKER"), ("R20", "PASS"), ("R21", "BLOCKER"), ("R21", "PASS")])
def test_protected_rules_reject_unsupported_automatic_results(rid, status):
    evidence = Evidence(source="test", locator="test", excerpt="test")
    with pytest.raises(ValidationError):
        ValidationResult(id="test", requirement_id=rid, status=status, title="test", explanation="test",
                         action="test", announcement_evidence=evidence, submission_evidence=evidence)


@pytest.mark.parametrize("rid", ["R19", "R20", "R21"])
def test_adapter_reduces_adversarial_blocker_to_review(rid):
    # Explicit policy fault injection; never represents an observed frozen-engine output.
    rules = profile_requirements()
    quote = next(r.announcement_evidence.excerpt for r in rules if r.id == rid)
    raw = {"findings": [{"requirement_id": rid, "status": "BLOCKER", "message": "injected test", "evidence_quote": quote}],
           "blocker_rule_ids": [rid], "review_rule_ids": [], "vision_pending": []}
    run = validator_v15.adapt(rules, raw, demo.fixture_path("demo-fixed"))
    assert next(r.status for r in run.results if r.requirement_id == rid) == FindingStatus.REVIEW
    assert summarize(rules, run.results, validation_complete=run.complete) != SubmissionStatus.READY


def test_empty_evidence_rejected():
    for value in ("", "   "):
        with pytest.raises(ValidationError):
            Evidence(source="doc.pdf", locator="p1", excerpt=value)


def test_incomplete_run_cannot_be_ready():
    rule = next(r for r in profile_requirements() if r.id == "R13")
    result = ValidationResult(id="r13", requirement_id=rule.id, status="PASS", title=rule.title,
                              explanation="test", action="test", announcement_evidence=rule.announcement_evidence,
                              submission_evidence=Evidence(source="test.mp4", locator="duration", excerpt="45"))
    assert summarize([rule], [result], validation_complete=True) == SubmissionStatus.READY
    assert summarize([rule], [result], validation_complete=False) == SubmissionStatus.REVIEW_REQUIRED
    assert summarize([rule], [], validation_complete=True) == SubmissionStatus.REVIEW_REQUIRED
    assert summarize([rule], [result, result], validation_complete=True) == SubmissionStatus.REVIEW_REQUIRED


def test_runtime_failure_clears_stale_ready(client, monkeypatch):
    sid = start(client)
    upload(client, sid, "demo-fixed")
    sessions.SESSIONS[sid].status = SubmissionStatus.READY
    def fail(*args):
        raise ValidatorRuntimeError("injected runtime failure")
    monkeypatch.setattr(validator_v15, "validate", fail)
    response = client.post(f"/api/sessions/{sid}/validate")
    assert response.status_code == 502
    data = client.get(f"/api/sessions/{sid}").json()
    assert data["status"] == "REVIEW_REQUIRED"
    assert data["run_state"] == "FAILED" and not data["validation_complete"]
    assert data["results"] == []


def test_custom_announcement_does_not_inherit_frozen_profile(client):
    sid = start(client, "custom")
    response = client.post(f"/api/sessions/{sid}/announcement", files={"file": ("custom.txt", b"unrelated announcement", "text/plain")})
    assert response.status_code == 200 and response.json()["requirements"] == []
    upload(client, sid, "demo-fixed")
    assert client.post(f"/api/sessions/{sid}/validate").status_code == 503
    assert client.get(f"/api/sessions/{sid}").json()["status"] is None
    assert client.post(f"/api/sessions/{sid}/demo-announcement").status_code == 409


@pytest.mark.parametrize(("name", "content", "status"), [("bad.exe", b"X", 415), ("empty.pdf", b"", 422), ("../escape.pdf", b"X", 422), ("large.pdf", b"x" * 1025, 413)], ids=["unsupported", "empty", "traversal", "limit"])
def test_upload_boundaries(client, monkeypatch, name, content, status):
    monkeypatch.setattr(routes, "MAX_FILE_BYTES", 1024)
    sid = start(client)
    response = client.post(f"/api/sessions/{sid}/files", files=[("files", (name, content, "application/octet-stream"))])
    assert response.status_code == status
    assert client.get(f"/api/sessions/{sid}").json()["files"] == []


def test_duplicate_names_and_count_limits(client):
    sid = start(client)
    assert client.post(f"/api/sessions/{sid}/files", files=[("files", ("a.pdf", b"x")), ("files", ("A.pdf", b"y"))]).status_code == 422
    assert client.post(f"/api/sessions/{sid}/files", files=[("files", (f"{i}.pdf", b"x")) for i in range(9)]).status_code == 422


def test_session_isolation_and_expiry_cleanup(client):
    a, b = start(client), start(client)
    upload(client, a, "demo-fixed")
    path = sessions.package_path(a)
    assert path.exists()
    assert client.get(f"/api/sessions/{b}").json()["files"] == []
    sessions.SESSIONS[a].updated_at -= timedelta(hours=2)
    assert client.get(f"/api/sessions/{a}").status_code == 404
    assert not path.exists()


def test_package_tamper_does_not_produce_ready(client):
    sid = start(client)
    upload(client, sid, "demo-fixed")
    pdf = next(sessions.package_path(sid).glob("*.pdf"))
    pdf.write_bytes(b"changed after upload")
    assert client.post(f"/api/sessions/{sid}/validate").status_code == 502
    assert client.get(f"/api/sessions/{sid}").json()["status"] == "REVIEW_REQUIRED"


def test_actual_scanned_pdf_requests_review_without_vision(tmp_path):
    from pypdf import PdfReader
    source = demo.fixture_path("demo-fixed")
    video = next(source.glob("*.MP4"))
    pdf = next(source.glob("*.pdf"))
    shutil.copyfile(video, tmp_path / video.name)
    make_pdf(tmp_path / pdf.name, privacy=True, scanned=True)
    assert not "".join(page.extract_text() or "" for page in PdfReader(tmp_path / pdf.name).pages).strip()
    session = real_session(tmp_path)
    run = validator_v15.validate(session, tmp_path)
    assert len(run.raw["vision_pending"]) == 4
    assert run.complete is False
    for rid in ("R09", "R10", "R11"):
        finding = next(r for r in run.results if r.requirement_id == rid)
        assert finding.status == FindingStatus.REVIEW
        assert "Vision" in finding.explanation
    assert summarize(session.requirements, run.results, validation_complete=run.complete) == SubmissionStatus.REVIEW_REQUIRED


def test_frozen_profile_required_and_raw_shape_guard():
    directory = demo.fixture_path("demo-fixed")
    session = real_session(directory)
    session.requirements = session.requirements[:-1]
    with pytest.raises(RuntimeError):
        validator_v15.validate(session, directory)
    with pytest.raises(ValidatorRuntimeError):
        validator_v15.adapt(profile_requirements(), {}, directory)
