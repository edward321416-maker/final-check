"""Checkpointed two-stage extraction execution for one durable backend node."""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.jobs import ExtractionJob, JobStage, JobStatus
from app.models.schemas import CheckSession
from app.services import profiles, sessions
from app.services.ai_providers import ProviderExecutionError, RequirementGenerator, SemanticRequirementReviewer

MAX_ATTEMPTS = 3


def now() -> datetime:
    return datetime.now(timezone.utc)


def _category(error: Exception) -> str:
    message = str(error).casefold()
    if isinstance(error, ProviderExecutionError):
        if "auth" in message or "login" in message:
            return "AUTH_UNAVAILABLE"
        if "timeout" in message or "timed out" in message:
            return "TIMEOUT"
        if "schema" in message or "structured" in message:
            return "MALFORMED_OUTPUT"
        return "PROVIDER_UNAVAILABLE"
    if isinstance(error, ValueError):
        return "MALFORMED_OUTPUT"
    return "PROVIDER_UNAVAILABLE"


def _sync_summary(session: CheckSession, job: ExtractionJob) -> None:
    session.current_job_id = job.job_id
    session.current_job = job.summary()


def _checkpoint(job: ExtractionJob, session: CheckSession,
                profile, stage: JobStage | None = None) -> None:
    if stage is not None:
        job.stage = stage
    job.checkpoint_profile = profile.model_copy(deep=True)
    job.updated_at = now()
    sessions.job_store().save_job(job)
    session.generic_profile = profile.model_copy(deep=True)
    _sync_summary(session, job)
    sessions.save(session)


def _fail(job: ExtractionJob, session: CheckSession, error: Exception,
          failed_batch: int | None = None) -> ExtractionJob:
    job.error_category = _category(error)
    job.status = JobStatus.RETRYABLE if job.attempt < MAX_ATTEMPTS else JobStatus.FAILED
    job.finished_at = now() if job.status == JobStatus.FAILED else None
    job.updated_at = now()
    sessions.job_store().save_job(job)
    profile = (job.checkpoint_profile or session.generic_profile).model_copy(deep=True)
    profile.pipeline_status = "EXTRACTION_ERROR" if job.stage == JobStage.NOT_STARTED else "REVIEW_REQUIRED"
    profile.pipeline_error = job.error_category
    profile.status = "REVIEW_REQUIRED"
    profile.extraction_complete = False
    if failed_batch is not None:
        profile.failed_batches = sorted(set([*profile.failed_batches, failed_batch]))
    profile.notices = [
        "AI job이 완료되지 않았습니다. 저장된 checkpoint부터 명시적으로 다시 시도할 수 있습니다."
    ]
    session.generic_profile = profile
    _sync_summary(session, job)
    sessions.save(session)
    return job


def create_or_get(session: CheckSession, generator: RequirementGenerator,
                  reviewer: SemanticRequirementReviewer) -> ExtractionJob:
    if session.generic_profile is None:
        raise ValueError("Announcement profile is required")
    proposed = ExtractionJob.new(
        session_id=session.id, profile=session.generic_profile,
        job_kind="TWO_STAGE_EXTRACTION",
        provider_provenance=[generator.provenance, reviewer.provenance],
    )
    job = sessions.job_store().create_or_get_job(proposed)
    _sync_summary(session, job)
    sessions.save(session)
    return job


def execute(job_id: str, generator: RequirementGenerator,
            reviewer: SemanticRequirementReviewer) -> ExtractionJob:
    job = sessions.job_store().get_job(job_id)
    if job.status in {JobStatus.SUCCEEDED, JobStatus.FAILED}:
        return job
    if job.attempt >= MAX_ATTEMPTS:
        job.status = JobStatus.FAILED
        job.error_category = job.error_category or "RETRY_LIMIT"
        job.finished_at = job.updated_at = now()
        sessions.job_store().save_job(job)
        return job

    session = sessions.get(job.session_id)
    if session.generic_profile is None:
        return _fail(job, session, ValueError("Profile missing"))
    job.status = JobStatus.RUNNING
    job.attempt += 1
    job.started_at = job.started_at or now()
    job.finished_at = None
    job.error_category = None
    job.updated_at = now()
    sessions.job_store().save_job(job)
    _sync_summary(session, job)
    sessions.save(session)

    profile = (job.checkpoint_profile or session.generic_profile).model_copy(deep=True)
    if job.stage == JobStage.NOT_STARTED:
        profile = profiles.prepare_extraction(profile, generator, reviewer)
        job.checkpoint_profile = profile.model_copy(deep=True)
        sessions.job_store().save_job(job)
        try:
            if profile.announcement.ingestion_status != "READABLE":
                profile.notices.append(profile.announcement.notice)
                profile.status = "REVIEW_REQUIRED"
                profile.pipeline_status = "REVIEW_REQUIRED"
                profile = profiles._finish(profile)
                job.status, job.stage = JobStatus.SUCCEEDED, JobStage.FINALIZED
                job.finished_at = now()
                _checkpoint(job, session, profile)
                return job
            profile = profiles.stage1_checkpoint(profile, generator)
            if profile.raw_candidate_count > profiles.HARD_CANDIDATE_CEILING:
                profile = profiles._finish(profile)
                job.status, job.stage = JobStatus.FAILED, JobStage.STAGE1_COMPLETE
                job.error_category, job.finished_at = "HARD_CEILING_EXCEEDED", now()
                _checkpoint(job, session, profile)
                return job
            _checkpoint(job, session, profile, JobStage.STAGE1_COMPLETE)
        except Exception as error:
            return _fail(job, session, error)

    profile = (job.checkpoint_profile or profile).model_copy(deep=True)
    if job.stage == JobStage.STAGE1_COMPLETE:
        try:
            profile = profiles.gate_checkpoint(profile, generator.provenance)
            _checkpoint(job, session, profile, JobStage.GATE_COMPLETE)
        except Exception as error:
            return _fail(job, session, error)

    profile = (job.checkpoint_profile or profile).model_copy(deep=True)
    for batch_index in range(profile.review_batches):
        if batch_index in job.completed_stage2_batches:
            continue
        try:
            profile = profiles.stage2_batch_checkpoint(profile, reviewer, batch_index)
        except Exception as error:
            return _fail(job, session, error, batch_index)
        job.completed_stage2_batches.append(batch_index)
        _checkpoint(job, session, profile, JobStage.STAGE2_BATCH_N_COMPLETE)

    try:
        profile.failed_batches = []
        profile = profiles.finalize_checkpoints(profile)
        job.status = JobStatus.SUCCEEDED
        job.stage = JobStage.FINALIZED
        job.error_category = None
        job.finished_at = now()
        _checkpoint(job, session, profile)
        return job
    except Exception as error:
        return _fail(job, session, error)
