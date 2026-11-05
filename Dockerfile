# ==============================================================================
# Production Dockerfile for Shree Shanishwara Swamy Temple Website
# Multi-stage security hardening, non-root execution, minimal footprint
# ==============================================================================

FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install runtime dependencies for typography, PDF generation, and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libfreetype6 \
    libharfbuzz0b \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN groupadd -g 10001 templegroup && \
    useradd -u 10001 -g templegroup -m -s /bin/bash templeuser

WORKDIR /app

# Copy dependency specifications first to leverage Docker build cache
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application source and frontend static files
COPY backend /app/backend
COPY frontend /app/frontend

# Ensure upload directory exists and assign permissions to templeuser
RUN mkdir -p /app/frontend/assets/uploads && \
    chown -R templeuser:templegroup /app

# Switch to non-root user
USER templeuser

# Set working directory to backend
WORKDIR /app/backend

# Default port if not provided by host environment
ENV PORT=8000

# Expose port
EXPOSE 8000

# Launch production server with Uvicorn (supports dynamic cloud PORT)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
