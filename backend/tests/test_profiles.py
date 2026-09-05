"""TASK 03 integration/safety checks. Synthetic expectations are SELF-BENCHMARK."""
from pathlib import Path
import hashlib
import json
import subprocess
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app
from app.models.profiles import ExtractedRequirement, GenericRequirementProfile
from app.models.schemas import ValidationResult
from app.services import sessions, profiles, announcement_input
from app.services.ai_providers import (LocalFallbackRequirementGenerator, LocalFallbackSemanticReviewer,
                                       get_generator, get_reviewer, provenance)
from app.services.extractors import LocalRuleExtractor
from app.services.announcement_input import source_from_bytes
from app.validators.v15_adapter import FROZEN, EXPECTED_SHA256

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures/announcements"
TEXT = (FIXTURES / "submission.txt").read_text(encoding="utf-8")
QUOTE = "제안서는 PDF 형식으로 제출해야 한다."


@pytest.fixture
def client():
    sessions.close_all()
    app.dependency_overrides[get_generator] = lambda: LocalFallbackRequirementGenerator()
    app.dependency_overrides[get_reviewer] = lambda: LocalFallbackSemanticReviewer()
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()
    sessions.close_all()


def input_text(client, text=TEXT):
    sid = client.post("/api/sessions", json={"mode": "custom"}).json()["id"]
    result = client.post(f"/api/sessions/{sid}/announcement-text", json={"text": text, "name": "synthetic announcement"})
    assert result.status_code == 200, result.text
    return result.json()


def mutate(client, data, path, **body):
    return client.post(f"/api/sessions/{data['id']}/{path}", json={"expected_version": data["generic_profile"]["version"], **body})


def extracted(client):
    data = input_text(client)
    result = mutate(client, data, "extract")
    assert result.status_code == 200, result.text
    return result.json()


def candidate(**values):
    return {"requirement_id": "G001", "rule": QUOTE, "modality": "MUST", "severity": "BLOCKER",
            "verifier": "DETERMINISTIC", "condition": "always",
            "evidence": {"source_section": "제출방법", "quote": QUOTE}, "confidence": 0.5, **values}


class MockProvider:
    provenance = provenance("stage1", "SIMULATED", "test-only-fixture-provider")

    def __init__(self, items):
        self.items = items

    def generate(self, source):
        return self.items


@pytest.mark.parametrize("modality", ["SHOULD", "MAY", "INFO"])
def test_unsupported_blocker_is_schema_error(modality):
    with pytest.raises(ValidationError, match="cannot be BLOCKER"):
        ExtractedRequirement.model_validate(candidate(modality=modality))


@pytest.mark.parametrize("evidence", [None, {}, {"source_section": "x", "quote": " "}])
def test_no_evidence_no_rule(evidence):
    with pytest.raises(ValidationError):
        ExtractedRequirement.model_validate(candidate(evidence=evidence))


def test_provider_evidence_gate_rejects_rewritten_or_invented_quotes(client):
    app.dependency_overrides[get_generator] = lambda: MockProvider([
        candidate(evidence={"source_section": "제출방법", "quote": "PDF 제출이 필요합니다."}),
        candidate(requirement_id="G002"),
    ])
    data = extracted(client)
    profile = data["generic_profile"]
    assert len(profile["requirements"]) == 1 and profile["requirements"][0]["requirement_id"] == "G002"
    assert profile["execution_kind"] == "SIMULATED"
    assert any("거부" in n for n in profile["notices"])
    assert profile["status"] != "CONFIRMED" and data["validation_profile"] is None


def test_compound_provider_rule_is_flagged_and_cannot_approve(client):
    compound = "PDF는 10페이지 이하여야 하며 파일명은 이름_작품명 형식이어야 한다."
    app.dependency_overrides[get_generator] = lambda: MockProvider([candidate(rule=compound, evidence={"source_section": "제출방법", "quote": compound})])
    data = extracted(client)
    assert data["generic_profile"]["requirements"][0]["extraction_status"] == "NEEDS_REVIEW"
    assert mutate(client, data, "requirements/G001/review", action="APPROVE").status_code == 422


