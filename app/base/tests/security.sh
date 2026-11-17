#!/usr/bin/env bash
set -euo pipefail

api_call_expect "GET" "/auth/current-user" "401"

api_call "GET" "/dev/outbox/"
if [[ "${DEV_OUTBOX_ENABLED:-false}" == "true" ]]; then
  [[ "${API_LAST_STATUS}" == "200" ]] || api_fail "dev outbox should be available locally"
  api_record_pass "dev outbox available locally"
else
  [[ "${API_LAST_STATUS}" == "404" ]] || api_fail "dev outbox should be absent when disabled"
  api_record_pass "dev outbox absent when disabled"
fi

if [[ "${RATE_LIMIT_ENABLED:-false}" == "true" && "${E2E_RATE_LIMIT_PROBE:-false}" == "true" ]]; then
  for _ in 1 2 3 4 5 6; do
    api_call "POST" "/contact/" '{"full_name":"Rate Limit","email":"rate@example.com","description":"probe"}'
    if [[ "${API_LAST_STATUS}" == "429" ]]; then
      printf "%s" "${API_LAST_BODY}" | jq -e '.success == false and .data == null' >/dev/null
      api_record_pass "rate-limit 429 envelope observed"
      exit 0
    fi
  done
  api_fail "rate-limit probe did not observe 429"
else
  api_record_pass "rate-limit probe skipped for stable default E2E"
fi
