"""Evidence gates and explicit human-review lifecycle, shared by every provider."""
from datetime import datetime, timezone
from uuid import uuid4
from app.models.profiles import (AnnouncementSource, ExtractedRequirement, GenericRequirementProfile,
                                ProfileRequirement, ReviewEvent, ReviewRequest)
from app.services.extractors import RequirementExtractor, atomicity_issues


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_profile(source: AnnouncementSource) -> GenericRequirementProfile:
    return GenericRequirementProfile(profile_id=str(uuid4()), announcement=source, created_at=now(), updated_at=now())


def anchor(candidate: ExtractedRequirement, source: AnnouncementSource,
           original: ExtractedRequirement | None = None) -> ProfileRequirement:
    # Re-validate provider instances as well as dictionaries. No model can bypass the contract.
    data = candidate.model_dump() if isinstance(candidate, ExtractedRequirement) else candidate
    item = ExtractedRequirement.model_validate(data)
    start = source.text.find(item.evidence.quote)
    if start < 0:
        raise ValueError("EVIDENCE_REJECTED: exact quote is absent from the announcement")
    issues = atomicity_issues(item.rule)
    return ProfileRequirement(**item.model_dump(), evidence_start=start, evidence_end=start + len(item.evidence.quote),
                              original=original or item, extraction_status="NEEDS_REVIEW" if issues else "EXTRACTED", issues=issues)


def extract(profile: GenericRequirementProfile, provider: RequirementExtractor) -> GenericRequirementProfile:
    if profile.extraction_complete:
        raise ValueError("이미 추출했습니다. 재추출하려면 홈에서 새 공고를 입력하세요.")
    result = profile.model_copy(deep=True)
    result.provider, result.execution_kind = provider.name, provider.execution_kind
    result.notices = ["로컬 규칙 후보입니다. confidence=0.5는 미보정 값이며 정확도가 아닙니다. 원문 전체를 검토하세요."]
    if result.announcement.ingestion_status != "READABLE":
        result.notices.append(result.announcement.notice)
        result.status = "REVIEW_REQUIRED"
    else:
        items = provider.extract(result.announcement)
        if len(items) > 100:
            raise ValueError("Too many extraction candidates")
        seen: set[str] = set()
        for candidate in items:
            try:
                rule = anchor(candidate, result.announcement)
                if rule.requirement_id in seen:
                    raise ValueError("Duplicate requirement ID")
                seen.add(rule.requirement_id)
                result.requirements.append(rule)
            except ValueError:
                # Do not materialize unsupported or invented rules, even as findings.
                result.notices.append("후보 거부: evidence / schema / duplicate ID gate 실패. 원문을 직접 확인하세요.")
        result.extraction_complete = True
        if not result.requirements or any(r.issues for r in result.requirements):
            result.status = "REVIEW_REQUIRED"
        if not result.requirements:
            result.notices.append("지원하는 제출 조건 후보를 찾지 못했습니다. 내용이나 조건을 추정하지 않았습니다.")
    result.version += 1
    result.updated_at = now()
    result.history.append(ReviewEvent(action="EXTRACT", at=now()))
    return GenericRequirementProfile.model_validate(result.model_dump())


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
                       result.announcement, before.original)
        after.extraction_status = "NEEDS_REVIEW"
        if body.action == "APPROVE":
            if after.issues:
                raise ValueError("복합 조건은 단일 조건으로 수정한 후 승인하세요.")
            after.extraction_status = "CONFIRMED"
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
