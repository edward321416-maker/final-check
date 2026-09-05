from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.jobs import JobSummary
from app.models.profiles import GenericRequirementProfile


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FindingStatus(StrEnum):
    BLOCKER = "BLOCKER"
    REVIEW = "REVIEW"
    PASS = "PASS"
    EXTERNAL = "EXTERNAL"


class SubmissionStatus(StrEnum):
    BLOCKED = "BLOCKED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    READY = "READY"


class Evidence(Model):
    source: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)


class Requirement(Model):
    id: str
    title: str
    description: str
    verifier: Literal["DETERMINISTIC", "SEMANTIC", "VISION", "VISION_SEMANTIC", "URL_CHECK", "EXTERNAL"]
    announcement_evidence: Evidence


class ValidationResult(Model):
    id: str
    requirement_id: str
    status: FindingStatus
    title: str
    explanation: str
    action: str
    announcement_evidence: Evidence | None = None
    submission_evidence: Evidence | None = None
    source_mode: Literal["validator", "generic_review"] = "validator"

    @model_validator(mode="after")
    def enforce_product_lock(self) -> "ValidationResult":
        if self.source_mode == "generic_review" and self.status not in {FindingStatus.REVIEW, FindingStatus.EXTERNAL}:
            raise ValueError("Generic automatic verification is unsupported; no PASS/BLOCKER")
        if self.requirement_id in {"R20", "R21"} and self.status not in {FindingStatus.REVIEW, FindingStatus.EXTERNAL}:
            raise ValueError("Licensing and AI provenance have no automatic verification")
        if self.status == FindingStatus.BLOCKER:
            if self.requirement_id == "R19":
                raise ValueError("R19 must never be an automatic BLOCKER")
            if self.announcement_evidence is None or self.submission_evidence is None:
                raise ValueError("BLOCKER requires announcement and submission evidence")
        return self


class SubmissionFile(Model):
    name: str
    size_bytes: int = Field(ge=0)
    media_type: str
    sha256: str


class CheckSession(Model):
    id: str
    created_at: datetime
    updated_at: datetime
    mode: Literal["demo", "custom"]
    source_mode: Literal["validator", "generic_review", "unavailable"] = "unavailable"
    validation_profile: Literal["frozen_v15", "generic"] | None = None
    generic_profile: GenericRequirementProfile | None = None
    current_job_id: str | None = None
    current_job: JobSummary | None = None
    engine_sha256: str | None = None
    run_state: Literal["NOT_STARTED", "RUNNING", "COMPLETE", "FAILED"] = "NOT_STARTED"
    validation_complete: bool = False
    run_error: str | None = None
    announcement_name: str | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    files: list[SubmissionFile] = Field(default_factory=list)
    results: list[ValidationResult] = Field(default_factory=list)
    previous_results: list[ValidationResult] = Field(default_factory=list)
    status: SubmissionStatus | None = None
    revision: int = 0
    fixture: Literal["demo-broken", "demo-fixed"] | None = None


class CreateSession(Model):
    mode: Literal["demo", "custom"] = "demo"


class FixtureRequest(Model):
    fixture: Literal["demo-broken", "demo-fixed"]
