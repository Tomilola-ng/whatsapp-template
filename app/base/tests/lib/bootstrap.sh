#!/usr/bin/env bash
set -euo pipefail

API_BOOTSTRAP_SERVER_PID="${API_BOOTSTRAP_SERVER_PID:-}"
API_BOOTSTRAP_STARTED_SERVER="${API_BOOTSTRAP_STARTED_SERVER:-false}"

api_bootstrap_load_env() {
  local env_file="${1:-.env.e2e}"
  if [[ ! -f "${env_file}" ]]; then
    echo "Missing env file: ${env_file}" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
  export ENV_FILE="${env_file}"
  export API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:${PORT:-8015}${API_V1_PREFIX:-/api/v1}}"
  api_bootstrap_safety_gates
}

api_bootstrap_safety_gates() {
  command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
  command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
  command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
  command -v uv >/dev/null || { echo "uv is required" >&2; exit 1; }

  case "${DATABASE_URL:-}" in
    postgres://*|postgresql://*) ;;
    *) echo "E2E requires DATABASE_URL to start with postgres:// or postgresql://" >&2; exit 1 ;;
  esac

  case "${ENVIRONMENT:-}" in
    staging|production) echo "Refusing E2E against ENVIRONMENT=${ENVIRONMENT}" >&2; exit 1 ;;
  esac

  if [[ "${DEV_OUTBOX_ENABLED:-false}" != "true" && "${E2E_INTERACTIVE_OTP:-false}" != "true" ]]; then
    echo "DEV_OUTBOX_ENABLED=true is required unless E2E_INTERACTIVE_OTP=true" >&2
    exit 1
  fi
}

api_bootstrap_health_ok() {
  curl -fsS "${API_BASE_URL}/health" >/dev/null 2>&1
}

api_bootstrap_ensure_server() {
  local env_file="${1:-${ENV_FILE:-.env.e2e}}"
  if api_bootstrap_health_ok; then
    return 0
  fi

  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
  PORT="${PORT:-8015}" uv run fastapi dev main.py --host 127.0.0.1 --port "${PORT}" \
    > app/base/tests/api-server.log 2>&1 &
  API_BOOTSTRAP_SERVER_PID="$!"
  API_BOOTSTRAP_STARTED_SERVER="true"

  for _ in $(seq 1 60); do
    if api_bootstrap_health_ok; then
      return 0
    fi
    sleep 1
  done

  echo "Server did not become healthy within 60s. See app/base/tests/api-server.log" >&2
  exit 1
}

api_bootstrap_stop_server() {
  if [[ "${API_BOOTSTRAP_STARTED_SERVER}" == "true" && -n "${API_BOOTSTRAP_SERVER_PID}" ]]; then
    kill "${API_BOOTSTRAP_SERVER_PID}" >/dev/null 2>&1 || true
    wait "${API_BOOTSTRAP_SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
