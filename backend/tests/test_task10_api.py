"""Real local API/storage checks; only the external semantic reviewer is simulated."""
import json
import threading
import time

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.profiles import ExtractedRequirement, ProviderProvenance
from app.models.semantic_review import SemanticAIResponse
from app.services import generic_validation, profiles, sessions
from app.api.routes import semantic_reviewer_factory
from app.services.verifier_compiler import compile_profile
from app.services.public_guard import GuardConfig, GuardRejected, PublicGuard
from app.services.semantic_submission import prepare_semantic_submission
from app.services.task10_validation import run_generic_preflight
from test_task08_verifier import Planner, candidate, confirmed_profile, seeded_session


class Reviewer:
    requires_background = True
    provenance = ProviderProvenance(provider="test", model="simulated", prompt_version="test",
                                    prompt_sha256="a" * 64, execution_kind="SIMULATED")

    def __init__(self):
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()
        self.release.set()
        self.error = None
        self.mutate = None
        self.malformed = False

    def review(self, requirements, preparation):
        self.calls += 1
        self.started.set()
        assert self.release.wait(5), "test reviewer timed out"
        if self.mutate:
            self.mutate()
        if self.error:
            raise self.error
        if self.malformed:
            return {"reviews": [{"requirement_id": "G002", "status": "PASS"}]}
        return SemanticAIResponse(reviews=[dict(requirement_id=r.requirement_id,
            assessment="NO_CLEAR_EVIDENCE", evidence_candidates=[]) for r in requirements])


@pytest.fixture
def api():
    reviewer = Reviewer()
    app.dependency_overrides[semantic_reviewer_factory] = lambda: lambda: reviewer
    try:
        with TestClient(app) as client:
            yield client, reviewer
            reviewer.release.set()
    finally:
        reviewer.release.set()
        app.dependency_overrides.clear()


def seed(client, *, semantic=True, pdf=True):
    quote = "PDF는 2페이지 이내여야 합니다.\n사업의 기대효과를 설명해야 합니다."
    profile = confirmed_profile(quote, rule="PDF는 2페이지 이내여야 합니다.")
    if semantic:
        item = profiles.anchor(ExtractedRequirement(requirement_id="G002",
            rule="사업의 기대효과를 설명해야 합니다.", modality="MUST", severity="REVIEW",
            verifier="SEMANTIC", condition="always", evidence={"source_section": "내용",
            "quote": "사업의 기대효과를 설명해야 합니다."}, confidence=1), profile.announcement)
        item.extraction_status, item.authoritative = "CONFIRMED", True
        profile.requirements.append(item)
    session = seeded_session(profile)
    proposed = candidate(profile, checker_type="PDF_PAGE_COUNT", field="PAGE_COUNT", value=2,
                         unit="COUNT", selector_value=".pdf")
    proposed.parameter_provenance.source_substring = "2페이지 이내"
    proposals = [proposed]
    if semantic:
        proposals.append(proposed.model_copy(update={"requirement_id": "G002"}))
    session.verification_plan = compile_profile(profile, Planner(proposals))
    sessions.save(session)
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((30, 30), "EPHEMERAL_SENTINEL full private proposal text.")
    content = document.tobytes()
    document.close()
    name = "private.pdf" if pdf else "video.mp4"
    response = client.post("/api/sessions/task08-session/files", files={"files": (name, content)})
    assert response.status_code == 200
    return "/api/sessions/task08-session"


def finish(client, base):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        body = client.get(base).json()
        if body["run_state"] != "RUNNING":
            return body
        time.sleep(.01)
    pytest.fail("background run did not finish")


def test_deterministic_only_validate_remains_synchronous_and_zero_semantic_calls(api):
    client, reviewer = api
    base = seed(client, semantic=False)
    response = client.post(base + "/validate")
    assert response.status_code == 200
    assert response.json()["run_state"] == "COMPLETE"
    assert response.json()["results"][0]["status"] == "PASS"
    assert reviewer.calls == 0


@pytest.mark.parametrize("semantic,pdf,ack,count", [(True, True, True, 1), (True, False, False, 1), (False, True, False, 0)])
def test_readiness_is_local_read_only_and_requires_ack_only_for_callable_work(api, semantic, pdf, ack, count):
    client, reviewer = api
    base = seed(client, semantic=semantic, pdf=pdf)
    before = sessions.session_store().get_session("task08-session").model_dump(mode="json")
    response = client.get(base + "/semantic-readiness")
    assert response.status_code == 200
    assert response.json()["ack_required"] is ack
    assert response.json()["eligible_requirement_count"] == count
    assert "EPHEMERAL_SENTINEL" not in response.text
    assert sessions.session_store().get_session("task08-session").model_dump(mode="json") == before
    assert reviewer.calls == 0


