# Dockerfile for Railway/Render deployment
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (system deps already installed above)
RUN playwright install chromium

# Copy application code (see .dockerignore — the 67MB of unused GTFS fare
# tables and the frontend are excluded)
COPY . .

# Default suits Hugging Face Spaces; Railway/Render/Fly inject their own PORT.
ENV PORT=7860
EXPOSE 7860

# Single worker on purpose: each worker builds its own in-memory GTFS graph
# (~370MB RSS), so 2 workers would OOM anything under 1GB.
CMD ["sh", "-c", "uvicorn backend.api_server:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]

