#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-.env.e2e}"
source app/base/tests/lib/bootstrap.sh
api_bootstrap_load_env "${ENV_FILE}"
trap api_bootstrap_stop_server EXIT
api_bootstrap_ensure_server "${ENV_FILE}"
source app/base/tests/lib/common.sh
api_test_init_logging
bash "${SCRIPT_DIR}/contact.sh"
api_print_summary
