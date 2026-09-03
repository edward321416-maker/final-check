from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from app.models.profiles import ConfirmRequest, GenericRequirementProfile, ReviewRequest, TextAnnouncement, VersionRequest
from app.models.schemas import CheckSession
from app.services import profiles, sessions
from app.services.announcement_input import source_from_bytes
from app.services.extractors import RequirementExtractor, get_extractor
from app.services.generic_validation import canonical_requirements

router = APIRouter(prefix="/api/sessions")


def invalidate(session: CheckSession) -> None:
    session.requirements, session.results, session.previous_results = [], [], []
    session.validation_profile, session.engine_sha256, session.status = None, None, None
    session.source_mode, session.run_state = "unavailable", "NOT_STARTED"
    session.validation_complete, session.run_error = False, None
    session.revision = 0


def custom_session(session_id: str) -> CheckSession:
    session = sessions.get(session_id)
    if session.mode != "custom":
        raise HTTPException(409, "Start a custom announcement session.")
    if sessions.LOCKS[session_id].locked():
        raise HTTPException(409, "Another operation is running.")
    return session


@router.post("/{session_id}/announcement-text", response_model=CheckSession)
async def text_announcement(session_id: str, body: TextAnnouncement) -> CheckSession:
    session = custom_session(session_id)
    async with sessions.LOCKS[session_id]:
        data = body.text.encode("utf-8")
        try:
            source = source_from_bytes(body.name, data, "TEXT")
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        path = Path(sessions.WORKSPACES[session_id].name) / "announcement.bin"
        await run_in_threadpool(path.write_bytes, data)
        invalidate(session)
        session.announcement_name = source.name
        session.generic_profile = profiles.new_profile(source)
        return sessions.save(session)


def checked_profile(session: CheckSession, body: VersionRequest) -> GenericRequirementProfile:
    profile = session.generic_profile
    if profile is None:
        raise HTTPException(409, "공고를 먼저 입력하세요.")
    if body.expected_version != profile.version:
        raise HTTPException(409, "다른 검토로 profile이 변경됐습니다. 새로고침 후 다시 확인하세요.")
    return profile


@router.post("/{session_id}/extract", response_model=CheckSession)
async def extract(session_id: str, body: VersionRequest,
                  provider: Annotated[RequirementExtractor, Depends(get_extractor)]) -> CheckSession:
    session = custom_session(session_id)
    async with sessions.LOCKS[session_id]:
        profile = checked_profile(session, body)
        try:
            updated = await run_in_threadpool(profiles.extract, profile, provider)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except Exception as error:
            raise HTTPException(503, "추출 provider 실행 실패. 요구사항을 생성하지 않았습니다.") from error
        invalidate(session)
        session.generic_profile = updated
        return sessions.save(session)


@router.post("/{session_id}/requirements/{requirement_id}/review", response_model=CheckSession)
async def review(session_id: str, requirement_id: str, body: ReviewRequest) -> CheckSession:
    session = custom_session(session_id)
    async with sessions.LOCKS[session_id]:
        profile = checked_profile(session, body)
        try:
            updated = profiles.review(profile, requirement_id, body)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        invalidate(session)
        session.generic_profile = updated
        return sessions.save(session)


@router.post("/{session_id}/profile/confirm", response_model=CheckSession)
async def confirm(session_id: str, body: ConfirmRequest) -> CheckSession:
    session = custom_session(session_id)
    async with sessions.LOCKS[session_id]:
        profile = checked_profile(session, body)
        try:
            updated = profiles.confirm(profile)
            requirements = canonical_requirements(updated)
        except ValueError as error:
            raise HTTPException(422, "모든 항목을 검토·승인해야 합니다. 비어 있거나 읽을 수 없는 공고는 확정할 수 없습니다.") from error
        invalidate(session)
        session.generic_profile = updated
        session.requirements = requirements
        session.validation_profile, session.source_mode = "generic", "generic_review"
        return sessions.save(session)
