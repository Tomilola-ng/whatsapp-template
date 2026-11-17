#!/usr/bin/env bash
set -euo pipefail

suffix="$(date +%s)"
email="notifications-${suffix}@example.com"
password="Password123!"
api_call_expect "POST" "/auth/register" "201" "$(jq -nc \
  --arg email "${email}" --arg password "${password}" \
  '{first_name:"Notification",last_name:"Test",email:$email,password:$password}')"
otp="$(api_fetch_otp "${email}" "account_verification")"
api_call_expect "POST" "/auth/verify-otp" "200" \
  "$(jq -nc --arg email "${email}" --arg otp_code "${otp}" '{email:$email,otp_code:$otp_code}')"
token="$(api_json_field '.data.access')"

api_call_expect "GET" "/notifications/" "200" "" "${token}"
api_call_expect "GET" "/notifications/unread-count" "200" "" "${token}"
api_call_expect "POST" "/notifications/mark-all-read" "200" "" "${token}"
