import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
from typing import Annotated, Literal
from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from app.models.schemas import CheckSession, CreateSession, SubmissionFile, SubmissionStatus
from app.services import demo, sessions
from app.services import generic_policy, generic_validation, profiles
from app.services.announcement_input import MAX_ANNOUNCEMENT_BYTES, source_from_bytes
from app.services.ai_providers import provider_status
from app.services.public_guard import GuardConfig
from app.api.profiles import custom_session, invalidate
from app.services.policy import summarize
from app.validators.v15_adapter import EXPECTED_SHA256, ValidatorUnavailable, profile_requirements, validator_v15

router = APIRouter(prefix="/api")
MAX_FILE_BYTES = 320 * 1024 * 1024
MAX_PACKAGE_BYTES = 350 * 1024 * 1024
MAX_FILES = 8


def _positive_limit(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer") from error
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def upload_limits() -> tuple[int, int, int]:
    return (
        _positive_limit("FINAL_CHECK_MAX_FILE_BYTES", MAX_FILE_BYTES),
        _positive_limit("FINAL_CHECK_MAX_PACKAGE_BYTES", MAX_PACKAGE_BYTES),
        _positive_limit("FINAL_CHECK_MAX_FILES", MAX_FILES),
    )


async def receive(upload: UploadFile, allowed: set[str], directory: Path | None = None,
                  max_bytes: int | None = None) -> SubmissionFile:
    original = upload.filename or ""
    name = PurePosixPath(original.replace("\\", "/")).name
    if not name or len(name) > 200 or name != original or any(char in name for char in '<>:"|?*') or name.endswith((" ", ".")):
        raise HTTPException(422, "Invalid filename.")
    if PurePosixPath(name).suffix.lower() not in allowed:
        raise HTTPException(415, "Unsupported file type.")
    digest = hashlib.sha256()
    size = 0
    stream = (directory / name).open("xb") if directory else None
    configured_file_limit, _, _ = upload_limits()
    try:
        while chunk := await upload.read(64 * 1024):
            size += len(chunk)
            if size > (configured_file_limit if max_bytes is None else max_bytes):
                raise HTTPException(413, "File exceeds the upload size limit.")
            digest.update(chunk)
            if stream:
                await run_in_threadpool(stream.write, chunk)
    finally:
        if stream:
            stream.close()
        await upload.close()
    if not size:
        raise HTTPException(422, "Empty files are not accepted.")
    return SubmissionFile(name=name, size_bytes=size, media_type=upload.content_type or "application/octet-stream", sha256=digest.hexdigest())


def _ffprobe_status() -> dict[str, str | None]:
    executable = shutil.which("ffprobe")
    if not executable:
        return {"status": "unavailable", "version": None}
    try:
        result = subprocess.run(
            [executable, "-version"], capture_output=True, text=True, timeout=5, check=True,
        )
        return {"status": "available", "version": result.stdout.splitlines()[0][:200]}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unavailable", "version": None}


@router.get("/health")
async def health(response: Response) -> dict:
    available = await run_in_threadpool(lambda: validator_v15.available)
    ai = await run_in_threadpool(provider_status)
    ffprobe = await run_in_threadpool(_ffprobe_status)
    try:
        await run_in_threadpool(sessions.session_store().count_sessions)
        storage = "available"
    except Exception:
        storage = "unavailable"
    try:
        guard_config = GuardConfig.from_environment()
        public_guard = "enabled" if guard_config.enabled else "disabled"
    except RuntimeError:
        public_guard = "unavailable"
    ai_summary = {
        "provider": ai["provider"],
        "configured": ai.get("configured", ai.get("mode") != "unavailable"),
        "model": ai.get("model"),
        "reasoning": ai.get("reasoning"),
    }
    critical = available and storage == "available" and ffprobe["status"] == "available"
    if os.environ.get("FINAL_CHECK_ENV", "local").lower() == "production":
        critical = (
            critical
            and ai.get("provider") == "Codex CLI"
            and bool(ai_summary["configured"])
            and ai_summary["model"] == "gpt-5.6-sol"
            and ai_summary["reasoning"] == "high"
            and public_guard == "enabled"
        )
    if not critical:
        response.status_code = 503
    return {
        "status": "ok" if critical else "unavailable",
        "runtime": "single-node",
        "storage": storage,
        "mode": "frozen_v15",
        "validator": "available" if available else "unavailable",
        "ffprobe": ffprobe,
        "ai": ai_summary,
        "public_guard": public_guard,
        "engine_sha256": EXPECTED_SHA256,
        "vision_provider": "unavailable",
        "version": "0.6.0",
        "generic_extractor": "two-stage-ai-mvp",
        "generic_ai_provider": ai,
        "generic_verification": "typed-verifier-compiler-local-mvp",
    }


@router.post("/sessions", response_model=CheckSession, status_code=201)
async def create_session(body: CreateSession) -> CheckSession:
    return sessions.create(body.mode)


@router.get("/sessions/{session_id}", response_model=CheckSession)
async def get_session(session_id: str) -> CheckSession:
    return sessions.get(session_id)


@router.post("/sessions/{session_id}/demo-announcement", response_model=CheckSession)
async def announcement(session_id: str) -> CheckSession:
    session = sessions.get(session_id)
    if session.mode != "demo":
        raise HTTPException(409, "Custom announcements need their own verified requirement profile.")
    try:
        requirements = await run_in_threadpool(profile_requirements)
    except Exception as error:
        raise HTTPException(503, "Frozen validator profile is unavailable.") from error
    session.announcement_name = "동결 handoff 공고 발췌 · 숏폼 공모전"
    session.requirements = requirements
    session.validation_profile = "frozen_v15"
    session.source_mode = "validator"
    session.engine_sha256 = EXPECTED_SHA256
    return sessions.save(session)


@router.post("/sessions/{session_id}/announcement", response_model=CheckSession)
async def upload_announcement(session_id: str, file: Annotated[UploadFile, File()]) -> CheckSession:
    session = custom_session(session_id)
    async with sessions.LOCKS[session_id]:
        # Input files never share a directory with the submission package.
        with sessions.new_package(session_id) as temporary:
            receipt = await receive(file, {".pdf", ".txt"}, Path(temporary), MAX_ANNOUNCEMENT_BYTES)
            path = Path(temporary) / receipt.name
            data = await run_in_threadpool(path.read_bytes)
            source = await run_in_threadpool(source_from_bytes, receipt.name, data,
                                            "PDF" if path.suffix.lower() == ".pdf" else "TEXT", path)
            await run_in_threadpool(sessions.write_announcement, session_id, data)
        invalidate(session)
        session.current_job_id, session.current_job = None, None
        session.announcement_name = receipt.name
        session.generic_profile = profiles.new_profile(source)
        return sessions.save(session)


@router.get("/demo-files/{case}", response_model=list[SubmissionFile])
def demo_manifest(case: Literal["demo-broken", "demo-fixed"]) -> list[SubmissionFile]:
    return demo.fixture_files(case)


@router.get("/demo-files/{case}/{filename}")
def demo_download(case: Literal["demo-broken", "demo-fixed"], filename: str) -> FileResponse:
    try:
        file = demo.fixture_path(case, filename)
    except ValueError as error:
        raise HTTPException(404, "Unknown demo file") from error
    return FileResponse(file, filename=file.name, media_type="application/pdf" if file.suffix == ".pdf" else "video/mp4")


@router.post("/sessions/{session_id}/files", response_model=CheckSession)
async def upload_files(session_id: str, files: Annotated[list[UploadFile], File()]) -> CheckSession:
    session = sessions.get(session_id)
    _, package_limit, max_files = upload_limits()
    if not session.announcement_name:
        raise HTTPException(409, "Select an announcement first.")
    if not 1 <= len(files) <= max_files:
        raise HTTPException(422, f"Select between 1 and {max_files} files.")
    names = [(file.filename or "").casefold() for file in files]
    if len(set(names)) != len(names):
        raise HTTPException(422, "Duplicate file names are not accepted.")
    lock = sessions.LOCKS[session_id]
    if lock.locked():
        raise HTTPException(409, "Another upload or validation is already running.")
    async with lock:
        package = sessions.new_package(session_id)
        committed = False
        try:
            receipt = [await receive(file, {".pdf", ".mp4"}, Path(package.name)) for file in files]
            if sum(file.size_bytes for file in receipt) > package_limit:
                raise HTTPException(413, "Package exceeds the configured upload size limit.")
            session.previous_results = session.results or session.previous_results
            session.files = receipt
            session.results = []
            session.status = None
            session.validation_complete = False
            session.run_state = "NOT_STARTED"
            session.run_error = None
            session.fixture = await run_in_threadpool(demo.identify_fixture, receipt)
            sessions.replace_package(session_id, package)
            committed = True
            return sessions.save(session)
        finally:
            for file in files:
                await file.close()
            if not committed:
                package.cleanup()


@router.post("/sessions/{session_id}/validate", response_model=CheckSession)
async def validate(session_id: str) -> CheckSession:
    session = sessions.get(session_id)
    if session.validation_profile not in {"frozen_v15", "generic"}:
        raise HTTPException(503, "Announcement extraction is not connected; no verified requirement profile.")
    package = sessions.package_path(session_id)
    lock = sessions.LOCKS[session_id]
    if lock.locked():
        raise HTTPException(409, "Another upload or validation is already running.")
    async with lock:
        if session.results:
            session.previous_results = session.results
        session.results = []
        session.status = SubmissionStatus.REVIEW_REQUIRED
        session.run_state = "RUNNING"
        session.validation_complete = False
        session.run_error = None
        sessions.save(session)
        try:
            runner = generic_validation.validate if session.validation_profile == "generic" else validator_v15.validate
            run = await run_in_threadpool(runner, session.model_copy(deep=True), package)
            # Preserve raw output privately without adding output files to the submitted package.
            raw_path = sessions.workspace_path(session_id) / f"run-{session.revision + 1}-raw.json"
            await run_in_threadpool(raw_path.write_text, json.dumps(run.raw, ensure_ascii=False, indent=2), encoding="utf-8")
            session.results = run.results
            session.validation_complete = run.complete
            session.status = (
                generic_policy.summarize(session.generic_profile, run.results)
                if session.validation_profile == "generic" and session.generic_profile is not None
                else summarize(session.requirements, run.results, validation_complete=run.complete)
            )
            session.engine_sha256 = run.engine_sha256
            session.run_state = "COMPLETE"
            session.revision += 1
            return sessions.save(session)
        except Exception as error:
            session.results = []
            session.status = SubmissionStatus.REVIEW_REQUIRED
            session.validation_complete = False
            session.run_state = "FAILED"
            session.run_error = "실제 검증 실행이 완료되지 않았습니다. 파일을 확인하고 다시 시도하세요."
            sessions.save(session)
            raise HTTPException(503 if isinstance(error, ValidatorUnavailable) else 502, session.run_error) from error
