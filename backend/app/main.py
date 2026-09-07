from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import router, upload_limits
from app.api.profiles import router as profile_router
from app.services import sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    upload_limits()
    sessions.startup()
    yield
    sessions.close_all()


production = os.environ.get("FINAL_CHECK_ENV", "local").lower() == "production"
app = FastAPI(
    title="FINAL CHECK — AI Submission Preflight",
    version="0.6.0",
    lifespan=lifespan,
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
    description="Restart-safe single-node two-stage AI extraction with mandatory human confirmation. No Vision provider.",
)
app.include_router(router)
app.include_router(profile_router)


@app.middleware("http")
async def bound_request_size(request: Request, call_next):
    _, max_package_bytes, _ = upload_limits()
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > max_package_bytes + 1024 * 1024):
        return JSONResponse(
            status_code=413,
            content={"detail": "Upload package exceeds transport limit."},
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "X-Robots-Tag": "noindex, nofollow",
            },
        )
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
