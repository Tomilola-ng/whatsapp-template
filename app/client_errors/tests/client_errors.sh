#!/usr/bin/env bash
set -euo pipefail

api_call_expect "POST" "/client-errors/" "200" \
  '{"message":"E2E client error","flow":"e2e","screen":"smoke","platform":"web"}'

api_call_expect "GET" "/client-errors/?flow=e2e&page_size=5" "200"
