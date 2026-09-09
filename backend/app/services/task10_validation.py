"""TASK10 orchestration; AI supplies evidence candidates, never verdict authority."""
from pathlib import Path

from app.models.profiles import ProviderProvenance
from app.models.schemas import CheckSession, SemanticReviewMetadata, ValidationResult
from app.models.semantic_review import SemanticAIResponse, SemanticReadiness
from app.services import generic_validation
from app.services.generic_validation import GenericRun
from app.services.public_guard import GuardRejected, PublicGuard
from app.services.semantic_evidence import gate_semantic_reviews, semantic_evidence_fingerprint
from app.services.semantic_provider import SubmissionSemanticReviewer
from app.services.semantic_submission import (
    SemanticPreparation, eligible_semantic_requirements, prepare_semantic_submission,
)


class PackageChangedDuringRun(ValueError):
    pass


def check_integrity(session: CheckSession, package: Path) -> None:
    try:
        generic_validation.assert_submission_integrity(session, package)
    except Exception as error:
        raise PackageChangedDuringRun("PACKAGE_CHANGED_DURING_RUN") from error


def semantic_readiness(session: CheckSession, package: Path) -> SemanticReadiness:
    if session.validation_profile != "generic" or session.generic_profile is None:
        return SemanticReadiness(ack_required=False, eligible_requirement_count=0, reason_code="NOT_GENERIC")
    check_integrity(session, package)
    preparation = prepare_semantic_submission(session.generic_profile, package)
    check_integrity(session, package)
    return SemanticReadiness(ack_required=preparation.call_ai,
        eligible_requirement_count=len(preparation.eligible_requirement_ids), reason_code=preparation.reason_code)


def run_generic_preflight(
    session: CheckSession, package: Path, preparation: SemanticPreparation,
    reviewer: SubmissionSemanticReviewer | None, guard: PublicGuard | None,
) -> GenericRun:
    check_integrity(session, package)
    deterministic = generic_validation.validate(session, package)
    if not preparation.eligible_requirement_ids:
        check_integrity(session, package)
        return deterministic
    profile = session.generic_profile
    assert profile is not None
    semantic_results = {}
    reason = preparation.reason_code
    provenance = None
    reservation = None
    if preparation.call_ai:
        try:
            if guard is None:
                raise GuardRejected("GUARD_UNAVAILABLE")
            if reviewer is None:
                raise RuntimeError("Semantic reviewer unavailable")
            reservation = guard.reserve(session.id, "SEMANTIC",
                f"semantic:{session.id}:{session.revision + 1}:{preparation.file_sha256}:{profile.profile_id}:{profile.version}")
            check_integrity(session, package)
            provenance = ProviderProvenance.model_validate(reviewer.provenance)
            response = reviewer.review(eligible_semantic_requirements(profile), preparation)
            response = SemanticAIResponse.model_validate(response)
            semantic_results = gate_semantic_reviews(profile, preparation, response, provenance)
        except PackageChangedDuringRun:
            raise
        except GuardRejected:
            reason = "SEMANTIC_GUARD_UNAVAILABLE"
        except Exception:
            reason = "SEMANTIC_PROVIDER_UNAVAILABLE"
        finally:
            try:
                if guard is not None:
                    guard.release(reservation)
            except Exception:
                semantic_results = {}
                reason = "SEMANTIC_GUARD_UNAVAILABLE"
    check_integrity(session, package)
    by_id = {result.requirement_id: result for result in deterministic.results}
    if not semantic_results:
        for requirement_id in preparation.eligible_requirement_ids:
            metadata = SemanticReviewMetadata(coverage=preparation.coverage,
                reason_code=reason or "SEMANTIC_PROVIDER_UNAVAILABLE",
                evidence_fingerprint=semantic_evidence_fingerprint(requirement_id, None,
                    preparation.coverage, reason or "SEMANTIC_PROVIDER_UNAVAILABLE", []),
                provider=provenance)
            semantic_results[requirement_id] = ValidationResult.model_validate({
                **by_id[requirement_id].model_dump(),
                "id": f"{requirement_id}:semantic", "status": "REVIEW", "source_mode": "generic_review",
                "semantic_review": metadata, "submission_evidence": None,
                "verification_plan_id": None, "checker_type": None, "measured_fact": None,
                "expected_constraint": None,
                "explanation": "제출물 내용의 자동 검토를 완료하지 못했습니다.",
                "action": "공고 조건과 실제 제출물을 직접 확인하세요.",
            })
    by_id.update(semantic_results)
    deterministic.results = [by_id[item.requirement_id] for item in profile.requirements]
    deterministic.complete = False
    deterministic.raw["semantic"] = {
        "eligible_ids": list(preparation.eligible_requirement_ids),
        "coverage": preparation.coverage, "total_characters": preparation.total_characters,
        "page_count": len(preparation.pages), "file_sha256": preparation.file_sha256,
        "provider": provenance.model_dump(mode="json") if provenance else None,
        "reviews": [{"requirement_id": result.requirement_id,
            "assessment": result.semantic_review.assessment,
            "reason_code": result.semantic_review.reason_code,
            "evidence_fingerprint": result.semantic_review.evidence_fingerprint}
            for result in semantic_results.values()],
    }
    return deterministic
