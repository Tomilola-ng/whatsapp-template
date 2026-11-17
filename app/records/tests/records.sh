#!/usr/bin/env bash
set -euo pipefail

customer_token="$(api_session_get CUSTOMER_TOKEN)"
api_call_expect "GET" "/notifications/" "200" "" "${customer_token}"
