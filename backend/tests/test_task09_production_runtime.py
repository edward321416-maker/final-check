import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services import ai_providers, semantic_provider, sessions, verifier_planner
from app.services.public_guard import GuardConfig, GuardRejected, PublicGuard
from app.services.storage import SQLiteRuntimeStore


ROOT = Path(__file__).resolve().parents[2]


def guard(tmp_path, *, global_limit=40, session_limit=6, concurrent=2, now=None):
    store = SQLiteRuntimeStore(tmp_path)
    config = GuardConfig(
        enabled=True,
        global_per_hour=global_limit,
        session_per_hour=session_limit,
        max_concurrent=concurrent,
    )
    return PublicGuard(store, config=config, clock=(lambda: now) if now else None)


def test_zero_cost_provider_keeps_codex_and_rejects_openai_api(monkeypatch):
    monkeypatch.setenv("FINAL_CHECK_AI_PROVIDER", "codex")
    assert isinstance(ai_providers.get_generator(), ai_providers.CodexCliRequirementGenerator)
    assert isinstance(ai_providers.get_reviewer(), ai_providers.CodexCliSemanticReviewer)
    assert isinstance(verifier_planner.get_verification_planner(), verifier_planner.CodexCliVerificationPlanner)
    assert isinstance(
        semantic_provider.get_submission_semantic_reviewer(),
        semantic_provider.CodexCliSubmissionSemanticReviewer,
    )

    monkeypatch.setenv("FINAL_CHECK_AI_PROVIDER", "openai-api")
    with pytest.raises(ai_providers.ProviderExecutionError):
        ai_providers.get_generator()
    with pytest.raises(ai_providers.ProviderExecutionError):
        ai_providers.get_reviewer()
    with pytest.raises(ai_providers.ProviderExecutionError):
        verifier_planner.get_verification_planner()
    with pytest.raises(ai_providers.ProviderExecutionError):
        semantic_provider.get_submission_semantic_reviewer()


def test_codex_status_requires_auth_and_locked_model(monkeypatch, tmp_path):
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setenv("FINAL_CHECK_AI_PROVIDER", "codex")
    monkeypatch.setenv("FINAL_CHECK_AI_MODEL", "gpt-5.6-sol")
    monkeypatch.setenv("FINAL_CHECK_AI_REASONING", "high")
    monkeypatch.setattr(ai_providers, "codex_binary", lambda: Path("codex"))
    monkeypatch.setattr(ai_providers.subprocess, "check_output", lambda *_args, **_kwargs: "codex-cli test")

    status = ai_providers.provider_status()
    assert status == {
        "mode": "actual-local-ai",
        "provider": "Codex CLI",
        "version": "codex-cli test",
        "configured": True,
        "model": "gpt-5.6-sol",
        "reasoning": "high",
    }

    monkeypatch.setenv("FINAL_CHECK_AI_MODEL", "another-model")
    assert ai_providers.provider_status()["configured"] is False


def test_global_and_session_hourly_quotas(tmp_path):
    item = guard(tmp_path, global_limit=2, session_limit=1)
    first = item.reserve("s1", "EXTRACT", "extract:s1:1")
    item.release(first)
    with pytest.raises(GuardRejected) as session_rejection:
        item.reserve("s1", "PLAN", "plan:s1:1")
    assert session_rejection.value.reason == "SESSION_QUOTA"

    second = item.reserve("s2", "PLAN", "plan:s2:1")
    item.release(second)
    with pytest.raises(GuardRejected) as global_rejection:
        item.reserve("s3", "EXTRACT", "extract:s3:1")
    assert global_rejection.value.reason == "GLOBAL_QUOTA"


def test_polling_idempotency_and_concurrency(tmp_path):
    item = guard(tmp_path, global_limit=2, session_limit=2, concurrent=1)
    ignored = item.reserve("s1", "POLL", "poll:s1")
    assert not ignored.counted

    first = item.reserve("s1", "EXTRACT", "extract:s1:1")
    reused = item.reserve("s1", "EXTRACT", "extract:s1:1")
    assert reused.reused and not reused.counted
    with pytest.raises(GuardRejected) as raised:
        item.reserve("s2", "PLAN", "plan:s2:1")
    assert raised.value.reason == "CONCURRENCY"
    item.release(first)
    second = item.reserve("s2", "PLAN", "plan:s2:1")
    item.release(second)


