#!/usr/bin/env bash
set -euo pipefail

bash app/base/tests/run_all.sh "${1:-.env.e2e}"
