#!/usr/bin/env bash
# Probe API health after a deploy.
#
# Usage:
#   bash scripts/ops/healthcheck.sh http://localhost:8000
#   bash scripts/ops/healthcheck.sh https://api.example.com staging
set -euo pipefail

BASE_URL="${1:-}"
EXPECT_ENVIRONMENT="${2:-}"

if [[ -z "${BASE_URL}" ]]; then
  echo "usage: $0 <api-base-url> [expected-environment]" >&2
  exit 2
fi

URL="${BASE_URL%/}/api/v1/health"
echo "GET ${URL}"

BODY="$(curl -fsS --max-time 20 "${URL}")"
echo "${BODY}"

python3 - "${EXPECT_ENVIRONMENT}" "${BODY}" <<'PY'
import json, sys
expect, raw = sys.argv[1], sys.argv[2]
payload = json.loads(raw)
data = payload.get("data") or payload
if expect:
    environment = data.get("environment")
    if environment != expect:
        raise SystemExit(f"health environment={environment!r} expected {expect!r}")
    print(f"ok: environment is {environment}")
else:
    print("ok: health endpoint responded")
PY