def test_quota_survives_store_reconstruction(tmp_path):
    stamp = datetime(2026, 9, 7, tzinfo=timezone.utc)
    first = guard(tmp_path, global_limit=1, now=stamp)
    reservation = first.reserve("s1", "EXTRACT", "extract:s1:1")
    first.release(reservation)
    second = guard(tmp_path, global_limit=1, now=stamp + timedelta(minutes=5))
    with pytest.raises(GuardRejected):
        second.reserve("s2", "PLAN", "plan:s2:1")


def test_public_health_uses_codex_without_exposing_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("FINAL_CHECK_ENV", "production")
    monkeypatch.setenv("FINAL_CHECK_AI_PROVIDER", "codex")
    monkeypatch.setenv("FINAL_CHECK_PUBLIC_GUARD", "1")
    monkeypatch.setenv("FINAL_CHECK_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(routes, "provider_status", lambda: {
        "mode": "actual-local-ai",
        "provider": "Codex CLI",
        "version": "codex-cli test",
        "configured": True,
        "model": "gpt-5.6-sol",
        "reasoning": "high",
    })
    sessions.configure(tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["runtime"] == "single-node"
    assert body["storage"] == "available"
    assert body["ffprobe"]["status"] == "available"
    assert body["ai"] == {
        "provider": "Codex CLI",
        "configured": True,
        "model": "gpt-5.6-sol",
        "reasoning": "high",
    }
    assert "auth.json" not in response.text


@pytest.mark.parametrize(("provider", "guard_enabled"), [
    ("local-fallback", "1"),
    ("codex", "0"),
])
def test_public_health_fails_closed_on_wrong_provider_or_disabled_guard(
    monkeypatch, tmp_path, provider, guard_enabled,
):
    monkeypatch.setenv("FINAL_CHECK_ENV", "production")
    monkeypatch.setenv("FINAL_CHECK_AI_PROVIDER", provider)
    monkeypatch.setenv("FINAL_CHECK_PUBLIC_GUARD", guard_enabled)
    monkeypatch.setenv("FINAL_CHECK_DATA_DIR", str(tmp_path))
    sessions.configure(tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_public_upload_limits_are_environment_driven(monkeypatch):
    monkeypatch.setenv("FINAL_CHECK_MAX_FILE_BYTES", str(16 * 1024 * 1024))
    monkeypatch.setenv("FINAL_CHECK_MAX_PACKAGE_BYTES", str(24 * 1024 * 1024))
    monkeypatch.setenv("FINAL_CHECK_MAX_FILES", "8")
    assert routes.upload_limits() == (16 * 1024 * 1024, 24 * 1024 * 1024, 8)


def test_ngrok_public_runtime_contract():
    start = (ROOT / "scripts/start-public-judge.ps1").read_text(encoding="utf-8")
    stop = (ROOT / "scripts/stop-public-judge.ps1").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    deployment = (ROOT / "docs/TASK09_PUBLIC_DEPLOYMENT.md").read_text(encoding="utf-8")

    assert "FINAL_CHECK_AI_PROVIDER" in start and "codex" in start
    assert "FINAL_CHECK_ENV" in start and "production" in start
    assert "--workers" in start and "1" in start
    assert "--url" in start and "ngrok" in start
    assert "-WindowStyle Hidden" in start
    assert "StartTime" in stop and "Stop-Process" in stop
    assert "python-version: '3.14'" in workflow
    assert "node-version: '24'" in workflow
    assert "docker build" not in workflow
    assert "ngrok Free" in deployment
    assert "OPENAI_API_KEY" not in deployment
    assert not (ROOT / "backend/app/services/openai_responses.py").exists()
    assert not (ROOT / "deploy/backend.Dockerfile").exists()
    assert not (ROOT / "deploy/frontend.Dockerfile").exists()


def test_locked_sources_are_unchanged():
    locks = {
        "benchmarks/task04/gold_manifest.json": "035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89",
        "backend/app/validators/frozen_v15/validator_v1_5.py": "4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11",
        "backend/app/prompts/task06/stage1-v1.txt": "52b226089eddf6fb109ab07f676110c7dea48c602397a7d6c283384e3be4d7f4",
        "backend/app/prompts/task06/stage2-v1.txt": "be838b1ef8d57f921147a3dfb993fa3237fb56dd766b825c883b644aa131163f",
        "backend/app/prompts/task08/planner-v1.txt": "096fd93cd2c3770cd49dcdbe6131e0abda4ea8b3e074728dc7b45e219f36a4a6",
    }
    for path, expected in locks.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
