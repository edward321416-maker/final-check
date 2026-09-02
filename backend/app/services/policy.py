from app.models.schemas import FindingStatus, Requirement, SubmissionStatus, ValidationResult


def summarize(requirements: list[Requirement], results: list[ValidationResult],
              *, validation_complete: bool = False) -> SubmissionStatus:
    if any(result.status == FindingStatus.BLOCKER for result in results):
        return SubmissionStatus.BLOCKED
    required_ids = {rule.id for rule in requirements}
    result_ids = {result.requirement_id for result in results}
    complete = validation_complete and bool(required_ids) and result_ids == required_ids and len(results) == len(required_ids)
    if not complete or any(result.status != FindingStatus.PASS for result in results):
        return SubmissionStatus.REVIEW_REQUIRED
    return SubmissionStatus.READY
