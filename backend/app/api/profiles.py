import asyncio
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool
from app.models.profiles import ConfirmRequest, GenericRequirementProfile, ReviewRequest, TextAnnouncement, VersionRequest
from app.models.jobs import JobStatus
from app.models.schemas import CheckSession
from app.services import jobs, profiles, sessions
from app.services.announcement_input import source_from_bytes
from app.services.ai_providers import (RequirementGenerator, SemanticRequirementReviewer,
                                       ProviderExecutionError, get_generator, get_reviewer)
from app.services.generic_validation import canonical_requirements
from app.services.verifier_compiler import VerificationPlanner, compile_or_reuse
from app.services.verifier_planner import get_verification_planner

router = APIRouter(prefix="/api/sessions")
EXTRACTION_TASKS: dict[str, asyncio.Task[None]] = {}


def invalidate(session: CheckSession) -> None:
    session.requirements, session.results, session.previous_results = [], [], []
    session.validation_profile, session.engine_sha256, session.status = None, None, None
    session.source_mode, session.run_state = "unavailable", "NOT_STARTED"
    session.validation_complete, session.run_error = False, None
    session.verification_plan = None
    session.verification_plan_state = "NOT_STARTED"
    session.verification_plan_error = None
    session.revision = 0


def custom_session(session_id: str) -> CheckSession:
    session = sessions.get(session_id)
    if session.mode != "custom":
        raise HTTPException(409, "Start a custom announcement session.")
    if sessions.LOCKS[session_id].locked():
        raise HTTPException(409, "Another operation is running.")
    return session


async def complete_extraction(session_id: str, job_id: str,
                              generator: RequirementGenerator,
                              reviewer: SemanticRequirementReviewer) -> None:
    lock = sessions.LOCKS.get(session_id)
    if lock is None:
        return
    async with lock:
        await run_in_threadpool(jobs.execute, job_id, generator, reviewer)


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
        await run_in_threadpool(sessions.write_announcement, session_id, data)
        invalidate(session)
        session.current_job_id, session.current_job = None, None
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
        current = None
        if session.current_job_id:
            try:
                current = sessions.job_store().get_job(session.current_job_id)
            except KeyError:
                current = None
        if current and current.profile_id == profile.profile_id:
            if current.status in {JobStatus.PENDING, JobStatus.RUNNING}:
                return session
            if current.status == JobStatus.SUCCEEDED:
                return session
            if current.status == JobStatus.FAILED:
                raise HTTPException(409, "AI extraction retry limit reached. Start a new announcement profile.")
            extraction_job = current
        else:
            extraction_job = jobs.create_or_get(session, generator, reviewer)
        if not (getattr(generator, "requires_background", False)
                or getattr(reviewer, "requires_background", False)):
            invalidate(session)
            sessions.save(session)
            await run_in_threadpool(jobs.execute, extraction_job.job_id, generator, reviewer)
            return sessions.get(session_id)
        updated = profile.model_copy(deep=True)
        updated.pipeline_status = "RUNNING"
        updated.pipeline_error = None
        updated.status = "REVIEW_REQUIRED"
        updated.notices = ["Stage 1 생성과 Stage 2 의미 검토를 실행 중입니다. 완료 상태를 자동으로 확인합니다."]
        if extraction_job.attempt == 0:
            updated.version += 1
        updated.updated_at = profiles.now()
        invalidate(session)
        session.generic_profile = updated
        saved = sessions.save(session)
        task = asyncio.create_task(complete_extraction(session_id, extraction_job.job_id, generator, reviewer))
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


@router.post("/{session_id}/verification-plan/compile", response_model=CheckSession)
async def compile_verification_plan(
    session_id: str,
    body: VersionRequest,
    planner: Annotated[VerificationPlanner, Depends(get_verification_planner)],
) -> CheckSession:
    session = custom_session(session_id)
    async with sessions.LOCKS[session_id]:
        profile = checked_profile(session, body)
        if profile.status != "CONFIRMED":
            raise HTTPException(422, "Human-confirmed profile required before verifier compilation.")
        if session.verification_plan and session.verification_plan.is_valid_for(profile):
            return session
        session.verification_plan_state = "RUNNING"
        session.verification_plan_error = None
        sessions.save(session)
        try:
            plan_set = await run_in_threadpool(compile_or_reuse, profile, planner, session.verification_plan)
        except (ProviderExecutionError, ValueError) as error:
            session.verification_plan = None
            session.verification_plan_state = "REVIEW_REQUIRED"
            session.verification_plan_error = "PLANNER_UNAVAILABLE" if isinstance(error, ProviderExecutionError) else "PLANNER_SCHEMA_REJECTED"
            session.source_mode = "generic_review"
            session.status = None
            return sessions.save(session)
        session.verification_plan = plan_set
        session.verification_plan_state = "READY"
        session.verification_plan_error = None
        session.source_mode = "generic_verifier"
        session.status = None
        return sessions.save(session)
