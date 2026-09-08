"""Ground TASK10 semantic quotes locally before presenting REVIEW findings."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping

from app.models.profiles import GenericRequirementProfile, ProfileRequirement, ProviderProvenance
from app.models.schemas import Evidence, SemanticReviewMetadata, ValidationResult
from app.models.semantic_review import SemanticAIResponse, SemanticAssessment, SemanticCoverage
from app.services.verifier_engine import announcement_evidence
from app.services.semantic_submission import SemanticPreparation


def semantic_evidence_fingerprint(
    requirement_id: str,
    assessment: SemanticAssessment | None,
    coverage: SemanticCoverage,
    reason_code: str | None,
    evidence: Iterable[Evidence | Mapping[str, str]],
) -> str:
    trusted_evidence = sorted(
        (
            {
                "source": item.source if isinstance(item, Evidence) else item["source"],
                "locator": item.locator if isinstance(item, Evidence) else item["locator"],
                "excerpt": item.excerpt if isinstance(item, Evidence) else item["excerpt"],
            }
            for item in evidence
        ),
        key=lambda item: (item["source"], item["locator"], item["excerpt"]),
    )
    payload = {
        "assessment": assessment,
        "coverage": coverage,
        "evidence": trusted_evidence,
        "reason_code": reason_code,
        "requirement_id": requirement_id,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _accepted_evidence(preparation: SemanticPreparation, candidates) -> list[Evidence]:
    pages = {page.page_id: page for page in preparation.pages}
    accepted: list[Evidence] = []
    seen: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        page = pages.get(candidate.page_id)
        if candidate.document_id != preparation.document_id or page is None or preparation.actual_filename is None:
            continue
        offset = page.text.find(candidate.quote)
        if offset < 0:
            continue
        item = Evidence(
            source=preparation.actual_filename,
            locator=f"page {page.page_number} · chars {offset}:{offset + len(candidate.quote)}",
            excerpt=candidate.quote,
        )
        key = (item.source, item.locator, item.excerpt)
        if key not in seen:
            accepted.append(item)
            seen.add(key)
    return accepted


def _metadata(
    requirement_id: str,
    assessment: SemanticAssessment | None,
    preparation: SemanticPreparation,
    reason_code: str | None,
    evidence: list[Evidence],
    provenance: ProviderProvenance,
) -> SemanticReviewMetadata:
    return SemanticReviewMetadata(
        assessment=assessment,
        coverage=preparation.coverage,
        reason_code=reason_code,
        evidence=evidence,
        evidence_fingerprint=semantic_evidence_fingerprint(
            requirement_id,
            assessment,
            preparation.coverage,
            reason_code,
            evidence,
        ),
        provider=provenance,
    )


def _result(
    requirement: ProfileRequirement,
    profile: GenericRequirementProfile,
    metadata: SemanticReviewMetadata,
    explanation: str,
    action: str,
    submission_evidence: Evidence | None = None,
) -> ValidationResult:
    return ValidationResult(
        id=f"{requirement.requirement_id}:semantic",
        requirement_id=requirement.requirement_id,
        status="REVIEW",
        title=requirement.rule,
        explanation=explanation,
        action=action,
        announcement_evidence=announcement_evidence(requirement, profile.announcement),
        submission_evidence=submission_evidence,
        source_mode="generic_review",
        semantic_review=metadata,
    )


def gate_semantic_reviews(
    profile: GenericRequirementProfile,
    preparation: SemanticPreparation,
    response: SemanticAIResponse,
    provenance: ProviderProvenance,
) -> dict[str, ValidationResult]:
    requirements = {
        item.requirement_id: item
        for item in profile.requirements
        if item.requirement_id in preparation.eligible_requirement_ids
    }
    expected_ids = set(preparation.eligible_requirement_ids)
    if set(requirements) != expected_ids:
        raise ValueError("Semantic preparation requirements do not match the profile")

    reviews = {item.requirement_id: item for item in response.reviews}
    response_ids = [item.requirement_id for item in response.reviews]
    unknown_ids = set(response_ids) - expected_ids
    if unknown_ids:
        raise ValueError("Unknown semantic requirement ID")
    if len(reviews) != len(response_ids) or set(reviews) != expected_ids:
        raise ValueError("Semantic response must contain exactly one review per requirement")

    results: dict[str, ValidationResult] = {}
    for requirement_id in preparation.eligible_requirement_ids:
        requirement = requirements[requirement_id]
        review = reviews[requirement_id]
        evidence = _accepted_evidence(preparation, review.evidence_candidates)

        if review.assessment == "RELATED_EVIDENCE_FOUND" and evidence:
            reason_code = "PARTIAL_TEXT_COVERAGE" if preparation.coverage == "PARTIAL" else None
            metadata = _metadata(
                requirement_id,
                "RELATED_EVIDENCE_FOUND",
                preparation,
                reason_code,
                evidence,
                provenance,
            )
            action = (
                "읽을 수 없는 페이지가 있어 공고 조건과 제출물 전체를 직접 확인하세요."
                if preparation.coverage == "PARTIAL"
                else "공고 조건과 제출물 문맥을 직접 확인하세요."
            )
            results[requirement_id] = _result(
                requirement,
                profile,
                metadata,
                "제출물에서 공고 항목과 관련된 근거 후보를 확인했습니다.",
                action,
                evidence[0],
            )
            continue

        if review.assessment == "RELATED_EVIDENCE_FOUND":
            metadata = _metadata(
                requirement_id,
                None,
                preparation,
                "SEMANTIC_EVIDENCE_REJECTED",
                [],
                provenance,
            )
            results[requirement_id] = _result(
                requirement,
                profile,
                metadata,
                "AI가 제시한 제출물 근거를 원문에서 확인하지 못했습니다.",
                "공고 조건과 실제 제출물을 직접 확인하세요.",
            )
            continue

        if preparation.coverage == "FULL":
            metadata = _metadata(
                requirement_id,
                "NO_CLEAR_EVIDENCE",
                preparation,
                None,
                [],
                provenance,
            )
            results[requirement_id] = _result(
                requirement,
                profile,
                metadata,
                "명확한 관련 근거 후보를 찾지 못했습니다.",
                "공고 조건과 실제 제출물을 직접 확인하세요.",
            )
            continue

        reason_code = "PARTIAL_TEXT_COVERAGE" if preparation.coverage == "PARTIAL" else "TEXT_UNAVAILABLE"
        explanation = (
            "일부 페이지는 자동으로 읽을 수 없어 전체 내용을 직접 확인해야 합니다."
            if preparation.coverage == "PARTIAL"
            else "제출물 텍스트를 자동으로 읽을 수 없어 직접 확인해야 합니다."
        )
        metadata = _metadata(requirement_id, None, preparation, reason_code, [], provenance)
        results[requirement_id] = _result(
            requirement,
            profile,
            metadata,
            explanation,
            "공고 조건과 실제 제출물을 직접 확인하세요.",
        )
    return results
