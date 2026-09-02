import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from uuid import uuid4
from fastapi import HTTPException
from app.models.schemas import CheckSession

SESSIONS: dict[str, CheckSession] = {}
WORKSPACES: dict[str, tempfile.TemporaryDirectory] = {}
PACKAGES: dict[str, tempfile.TemporaryDirectory] = {}
LOCKS: dict[str, asyncio.Lock] = {}
TTL = timedelta(hours=1)
MAX_SESSIONS = 100


def now() -> datetime:
    return datetime.now(timezone.utc)


def remove(session_id: str) -> None:
    # Delete only application-created ephemeral directories, never user paths.
    package = PACKAGES.pop(session_id, None)
    if package:
        package.cleanup()
    workspace = WORKSPACES.pop(session_id, None)
    if workspace:
        workspace.cleanup()
    SESSIONS.pop(session_id, None)
    LOCKS.pop(session_id, None)


def close_all() -> None:
    for key in list(SESSIONS):
        remove(key)


def cleanup() -> None:
    for key, session in list(SESSIONS.items()):
        if now() - session.updated_at > TTL and not LOCKS[key].locked():
            remove(key)


def create(mode: str) -> CheckSession:
    cleanup()
    if len(SESSIONS) >= MAX_SESSIONS:
        raise HTTPException(503, "Local session capacity reached.")
    session = CheckSession(id=str(uuid4()), created_at=now(), updated_at=now(), mode=mode)
    SESSIONS[session.id] = session
    WORKSPACES[session.id] = tempfile.TemporaryDirectory(prefix="final_check_")
    LOCKS[session.id] = asyncio.Lock()
    return session


def get(session_id: str) -> CheckSession:
    cleanup()
    if session_id not in SESSIONS:
        raise HTTPException(404, "Session expired or missing. Start a new check.")
    return SESSIONS[session_id]


def save(session: CheckSession) -> CheckSession:
    session.updated_at = now()
    SESSIONS[session.id] = session
    return session


def new_package(session_id: str) -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix="package_", dir=WORKSPACES[session_id].name)


def replace_package(session_id: str, package: tempfile.TemporaryDirectory) -> None:
    previous = PACKAGES.get(session_id)
    PACKAGES[session_id] = package
    if previous:
        previous.cleanup()


def package_path(session_id: str) -> Path:
    if session_id not in PACKAGES:
        raise HTTPException(409, "Upload a submission package first.")
    return Path(PACKAGES[session_id].name)
