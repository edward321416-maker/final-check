"""Map deterministic checker measurements to product findings under strict authority gates."""
import json

from app.models.profiles import AnnouncementSource, ProfileRequirement
from app.models.schemas import Evidence, ValidationResult
from app.models.verifier_plans import GatedVerificationPlan
from app.services.generic_inspection import CheckerOutcome


def announcement_evidence(requirement: ProfileRequirement, source: AnnouncementSource) -> Evidence:
    return Evidence(
        source=source.name,
        locator=f"{requirement.evidence.source_section} · chars {requirement.evidence_start}:{requirement.evidence_end}",
        excerpt=requirement.evidence.quote,
    )


def result_for(
    requirement: ProfileRequirement,
    source: AnnouncementSource,
    plan: GatedVerificationPlan | None,
    outcome: CheckerOutcome | None,
) -> ValidationResult:
    source_evidence = announcement_evidence(requirement, source)
    external = requirement.verifier == "EXTERNAL" or requirement.severity == "EXTERNAL" or (plan and plan.status == "EXTERNAL")
    if plan is None or plan.status != "VERIFIED" or outcome is None:
        return ValidationResult(
            id=f"{requirement.requirement_id}:review",
            requirement_id=requirement.requirement_id,
            status="EXTERNAL" if external else "REVIEW",
            title=requirement.rule,
            explanation="외부 확인이 필요한 항목입니다." if external else "안전하게 실행할 수 있는 확정 검사 계획이 없습니다.",
            action="공고 근거와 실제 제출물을 직접 확인하세요.",
            announcement_evidence=source_evidence,
            source_mode="generic_verifier" if plan else "generic_review",
            verification_plan_id=plan.plan_id if plan else None,
            checker_type=plan.checker_type if plan else None,
            measured_fact=outcome.measured_fact if outcome else None,
            expected_constraint=json.dumps(plan.constraint.model_dump(), ensure_ascii=False, sort_keys=True) if plan else None,
        )
    expected = json.dumps(plan.constraint.model_dump(), ensure_ascii=False, sort_keys=True)
    definite = outcome.status in {"PASS", "VIOLATION"} and outcome.submission_evidence is not None
    if not definite:
        status = "REVIEW"
    elif outcome.status == "PASS":
        status = "PASS"
    elif (
        requirement.authoritative
        and requirement.extraction_status == "CONFIRMED"
        and requirement.modality in {"MUST", "MUST_NOT"}
        and requirement.severity == "BLOCKER"
        and requirement.verifier == "DETERMINISTIC"
        and requirement.condition.strip().casefold() == "always"
    ):
        status = "BLOCKER"
    else:
        status = "REVIEW"
    return ValidationResult(
        id=f"{requirement.requirement_id}:{plan.plan_id}",
        requirement_id=requirement.requirement_id,
        status=status,
        title=requirement.rule,
        explanation=f"코드 검사 결과: {outcome.measured_fact}",
        action="위반한 제출 조건을 수정하세요." if status == "BLOCKER" else "측정 근거와 공고 조건을 확인하세요.",
        announcement_evidence=source_evidence,
        submission_evidence=outcome.submission_evidence,
        source_mode="generic_verifier",
        verification_plan_id=plan.plan_id,
        checker_type=plan.checker_type,
        measured_fact=outcome.measured_fact,
        expected_constraint=expected,
    )
