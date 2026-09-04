# Breast Cancer AI

Research and educational prototype for breast cancer screening support using structured clinical machine learning, mammography-image deep learning, and a demo multimodal web workflow.

> Research / Educational Prototype Only. This project is not a medical device and must not be used for clinical diagnosis, treatment decisions, or replacing qualified clinicians.

## Overview

Breast Cancer AI combines:

- FastAPI backend for authentication, patient records, prediction, chat/advice, history, reports, and research summaries.
- Static HTML/CSS/JavaScript frontend for the demo web app.
- Classical ML models for WDBC-style structured features.
- DL image prediction with Grad-CAM-style visual explanation.
- Research artifacts for model comparison, calibration, ablation, and statistical analysis.
- Docker Compose deployment with API + Nginx web service.

## Research Objective

Evaluate whether structured ML, image DL, and multimodal fusion can provide reliable breast cancer screening signals in a reproducible research/demo setting.

The current project is not yet ready for final scientific defense because the processed CBIS-DDSM image split has a critical leakage risk and multimodal fusion is currently a heuristic demo.

## Research Questions

- Which structured ML model performs best on WDBC under reproducible evaluation?
- How does DL image screening perform under leakage-safe patient/study-level splits?
- Does ROI preprocessing improve DL performance?
- Are prediction probabilities calibrated well enough for risk communication?
- Does multimodal fusion improve over ML-only and DL-only when evaluated on paired validation/test data?

## Key Contributions

- End-to-end demo system: web UI, API, model inference, history, reports, and deployment scaffold.
- Structured ML baseline with calibrated Logistic Regression and Random Forest artifacts.
- DL image inference with model discovery, threshold profile, and explanation image support.
- Research dashboard backed by saved experiment JSON/CSV artifacts.
- Explicit research safety framing: not for clinical diagnosis.

## Architecture

```text
frontend/                 Static web app
backend/app/main.py       FastAPI app, CORS, static results, health endpoints
backend/app/api/          API schemas and endpoints
backend/app/services/     ML, DL, and AI advisor services
src/                      Research/model/data-processing utilities
scripts/                  Reproducible training/evaluation/audit helpers
experiments/results/      Small research outputs when available
models/                   Local model artifacts, not for normal Git tracking
deploy/nginx.conf         Docker Nginx config
docker-compose.yml        API + web deployment
```

## Dataset

### WDBC

- 569 structured samples.
- 30 numeric features.
- Used for classical ML.

### CBIS-DDSM Processed Images

Local processed image snapshot:

| Split | Benign | Malignant | Total |
| --- | ---: | ---: | ---: |
| Train | 1040 | 750 | 1790 |
| Validation | 223 | 160 | 383 |
| Test | 224 | 162 | 386 |

Current audit found 90 study-like filename prefixes appearing across multiple splits. Treat current DL metrics as development evidence only until the split is rebuilt by patient/study.

Run:

```bash
python scripts/audit_cbis_splits.py --json
```

See [docs/DATA_CARD.md](docs/DATA_CARD.md).

## Methodology

### ML Models

Current runtime smoke test detected:

- Logistic Regression
- Random Forest

XGBoost artifacts exist historically, but the runtime health check disabled the current XGBoost artifact.

Training entry point:

```bash
PYTHONPATH=backend python scripts/train_ml_calibrated.py
```

### DL Models

Current runtime smoke test detected:

- Custom CNN

Historical/development artifacts include ResNet50 and EfficientNet-B0. They should be re-evaluated on leakage-safe splits before use in final claims.

Training entry point:

```bash
PYTHONPATH=backend python scripts/train_dl_finetune_calibrated.py --architecture custom_cnn
```

### Multimodal Fusion

The current web/API multimodal endpoint uses:

```text
combined_probability = 0.4 * ml_probability + 0.6 * dl_probability
```

This is a demo heuristic. A scientific multimodal claim requires paired clinical-image samples, validation-only weight tuning, and final test evaluation.

See [docs/RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md).

## Evaluation

Required final metrics:

- Accuracy
- Precision
- Sensitivity / Recall
- Specificity
- F1-score
- ROC-AUC
- PR-AUC
- Balanced Accuracy
- Confusion Matrix
- False negative count
- Calibration metrics such as Brier score and calibration curve

Existing JSON/CSV artifacts are useful for development but must be regenerated after leakage-safe splitting.

## Web Application

Main flows:

- Home and educational content
- AI assistant/advice
- ML clinical prediction
- DL image prediction
- Multimodal demo prediction
- Auth/profile
- Doctor patient records
- Prediction history
- Downloadable HTML prediction reports
- Research/statistics dashboard

The frontend is static HTML/CSS/JavaScript. Do not migrate to React/NextJS unless a future requirement clearly needs it.

## Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

For full training workflows, install:

```bash
pip install -r requirements.txt
```

## Environment Variables

Start from `.env.example`. Do not commit `.env`.

Important variables:

- `APP_FRONTEND_URL`
- `APP_CORS_ORIGINS`
- `APP_MAX_IMAGE_UPLOAD_MB`
- `AI_ADVISOR_PROVIDER`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `APP_MAIL_MODE`
- `SMTP_*`
- `DL_PRELOAD_ON_STARTUP`

## Run Backend

```bash
cd backend
DL_PRELOAD_ON_STARTUP=false uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health endpoints:

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

## Run Frontend

From repository root:

```bash
python3 -m http.server 8080 -d frontend
```

Open:

```text
http://127.0.0.1:8080
```

## Docker

```bash
docker compose up -d --build
docker compose logs -f api
```

Model weights are intentionally not meant to be normal Git-tracked files. Place production model artifacts in the server `models/` volume or publish them separately as release artifacts.

## Reproduce Experiments

Current useful commands:

```bash
python scripts/audit_cbis_splits.py --json
PYTHONPATH=backend python scripts/train_ml_calibrated.py
PYTHONPATH=backend python scripts/train_dl_finetune_calibrated.py --architecture custom_cnn
PYTHONPATH=backend python scripts/smoke_test_api.py
```

Before final research reporting, rebuild the CBIS split safely and regenerate evaluation artifacts.

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

Target:

- Ubuntu VPS
- Docker Compose
- Nginx
- domain
- HTTPS
- persistent `backend/data` and `models` volumes

## Documentation

- [docs/PROJECT_AUDIT.md](docs/PROJECT_AUDIT.md)
- [docs/RESEARCH_GAP_ANALYSIS.md](docs/RESEARCH_GAP_ANALYSIS.md)
- [docs/RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md)
- [docs/PRODUCTION_ROADMAP.md](docs/PRODUCTION_ROADMAP.md)
- [docs/MODEL_CARD.md](docs/MODEL_CARD.md)
- [docs/DATA_CARD.md](docs/DATA_CARD.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Limitations

- Current DL split has detected leakage risk.
- Current multimodal fusion is not scientifically validated.
- No external validation dataset is documented.
- Demo records should be synthetic.
- AI-generated advice is product support text, not model explanation or medical advice.

## Ethical / Medical Disclaimer

This repository is for research, education, and software demonstration. It cannot diagnose breast cancer. Any suspicious symptom, imaging abnormality, or clinical concern must be reviewed by qualified healthcare professionals.

## Future Work

- Rebuild CBIS-DDSM patient/study-level splits.
- Add paired multimodal evaluation only if paired data is available.
- Regenerate final metrics, calibration plots, and confidence intervals.
- Publish model artifacts through a documented non-Git strategy.
- Add Docker healthchecks and deployment automation.

## Authors

Giang Nguyen Huy and contributors.
