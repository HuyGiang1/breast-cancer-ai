from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(project_root / ".env")

from app.api import endpoints
from app.core.database import db
from app.services.final_dl_runtime import final_dl_runtime_service
from app.services.final_ml_runtime import final_ml_runtime_service

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
APP_ENABLE_API_DOCS = os.getenv(
    "APP_ENABLE_API_DOCS",
    "true" if APP_ENV != "production" else "false"
).strip().lower() == "true"

app = FastAPI(
    title="Breast Health Studio Research API",
    description=(
        "Research and educational API for frozen breast-health ML/DL experiments. "
        "Not a medical device and not for autonomous clinical diagnosis."
    ),
    version="1.0.0",
    docs_url="/docs" if APP_ENABLE_API_DOCS else None,
    redoc_url="/redoc" if APP_ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if APP_ENABLE_API_DOCS else None,
)

DEFAULT_CORS_ORIGINS: List[str] = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]


def get_cors_origins() -> List[str]:
    app_env = os.getenv("APP_ENV", APP_ENV).strip().lower()
    raw_origins = os.getenv("APP_CORS_ORIGINS", "").strip()

    if app_env == "production":
        if not raw_origins or raw_origins == "*":
            raise RuntimeError(
                "Production configuration error: APP_CORS_ORIGINS must be explicitly configured and cannot be '*' in production."
            )
        origins = [origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip()]
        if not origins:
            raise RuntimeError(
                "Production configuration error: APP_CORS_ORIGINS contains no valid origins."
            )
        for origin in origins:
            if not origin.startswith("https://"):
                raise RuntimeError(
                    f"Production configuration error: CORS origin '{origin}' must use HTTPS in production."
                )
            if "localhost" in origin or "127.0.0.1" in origin:
                raise RuntimeError(
                    f"Production configuration error: CORS origin '{origin}' cannot target localhost/127.0.0.1 in production."
                )
        return origins

    if not raw_origins:
        return DEFAULT_CORS_ORIGINS

    origins = [
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    ]
    return origins or DEFAULT_CORS_ORIGINS


cors_methods = (
    ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    if APP_ENV == "production"
    else ["*"]
)
cors_headers = (
    ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"]
    if APP_ENV == "production"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

app.include_router(endpoints.router, prefix="/api/v1")

results_dir = project_root / "frontend" / "results"
results_dir.mkdir(parents=True, exist_ok=True)
app.mount("/results", StaticFiles(directory=str(results_dir)), name="results")


@app.on_event("startup")
def init_database():
    db.init()
    if os.getenv("DL_PRELOAD_ON_STARTUP", "true").strip().lower() == "true":
        final_dl_runtime_service.preload_models()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz(response: Response):
    db_ok = False
    try:
        row = db.fetch_one("SELECT 1")
        db_ok = row is not None
    except Exception:
        db_ok = False

    ml_status = final_ml_runtime_service.get_model_status()
    dl_status = final_dl_runtime_service.get_model_status()
    ml_healthy = ml_status.get("artifact_verified", False) or ml_status.get("status") != "unavailable"
    dl_healthy = dl_status.get("artifact_verified", False) or dl_status.get("status") != "unavailable"

    is_ready = db_ok and ml_healthy and dl_healthy
    if not is_ready:
        response.status_code = 503

    return {
        "status": "ready" if is_ready else "degraded",
        "database": "ok" if db_ok else "unavailable",
        "final_ml": ml_status.get("status", "unavailable"),
        "final_dl": dl_status.get("status", "unavailable"),
    }


@app.get("/")
def read_root():
    docs_msg = " Visit /docs for interactive API documentation." if APP_ENABLE_API_DOCS else ""
    return {
        "message": f"Breast Health Studio Research API.{docs_msg}",
        "status": "running",
        "environment": APP_ENV,
    }