def test_semantic_missing_target_stays_synchronous_and_zero_ai_calls(api):
    client, reviewer = api
    base = seed(client, pdf=False)
    response = client.post(base + "/validate")
    assert response.status_code == 200
    assert response.json()["run_state"] == "COMPLETE"
    result = response.json()["results"][1]
    assert result["semantic_review"]["reason_code"] == "SEMANTIC_TARGET_MISSING"
    assert result["status"] == "REVIEW" and reviewer.calls == 0


def test_ack_missing_rejected_before_run_state_mutation(api):
    client, reviewer = api
    base = seed(client)
    session = sessions.get("task08-session")
    session.results = generic_validation.validate(session, sessions.package_path(session.id)).results
    sessions.save(session)
    before = sessions.session_store().get_session(session.id).model_dump(mode="json")
    response = client.post(base + "/validate")
    assert response.status_code == 409
    assert sessions.session_store().get_session(session.id).model_dump(mode="json") == before
    assert reviewer.calls == 0


def test_semantic_validate_returns_running_promptly_and_rejects_duplicate(api):
    client, reviewer = api
    base = seed(client)
    reviewer.release.clear()
    try:
        start = time.monotonic()
        response = client.post(base + "/validate", json={"semantic_text_ai_acknowledged": True})
        assert time.monotonic() - start < 1
        assert response.status_code == 200 and response.json()["run_state"] == "RUNNING"
        assert response.json()["results"] == []
        assert reviewer.started.wait(2)
        assert client.post(base + "/validate", json={"semantic_text_ai_acknowledged": True}).status_code == 409
        assert client.get(base).json()["run_state"] == "RUNNING"
    finally:
        reviewer.release.set()
    assert finish(client, base)["run_state"] == "COMPLETE"
    assert reviewer.calls == 1


@pytest.mark.parametrize("failure", ["provider", "schema", "provenance", "none"])
def test_semantic_replacement_preserves_deterministic_results_and_no_persisted_text(api, failure):
    client, reviewer = api
    base = seed(client)
    if failure == "provider":
        reviewer.error = RuntimeError("EPHEMERAL_SENTINEL provider request leaked")
    reviewer.malformed = failure == "schema"
    if failure == "provenance":
        reviewer.provenance = {"provider": "malformed"}
    client.post(base + "/validate", json={"semantic_text_ai_acknowledged": True})
    body = finish(client, base)
    assert body["run_state"] == "COMPLETE"
    assert body["status"] == "REVIEW_REQUIRED" and body["validation_complete"] is False
    assert [r["requirement_id"] for r in body["results"]] == ["G001", "G002"]
    assert [r["status"] for r in body["results"]] == ["PASS", "REVIEW"]
    semantic = body["results"][1]
    assert semantic["source_mode"] == "generic_review" and semantic["semantic_review"] is not None
    if failure != "none":
        assert semantic["semantic_review"]["reason_code"] is not None
    assert "EPHEMERAL_SENTINEL" not in json.dumps(body)
    raw = list(sessions.workspace_path("task08-session").glob("run-*-raw.json"))
    assert len(raw) == 1 and "EPHEMERAL_SENTINEL" not in raw[0].read_text(encoding="utf-8")
    assert "EPHEMERAL_SENTINEL" not in sessions.session_store().get_session("task08-session").model_dump_json()


def test_package_change_before_commit_fails_and_publishes_no_current_results(api):
    client, reviewer = api
    base = seed(client)
    path = sessions.package_path("task08-session") / "private.pdf"
    reviewer.mutate = lambda: path.write_bytes(path.read_bytes() + b"changed")
    client.post(base + "/validate", json={"semantic_text_ai_acknowledged": True})
    body = finish(client, base)
    assert body["run_state"] == "FAILED"
    assert body["run_error"] == "PACKAGE_CHANGED_DURING_RUN"
    assert body["results"] == [] and body["status"] == "REVIEW_REQUIRED"
    assert not list(sessions.workspace_path("task08-session").glob("run-*-raw.json"))


@pytest.mark.parametrize("route", ["files", "requirements/G002/review", "profile/confirm", "verification-plan/compile"])
def test_mutations_rejected_while_running_even_before_worker_takes_lock(api, route):
    client, _ = api
    base = seed(client)
    session = sessions.get("task08-session")
    session.run_state = "RUNNING"
    sessions.save(session)
    before = session.model_dump(mode="json")
    if route == "files":
        response = client.post(base + "/" + route, files={"files": ("new.pdf", b"new")})
    else:
        body = {"expected_version": session.generic_profile.version}
        if route.endswith("review"):
            body["action"] = "APPROVE"
        if route == "profile/confirm":
            body["reviewed_full_source"] = True
        response = client.post(base + "/" + route, json=body)
    assert response.status_code == 409
    assert sessions.session_store().get_session(session.id).model_dump(mode="json") == before


