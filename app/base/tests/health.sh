#!/usr/bin/env bash
set -euo pipefail

api_call_expect "GET" "/health" "200"
api_record_pass "health smoke completed"
