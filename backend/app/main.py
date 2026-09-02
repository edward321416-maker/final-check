from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="FINAL CHECK — AI Submission Preflight", version="0.1.0",
              description="Local TASK 01 skeleton. Demo findings are mocked. Validator v1.5 is unavailable.")
app.include_router(router)
