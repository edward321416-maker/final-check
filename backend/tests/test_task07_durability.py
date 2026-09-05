import os
import socket
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import httpx
import pytest

from app.models.jobs import ExtractionJob, JobStage, JobStatus
from app.models.profiles import ExtractedRequirement, ProviderProvenance, ReviewRequest, SemanticReview
from app.models.schemas import CheckSession
from app.services import jobs, profiles, sessions
from app.services.announcement_input import source_from_bytes
from app.services.storage import LocalArtifactStore, SQLiteRuntimeStore


SOURCE = "지원자는 MP4 영상을 제출해야 합니다. 개인정보 동의서를 포함해야 합니다."
PROVENANCE = ProviderProvenance(
    provider="test-provider", model="test-model", prompt_version="test-v1",
    prompt_sha256="a" * 64, execution_kind="SIMULATED",
)


def candidate(index: int, severity: str = "REVIEW") -> ExtractedRequirement:
    quote = "지원자는 MP4 영상을 제출해야 합니다."
    return ExtractedRequirement(
        requirement_id=f"A{index:03d}", rule=f"MP4 영상을 제출해야 합니다 {index}",
        modality="MUST", severity=severity, verifier="SEMANTIC", condition="제출 시",
        evidence={"source_section": "본문", "quote": quote}, confidence=0.8,
    )


class Generator:
    provenance = PROVENANCE
    requires_background = False

    def __init__(self, count=1, error: Exception | None = None):
        self.count = count
        self.error = error
        self.calls = 0

    def generate(self, source):
        self.calls += 1
        if self.error:
            raise self.error
        return [candidate(index + 1) for index in range(self.count)]


class Reviewer:
    provenance = PROVENANCE
    requires_background = False

    def __init__(self, fail_call: int | None = None):
        self.fail_call = fail_call
        self.calls: list[list[str]] = []

    def review(self, source, batch):
        self.calls.append([item.requirement_id for item in batch])
        if self.fail_call == len(self.calls):
            raise RuntimeError("simulated batch interruption")
        return [SemanticReview(
            requirement_id=item.requirement_id, decision="KEEP", reason="supported",
            semantic_support=True, condition_preserved=True, modality_supported=True,
            reviewer=self.provenance,
        ) for item in batch]


def make_session(store: SQLiteRuntimeStore, *, updated_delta: timedelta | None = None) -> CheckSession:
    stamp = sessions.now()
    if updated_delta:
        stamp -= updated_delta
    source = source_from_bytes("notice.txt", SOURCE.encode(), "TEXT")
    session = CheckSession(
        id="11111111-1111-4111-8111-111111111111", created_at=stamp, updated_at=stamp,
        mode="custom", announcement_name="notice.txt", generic_profile=profiles.new_profile(source),
    )
    store.save_session(session)
    return session


def make_job(session: CheckSession, *, status=JobStatus.PENDING, attempt=0) -> ExtractionJob:
    assert session.generic_profile
    return ExtractionJob.new(
        session_id=session.id, profile=session.generic_profile, job_kind="TWO_STAGE_EXTRACTION",
        status=status, attempt=attempt, provider_provenance=[PROVENANCE],
    )


def rebuild(data_dir: Path) -> SQLiteRuntimeStore:
    return SQLiteRuntimeStore(data_dir)


def test_t1_session_persists_across_store_reconstruction(tmp_path):
    store = SQLiteRuntimeStore(tmp_path)
    original = make_session(store)
    assert rebuild(tmp_path).get_session(original.id) == original


def test_t2_human_review_progress_survives_restart(tmp_path):
    store = SQLiteRuntimeStore(tmp_path)
    session = make_session(store)
    assert session.generic_profile
    extracted = profiles.extract(session.generic_profile, Generator(), Reviewer())
    reviewed = profiles.review(
        extracted, "A001", ReviewRequest(expected_version=extracted.version, action="APPROVE")
    )
    session.generic_profile = reviewed
    store.save_session(session)
    restored = rebuild(tmp_path).get_session(session.id)
    assert restored.generic_profile.requirements[0].authoritative is True
    assert restored.generic_profile.history[-1].action == "APPROVE"


