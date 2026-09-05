import asyncio
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from app.models.profiles import ConfirmRequest, GenericRequirementProfile, ReviewRequest, TextAnnouncement, VersionRequest
from app.models.schemas import CheckSession
from app.services import profiles, sessions
from app.services.announcement_input import source_from_bytes
from app.services.ai_providers import (RequirementGenerator, SemanticRequirementReviewer,
                                       get_generator, get_reviewer)
from app.services.generic_validation import canonical_requirements

router = APIRouter(prefix="/api/sessions")
EXTRACTION_TASKS: dict[str, asyncio.Task[None]] = {}


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


async def complete_extraction(session_id: str, base: GenericRequirementProfile,
                              generator: RequirementGenerator,
                              reviewer: SemanticRequirementReviewer) -> None:
    try:
        updated = await run_in_threadpool(profiles.extract, base, generator, reviewer)
    except Exception as error:
        updated = base.model_copy(deep=True)
        updated.pipeline_status = "EXTRACTION_ERROR"
        updated.pipeline_error = type(error).__name__
        updated.status = "REVIEW_REQUIRED"
        updated.notices = ["Two-stage provider 실행이 완료되지 않았습니다. 결과를 만들지 않았으며 다시 시도할 수 있습니다."]
        updated.version += 1
        updated.updated_at = profiles.now()
    lock = sessions.LOCKS.get(session_id)
    if lock is None:
        return
    async with lock:
        session = sessions.get(session_id)
        current = session.generic_profile
        if current and current.profile_id == base.profile_id and current.version == base.version:
            invalidate(session)
            session.generic_profile = updated
            sessions.save(session)


def forget_extraction(session_id: str, completed: asyncio.Task[None]) -> None:
    if EXTRACTION_TASKS.get(session_id) is completed:
        EXTRACTION_TASKS.pop(session_id, None)
    try:
        completed.exception()
    except asyncio.CancelledError:
        pass


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
                  generator: Annotated[RequirementGenerator, Depends(get_generator)],
                  reviewer: Annotated[SemanticRequirementReviewer, Depends(get_reviewer)]) -> CheckSession:
    session = custom_session(session_id)
    async with sessions.LOCKS[session_id]:
        profile = checked_profile(session, body)
        if profile.pipeline_status == "RUNNING":
            raise HTTPException(409, "Two-stage extraction is already running.")
        if not (getattr(generator, "requires_background", False)
                or getattr(reviewer, "requires_background", False)):
            try:
                updated = await run_in_threadpool(profiles.extract, profile, generator, reviewer)
            except ValueError as error:
                raise HTTPException(422, str(error)) from error
            except Exception as error:
                raise HTTPException(503, "Two-stage provider 실행 실패. Profile은 확정되지 않았습니다.") from error
            invalidate(session)
            session.generic_profile = updated
            return sessions.save(session)
        updated = profiles.mark_running(profile, generator, reviewer)
        invalidate(session)
        session.generic_profile = updated
        saved = sessions.save(session)
        task = asyncio.create_task(complete_extraction(session_id, updated.model_copy(deep=True), generator, reviewer))
        EXTRACTION_TASKS[session_id] = task
        task.add_done_callback(lambda completed, key=session_id: forget_extraction(key, completed))
        return saved


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
