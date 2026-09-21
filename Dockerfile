# ── Stage 1: Build ─────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# Install OS-level dependencies needed by PaddleOCR / OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies (no cache to keep image lean)
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ────────────────────────────────────────────
FROM python:3.10-slim

WORKDIR /app

# Re-install OS runtime libs in final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app source code
COPY main.py .
COPY paddle_extractor.py .

# PaddleOCR downloads model weights on first run.
# Pre-warm them during the Docker build so cold starts are instant.
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='hi')" || true

# Create writable uploads directory
RUN mkdir -p /tmp/uploads

# Expose port (Render/Railway inject $PORT at runtime)
EXPOSE 8000

# Start the FastAPI server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
