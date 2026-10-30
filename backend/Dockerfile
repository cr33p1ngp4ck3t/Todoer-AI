# Multi-stage build for backend
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY src ./src
COPY alembic.ini .
COPY alembic ./alembic

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://localhost:8000/health/ready', timeout=5)"]

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
