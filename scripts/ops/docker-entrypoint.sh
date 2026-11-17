#!/usr/bin/env bash
# Container entrypoint. Roles: api | worker | migrate.
set -euo pipefail
cd /app

ROLE="${1:-api}"
if [[ $# -gt 0 ]]; then
  shift
fi

PYTHON="${PYTHON:-/app/.venv/bin/python}"
FASTAPI="${FASTAPI:-/app/.venv/bin/fastapi}"

apply_schema() {
  "${PYTHON}" /app/scripts/ops/apply_schema.py
}

case "${ROLE}" in
  api)
    apply_schema
    exec "${FASTAPI}" run ./main.py --port 80 --host 0.0.0.0 "$@"
    ;;
  worker)
    apply_schema
    exec "${PYTHON}" /app/scripts/job_worker.py "$@"
    ;;
  migrate)
    exec "${PYTHON}" /app/scripts/ops/apply_schema.py
    ;;
  *)
    exec "${ROLE}" "$@"
    ;;
esac
