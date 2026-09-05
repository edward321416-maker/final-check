"""Canonical generic extraction contract, separate from frozen v1.5 rules."""
import hashlib
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Modality = Literal["MUST", "MUST_NOT", "SHOULD", "MAY", "INFO"]
Severity = Literal["BLOCKER", "REVIEW", "INFO", "EXTERNAL"]
Verifier = Literal["DETERMINISTIC", "SEMANTIC", "VISION_SEMANTIC", "URL_CHECK", "EXTERNAL"]
ExtractionStatus = Literal["EXTRACTED", "NEEDS_REVIEW", "CONFIRMED", "UNSUPPORTED"]
Stage2Decision = Literal["KEEP", "REVIEW", "DROP"]
PipelineStatus = Literal["NOT_STARTED", "RUNNING", "COMPLETE", "OVERFLOW_REVIEW", "REVIEW_REQUIRED", "EXTRACTION_ERROR"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceEvidence(StrictModel):
    source_section: str = Field(min_length=1, max_length=300)
    quote: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def nonblank(self) -> "SourceEvidence":
        if not self.quote.strip() or not self.source_section.strip():
            raise ValueError("NO EVIDENCE -> NO RULE")
        return self


class ExtractedRequirement(StrictModel):
    requirement_id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
    rule: str = Field(min_length=1, max_length=2000)
    modality: Modality
    severity: Severity
    verifier: Verifier
    condition: str = Field(min_length=1, max_length=1000)
    evidence: SourceEvidence
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def safe_severity(self) -> "ExtractedRequirement":
        if not self.rule.strip() or not self.condition.strip():
            raise ValueError("Rule and condition must be nonblank")
        if self.modality in {"SHOULD", "MAY", "INFO"} and self.severity == "BLOCKER":
            raise ValueError("SHOULD/MAY/INFO cannot be BLOCKER")
        return self


class ProviderProvenance(StrictModel):
    provider: str = Field(min_length=1, max_length=200)
    model: str | None = Field(default=None, max_length=100)
    prompt_version: str = Field(min_length=1, max_length=100)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_kind: Literal["ACTUAL", "SIMULATED"]


class SemanticReview(StrictModel):
    requirement_id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
    decision: Stage2Decision
    reason: str = Field(min_length=1, max_length=1000)
    semantic_support: bool
    condition_preserved: bool
    modality_supported: bool
    needs_more_context: bool = False
    duplicate_of: str | None = Field(default=None, pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
    reviewer: ProviderProvenance


class ProfileRequirement(ExtractedRequirement):
    extraction_status: ExtractionStatus = "EXTRACTED"
    evidence_start: int = Field(ge=0)
    evidence_end: int = Field(gt=0)
    issues: list[str] = Field(default_factory=list)
    original: ExtractedRequirement
    stage1: ProviderProvenance | None = None
    stage2_decision: Literal["KEEP", "REVIEW"] | None = None
    stage2_reason: str = ""
    stage2: ProviderProvenance | None = None
    authoritative: bool = False


class AnnouncementSource(StrictModel):
    source_type: Literal["TEXT", "PDF"]
    name: str = Field(min_length=1, max_length=200)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    text: str = Field(max_length=100_000)
    ingestion_status: Literal["READABLE", "VISION_REQUIRED", "UNREADABLE", "UNSUPPORTED"]
    page_count: int | None = None
    notice: str = ""

    @model_validator(mode="after")
    def text_integrity(self) -> "AnnouncementSource":
        if hashlib.sha256(self.text.encode("utf-8")).hexdigest() != self.text_sha256:
            raise ValueError("Announcement text hash mismatch")
        return self


class ReviewEvent(StrictModel):
    action: Literal["EXTRACT", "EDIT", "NEEDS_REVIEW", "APPROVE", "DELETE", "CONFIRM_PROFILE"]
    requirement_id: str | None = None
    at: datetime
    before: ProfileRequirement | None = None
    after: ProfileRequirement | None = None


class GenericRequirementProfile(StrictModel):
    profile_type: Literal["generic"] = "generic"
    profile_id: str
    announcement: AnnouncementSource
    status: Literal["DRAFT", "REVIEW_REQUIRED", "CONFIRMED"] = "DRAFT"
    requirements: list[ProfileRequirement] = Field(default_factory=list, max_length=500)
    raw_candidates: list[ExtractedRequirement] = Field(default_factory=list, max_length=1000)
    gated_candidate_ids: list[str] = Field(default_factory=list, max_length=500)
    stage2_reviews: list[SemanticReview] = Field(default_factory=list, max_length=500)
    provider: str | None = None
    execution_kind: Literal["ACTUAL", "SIMULATED"] | None = None
    stage1: ProviderProvenance | None = None
    stage2: ProviderProvenance | None = None
    pipeline_status: PipelineStatus = "NOT_STARTED"
    pipeline_error: str | None = Field(default=None, max_length=300)
    raw_candidate_count: int = Field(default=0, ge=0)
    gated_candidate_count: int = Field(default=0, ge=0, le=500)
    dropped_candidate_count: int = Field(default=0, ge=0)
    review_batches: int = Field(default=0, ge=0, le=10)
    failed_batches: list[int] = Field(default_factory=list, max_length=10)
    overflow: bool = False
    overflow_policy: str = "100개 초과 후보도 50개 단위로 검토하며, 절대 상한은 500개입니다."
    extraction_complete: bool = False
    notices: list[str] = Field(default_factory=list)
    history: list[ReviewEvent] = Field(default_factory=list, max_length=500)
    version: int = 1
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def source_links(self) -> "GenericRequirementProfile":
        ids = [r.requirement_id for r in self.requirements]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate requirement IDs")
        for requirement in self.requirements:
            if self.announcement.text[requirement.evidence_start:requirement.evidence_end] != requirement.evidence.quote:
                raise ValueError("Evidence must be an exact source substring at its recorded offset")
            if requirement.authoritative != (requirement.extraction_status == "CONFIRMED"):
                raise ValueError("Only a human-confirmed requirement may be authoritative")
        if self.status == "CONFIRMED" and (
            not self.extraction_complete or not self.requirements
            or self.announcement.ingestion_status != "READABLE"
            or self.failed_batches
            or any(r.extraction_status != "CONFIRMED" or not r.authoritative or r.issues for r in self.requirements)
        ):
            raise ValueError("Only a reviewed, nonempty profile can be confirmed")
        return self


class TextAnnouncement(StrictModel):
    name: str = Field(default="직접 입력한 공고", min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=100_000)


class VersionRequest(StrictModel):
    expected_version: int = Field(ge=1)


class ReviewRequest(VersionRequest):
    action: Literal["EDIT", "NEEDS_REVIEW", "APPROVE", "DELETE"]
    requirement: ExtractedRequirement | None = None


class ConfirmRequest(VersionRequest):
    reviewed_full_source: Literal[True]
