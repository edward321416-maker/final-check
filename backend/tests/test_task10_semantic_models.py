import pytest
from pydantic import ValidationError

from app.models.schemas import Evidence, ValidationResult
from app.models.schemas import SemanticReviewMetadata
from app.models.semantic_review import (
    SemanticAIResponse,
    SemanticReadiness,
    ValidateRequest,
)


def metadata(**updates):
    value = {
        "assessment": "RELATED_EVIDENCE_FOUND",
        "coverage": "FULL",
        "reason_code": None,
        "evidence": [
            {"source": "proposal.pdf", "locator": "page 2 · chars 10:20", "excerpt": "기대효과"}
        ],
        "evidence_fingerprint": "a" * 64,
        "provider": {
            "provider": "test",
            "model": "test-model",
            "prompt_version": "task10-semantic-review-v1",
            "prompt_sha256": "b" * 64,
            "execution_kind": "SIMULATED",
        },
    }
    value.update(updates)
    return SemanticReviewMetadata.model_validate(value)


def test_semantic_metadata_forces_review_only():
    item = metadata()
    with pytest.raises(ValidationError):
        ValidationResult(
            id="G001:semantic",
            requirement_id="G001",
            status="PASS",
            title="기대효과를 포함해야 한다",
            explanation="x",
            action="x",
            announcement_evidence=Evidence(source="a", locator="b", excerpt="c"),
            source_mode="generic_review",
            semantic_review=item,
        )


def test_semantic_metadata_rejects_external_status_independently():
    with pytest.raises(ValidationError, match="Semantic review can only produce REVIEW"):
        ValidationResult(
            id="G001:semantic",
            requirement_id="G001",
            status="EXTERNAL",
            title="기대효과를 포함해야 한다",
            explanation="x",
            action="x",
            source_mode="generic_review",
            semantic_review=metadata(),
        )


@pytest.mark.parametrize("source_mode", ["validator", "generic_verifier"])
def test_semantic_metadata_requires_generic_review_source_mode(source_mode):
    with pytest.raises(ValidationError, match="Semantic review requires generic_review"):
        ValidationResult(
            id="G001:semantic",
            requirement_id="G001",
            status="REVIEW",
            title="기대효과를 포함해야 한다",
            explanation="x",
            action="x",
            source_mode=source_mode,
            semantic_review=metadata(),
        )


def test_semantic_ai_schema_has_no_verdict_field():
    payload = {
        "reviews": [{
            "requirement_id": "G001",
            "assessment": "RELATED_EVIDENCE_FOUND",
            "evidence_candidates": [{
                "document_id": "D01",
                "page_id": "D01-P002",
                "quote": "기대효과를 설명한다",
            }],
            "status": "PASS",
        }]
    }
    with pytest.raises(ValidationError):
        SemanticAIResponse.model_validate(payload)


def test_ai_evidence_candidate_count_is_bounded():
    payload = {
        "reviews": [{
            "requirement_id": "G001",
            "assessment": "RELATED_EVIDENCE_FOUND",
            "evidence_candidates": [
                {"document_id": "D01", "page_id": f"D01-P00{i}", "quote": f"quote{i}"}
                for i in range(1, 5)
            ],
        }]
    }
    with pytest.raises(ValidationError):
        SemanticAIResponse.model_validate(payload)


def test_related_evidence_found_requires_candidates():
    with pytest.raises(ValidationError):
        SemanticAIResponse.model_validate({
            "reviews": [{
                "requirement_id": "G001",
                "assessment": "RELATED_EVIDENCE_FOUND",
            }]
        })


def test_no_clear_evidence_rejects_candidates():
    with pytest.raises(ValidationError):
        SemanticAIResponse.model_validate({
            "reviews": [{
                "requirement_id": "G001",
                "assessment": "NO_CLEAR_EVIDENCE",
                "evidence_candidates": [{
                    "document_id": "D01",
                    "page_id": "D01-P002",
                    "quote": "기대효과를 설명한다",
                }],
            }]
        })


def test_semantic_literals_are_strict():
    with pytest.raises(ValidationError):
        SemanticAIResponse.model_validate({
            "reviews": [{
                "requirement_id": "G001",
                "assessment": "PASS",
            }]
        })
    with pytest.raises(ValidationError):
        metadata(coverage="UNKNOWN")


def test_validate_request_defaults_acknowledgement_to_false():
    assert ValidateRequest().semantic_text_ai_acknowledged is False


def test_semantic_readiness_contains_no_extracted_text():
    readiness = SemanticReadiness(ack_required=True, eligible_requirement_count=1)
    assert "text" not in SemanticReadiness.model_fields
    assert "extracted_text" not in SemanticReadiness.model_fields
