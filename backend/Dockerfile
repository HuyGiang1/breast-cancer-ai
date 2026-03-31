FROM python:3.13-slim

WORKDIR /app

# Install dependencies required by python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file (we assume requirements.txt is at project root, 
# but docker context is usually the backend folder so we'll construct it accordingly)
COPY requirements.txt .

# For a production backend, we just need these:
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic python-multipart joblib scikit-learn numpy pandas xgboost

# Copy the backend code
COPY . /app

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
