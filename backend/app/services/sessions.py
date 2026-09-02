from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import HTTPException
from app.models.schemas import CheckSession

SESSIONS: dict[str, CheckSession] = {}
TTL = timedelta(hours=1)
MAX_SESSIONS = 100


def now() -> datetime:
    return datetime.now(timezone.utc)


def cleanup() -> None:
    expired = [key for key, session in SESSIONS.items() if now() - session.updated_at > TTL]
    for key in expired:
        del SESSIONS[key]


def create(mode: str) -> CheckSession:
    cleanup()
    if len(SESSIONS) >= MAX_SESSIONS:
        raise HTTPException(503, "Local session capacity reached; restart the demo server.")
    session = CheckSession(id=str(uuid4()), created_at=now(), updated_at=now(), mode=mode,
                           source_mode="mock" if mode == "demo" else "unavailable")
    SESSIONS[session.id] = session
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
