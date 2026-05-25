from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Breast Cancer AI Prediction API. Visit /docs for the interactive API documentation."}
