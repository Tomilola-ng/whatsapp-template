#!/usr/bin/env bash
set -euo pipefail

api_auth_register_and_login_customer() {
  local email="${E2E_CUSTOMER_EMAIL:-customer+e2e@example.com}"
  local password="${E2E_CUSTOMER_PASSWORD:-Password123!}"
  local first_name="${E2E_CUSTOMER_FIRST_NAME:-E2E}"
  local last_name="${E2E_CUSTOMER_LAST_NAME:-Customer}"
  local phone="${E2E_CUSTOMER_PHONE:-+15550101010}"
  local body
  body="$(jq -nc \
    --arg first_name "${first_name}" \
    --arg last_name "${last_name}" \
    --arg phone_number "${phone}" \
    --arg email "${email}" \
    --arg password "${password}" \
    '{first_name:$first_name,last_name:$last_name,phone_number:$phone_number,email:$email,password:$password,state:"E2E"}')"

  api_call "POST" "/auth/register" "${body}"
  if [[ "${API_LAST_STATUS}" == "201" ]]; then
    api_record_pass "register accepted ${API_LAST_STATUS}"
  elif [[ "${API_LAST_STATUS}" == "400" ]]; then
    local login_body
    login_body="$(jq -nc --arg email "${email}" --arg password "${password}" '{email:$email,password:$password}')"
    api_call "POST" "/auth/login" "${login_body}"
    if [[ "${API_LAST_STATUS}" == "200" ]]; then
      api_record_pass "existing active customer logged in"
      api_session_set "CUSTOMER_TOKEN" "$(api_json_field ".data.access")"
      api_session_set "CUSTOMER_REFRESH_TOKEN" "$(api_json_field ".data.refresh")"
      api_session_set "CUSTOMER_EMAIL" "${email}"
      api_session_set "CUSTOMER_PASSWORD" "${password}"
      api_session_set "CUSTOMER_ID" "$(api_json_field ".data.user.id")"
      return 0
    fi
    api_call_expect "POST" "/auth/send-otp" "200" "$(jq -nc --arg email "${email}" '{email:$email}')"
  else
    api_fail "register failed: ${API_LAST_STATUS} ${API_LAST_BODY}"
  fi

  local otp
  otp="$(api_fetch_otp "${email}" "account_verification")"
  local verify_body
  verify_body="$(jq -nc --arg email "${email}" --arg otp_code "${otp}" '{email:$email,otp_code:$otp_code}')"
  api_call_expect "POST" "/auth/verify-otp" "200" "${verify_body}"

  login_body="$(jq -nc --arg email "${email}" --arg password "${password}" '{email:$email,password:$password}')"
  api_call_expect "POST" "/auth/login" "200" "${login_body}"
  api_session_set "CUSTOMER_TOKEN" "$(api_json_field ".data.access")"
  api_session_set "CUSTOMER_REFRESH_TOKEN" "$(api_json_field ".data.refresh")"
  api_session_set "CUSTOMER_EMAIL" "${email}"
  api_session_set "CUSTOMER_PASSWORD" "${password}"
  api_session_set "CUSTOMER_ID" "$(api_json_field ".data.user.id")"
}

api_auth_promote_admin() {
  local email="${E2E_ADMIN_EMAIL:-admin+e2e@example.com}"
  local name="${E2E_ADMIN_NAME:-E2E Admin}"
  uv run python scripts/make_admin.py --email "${email}" --name "${name}" >> "${API_TEST_LOG_FILE}" 2>&1
  api_record_pass "admin promotion script completed"
  api_session_set "ADMIN_EMAIL" "${email}"
}
