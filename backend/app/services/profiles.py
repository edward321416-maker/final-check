"""Evidence gates and explicit human-review lifecycle, shared by every provider."""
from datetime import datetime, timezone
from math import ceil
from uuid import uuid4
from app.models.profiles import (AnnouncementSource, ExtractedRequirement, GenericRequirementProfile,
                                ProfileRequirement, ProviderProvenance, ReviewEvent, ReviewRequest,
                                SemanticReview)
from app.services.ai_providers import ProviderExecutionError, RequirementGenerator, SemanticRequirementReviewer
from app.services.extractors import atomicity_issues

OVERFLOW_THRESHOLD = 100
STAGE2_BATCH_SIZE = 50
HARD_CANDIDATE_CEILING = 500


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_profile(source: AnnouncementSource) -> GenericRequirementProfile:
    return GenericRequirementProfile(profile_id=str(uuid4()), announcement=source, created_at=now(), updated_at=now())


def mark_running(profile: GenericRequirementProfile, generator: RequirementGenerator,
                 reviewer: SemanticRequirementReviewer) -> GenericRequirementProfile:
    result = profile.model_copy(deep=True)
    result.provider = f"{generator.provenance.provider} → {reviewer.provenance.provider}"
    result.execution_kind = "ACTUAL" if generator.provenance.execution_kind == reviewer.provenance.execution_kind == "ACTUAL" else "SIMULATED"
    result.stage1, result.stage2 = generator.provenance, reviewer.provenance
    result.pipeline_status = "RUNNING"
    result.pipeline_error = None
    result.status = "REVIEW_REQUIRED"
    result.notices = ["Stage 1 생성과 Stage 2 의미 검토를 실행 중입니다. 이 화면은 완료 상태를 자동으로 확인합니다."]
    result.version += 1
    result.updated_at = now()
    return GenericRequirementProfile.model_validate(result.model_dump())


def anchor(candidate: ExtractedRequirement, source: AnnouncementSource,
           original: ExtractedRequirement | None = None, stage1: ProviderProvenance | None = None,
           semantic_review: SemanticReview | None = None) -> ProfileRequirement:
    # Re-validate provider instances as well as dictionaries. No model can bypass the contract.
    data = candidate.model_dump() if isinstance(candidate, ExtractedRequirement) else candidate
    item = ExtractedRequirement.model_validate(data)
    start = source.text.find(item.evidence.quote)
    if start < 0:
        raise ValueError("EVIDENCE_REJECTED: exact quote is absent from the announcement")
    issues = atomicity_issues(item.rule)
    review_required = semantic_review is not None and semantic_review.decision == "REVIEW"
    return ProfileRequirement(
        **item.model_dump(), evidence_start=start, evidence_end=start + len(item.evidence.quote),
        original=original or item, extraction_status="NEEDS_REVIEW" if issues or review_required else "EXTRACTED",
        issues=issues, stage1=stage1,
        stage2_decision=semantic_review.decision if semantic_review else None,
        stage2_reason=semantic_review.reason if semantic_review else "",
        stage2=semantic_review.reviewer if semantic_review else None,
        authoritative=False,
    )


def _finish(result: GenericRequirementProfile) -> GenericRequirementProfile:
    result.version += 1
    result.updated_at = now()
    result.history.append(ReviewEvent(action="EXTRACT", at=now()))
    return GenericRequirementProfile.model_validate(result.model_dump())


def _review_batch(reviewer: SemanticRequirementReviewer, source: AnnouncementSource,
                  batch: list[ExtractedRequirement]) -> list[SemanticReview]:
    reviews = reviewer.review(source, batch)
    expected = [candidate.requirement_id for candidate in batch]
    actual = [review.requirement_id for review in reviews]
    if len(set(actual)) != len(actual) or set(actual) != set(expected):
        raise ValueError("Stage 2 must return exactly one decision for every candidate")
    return reviews


def prepare_extraction(profile: GenericRequirementProfile, generator: RequirementGenerator,
                       reviewer: SemanticRequirementReviewer) -> GenericRequirementProfile:
    result = profile.model_copy(deep=True)
    result.provider = f"{generator.provenance.provider} → {reviewer.provenance.provider}"
    result.execution_kind = "ACTUAL" if generator.provenance.execution_kind == reviewer.provenance.execution_kind == "ACTUAL" else "SIMULATED"
    result.stage1, result.stage2 = generator.provenance, reviewer.provenance
    result.pipeline_status = "RUNNING"
    result.pipeline_error = None
    result.status = "REVIEW_REQUIRED"
    result.notices = ["AI가 공고에서 추출하고 검토한 후보입니다. 공식 공고 규칙이 아니며, 원문 전체와 모든 항목을 사람이 확인해야 합니다."]
    result.updated_at = now()
    return result


