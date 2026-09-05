from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import router, MAX_PACKAGE_BYTES
from app.api.profiles import router as profile_router
from app.services import sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    sessions.startup()
    yield
    sessions.close_all()


app = FastAPI(title="FINAL CHECK — AI Submission Preflight", version="0.5.0", lifespan=lifespan,
              description="Restart-safe single-node two-stage local AI extraction with mandatory human confirmation. No Vision provider.")
app.include_router(router)
app.include_router(profile_router)


@app.middleware("http")
async def bound_request_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > MAX_PACKAGE_BYTES + 1024 * 1024):
        return JSONResponse(status_code=413, content={"detail": "Upload package exceeds transport limit."})
    return await call_next(request)
