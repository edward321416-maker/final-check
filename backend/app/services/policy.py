from app.models.schemas import FindingStatus, Requirement, SubmissionStatus, ValidationResult


def summarize(requirements: list[Requirement], results: list[ValidationResult]) -> SubmissionStatus:
    if not results:
        return SubmissionStatus.NOT_CHECKED
    if any(result.status == FindingStatus.BLOCKER for result in results):
        return SubmissionStatus.BLOCKED
    required_ids = {rule.id for rule in requirements}
    result_ids = {result.requirement_id for result in results}
    complete = bool(required_ids) and result_ids == required_ids and len(results) == len(required_ids)
    if not complete or any(result.status != FindingStatus.PASS for result in results):
        return SubmissionStatus.NEEDS_REVIEW
    return SubmissionStatus.READY