def stage1_checkpoint(result: GenericRequirementProfile,
                      generator: RequirementGenerator) -> GenericRequirementProfile:
    generated = generator.generate(result.announcement)
    result.raw_candidate_count = len(generated)
    result.raw_candidates = []
    for candidate in generated:
        try:
            result.raw_candidates.append(ExtractedRequirement.model_validate(candidate))
        except ValueError:
            result.notices.append("Stage 1 후보 거부: canonical schema 또는 enum gate 실패.")
    if result.raw_candidate_count > HARD_CANDIDATE_CEILING:
        result.pipeline_status = "EXTRACTION_ERROR"
        result.status = "REVIEW_REQUIRED"
        result.pipeline_error = f"HARD_CEILING_EXCEEDED: {result.raw_candidate_count}>{HARD_CANDIDATE_CEILING}"
        result.notices.append(f"HARD_CEILING_EXCEEDED: {result.raw_candidate_count}개 후보를 처리하지 않았습니다. 절대 상한은 {HARD_CANDIDATE_CEILING}개이며 READY가 될 수 없습니다.")
    result.overflow = result.raw_candidate_count > OVERFLOW_THRESHOLD
    if result.overflow and result.raw_candidate_count <= HARD_CANDIDATE_CEILING:
        result.notices.append(f"OVERFLOW_REVIEW: {result.raw_candidate_count}개 후보를 버리지 않고 {STAGE2_BATCH_SIZE}개 단위로 검토합니다.")
    result.updated_at = now()
    return result


def gate_checkpoint(result: GenericRequirementProfile,
                    stage1: ProviderProvenance) -> GenericRequirementProfile:
    seen: set[str] = set()
    result.gated_candidate_ids = []
    result.requirements = []
    result.stage2_reviews = []
    for candidate in result.raw_candidates:
        try:
            rule = anchor(candidate, result.announcement, stage1=stage1)
            if rule.requirement_id in seen:
                raise ValueError("Duplicate requirement ID")
            seen.add(rule.requirement_id)
            result.gated_candidate_ids.append(candidate.requirement_id)
        except ValueError:
            result.notices.append("후보 거부: evidence / offset / schema / duplicate ID gate 실패. 원문을 직접 확인하세요.")
    result.gated_candidate_count = len(result.gated_candidate_ids)
    result.review_batches = ceil(result.gated_candidate_count / STAGE2_BATCH_SIZE) if result.gated_candidate_count else 0
    result.failed_batches = []
    result.updated_at = now()
    return result


def stage2_batch_checkpoint(result: GenericRequirementProfile,
                            reviewer: SemanticRequirementReviewer,
                            batch_index: int) -> GenericRequirementProfile:
    gated = set(result.gated_candidate_ids)
    items = [item for item in result.raw_candidates if item.requirement_id in gated]
    batches = [items[index:index + STAGE2_BATCH_SIZE] for index in range(0, len(items), STAGE2_BATCH_SIZE)]
    if batch_index >= len(batches):
        return result
    batch = batches[batch_index]
    reviews = _review_batch(reviewer, result.announcement, batch)
    by_id = {candidate.requirement_id: candidate for candidate in batch}
    existing_reviews = {review.requirement_id for review in result.stage2_reviews}
    existing_requirements = {requirement.requirement_id for requirement in result.requirements}
    for semantic_review in reviews:
        if semantic_review.requirement_id not in existing_reviews:
            result.stage2_reviews.append(semantic_review)
        if semantic_review.decision == "DROP":
            continue
        candidate = by_id[semantic_review.requirement_id]
        if candidate.requirement_id not in existing_requirements:
            result.requirements.append(anchor(
                candidate, result.announcement, stage1=result.stage1,
                semantic_review=semantic_review,
            ))
    result.updated_at = now()
    return result


def finalize_checkpoints(result: GenericRequirementProfile) -> GenericRequirementProfile:
    result.dropped_candidate_count = len([review for review in result.stage2_reviews if review.decision == "DROP"])
    result.failed_batches = sorted(set(result.failed_batches))
    result.extraction_complete = not result.failed_batches
    if result.failed_batches:
        result.pipeline_status = "REVIEW_REQUIRED"
        result.status = "REVIEW_REQUIRED"
    else:
        result.pipeline_status = "OVERFLOW_REVIEW" if result.overflow else "COMPLETE"
        result.status = "DRAFT" if result.requirements else "REVIEW_REQUIRED"
        if not result.requirements:
            result.notices.append("Stage 2가 유지한 applicant-facing 후보가 없습니다. 원문을 직접 확인하세요.")
    return _finish(result)


