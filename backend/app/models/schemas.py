from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FindingStatus(StrEnum):
    BLOCKER = "BLOCKER"
    REVIEW = "REVIEW"
    PASS = "PASS"
    EXTERNAL = "EXTERNAL"


class SubmissionStatus(StrEnum):
    NOT_CHECKED = "NOT_CHECKED"
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    READY = "READY"


class Evidence(Model):
    source: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)


class Requirement(Model):
    id: str
    title: str
    description: str
    verifier: Literal["DETERMINISTIC", "SEMANTIC", "VISION", "EXTERNAL"]
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
    source_mode: Literal["mock", "validator"] = "mock"

    @model_validator(mode="after")
    def enforce_product_lock(self) -> "ValidationResult":
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
    source_mode: Literal["mock", "unavailable"] = "mock"
    announcement_name: str | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    files: list[SubmissionFile] = Field(default_factory=list)
    results: list[ValidationResult] = Field(default_factory=list)
    previous_results: list[ValidationResult] = Field(default_factory=list)
    status: SubmissionStatus = SubmissionStatus.NOT_CHECKED
    revision: int = 0
    fixture: Literal["demo-broken", "demo-fixed"] | None = None


class CreateSession(Model):
    mode: Literal["demo", "custom"] = "demo"


class FixtureRequest(Model):
    fixture: Literal["demo-broken", "demo-fixed"]