def test_guard_unavailable_preserves_deterministic_findings(api, monkeypatch):
    client, reviewer = api
    base = seed(client)
    monkeypatch.setenv("FINAL_CHECK_AI_MAX_OPERATIONS_PER_HOUR", "invalid")
    client.post(base + "/validate", json={"semantic_text_ai_acknowledged": True})
    body = finish(client, base)
    assert body["run_state"] == "COMPLETE"
    assert [r["status"] for r in body["results"]] == ["PASS", "REVIEW"]
    assert body["results"][1]["semantic_review"]["reason_code"] == "SEMANTIC_GUARD_UNAVAILABLE"
    assert reviewer.calls == 0


def test_guard_rejects_semantic_without_discarding_deterministic_results(api, monkeypatch):
    client, reviewer = api
    base = seed(client)
    monkeypatch.setenv("FINAL_CHECK_PUBLIC_GUARD", "1")
    monkeypatch.setenv("FINAL_CHECK_AI_MAX_OPERATIONS_PER_HOUR", "1")
    guard = PublicGuard(sessions.session_store())
    guard.release(guard.reserve("another", "PLAN", "used"))
    client.post(base + "/validate", json={"semantic_text_ai_acknowledged": True})
    body = finish(client, base)
    assert body["run_state"] == "COMPLETE"
    assert [r["status"] for r in body["results"]] == ["PASS", "REVIEW"]
    assert body["results"][1]["semantic_review"]["reason_code"] == "SEMANTIC_GUARD_UNAVAILABLE"
    assert reviewer.calls == 0


def test_stable_snapshot_operation_identity_reuses_quota_and_releases_lease(api):
    client, reviewer = api
    seed(client)
    session = sessions.get("task08-session").model_copy(deep=True)
    package = sessions.package_path(session.id)
    preparation = prepare_semantic_submission(session.generic_profile, package)
    guard = PublicGuard(sessions.session_store(), GuardConfig(enabled=True, global_per_hour=2,
        session_per_hour=2, max_concurrent=1))
    for _ in range(2):
        result = run_generic_preflight(session, package, preparation, reviewer, guard)
        assert [r.status for r in result.results] == ["PASS", "REVIEW"]
    other = guard.reserve("other", "PLAN", "other")
    guard.release(other)
    with pytest.raises(GuardRejected):
        guard.reserve("third", "PLAN", "third")


def test_unavailable_provider_factory_never_runs_for_deterministic_validation(api):
    client, _ = api
    base = seed(client, semantic=False)
    def unavailable():
        raise RuntimeError("provider is not configured")
    app.dependency_overrides[semantic_reviewer_factory] = lambda: unavailable
    body = client.post(base + "/validate").json()
    assert body["run_state"] == "COMPLETE" and body["status"] == "READY"


def test_package_changed_before_provider_call_is_rejected_without_call(api):
    client, reviewer = api
    base = seed(client)
    def factory():
        path = sessions.package_path("task08-session") / "private.pdf"
        path.write_bytes(path.read_bytes() + b"changed")
        return reviewer
    app.dependency_overrides[semantic_reviewer_factory] = lambda: factory
    client.post(base + "/validate", json={"semantic_text_ai_acknowledged": True})
    body = finish(client, base)
    assert body["run_state"] == "FAILED" and body["run_error"] == "PACKAGE_CHANGED_DURING_RUN"
    assert reviewer.calls == 0 and body["results"] == []


def test_degraded_results_still_use_validated_finding_enums(api):
    from app.models.schemas import FindingStatus
    client, reviewer = api
    seed(client, pdf=False)
    session = sessions.get("task08-session")
    package = sessions.package_path(session.id)
    preparation = prepare_semantic_submission(session.generic_profile, package)
    run = run_generic_preflight(session, package, preparation, reviewer, PublicGuard(sessions.session_store()))
    assert isinstance(run.results[1].status, FindingStatus)


def test_initial_receipt_mismatch_invalidates_previous_ready_results(api):
    client, reviewer = api
    base = seed(client, semantic=False)
    original = client.post(base + "/validate").json()
    assert original["status"] == "READY"
    path = sessions.package_path("task08-session") / "private.pdf"
    path.write_bytes(path.read_bytes() + b"changed")
    response = client.post(base + "/validate")
    assert response.status_code in {409, 502}
    body = client.get(base).json()
    assert body["run_state"] == "FAILED"
    assert body["run_error"] == "PACKAGE_CHANGED_DURING_RUN"
    assert body["status"] == "REVIEW_REQUIRED" and body["results"] == []
    assert body["previous_results"] == original["results"]
    assert reviewer.calls == 0
