FROM python:3.13-slim

# Install uv via pip so builds do not depend on ghcr.io (often blocked on PaaS hosts).
RUN pip install --no-cache-dir uv

COPY . /app
WORKDIR /app
RUN uv sync --frozen --no-cache \
    && chmod +x /app/scripts/ops/docker-entrypoint.sh /app/scripts/ops/healthcheck.sh

# Default: apply schema then serve the API. Worker services should override the
# Docker command to `worker`. One-shot migrate: `migrate`.
ENTRYPOINT ["/app/scripts/ops/docker-entrypoint.sh"]
CMD ["api"]
