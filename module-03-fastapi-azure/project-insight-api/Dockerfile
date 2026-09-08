# ---------------------------------------------------------------------------
# Stage 1: build. Compilers and headers live here and are thrown away.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# libpq-dev + gcc are needed to install psycopg2; neither ships in the final image.
# The apt lists are removed in the SAME RUN - deleting them in a later layer
# would not shrink the image, because the earlier layer still contains them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first (they change rarely), source code last (it changes constantly).
# Get this order wrong and every one-line edit reinstalls every dependency.
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir --prefix=/install .

# ---------------------------------------------------------------------------
# Stage 2: runtime. A fresh filesystem - only what we COPY --from survives.
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# libpq5 is the runtime library psycopg2 links against (not the -dev headers).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /app/src ./src

# Least privilege: after the installs (which need write access), before CMD.
USER appuser

# Documentation only - publishing the port is `docker run -p 8000:8000`.
EXPOSE 8000

# `python`, not `curl`: a slim image has no curl and adding one is pure weight.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Exec form (a JSON array) so SIGTERM reaches uvicorn and it can shut down
# cleanly. Shell form would put /bin/sh at PID 1, which swallows the signal.
# --host 0.0.0.0, or the container answers nobody from outside.
CMD ["uvicorn", "insight_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
