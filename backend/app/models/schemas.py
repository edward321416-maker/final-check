from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from app.models.jobs import JobSummary
from app.models.profiles import GenericRequirementProfile, ProviderProvenance
from app.models.semantic_review import SemanticAssessment, SemanticCoverage
from app.models.verifier_plans import CheckerType, VerificationPlanSet


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


VerbatimExcerpt = Annotated[str, StringConstraints(strip_whitespace=False, min_length=1)]


class Evidence(Model):
    source: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    excerpt: VerbatimExcerpt

    @model_validator(mode="after")
    def nonblank_excerpt(self) -> "Evidence":
        if not self.excerpt.strip():
            raise ValueError("Evidence excerpt must be nonblank")
        return self


class SemanticReviewMetadata(Model):
    assessment: SemanticAssessment | None = None
    coverage: SemanticCoverage
    reason_code: str | None = Field(default=None, max_length=100)
    evidence: list[Evidence] = Field(default_factory=list, max_length=3)
    evidence_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    provider: ProviderProvenance | None = None

    @model_validator(mode="after")
    def trusted_evidence_shape(self) -> "SemanticReviewMetadata":
        if self.assessment == "RELATED_EVIDENCE_FOUND" and not self.evidence:
            raise ValueError("RELATED_EVIDENCE_FOUND requires trusted evidence")
        if self.assessment != "RELATED_EVIDENCE_FOUND" and self.evidence:
            raise ValueError("Only RELATED_EVIDENCE_FOUND can include trusted evidence")
        if self.assessment == "NO_CLEAR_EVIDENCE" and self.coverage != "FULL":
            raise ValueError("NO_CLEAR_EVIDENCE requires FULL text coverage")
        return self


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
    source_mode: Literal["validator", "generic_review", "generic_verifier"] = "validator"
    verification_plan_id: str | None = None
    checker_type: CheckerType | None = None
    measured_fact: str | None = None
    expected_constraint: str | None = None
    semantic_review: SemanticReviewMetadata | None = None

    @model_validator(mode="after")
    def enforce_product_lock(self) -> "ValidationResult":
        if self.source_mode == "generic_review" and self.status not in {FindingStatus.REVIEW, FindingStatus.EXTERNAL}:
            raise ValueError("Generic automatic verification is unsupported; no PASS/BLOCKER")
        if self.source_mode == "generic_verifier" and self.status in {FindingStatus.PASS, FindingStatus.BLOCKER}:
            if not all((self.announcement_evidence, self.submission_evidence, self.verification_plan_id,
                        self.checker_type, self.measured_fact, self.expected_constraint)):
                raise ValueError("Generic verifier PASS/BLOCKER requires plan and both evidence sources")
        if self.semantic_review is not None and self.status != FindingStatus.REVIEW:
            raise ValueError("Semantic review can only produce REVIEW")
        if self.semantic_review is not None and self.source_mode != "generic_review":
            raise ValueError("Semantic review requires generic_review")
        if self.semantic_review is not None:
            evidence = self.semantic_review.evidence
            if evidence and self.submission_evidence != evidence[0]:
                raise ValueError("Primary submission evidence must match semantic evidence")
            if not evidence and self.submission_evidence is not None:
                raise ValueError("Semantic review without trusted evidence cannot set submission evidence")
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
    source_mode: Literal["validator", "generic_review", "generic_verifier", "unavailable"] = "unavailable"
    validation_profile: Literal["frozen_v15", "generic"] | None = None
    generic_profile: GenericRequirementProfile | None = None
    verification_plan: VerificationPlanSet | None = None
    verification_plan_state: Literal["NOT_STARTED", "RUNNING", "READY", "REVIEW_REQUIRED"] = "NOT_STARTED"
    verification_plan_error: str | None = Field(default=None, max_length=300)
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
