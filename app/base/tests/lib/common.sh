#!/usr/bin/env bash
set -euo pipefail

API_TEST_PASS_COUNT=0
API_TEST_FAIL_COUNT=0
API_LAST_STATUS=""
API_LAST_BODY=""
API_TEST_LOG_FILE="${API_TEST_LOG_FILE:-app/base/tests/api-test.log}"
API_SESSION_FILE="${API_SESSION_FILE:-app/base/tests/.session.env}"

api_test_init_logging() {
  : > "${API_TEST_LOG_FILE}"
  : > "${API_SESSION_FILE}"
}

api_redact() {
  sed -E 's/(access|refresh|refresh_token|token|password)"[[:space:]]*:[[:space:]]*"[^"]+"/\1":"[REDACTED]"/g'
}

api_record_pass() {
  API_TEST_PASS_COUNT=$((API_TEST_PASS_COUNT + 1))
  printf "PASS %s\n" "$*" | tee -a "${API_TEST_LOG_FILE}"
}

api_record_fail() {
  API_TEST_FAIL_COUNT=$((API_TEST_FAIL_COUNT + 1))
  printf "FAIL %s\n" "$*" | tee -a "${API_TEST_LOG_FILE}" >&2
}

api_fail() {
  api_record_fail "$*"
  exit 1
}

api_call() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local token="${4:-}"
  local response_file
  response_file="$(mktemp)"
  local headers=(-H "Content-Type: application/json")
  if [[ -n "${API_EXTRA_HEADERS:-}" ]]; then
    headers+=(-H "${API_EXTRA_HEADERS}")
  fi
  if [[ -n "${token}" ]]; then
    headers+=(-H "Authorization: Bearer ${token}")
  fi
  if [[ -n "${body}" ]]; then
    API_LAST_STATUS="$(curl -sS -o "${response_file}" -w "%{http_code}" -X "${method}" "${headers[@]}" -d "${body}" "${API_BASE_URL}${path}")"
  else
    API_LAST_STATUS="$(curl -sS -o "${response_file}" -w "%{http_code}" -X "${method}" "${headers[@]}" "${API_BASE_URL}${path}")"
  fi
  API_LAST_BODY="$(cat "${response_file}")"
  rm -f "${response_file}"
  printf "%s %s -> %s %s\n" "${method}" "${path}" "${API_LAST_STATUS}" "$(printf "%s" "${API_LAST_BODY}" | api_redact)" >> "${API_TEST_LOG_FILE}"
}

api_call_expect() {
  local method="$1"
  local path="$2"
  local expected="$3"
  local body="${4:-}"
  local token="${5:-}"
  api_call "${method}" "${path}" "${body}" "${token}"
  if [[ "${API_LAST_STATUS}" == "${expected}" ]]; then
    api_record_pass "${method} ${path} returned ${expected}"
  else
    api_fail "${method} ${path} expected ${expected}, got ${API_LAST_STATUS}: ${API_LAST_BODY}"
  fi
}

api_json_field() {
  local filter="$1"
  printf "%s" "${API_LAST_BODY}" | jq -r "${filter}"
}

api_fetch_otp() {
  local recipient="$1"
  local purpose="$2"
  local encoded_recipient encoded_purpose
  encoded_recipient="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "${recipient}")"
  encoded_purpose="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "${purpose}")"
  api_call "GET" "/dev/outbox/latest-otp?recipient=${encoded_recipient}&purpose=${encoded_purpose}"
  if [[ "${API_LAST_STATUS}" != "200" ]]; then
    api_fail "Could not fetch OTP for ${recipient}/${purpose}: ${API_LAST_BODY}"
  fi
  api_json_field ".data.otp"
}

api_session_set() {
  local key="$1"
  local value="$2"
  python3 - "$API_SESSION_FILE" "$key" "$value" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3].replace("'", "'\"'\"'")
rows = []
if path.exists():
    rows = [line for line in path.read_text().splitlines() if not line.startswith(f"export {key}=")]
rows.append(f"export {key}='{value}'")
path.write_text("\n".join(rows) + "\n")
PY
}

api_session_get() {
  local key="$1"
  if [[ -f "${API_SESSION_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${API_SESSION_FILE}"
  fi
  printf "%s" "${!key:-}"
}

api_print_summary() {
  printf "\nAPI E2E summary: %s passed, %s failed\n" "${API_TEST_PASS_COUNT}" "${API_TEST_FAIL_COUNT}"
  if [[ "${API_TEST_FAIL_COUNT}" -gt 0 ]]; then
    exit 1
  fi
}
