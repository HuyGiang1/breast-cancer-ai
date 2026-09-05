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

COPY backend /app/backend
COPY frontend /app/frontend
COPY models/model_registry.example.json /app/models/model_registry.example.json
COPY models/calibration/efficientnet_b0_platt_final_seed42.json /app/models/calibration/efficientnet_b0_platt_final_seed42.json

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
