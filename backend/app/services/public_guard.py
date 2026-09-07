"""Durable fail-closed limits for public AI operations."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from app.services.storage import SQLiteRuntimeStore


PUBLIC_MESSAGE = "현재 데모 사용량이 많습니다. 잠시 후 다시 시도해주세요."


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class GuardConfig:
    enabled: bool = False
    global_per_hour: int = 40
    session_per_hour: int = 6
    max_concurrent: int = 2
    lease_seconds: int = 1800

    @classmethod
    def from_environment(cls) -> "GuardConfig":
        return cls(
            enabled=os.environ.get("FINAL_CHECK_PUBLIC_GUARD", "0") == "1",
            global_per_hour=_positive_int("FINAL_CHECK_AI_MAX_OPERATIONS_PER_HOUR", 40),
            session_per_hour=_positive_int("FINAL_CHECK_AI_MAX_OPERATIONS_PER_SESSION_HOUR", 6),
            max_concurrent=_positive_int("FINAL_CHECK_AI_MAX_CONCURRENT_WORKFLOWS", 2),
            lease_seconds=_positive_int("FINAL_CHECK_AI_LEASE_SECONDS", 1800),
        )


@dataclass(frozen=True)
class GuardReservation:
    counted: bool
    reused: bool
    token: str | None


class GuardRejected(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(PUBLIC_MESSAGE)
        self.reason = reason


class PublicGuard:
    def __init__(
        self,
        store: SQLiteRuntimeStore,
        config: GuardConfig | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self.store = store
        self.config = config or GuardConfig.from_environment()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def reserve(self, session_id: str, operation_kind: str, operation_id: str) -> GuardReservation:
        if not self.config.enabled or operation_kind == "POLL":
            return GuardReservation(counted=False, reused=False, token=None)
        if operation_kind not in {"EXTRACT", "PLAN"}:
            raise ValueError("Unsupported public AI operation kind")
        status, token = self.store.reserve_ai_operation(
            operation_id=operation_id,
            session_id=session_id,
            operation_kind=operation_kind,
            now=self.clock(),
            global_per_hour=self.config.global_per_hour,
            session_per_hour=self.config.session_per_hour,
            max_concurrent=self.config.max_concurrent,
            lease_seconds=self.config.lease_seconds,
        )
        if status == "RESERVED":
            return GuardReservation(counted=True, reused=False, token=token)
        if status == "REUSED":
            return GuardReservation(counted=False, reused=True, token=None)
        public_reason = {
            "GLOBAL_LIMIT": "GLOBAL_QUOTA",
            "SESSION_LIMIT": "SESSION_QUOTA",
            "CONCURRENCY_LIMIT": "CONCURRENCY",
        }.get(status, "GUARD_UNAVAILABLE")
        raise GuardRejected(public_reason)

    def release(self, reservation: GuardReservation | None) -> None:
        if reservation:
            self.store.release_ai_operation(reservation.token)
