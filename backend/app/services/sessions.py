"""Durable session facade with process-local locks for the single-node MVP."""
from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.models.schemas import CheckSession
from app.services.storage import LocalArtifactStore, SQLiteRuntimeStore, default_data_dir

SESSIONS: dict[str, CheckSession] = {}
WORKSPACES: dict[str, "DirectoryRef"] = {}
PACKAGES: dict[str, "DirectoryRef"] = {}
LOCKS: dict[str, asyncio.Lock] = {}
TTL = timedelta(hours=1)
MAX_SESSIONS = 100

_STORE: SQLiteRuntimeStore | None = None
_ARTIFACTS: LocalArtifactStore | None = None
_DATA_DIR: Path | None = None


@dataclass
class DirectoryRef:
    name: str


class DurableStagingDirectory:
    def __init__(self, path: Path):
        self.path = path
        self.name = str(path)
        self._committed = False

    def __enter__(self) -> str:
        return self.name

    def __exit__(self, *_args) -> None:
        if not self._committed:
            self.cleanup()

    def cleanup(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path)


def now() -> datetime:
    return datetime.now(timezone.utc)


def configure(data_dir: Path | str | None = None) -> list[str]:
    global _STORE, _ARTIFACTS, _DATA_DIR
    close_all()
    _DATA_DIR = Path(data_dir).resolve() if data_dir is not None else default_data_dir()
    _STORE = SQLiteRuntimeStore(_DATA_DIR)
    _ARTIFACTS = LocalArtifactStore(_DATA_DIR)
    recovered = _STORE.recover_stale_jobs()
    for job_id in recovered:
        job = _STORE.get_job(job_id)
        session = _STORE.get_session_or_none(job.session_id)
        if session is None:
            continue
        session.current_job_id = job.job_id
        session.current_job = job.summary()
        if session.generic_profile and session.generic_profile.pipeline_status == "RUNNING":
            session.generic_profile.pipeline_status = "REVIEW_REQUIRED"
            session.generic_profile.pipeline_error = "PROCESS_RESTART"
            session.generic_profile.status = "REVIEW_REQUIRED"
            session.generic_profile.notices = [
                "이전 backend process의 AI job을 복구했습니다. 완료된 checkpoint부터 명시적으로 다시 시도하세요."
            ]
        if session.verification_plan_state == "RUNNING":
            session.verification_plan_state = "REVIEW_REQUIRED"
            session.verification_plan_error = "PROCESS_RESTART"
            session.source_mode = "generic_review"
        _STORE.save_session(session)
    return recovered


def _ensure_configured() -> None:
    expected = default_data_dir()
    if _STORE is None or _ARTIFACTS is None or _DATA_DIR != expected:
        configure(expected)


def session_store() -> SQLiteRuntimeStore:
    _ensure_configured()
    assert _STORE is not None
    return _STORE


def job_store() -> SQLiteRuntimeStore:
    return session_store()


def artifact_store() -> LocalArtifactStore:
    _ensure_configured()
    assert _ARTIFACTS is not None
    return _ARTIFACTS


def _cache(session: CheckSession) -> CheckSession:
    artifacts = artifact_store()
    root = artifacts.ensure_session(session.id)
    SESSIONS[session.id] = session
    WORKSPACES[session.id] = DirectoryRef(str(root))
    package = artifacts.submission_path(session.id)
    if package.is_dir():
        PACKAGES[session.id] = DirectoryRef(str(package))
    LOCKS.setdefault(session.id, asyncio.Lock())
    return session


def remove(session_id: str) -> None:
    session_store().delete_session(session_id)
    artifact_store().delete_session(session_id)
    SESSIONS.pop(session_id, None)
    WORKSPACES.pop(session_id, None)
    PACKAGES.pop(session_id, None)
    LOCKS.pop(session_id, None)


def close_all() -> None:
    """Release process-local references without deleting durable state."""
    SESSIONS.clear()
    WORKSPACES.clear()
    PACKAGES.clear()
    LOCKS.clear()


def cleanup() -> list[str]:
    store = session_store()
    for session in list(SESSIONS.values()):
        store.save_session(session)
    process_active = {key for key, lock in LOCKS.items() if lock.locked()}
    removed = store.cleanup_sessions(now() - TTL, artifact_store(), process_active)
    for key in removed:
        SESSIONS.pop(key, None)
        WORKSPACES.pop(key, None)
        PACKAGES.pop(key, None)
        LOCKS.pop(key, None)
    return removed


def startup() -> list[str]:
    return configure(default_data_dir())


def create(mode: str) -> CheckSession:
    cleanup()
    if session_store().count_sessions() >= MAX_SESSIONS:
        raise HTTPException(503, "Local session capacity reached.")
    stamp = now()
    session = CheckSession(id=str(uuid4()), created_at=stamp, updated_at=stamp, mode=mode)
    session_store().save_session(session)
    return _cache(session)


def get(session_id: str) -> CheckSession:
    cleanup()
    if session_id in SESSIONS:
        return SESSIONS[session_id]
    session = session_store().get_session_or_none(session_id)
    if session is None:
        raise HTTPException(404, "Session expired or missing. Start a new check.")
    return _cache(session)


def save(session: CheckSession, *, touch: bool = True) -> CheckSession:
    if touch:
        session.updated_at = now()
    session_store().save_session(session)
    return _cache(session)


def new_package(session_id: str) -> DurableStagingDirectory:
    get(session_id)
    return DurableStagingDirectory(artifact_store().begin_submission(session_id))


def replace_package(session_id: str, package: DurableStagingDirectory) -> None:
    target = artifact_store().commit_submission(session_id, package.path)
    package._committed = True
    PACKAGES[session_id] = DirectoryRef(str(target))


def package_path(session_id: str) -> Path:
    get(session_id)
    path = artifact_store().submission_path(session_id)
    if not path.is_dir():
        raise HTTPException(409, "Upload a submission package first.")
    PACKAGES[session_id] = DirectoryRef(str(path))
    return path


def write_announcement(session_id: str, data: bytes) -> Path:
    get(session_id)
    return artifact_store().write_announcement(session_id, data)


def workspace_path(session_id: str) -> Path:
    get(session_id)
    return artifact_store().ensure_session(session_id)