def test_actual_text_profile_atomic_candidates_and_provenance(client):
    data = extracted(client)
    p = data["generic_profile"]
    assert p["execution_kind"] == "SIMULATED" and p["provider"].startswith("Fallback suggestions")
    assert p["status"] == "DRAFT" and data["requirements"] == []
    # SELF-BENCHMARK: this input and these expectations were authored together.
    assert len(p["requirements"]) == 5
    assert any("10페이지" in r["rule"] for r in p["requirements"])
    assert any("파일명" in r["rule"] for r in p["requirements"])
    assert all(not ("10페이지" in r["rule"] and "파일명" in r["rule"]) for r in p["requirements"])
    for r in p["requirements"]:
        assert TEXT[r["evidence_start"]:r["evidence_end"]] == r["evidence"]["quote"]
        assert r["rule"] in TEXT and r["extraction_status"] == "NEEDS_REVIEW"
    assert p["announcement"]["sha256"] == hashlib.sha256(TEXT.encode()).hexdigest()
    assert p["announcement"]["text_sha256"] == p["announcement"]["sha256"]
    (ROOT / "artifacts/task03/text-profile-extracted.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.mark.parametrize(("filename", "status"), [("submission.pdf", "READABLE"), ("scanned.pdf", "VISION_REQUIRED")])
def test_actual_pdf_bytes_ingestion_and_extraction(client, filename, status):
    sid = client.post("/api/sessions", json={"mode": "custom"}).json()["id"]
    original = (FIXTURES / filename).read_bytes()
    result = client.post(f"/api/sessions/{sid}/announcement", files={"file": (filename, original, "application/pdf")})
    assert result.status_code == 200, result.text
    data = result.json()
    source = data["generic_profile"]["announcement"]
    assert source["sha256"] == hashlib.sha256(original).hexdigest()
    assert source["ingestion_status"] == status and source["page_count"] == 1
    result = mutate(client, data, "extract")
    assert result.status_code == 200, result.text
    p = result.json()["generic_profile"]
    if status == "READABLE":
        assert QUOTE in source["text"] and len(p["requirements"]) == 5
        for r in p["requirements"]:
            assert r["evidence"]["quote"] in source["text"]
    else:
        assert not source["text"].strip() and p["requirements"] == []
        assert p["status"] == "REVIEW_REQUIRED"
        assert mutate(client, result.json(), "profile/confirm", reviewed_full_source=True).status_code == 422
    (ROOT / f"artifacts/task03/{filename}-profile.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def test_review_edit_approval_confirmation_handoff_and_invalidation(client):
    data = extracted(client)
    original = data["generic_profile"]["requirements"][0]
    assert mutate(client, data, "profile/confirm", reviewed_full_source=True).status_code == 422
    assert client.post(f"/api/sessions/{data['id']}/validate").status_code == 503
    data = mutate(client, data, "requirements/G001/review", action="NEEDS_REVIEW").json()
    assert data["generic_profile"]["requirements"][0]["extraction_status"] == "NEEDS_REVIEW"
    edit = candidate(rule="제안서는 PDF 형식으로 제출해야 한다", severity="REVIEW")
    data = mutate(client, data, "requirements/G001/review", action="EDIT", requirement=edit).json()
    assert data["generic_profile"]["requirements"][0]["original"] == original["original"]
    # Every retained item needs a separate human approval.
    for r in list(data["generic_profile"]["requirements"]):
        response = mutate(client, data, f"requirements/{r['requirement_id']}/review", action="APPROVE")
        assert response.status_code == 200, response.text
        data = response.json()
    assert data["generic_profile"]["status"] == "REVIEW_REQUIRED"
    assert mutate(client, data, "profile/confirm", reviewed_full_source=False).status_code == 422
    data = mutate(client, data, "profile/confirm", reviewed_full_source=True).json()
    assert data["validation_profile"] == "generic" and len(data["requirements"]) == 5
    sid = data["id"]
    uploaded = client.post(f"/api/sessions/{sid}/files", files=[("files", ("submission.pdf", (FIXTURES / "submission.pdf").read_bytes(), "application/pdf"))])
    assert uploaded.status_code == 200
    response = client.post(f"/api/sessions/{sid}/validate")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "REVIEW_REQUIRED" and not result["validation_complete"]
    assert result["source_mode"] == "generic_review" and result["engine_sha256"] is None
    assert {r["status"] for r in result["results"]} == {"REVIEW", "EXTERNAL"}
    assert all(r["announcement_evidence"] and r["submission_evidence"] is None for r in result["results"])
    assert result["generic_profile"]["announcement"] == data["generic_profile"]["announcement"]
    (ROOT / "artifacts/task03/confirmed-handoff.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = mutate(client, result, "requirements/G001/review", action="NEEDS_REVIEW").json()
    assert changed["validation_profile"] is None and changed["results"] == [] and changed["previous_results"] == []
    assert changed["requirements"] == [] and changed["status"] is None
    assert client.post(f"/api/sessions/{sid}/validate").status_code == 503


def test_edit_cannot_invent_quote_and_stale_approval_rejected(client):
    data = extracted(client)
    invalid = candidate(evidence={"source_section": "제출방법", "quote": "없는 서명이 필요하다"})
    assert mutate(client, data, "requirements/G001/review", action="EDIT", requirement=invalid).status_code == 422
    updated = mutate(client, data, "requirements/G001/review", action="APPROVE")
    assert updated.status_code == 200
    assert mutate(client, data, "requirements/G001/review", action="APPROVE").status_code == 409


def test_delete_keeps_audit_and_empty_profile_cannot_confirm(client):
    data = extracted(client)
    for r in list(data["generic_profile"]["requirements"]):
        data = mutate(client, data, f"requirements/{r['requirement_id']}/review", action="DELETE").json()
    p = data["generic_profile"]
    assert p["requirements"] == [] and len([x for x in p["history"] if x["action"] == "DELETE"]) == 5
    assert p["history"][-1]["before"]["evidence"]["quote"] in TEXT
    assert mutate(client, data, "profile/confirm", reviewed_full_source=True).status_code == 422


def test_unknown_source_produces_no_invented_rule(client):
    data = input_text(client, "오늘 날씨는 맑습니다.")
    data = mutate(client, data, "extract").json()
    assert data["generic_profile"]["requirements"] == []
    assert data["generic_profile"]["status"] == "REVIEW_REQUIRED"


@pytest.mark.parametrize("status", ["PASS", "BLOCKER"])
def test_generic_results_cannot_fake_automatic_verdicts(status):
    with pytest.raises(ValidationError, match="Generic automatic"):
        ValidationResult(id="x", requirement_id="G001", status=status, title="x", explanation="x", action="x", source_mode="generic_review")


def test_profile_evidence_offset_and_hash_tampering_rejected(client):
    data = extracted(client)["generic_profile"]
    data["requirements"][0]["evidence_start"] += 1
    with pytest.raises(ValidationError, match="exact source substring"):
        GenericRequirementProfile.model_validate(data)
    data["announcement"]["text"] += " forged"
    with pytest.raises(ValidationError, match="text hash mismatch"):
        GenericRequirementProfile.model_validate(data)


def test_unreadable_pdf_and_timeout_do_not_generate_contents(client, monkeypatch):
    sid = client.post("/api/sessions", json={"mode": "custom"}).json()["id"]
    response = client.post(f"/api/sessions/{sid}/announcement", files={"file": ("broken.pdf", b"not a PDF", "application/pdf")})
    assert response.status_code == 200
    assert response.json()["generic_profile"]["announcement"]["ingestion_status"] == "UNREADABLE"
    assert mutate(client, response.json(), "extract").json()["generic_profile"]["requirements"] == []
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("injected", 30)
    monkeypatch.setattr(announcement_input.subprocess, "run", timeout)
    source = source_from_bytes("timeout.pdf", b"pdf", "PDF", Path("unused"))
    assert source.ingestion_status == "UNREADABLE" and not source.text


def test_provider_exception_does_not_confirm_or_create_findings(client):
    class BrokenProvider(MockProvider):
        def generate(self, source):
            raise RuntimeError("test-only injected provider failure")
    app.dependency_overrides[get_generator] = lambda: BrokenProvider([])
    data = input_text(client)
    failed = mutate(client, data, "extract")
    assert failed.status_code == 200
    assert failed.json()["generic_profile"]["pipeline_status"] == "EXTRACTION_ERROR"
    saved = client.get(f"/api/sessions/{data['id']}").json()
    assert saved["generic_profile"]["status"] == "REVIEW_REQUIRED" and saved["results"] == []


def test_frozen_before_and_current_directory_hashes_match():
    before = json.loads((ROOT / "artifacts/task03/frozen-before.json").read_text(encoding="utf-8-sig"))
    for entry in before:
        assert hashlib.sha256((FROZEN.parent / entry["file"]).read_bytes()).hexdigest() == entry["sha256"]
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == EXPECTED_SHA256
