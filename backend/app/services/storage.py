"""Small durable boundaries backed by SQLite and application-owned paths."""
from __future__ import annotations

import re
import shutil
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.models.jobs import ExtractionJob, JobStatus
from app.models.schemas import CheckSession


class SessionStore(Protocol):
    def save_session(self, session: CheckSession) -> CheckSession: ...
    def get_session_or_none(self, session_id: str) -> CheckSession | None: ...


class JobStore(Protocol):
    def create_or_get_job(self, job: ExtractionJob) -> ExtractionJob: ...
    def save_job(self, job: ExtractionJob) -> ExtractionJob: ...
    def get_job(self, job_id: str) -> ExtractionJob: ...


class ArtifactStore(Protocol):
    def write_announcement(self, session_id: str, content: bytes) -> Path: ...
    def submission_path(self, session_id: str) -> Path: ...
    def delete_session(self, session_id: str) -> None: ...


def default_data_dir() -> Path:
    import os

    configured = os.environ.get("FINAL_CHECK_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).resolve().parents[3] / ".final-check" / "runtime").resolve()


class SQLiteRuntimeStore:
    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "runtime.sqlite3"
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS sessions ("
                "id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS jobs ("
                "job_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, profile_id TEXT NOT NULL, "
                "profile_version INTEGER NOT NULL, job_kind TEXT NOT NULL, status TEXT NOT NULL, "
                "updated_at TEXT NOT NULL, payload TEXT NOT NULL, "
                "UNIQUE(session_id, profile_id, profile_version, job_kind), "
                "FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE)"
            )
            connection.execute("CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs(status)")

    def save_session(self, session: CheckSession) -> CheckSession:
        payload = session.model_dump_json()
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO sessions(id, updated_at, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at, payload=excluded.payload",
                (session.id, session.updated_at.isoformat(), payload),
            )
        return session

    def get_session_or_none(self, session_id: str) -> CheckSession | None:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT payload FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return CheckSession.model_validate_json(row[0]) if row else None

    def get_session(self, session_id: str) -> CheckSession:
        session = self.get_session_or_none(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def count_sessions(self) -> int:
        with self._lock, self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])

    def delete_session(self, session_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def create_or_get_job(self, job: ExtractionJob) -> ExtractionJob:
        identity = (job.session_id, job.profile_id, job.profile_version, job.job_kind)
        with self._lock, self._connect() as connection:
            existing = connection.execute(
                "SELECT payload FROM jobs WHERE session_id=? AND profile_id=? AND profile_version=? AND job_kind=?",
                identity,
            ).fetchone()
            if existing:
                return ExtractionJob.model_validate_json(existing[0])
            connection.execute(
                "INSERT INTO jobs(job_id, session_id, profile_id, profile_version, job_kind, status, updated_at, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job.job_id, job.session_id, job.profile_id, job.profile_version, job.job_kind,
                    job.status.value, job.updated_at.isoformat(), job.model_dump_json(),
                ),
            )
        return job

    def save_job(self, job: ExtractionJob) -> ExtractionJob:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO jobs(job_id, session_id, profile_id, profile_version, job_kind, status, updated_at, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(job_id) DO UPDATE SET "
                "status=excluded.status, updated_at=excluded.updated_at, payload=excluded.payload",
                (
                    job.job_id, job.session_id, job.profile_id, job.profile_version, job.job_kind,
                    job.status.value, job.updated_at.isoformat(), job.model_dump_json(),
                ),
            )
        return job

    def get_job(self, job_id: str) -> ExtractionJob:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT payload FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if not row:
            raise KeyError(job_id)
        return ExtractionJob.model_validate_json(row[0])

    def count_jobs(self) -> int:
        with self._lock, self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])

    def recover_stale_jobs(self) -> list[str]:
        recovered: list[str] = []
        stamp = datetime.now(timezone.utc)
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT job_id, payload FROM jobs WHERE status IN (?, ?)",
                (JobStatus.PENDING.value, JobStatus.RUNNING.value),
            ).fetchall()
            for job_id, payload in rows:
                job = ExtractionJob.model_validate_json(payload)
                job.status = JobStatus.RETRYABLE
                job.error_category = "PROCESS_RESTART"
                job.updated_at = stamp
                connection.execute(
                    "UPDATE jobs SET status=?, updated_at=?, payload=? WHERE job_id=?",
                    (job.status.value, stamp.isoformat(), job.model_dump_json(), job_id),
                )
                recovered.append(job_id)
        return recovered

    def jobs_for_session(self, session_id: str) -> list[ExtractionJob]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM jobs WHERE session_id=? ORDER BY updated_at DESC", (session_id,)
            ).fetchall()
        return [ExtractionJob.model_validate_json(row[0]) for row in rows]

    def cleanup_sessions(self, cutoff: datetime, artifacts: ArtifactStore,
                         protected_session_ids: set[str] | None = None) -> list[str]:
        protected = (JobStatus.PENDING.value, JobStatus.RUNNING.value, JobStatus.RETRYABLE.value)
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT id FROM sessions WHERE updated_at < ? AND id NOT IN ("
                "SELECT session_id FROM jobs WHERE status IN (?, ?, ?)) ORDER BY id",
                (cutoff.isoformat(), *protected),
            ).fetchall()
            process_active = protected_session_ids or set()
            removed = [row[0] for row in rows if row[0] not in process_active]
            for session_id in removed:
                connection.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        for session_id in removed:
            artifacts.delete_session(session_id)
        return removed


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class LocalArtifactStore:
    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir).resolve()
        self.sessions_root = self.data_dir / "sessions"
        self.sessions_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_id(session_id: str) -> str:
        if not _SAFE_ID.fullmatch(session_id):
            raise ValueError("Invalid application session ID")
        return session_id

    def session_path(self, session_id: str) -> Path:
        return self.sessions_root / self._validate_id(session_id)

    def ensure_session(self, session_id: str) -> Path:
        path = self.session_path(session_id)
        (path / "announcement").mkdir(parents=True, exist_ok=True)
        return path

    def announcement_path(self, session_id: str) -> Path:
        return self.session_path(session_id) / "announcement" / "source.bin"

    def write_announcement(self, session_id: str, content: bytes) -> Path:
        target = self.ensure_session(session_id) / "announcement" / "source.bin"
        temporary = target.with_suffix(f".tmp-{uuid4().hex}")
        temporary.write_bytes(content)
        temporary.replace(target)
        return target

    def begin_submission(self, session_id: str) -> Path:
        root = self.ensure_session(session_id)
        path = root / f"submission-staging-{uuid4().hex}"
        path.mkdir()
        return path

    def commit_submission(self, session_id: str, staging: Path) -> Path:
        root = self.ensure_session(session_id).resolve()
        staging = staging.resolve()
        if staging.parent != root or not staging.name.startswith("submission-staging-"):
            raise ValueError("Submission staging path is outside application storage")
        target = root / "submission"
        backup = root / f"submission-backup-{uuid4().hex}"
        if target.exists():
            target.replace(backup)
        try:
            staging.replace(target)
        except Exception:
            if backup.exists() and not target.exists():
                backup.replace(target)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return target

    def submission_path(self, session_id: str) -> Path:
        root = self.session_path(session_id)
        target = root / "submission"
        backups = sorted(root.glob("submission-backup-*"), key=lambda path: path.stat().st_mtime, reverse=True) if root.exists() else []
        if not target.exists() and backups:
            backups.pop(0).replace(target)
        for backup in backups:
            if backup.exists():
                shutil.rmtree(backup)
        return target

    def delete_session(self, session_id: str) -> None:
        target = self.session_path(session_id).resolve()
        if target.parent != self.sessions_root.resolve():
            raise ValueError("Refusing to delete outside application storage")
        if target.exists():
            shutil.rmtree(target)
