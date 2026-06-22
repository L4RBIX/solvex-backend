from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from contestiq_api import MODEL_VERSION
from contestiq_api.errors import APIError
from contestiq_api.routes import analysis, coach, copilot, execute, feedback, health, share, workspace
from contestiq_api.settings import get_settings

settings = get_settings()
app = FastAPI(title="ContestIQ API", version=MODEL_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
async def api_error_handler(_, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "failed",
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(execute.router)
app.include_router(share.router)
app.include_router(workspace.router)
app.include_router(feedback.router)
app.include_router(copilot.router)
app.include_router(coach.router)
