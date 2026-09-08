import hashlib
import importlib
import importlib.util

import pytest

from app.models.profiles import AnnouncementSource, ExtractedRequirement, ProviderProvenance
from app.models.semantic_review import SemanticAIResponse
from app.services import profiles
from app.services.semantic_submission import SemanticPage, SemanticPreparation


def semantic_evidence_module():
    module = importlib.util.find_spec("app.services.semantic_evidence")
    assert module is not None, "TASK10 semantic evidence gate is not implemented"
    return importlib.import_module("app.services.semantic_evidence")


def profile_requirement(requirement_id: str, *, modality: str = "MUST"):
    text = "제출 PDF에는 기대효과를 설명해야 합니다."
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    source = AnnouncementSource(
        source_type="TEXT",
        name="announcement.txt",
        sha256=digest,
        text_sha256=digest,
        text=text,
        ingestion_status="READABLE",
    )
    extracted = ExtractedRequirement(
        requirement_id=requirement_id,
        rule="기대효과를 설명해야 합니다.",
        modality=modality,
        severity="REVIEW",
        verifier="SEMANTIC",
        condition="always",
        evidence={"source_section": "제출 내용", "quote": text},
        confidence=1,
    )
    item = profiles.anchor(extracted, source)
    item.extraction_status = "CONFIRMED"
    item.authoritative = True
    return item, source


def profile(*items):
    _, source = profile_requirement("SOURCE")
    result = profiles.new_profile(source)
    result.requirements = list(items)
    result.extraction_complete = True
    result.status = "CONFIRMED"
    return result


def preparation(*, coverage: str = "FULL") -> SemanticPreparation:
    return SemanticPreparation(
        eligible_requirement_ids=("R01",),
        document_id="D01",
        actual_filename="submission.pdf",
        file_sha256="f" * 64,
        coverage=coverage,
        pages=(
            SemanticPage(
                page_id="D01-P001",
                page_number=1,
                text="첫 페이지에는 기대효과가 없습니다.",
                text_sha256="a" * 64,
            ),
            SemanticPage(
                page_id="D01-P002",
                page_number=2,
                text="둘째 페이지는 기대효과를 구체적으로 설명합니다.",
                text_sha256="b" * 64,
            ),
        ),
        total_characters=44,
        call_ai=True,
        reason_code=None,
    )


def response(requirement_id: str = "R01", assessment: str = "RELATED_EVIDENCE_FOUND", candidates=None):
    if candidates is None:
        candidates = [{
            "document_id": "D01",
            "page_id": "D01-P002",
            "quote": "기대효과를 구체적으로 설명합니다",
        }]
    return SemanticAIResponse.model_validate({"reviews": [{
        "requirement_id": requirement_id,
        "assessment": assessment,
        "evidence_candidates": candidates,
    }]})


def provenance() -> ProviderProvenance:
    return ProviderProvenance(
        provider="test-provider",
        model="test-model",
        prompt_version="task10-semantic-review-v1",
        prompt_sha256="c" * 64,
        execution_kind="SIMULATED",
    )


def gate(*, response_value=None, preparation_value=None, modality: str = "MUST"):
    item, _ = profile_requirement("R01", modality=modality)
    return semantic_evidence_module().gate_semantic_reviews(
        profile(item),
        preparation_value or preparation(),
        response_value or response(),
        provenance(),
    )["R01"]


def test_exact_quote_on_declared_page_is_accepted():
    result = gate()

    assert result.status == "REVIEW"
    assert result.semantic_review.assessment == "RELATED_EVIDENCE_FOUND"
    assert result.submission_evidence.model_dump() == {
        "source": "submission.pdf",
        "locator": "page 2 · chars 8:25",
        "excerpt": "기대효과를 구체적으로 설명합니다",
    }


def test_quote_on_wrong_page_is_rejected():
    result = gate(response_value=response(candidates=[{
        "document_id": "D01",
        "page_id": "D01-P001",
        "quote": "기대효과를 구체적으로 설명합니다",
    }]))

    assert result.semantic_review.assessment is None
    assert result.semantic_review.reason_code == "SEMANTIC_EVIDENCE_REJECTED"
    assert result.submission_evidence is None


