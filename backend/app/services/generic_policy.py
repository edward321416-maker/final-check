"""Generic readiness policy, independent from the frozen validator summary."""
from app.models.profiles import GenericRequirementProfile
from app.models.schemas import FindingStatus, SubmissionStatus, ValidationResult


def summarize(profile: GenericRequirementProfile, results: list[ValidationResult]) -> SubmissionStatus:
    by_id = {result.requirement_id: result for result in results}
    mandatory = [item for item in profile.requirements if item.modality in {"MUST", "MUST_NOT"}]
    if any(
        item.authoritative
        and item.extraction_status == "CONFIRMED"
        and item.severity == "BLOCKER"
        and item.verifier == "DETERMINISTIC"
        and item.condition.strip().casefold() == "always"
        and by_id.get(item.requirement_id)
        and by_id[item.requirement_id].status == FindingStatus.BLOCKER
        for item in mandatory
    ):
        return SubmissionStatus.BLOCKED
    if any(by_id.get(item.requirement_id) is None or by_id[item.requirement_id].status != FindingStatus.PASS for item in mandatory):
        return SubmissionStatus.REVIEW_REQUIRED
    return SubmissionStatus.READY
