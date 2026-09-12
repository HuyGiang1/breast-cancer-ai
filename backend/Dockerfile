FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-runtime.txt /app/requirements-runtime.txt

RUN pip install --upgrade pip && pip install -r /app/requirements-runtime.txt

# Create unprivileged application user and group (non-root UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

COPY backend /app/backend
COPY frontend /app/frontend
COPY models/model_registry.example.json /app/models/model_registry.example.json
COPY models/calibration/efficientnet_b0_platt_final_seed42.json /app/models/calibration/efficientnet_b0_platt_final_seed42.json

# Pre-create runtime directories and assign ownership to unprivileged user
RUN mkdir -p /app/backend/data /app/backend/backups /app/frontend/results /app/runtime_models && \
    chown -R appuser:appgroup /app/backend/data /app/backend/backups /app/frontend/results /app/runtime_models

USER appuser

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
