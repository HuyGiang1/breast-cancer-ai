from fastapi import FastAPI
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
from app.services.prediction_dl import dl_prediction_service

app = FastAPI(
    title="Breast Cancer AI Prediction API",
    description="API for classifying breast cancer as Benign or Malignant using ML/DL models.",
    version="1.0.0"
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
    raw_origins = os.getenv("APP_CORS_ORIGINS", "").strip()
    if not raw_origins:
        return DEFAULT_CORS_ORIGINS

    origins = [
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    ]
    return origins or DEFAULT_CORS_ORIGINS


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api/v1")

results_dir = project_root / "frontend" / "results"
results_dir.mkdir(parents=True, exist_ok=True)
app.mount("/results", StaticFiles(directory=str(results_dir)), name="results")


@app.on_event("startup")
def init_database():
    db.init()
    if os.getenv("DL_PRELOAD_ON_STARTUP", "true").strip().lower() == "true":
        try:
            dl_prediction_service.preload_models()
        except Exception as exc:
            print(f"DL preload skipped: {exc}")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {
        "status": "ready",
        "database": "ok" if db.db_path.exists() else "missing",
        "dl_models_discovered": len(dl_prediction_service.model_paths),
    }


@app.get("/")
def read_root():
    return {"message": "Welcome to the Breast Cancer AI Prediction API. Visit /docs for the interactive API documentation."}
