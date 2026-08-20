# Production Dockerfile for Google Cloud Run Deployment
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Launch FastAPI with Uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