def test_fabricated_quote_is_rejected():
    result = gate(response_value=response(candidates=[{
        "document_id": "D01",
        "page_id": "D01-P002",
        "quote": "존재하지 않는 문장",
    }]))

    assert result.semantic_review.reason_code == "SEMANTIC_EVIDENCE_REJECTED"
    assert result.explanation == "AI가 제시한 제출물 근거를 원문에서 확인하지 못했습니다."


def test_whitespace_rewritten_quote_is_rejected_without_normalization():
    result = gate(response_value=response(candidates=[{
        "document_id": "D01",
        "page_id": "D01-P002",
        "quote": " 기대효과를 구체적으로 설명합니다 ",
    }]))

    assert result.semantic_review.assessment is None
    assert result.semantic_review.reason_code == "SEMANTIC_EVIDENCE_REJECTED"


def test_unknown_requirement_id_is_rejected():
    with pytest.raises(ValueError, match="Unknown semantic requirement ID"):
        gate(response_value=response(requirement_id="R99"))


def test_positive_partial_coverage_can_show_grounded_quote_with_warning():
    result = gate(preparation_value=preparation(coverage="PARTIAL"))

    assert result.semantic_review.assessment == "RELATED_EVIDENCE_FOUND"
    assert result.semantic_review.reason_code == "PARTIAL_TEXT_COVERAGE"
    assert result.submission_evidence is not None
    assert "읽을 수 없는 페이지" in result.action


def test_negative_partial_coverage_never_claims_absence():
    result = gate(
        preparation_value=preparation(coverage="PARTIAL"),
        response_value=response(assessment="NO_CLEAR_EVIDENCE", candidates=[]),
    )

    assert result.semantic_review.assessment is None
    assert result.semantic_review.reason_code == "PARTIAL_TEXT_COVERAGE"
    assert result.explanation == "일부 페이지는 자동으로 읽을 수 없어 전체 내용을 직접 확인해야 합니다."


def test_negative_full_coverage_uses_no_clear_evidence_template():
    result = gate(response_value=response(assessment="NO_CLEAR_EVIDENCE", candidates=[]))

    assert result.semantic_review.assessment == "NO_CLEAR_EVIDENCE"
    assert result.semantic_review.reason_code is None
    assert result.submission_evidence is None
    assert result.explanation == "명확한 관련 근거 후보를 찾지 못했습니다."


def test_must_not_related_evidence_stays_review():
    result = gate(modality="MUST_NOT")

    assert result.status == "REVIEW"
    assert result.semantic_review.assessment == "RELATED_EVIDENCE_FOUND"
    assert result.submission_evidence is not None


def test_primary_submission_evidence_matches_first_semantic_evidence():
    result = gate(response_value=response(candidates=[
        {
            "document_id": "D01",
            "page_id": "D01-P002",
            "quote": "기대효과를 구체적으로 설명합니다",
        },
        {
            "document_id": "D01",
            "page_id": "D01-P002",
            "quote": "둘째 페이지는",
        },
    ]))

    assert result.submission_evidence == result.semantic_review.evidence[0]
    assert len(result.semantic_review.evidence) == 2


def test_semantic_fingerprint_changes_when_assessment_or_evidence_changes():
    module = semantic_evidence_module()
    base = gate()
    changed_assessment = gate(response_value=response(assessment="NO_CLEAR_EVIDENCE", candidates=[]))
    changed_evidence = module.semantic_evidence_fingerprint(
        "R01", "RELATED_EVIDENCE_FOUND", "FULL", None,
        [{"source": "submission.pdf", "locator": "page 2 · chars 0:5", "excerpt": "둘째"}],
    )

    assert base.semantic_review.evidence_fingerprint != changed_assessment.semantic_review.evidence_fingerprint
    assert base.semantic_review.evidence_fingerprint != changed_evidence