def test_t3_confirmed_profile_survives_restart(tmp_path):
    store = SQLiteRuntimeStore(tmp_path)
    session = make_session(store)
    extracted = profiles.extract(session.generic_profile, Generator(), Reviewer())
    approved = profiles.review(
        extracted, "A001", ReviewRequest(expected_version=extracted.version, action="APPROVE")
    )
    session.generic_profile = profiles.confirm(approved)
    store.save_session(session)
    assert rebuild(tmp_path).get_session(session.id).generic_profile.status == "CONFIRMED"


def test_t4_ai_blocker_remains_non_authoritative_after_restart(tmp_path):
    store = SQLiteRuntimeStore(tmp_path)
    session = make_session(store)
    session.generic_profile = profiles.extract(session.generic_profile, Generator(), Reviewer())
    session.generic_profile.requirements[0].severity = "BLOCKER"
    store.save_session(session)
    item = rebuild(tmp_path).get_session(session.id).generic_profile.requirements[0]
    assert item.severity == "BLOCKER" and item.authoritative is False


def test_t5_announcement_artifact_survives_restart(tmp_path):
    artifacts = LocalArtifactStore(tmp_path)
    path = artifacts.write_announcement("session-a", b"announcement")
    assert LocalArtifactStore(tmp_path).announcement_path("session-a").read_bytes() == path.read_bytes()


def test_t6_submission_artifact_survives_restart(tmp_path):
    artifacts = LocalArtifactStore(tmp_path)
    staging = artifacts.begin_submission("session-a")
    (staging / "entry.pdf").write_bytes(b"pdf")
    artifacts.commit_submission("session-a", staging)
    target = LocalArtifactStore(tmp_path).submission_path("session-a")
    backup = target.parent / "submission-backup-interrupted"
    target.replace(backup)
    assert (LocalArtifactStore(tmp_path).submission_path("session-a") / "entry.pdf").read_bytes() == b"pdf"


@pytest.mark.parametrize("stale_status", [JobStatus.PENDING, JobStatus.RUNNING])
def test_t7_abandoned_job_becomes_retryable_after_restart(tmp_path, stale_status):
    store = SQLiteRuntimeStore(tmp_path)
    session = make_session(store)
    job = make_job(session, status=stale_status, attempt=1)
    store.save_job(job)
    recovered = rebuild(tmp_path).recover_stale_jobs()
    assert recovered == [job.job_id]
    assert rebuild(tmp_path).get_job(job.job_id).status == JobStatus.RETRYABLE


def test_t8_completed_stage1_is_not_called_twice_after_restart(isolated_runtime):
    session = sessions.create("custom")
    session.announcement_name = "notice.txt"
    session.generic_profile = profiles.new_profile(source_from_bytes("notice.txt", SOURCE.encode(), "TEXT"))
    sessions.save(session)
    generator, reviewer = Generator(2), Reviewer(fail_call=1)
    job = jobs.create_or_get(session, generator, reviewer)
    jobs.execute(job.job_id, generator, reviewer)
    assert sessions.job_store().get_job(job.job_id).stage == JobStage.GATE_COMPLETE
    jobs.execute(job.job_id, generator, Reviewer())
    assert generator.calls == 1


def test_t9_completed_stage2_batch_is_not_repeated(isolated_runtime):
    session = sessions.create("custom")
    session.announcement_name = "notice.txt"
    session.generic_profile = profiles.new_profile(source_from_bytes("notice.txt", SOURCE.encode(), "TEXT"))
    sessions.save(session)
    generator, first_reviewer = Generator(51), Reviewer(fail_call=2)
    job = jobs.create_or_get(session, generator, first_reviewer)
    jobs.execute(job.job_id, generator, first_reviewer)
    assert first_reviewer.calls[0] == [f"A{i:03d}" for i in range(1, 51)]
    second_reviewer = Reviewer()
    jobs.execute(job.job_id, generator, second_reviewer)
    assert second_reviewer.calls == [["A051"]]


def test_t10_duplicate_extract_identity_reuses_job(isolated_runtime):
    session = sessions.create("custom")
    session.generic_profile = profiles.new_profile(source_from_bytes("notice.txt", SOURCE.encode(), "TEXT"))
    sessions.save(session)
    first = jobs.create_or_get(session, Generator(), Reviewer())
    second = jobs.create_or_get(session, Generator(), Reviewer())
    assert first.job_id == second.job_id
    assert sessions.job_store().count_jobs() == 1