def extract(profile: GenericRequirementProfile, generator: RequirementGenerator,
            reviewer: SemanticRequirementReviewer) -> GenericRequirementProfile:
    if profile.extraction_complete:
        raise ValueError("이미 추출했습니다. 재추출하려면 홈에서 새 공고를 입력하세요.")
    result = prepare_extraction(profile, generator, reviewer)
    if result.announcement.ingestion_status != "READABLE":
        result.notices.append(result.announcement.notice)
        result.status = "REVIEW_REQUIRED"
        result.pipeline_status = "REVIEW_REQUIRED"
        return _finish(result)

    retry_batches = set(result.failed_batches)
    if result.raw_candidates and retry_batches:
        items = [item for item in result.raw_candidates if item.requirement_id in set(result.gated_candidate_ids)]
        result.failed_batches = []
        batch_indexes = retry_batches
        result.notices.append("실패한 Stage 2 batch만 다시 실행합니다. 완료된 batch 결과는 보존했습니다.")
    else:
        try:
            result = stage1_checkpoint(result, generator)
        except Exception as error:
            result.pipeline_status = "EXTRACTION_ERROR"
            result.status = "REVIEW_REQUIRED"
            result.pipeline_error = str(error) if isinstance(error, ProviderExecutionError) else type(error).__name__
            result.notices.append("Stage 1 actual provider가 완료되지 않았습니다. 결과를 만들지 않았으며 다시 시도할 수 있습니다.")
            return _finish(result)
        if result.raw_candidate_count > HARD_CANDIDATE_CEILING:
            return _finish(result)
        result = gate_checkpoint(result, generator.provenance)
        items = [item for item in result.raw_candidates if item.requirement_id in set(result.gated_candidate_ids)]
        batch_indexes = set(range(result.review_batches))

    batches = [items[index:index + STAGE2_BATCH_SIZE] for index in range(0, len(items), STAGE2_BATCH_SIZE)]
    for batch_index in sorted(batch_indexes):
        if batch_index >= len(batches):
            continue
        batch = batches[batch_index]
        try:
            result = stage2_batch_checkpoint(result, reviewer, batch_index)
        except Exception as error:
            result.failed_batches.append(batch_index)
            result.pipeline_error = str(error) if isinstance(error, ProviderExecutionError) else type(error).__name__
            result.notices.append(f"Stage 2 batch {batch_index + 1}/{len(batches)} 실패. 완료된 결과는 보존했으며 재시도할 수 있습니다.")
            continue
    return finalize_checkpoints(result)


def review(profile: GenericRequirementProfile, requirement_id: str, body: ReviewRequest) -> GenericRequirementProfile:
    if len(profile.history) >= 499:
        raise ValueError("검토 이력 한도에 도달했습니다. 새 세션을 시작하세요.")
    result = profile.model_copy(deep=True)
    index = next((i for i, r in enumerate(result.requirements) if r.requirement_id == requirement_id), None)
    if index is None:
        raise ValueError("Requirement not found")
    before = result.requirements[index].model_copy(deep=True)
    after = None
    if body.action == "DELETE":
        result.requirements.pop(index)
    else:
        if body.requirement and body.requirement.requirement_id != requirement_id:
            raise ValueError("Requirement ID cannot change")
        after = anchor(body.requirement or ExtractedRequirement.model_validate(before.model_dump(include=set(ExtractedRequirement.model_fields))),
                       result.announcement, before.original, before.stage1)
        after.stage2_decision, after.stage2_reason, after.stage2 = before.stage2_decision, before.stage2_reason, before.stage2
        after.extraction_status = "NEEDS_REVIEW"
        after.authoritative = False
        if body.action == "APPROVE":
            if after.issues:
                raise ValueError("복합 조건은 단일 조건으로 수정한 후 승인하세요.")
            after.extraction_status = "CONFIRMED"
            after.authoritative = True
        result.requirements[index] = after
    result.status = "REVIEW_REQUIRED"
    result.version += 1
    result.updated_at = now()
    result.history.append(ReviewEvent(action=body.action, requirement_id=requirement_id, at=now(), before=before, after=after))
    return GenericRequirementProfile.model_validate(result.model_dump())


def confirm(profile: GenericRequirementProfile) -> GenericRequirementProfile:
    result = profile.model_copy(deep=True)
    result.status = "CONFIRMED"
    result.version += 1
    result.updated_at = now()
    result.history.append(ReviewEvent(action="CONFIRM_PROFILE", at=now()))
    return GenericRequirementProfile.model_validate(result.model_dump())
