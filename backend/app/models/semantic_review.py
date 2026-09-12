from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


SemanticAssessment = Literal["RELATED_EVIDENCE_FOUND", "NO_CLEAR_EVIDENCE"]
SemanticCoverage = Literal["FULL", "PARTIAL", "NONE"]
ExactQuote = Annotated[str, StringConstraints(strip_whitespace=False, min_length=1, max_length=2000)]


class SemanticEvidenceCandidate(StrictModel):
    document_id: Literal["D01"]
    page_id: str = Field(pattern=r"^D01-P\d{3}$")
    quote: ExactQuote


class SemanticAIReviewItem(StrictModel):
    requirement_id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
    assessment: SemanticAssessment
    evidence_candidates: list[SemanticEvidenceCandidate] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def evidence_shape(self):
        if self.assessment == "RELATED_EVIDENCE_FOUND" and not self.evidence_candidates:
            raise ValueError("RELATED_EVIDENCE_FOUND requires evidence candidates")
        if self.assessment == "NO_CLEAR_EVIDENCE" and self.evidence_candidates:
            raise ValueError("NO_CLEAR_EVIDENCE cannot carry evidence candidates")
        return self


class SemanticAIResponse(StrictModel):
    reviews: list[SemanticAIReviewItem] = Field(max_length=50)


class SemanticReadiness(StrictModel):
    ack_required: bool
    eligible_requirement_count: int = Field(ge=0, le=500)
    reason_code: str | None = Field(default=None, max_length=100)


class ValidateRequest(StrictModel):
    semantic_text_ai_acknowledged: bool = False
