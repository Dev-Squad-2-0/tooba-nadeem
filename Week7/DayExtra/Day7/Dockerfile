# Meridian Homes Pakistan — Real Estate Voice Agent
# Day 6: Deployment readiness.

FROM python:3.12-slim

WORKDIR /app

# System deps: build tools for packages with C extensions (e.g. some
# sentence-transformers/chromadb dependencies), removed after install to
# keep the image smaller.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

# Pre-download and cache the embedding model at build time. app/config.py
# sets HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 for runtime, so the
# model must already exist in the image's HF cache before the container
# starts, or RAGPipeline() startup will fail trying to reach huggingface.co.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# credentials.json and .env are intentionally NOT copied here if excluded
# via .dockerignore -- they must be mounted or injected at runtime (e.g.
# via `docker run -v`/`--env-file`, or your platform's secrets mechanism).
# This image never bakes secrets in.

EXPOSE 8000

# Lightweight health check — hits /health, which app/api/routes.py
# implements as a pure liveness check with NO external API dependency
# (no OpenRouter/Deepgram/Calendar call), per the Day 6 requirement that
# health checks must not depend on external services being reachable.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]