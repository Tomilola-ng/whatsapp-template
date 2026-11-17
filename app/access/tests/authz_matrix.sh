#!/usr/bin/env bash
set -euo pipefail

customer_token="$(api_session_get CUSTOMER_TOKEN)"
customer_id="$(api_session_get CUSTOMER_ID)"

api_call "GET" "/admin/audit-logs" "" "${customer_token}"
[[ "${API_LAST_STATUS}" == "403" ]] \
  && api_record_pass "customer blocked from audit logs" \
  || api_fail "audit log permission gate expected 403, got ${API_LAST_STATUS}"

api_call "POST" "/admin/notifications/broadcast" \
  '{"title":"Forbidden","message":"No self escalation"}' "${customer_token}"
[[ "${API_LAST_STATUS}" == "403" ]] \
  && api_record_pass "customer blocked from notification broadcast" \
  || api_fail "broadcast permission gate expected 403, got ${API_LAST_STATUS}"

api_call "PUT" "/access/accounts/${customer_id}/permissions" \
  '{"permissions":[{"codename":"*","granted":true}]}' "${customer_token}"
[[ "${API_LAST_STATUS}" == "403" ]] \
  && api_record_pass "customer blocked from direct self escalation" \
  || api_fail "self escalation expected 403, got ${API_LAST_STATUS}"
