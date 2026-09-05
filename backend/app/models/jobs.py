"""Durable extraction-job contract for the single-node runtime."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.profiles import GenericRequirementProfile, ProviderProvenance


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE = "RETRYABLE"
    FAILED = "FAILED"


class JobStage(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    STAGE1_COMPLETE = "STAGE1_COMPLETE"
    GATE_COMPLETE = "GATE_COMPLETE"
    STAGE2_BATCH_N_COMPLETE = "STAGE2_BATCH_N_COMPLETE"
    FINALIZED = "FINALIZED"


class JobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus
    stage: JobStage
    attempt: int = Field(ge=0)
    completed_stage2_batches: list[int] = Field(default_factory=list)
    error_category: str | None = None
    updated_at: datetime


class ExtractionJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    session_id: str
    profile_id: str
    profile_version: int = Field(ge=1)
    job_kind: Literal["TWO_STAGE_EXTRACTION"]
    status: JobStatus = JobStatus.PENDING
    stage: JobStage = JobStage.NOT_STARTED
    attempt: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_category: str | None = Field(default=None, max_length=100)
    provider_provenance: list[ProviderProvenance] = Field(default_factory=list, max_length=2)
    completed_stage2_batches: list[int] = Field(default_factory=list, max_length=10)
    checkpoint_profile: GenericRequirementProfile | None = None

    @classmethod
    def new(
        cls,
        *,
        session_id: str,
        profile: GenericRequirementProfile,
        job_kind: Literal["TWO_STAGE_EXTRACTION"],
        status: JobStatus = JobStatus.PENDING,
        attempt: int = 0,
        provider_provenance: list[ProviderProvenance] | None = None,
    ) -> "ExtractionJob":
        stamp = datetime.now(timezone.utc)
        return cls(
            job_id=str(uuid4()), session_id=session_id, profile_id=profile.profile_id,
            profile_version=profile.version, job_kind=job_kind, status=status, attempt=attempt,
            created_at=stamp, updated_at=stamp,
            provider_provenance=provider_provenance or [],
        )

    def summary(self) -> JobSummary:
        return JobSummary(
            job_id=self.job_id, status=self.status, stage=self.stage, attempt=self.attempt,
            completed_stage2_batches=self.completed_stage2_batches,
            error_category=self.error_category, updated_at=self.updated_at,
        )
