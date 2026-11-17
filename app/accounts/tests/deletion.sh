#!/usr/bin/env bash
set -euo pipefail

suffix="$(date +%s)"
email="deletion-${suffix}@example.com"
password="Password123!"
body="$(jq -nc --arg email "${email}" --arg password "${password}" \
  '{first_name:"Delete",last_name:"Test",email:$email,password:$password}')"
api_call_expect "POST" "/auth/register" "201" "${body}"
otp="$(api_fetch_otp "${email}" "account_verification")"
api_call_expect "POST" "/auth/verify-otp" "200" \
  "$(jq -nc --arg email "${email}" --arg otp_code "${otp}" '{email:$email,otp_code:$otp_code}')"
token="$(api_json_field '.data.access')"
api_call_expect "GET" "/auth/preferences" "200" "" "${token}"
api_call_expect "DELETE" "/auth/account" "200" \
  '{"confirm":true,"confirmation_phrase":"DELETE MY ACCOUNT"}' "${token}"
api_call "GET" "/auth/current-user" "" "${token}"
[[ "${API_LAST_STATUS}" == "401" ]] \
  && api_record_pass "account deletion revoked active token" \
  || api_fail "deleted account token expected 401, got ${API_LAST_STATUS}"
