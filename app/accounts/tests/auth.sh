#!/usr/bin/env bash
set -euo pipefail

api_auth_register_and_login_customer

customer_token="$(api_session_get CUSTOMER_TOKEN)"
refresh_token="$(api_session_get CUSTOMER_REFRESH_TOKEN)"
api_call_expect "GET" "/auth/current-user" "200" "" "${customer_token}"

api_call_expect "POST" "/auth/refresh-token" "200" "$(jq -nc --arg refresh_token "${refresh_token}" '{refresh_token:$refresh_token}')"

api_call_expect "POST" "/auth/logout" "200" "" "${customer_token}"
api_call "GET" "/auth/current-user" "" "${customer_token}"
if [[ "${API_LAST_STATUS}" == "401" ]]; then
  api_record_pass "revoked token rejected after logout"
else
  api_fail "revoked token expected 401, got ${API_LAST_STATUS}"
fi

email="$(api_session_get CUSTOMER_EMAIL)"
password="$(api_session_get CUSTOMER_PASSWORD)"
api_call_expect "POST" "/auth/login" "200" "$(jq -nc --arg email "${email}" --arg password "${password}" '{email:$email,password:$password}')"
api_session_set "CUSTOMER_TOKEN" "$(api_json_field ".data.access")"
api_session_set "CUSTOMER_ID" "$(api_json_field ".data.user.id")"
