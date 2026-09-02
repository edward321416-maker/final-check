import hashlib
from pathlib import PurePosixPath
from typing import Annotated
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.models.schemas import CheckSession, CreateSession, FixtureRequest, SubmissionFile, SubmissionStatus
from app.services import demo, sessions
from app.services.policy import summarize
from app.validators.v15_adapter import ValidatorUnavailable, validator_v15

router = APIRouter(prefix="/api")
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PACKAGE_BYTES = 40 * 1024 * 1024
MAX_FILES = 8


async def file_metadata(upload: UploadFile, allowed: set[str]) -> SubmissionFile:
    name = PurePosixPath((upload.filename or "").replace("\\", "/")).name
    if PurePosixPath(name).suffix.lower() not in allowed:
        raise HTTPException(415, "Unsupported file type.")
    digest = hashlib.sha256()
    size = 0
    try:
        while chunk := await upload.read(64 * 1024):
            size += len(chunk)
            if size > MAX_FILE_BYTES:
                raise HTTPException(413, "Each file must be at most 20 MiB.")
            digest.update(chunk)
    finally:
        await upload.close()
    if not size:
        raise HTTPException(422, "Empty files are not accepted.")
    return SubmissionFile(name=name, size_bytes=size, media_type=upload.content_type or "application/octet-stream", sha256=digest.hexdigest())


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "mode": "mock", "validator": "available" if validator_v15.available else "unavailable", "version": "0.1.0"}


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
        raise HTTPException(409, "Demo evidence cannot be attached to custom uploads.")
    session.announcement_name = "demo-announcement.txt"
    session.requirements = demo.load_requirements()
    return sessions.save(session)


@router.post("/sessions/{session_id}/announcement", response_model=CheckSession)
async def upload_announcement(session_id: str, file: Annotated[UploadFile, File()]) -> CheckSession:
    session = sessions.get(session_id)
    if session.mode != "custom":
        raise HTTPException(409, "Start a custom session to upload your announcement.")
    metadata = await file_metadata(file, {".pdf", ".txt"})
    session.announcement_name = metadata.name
    session.requirements = []
    session.revision = 0
    session.files = []
    session.results = []
    session.previous_results = []
    session.status = SubmissionStatus.NOT_CHECKED
    return sessions.save(session)


@router.post("/sessions/{session_id}/fixture", response_model=CheckSession)
async def select_fixture(session_id: str, body: FixtureRequest) -> CheckSession:
    session = sessions.get(session_id)
    if session.mode != "demo" or not session.requirements:
        raise HTTPException(409, "Analyze the demo announcement first.")
    session.files = demo.fixture_files(body.fixture)
    session.fixture = body.fixture
    session.status = SubmissionStatus.NOT_CHECKED
    # Keep the latest checked results separately until the next run completes.
    if session.results:
        session.previous_results = session.results
    session.results = []
    return sessions.save(session)


@router.post("/sessions/{session_id}/files", response_model=CheckSession)
async def upload_files(session_id: str, files: Annotated[list[UploadFile], File()]) -> CheckSession:
    session = sessions.get(session_id)
    if not session.announcement_name:
        raise HTTPException(409, "Select an announcement first.")
    if not 1 <= len(files) <= MAX_FILES:
        raise HTTPException(422, "Select between 1 and 8 files.")
    try:
        metadata = [await file_metadata(file, {".pdf", ".mp4"}) for file in files]
    finally:
        for file in files:
            await file.close()
    if sum(file.size_bytes for file in metadata) > MAX_PACKAGE_BYTES:
        raise HTTPException(413, "Package must be at most 40 MiB.")
    if len({file.name.lower() for file in metadata}) != len(metadata):
        raise HTTPException(422, "Duplicate file names are not accepted.")
    # Custom files are never validated against synthetic demo results.
    session.mode = "custom"
    session.source_mode = "unavailable"
    session.fixture = None
    session.files = metadata
    session.revision = 0
    session.requirements = []
    session.results = []
    session.previous_results = []
    session.status = SubmissionStatus.NOT_CHECKED
    return sessions.save(session)


@router.post("/sessions/{session_id}/validate", response_model=CheckSession)
async def validate(session_id: str) -> CheckSession:
    session = sessions.get(session_id)
    if session.mode != "demo":
        try:
            validator_v15.require_available()
        except ValidatorUnavailable as error:
            raise HTTPException(503, str(error)) from error
        # Real file retention/dispatch requires the verified native engine contract.
        raise HTTPException(503, "Real validation dispatch is not configured.")
    if not session.requirements or not session.files or not session.fixture:
        raise HTTPException(409, "Select the announcement and submission package first.")
    if session.results:
        session.previous_results = session.results
    session.results = demo.fixture_results(session.fixture)
    session.status = summarize(session.requirements, session.results)
    session.revision += 1
    return sessions.save(session)
