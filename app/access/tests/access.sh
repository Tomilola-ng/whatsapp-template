#!/usr/bin/env bash
set -euo pipefail

customer_token="$(api_session_get CUSTOMER_TOKEN)"
customer_id="$(api_session_get CUSTOMER_ID)"

api_call_expect "GET" "/access/me/permissions" "200" "" "${customer_token}"

perms="$(api_json_field '.permissions | join(",")')"
if [[ "${perms}" == *"notifications.manage"* ]]; then
  api_record_pass "customer token includes notifications.manage"
else
  api_fail "customer token missing notifications.manage: ${API_LAST_BODY}"
fi

api_call "GET" "/access/permissions" "" "${customer_token}"
if [[ "${API_LAST_STATUS}" == "403" ]]; then
  api_record_pass "customer blocked from access.read"
else
  api_fail "customer expected 403 on access.read, got ${API_LAST_STATUS}"
fi

if [[ -n "${customer_id}" ]]; then
  api_call "PUT" "/access/accounts/${customer_id}/roles" \
    "$(jq -nc --arg slug "customer_basic" '{role_slugs:[$slug]}')" \
    "${customer_token}"
  if [[ "${API_LAST_STATUS}" == "403" ]]; then
    api_record_pass "customer blocked from self role assignment"
  else
    api_fail "customer expected 403 on self assign_roles, got ${API_LAST_STATUS}"
  fi

  api_call "PUT" "/access/accounts/${customer_id}/roles" \
    "$(jq -nc '{role_slugs:[]}')" \
    "${customer_token}"
  if [[ "${API_LAST_STATUS}" == "403" ]]; then
    api_record_pass "customer blocked from empty role assignment"
  elif [[ "${API_LAST_STATUS}" == "400" ]]; then
    api_record_pass "empty role assignment rejected with 400"
  else
    api_fail "empty role assignment expected 400/403, got ${API_LAST_STATUS}"
  fi
fi

api_call "GET" "/notifications/" "" "${customer_token}"
if [[ "${API_LAST_STATUS}" == "200" ]]; then
  api_record_pass "customer can list notifications with notifications.read"
else
  api_fail "customer notifications list expected 200, got ${API_LAST_STATUS}: ${API_LAST_BODY}"
fi