def test_t11_retry_limit_is_enforced_without_automatic_loop(isolated_runtime):
    session = sessions.create("custom")
    session.generic_profile = profiles.new_profile(source_from_bytes("notice.txt", SOURCE.encode(), "TEXT"))
    sessions.save(session)
    generator = Generator(error=RuntimeError("provider unavailable"))
    job = jobs.create_or_get(session, generator, Reviewer())
    for _ in range(jobs.MAX_ATTEMPTS):
        jobs.execute(job.job_id, generator, Reviewer())
    stored = sessions.job_store().get_job(job.job_id)
    assert stored.status == JobStatus.FAILED and stored.attempt == jobs.MAX_ATTEMPTS
    assert generator.calls == jobs.MAX_ATTEMPTS


def test_t12_expired_safe_session_cleanup_removes_metadata_and_artifacts(tmp_path):
    store = SQLiteRuntimeStore(tmp_path)
    artifacts = LocalArtifactStore(tmp_path)
    session = make_session(store, updated_delta=timedelta(hours=2))
    artifacts.write_announcement(session.id, b"old")
    removed = store.cleanup_sessions(sessions.now() - timedelta(hours=1), artifacts)
    assert removed == [session.id]
    assert store.get_session_or_none(session.id) is None
    assert not artifacts.session_path(session.id).exists()


@pytest.mark.parametrize("status", [JobStatus.RUNNING, JobStatus.RETRYABLE])
def test_t13_active_or_retryable_session_is_not_cleaned(tmp_path, status):
    store = SQLiteRuntimeStore(tmp_path)
    artifacts = LocalArtifactStore(tmp_path)
    session = make_session(store, updated_delta=timedelta(hours=2))
    store.save_job(make_job(session, status=status, attempt=1))
    assert store.cleanup_sessions(sessions.now() - timedelta(hours=1), artifacts) == []
    assert store.get_session(session.id).id == session.id


def test_t13_process_active_session_is_not_cleaned(tmp_path):
    store = SQLiteRuntimeStore(tmp_path)
    artifacts = LocalArtifactStore(tmp_path)
    session = make_session(store, updated_delta=timedelta(hours=2))
    assert store.cleanup_sessions(
        sessions.now() - timedelta(hours=1), artifacts, {session.id}
    ) == []
    assert store.get_session(session.id).id == session.id


def test_t14_provider_secrets_and_raw_errors_are_not_persisted(isolated_runtime):
    secret = "sk-test-secret-never-store"
    session = sessions.create("custom")
    session.generic_profile = profiles.new_profile(source_from_bytes("notice.txt", SOURCE.encode(), "TEXT"))
    sessions.save(session)
    job = jobs.create_or_get(session, Generator(error=RuntimeError(secret)), Reviewer())
    jobs.execute(job.job_id, Generator(error=RuntimeError(secret)), Reviewer())
    paths = list(Path(isolated_runtime).rglob("*"))
    assert all(secret.encode() not in path.read_bytes() for path in paths if path.is_file())
    assert "auth.json" not in "\n".join(str(path) for path in paths)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start_backend(data_dir: Path, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env["FINAL_CHECK_DATA_DIR"] = str(data_dir)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=Path(__file__).parents[1], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            if httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=0.5).status_code == 200:
                return process
        except httpx.HTTPError:
            time.sleep(0.1)
    process.terminate()
    raise AssertionError("backend did not start")


def test_actual_backend_process_restart_restores_meaningful_profile(tmp_path):
    port = _free_port()
    data_dir = tmp_path / "actual-runtime"
    first = _start_backend(data_dir, port)
    try:
        created = httpx.post(f"http://127.0.0.1:{port}/api/sessions", json={"mode": "custom"}).json()
        updated = httpx.post(
            f"http://127.0.0.1:{port}/api/sessions/{created['id']}/announcement-text",
            json={"name": "restart.txt", "text": SOURCE},
        ).json()
        assert updated["generic_profile"]["announcement"]["text"] == SOURCE
    finally:
        first.terminate()
        first.wait(timeout=10)
    second = _start_backend(data_dir, port)
    try:
        restored = httpx.get(f"http://127.0.0.1:{port}/api/sessions/{created['id']}")
        assert restored.status_code == 200
        assert restored.json()["generic_profile"]["announcement"]["name"] == "restart.txt"
    finally:
        second.terminate()
        second.wait(timeout=10)
