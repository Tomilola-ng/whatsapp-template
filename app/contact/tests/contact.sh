#!/usr/bin/env bash
set -euo pipefail

api_call_expect "POST" "/contact/" "200" '{"full_name":"E2E Contact","email":"contact@example.com","description":"Shell smoke"}'
