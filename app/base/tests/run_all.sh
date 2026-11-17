#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.e2e}"
source app/base/tests/lib/bootstrap.sh
api_bootstrap_load_env "${ENV_FILE}"
trap api_bootstrap_stop_server EXIT
api_bootstrap_ensure_server "${ENV_FILE}"
source app/base/tests/lib/common.sh
source app/base/tests/lib/auth.sh
source app/base/tests/lib/prerequisites.sh
api_test_init_logging

# shellcheck disable=SC1091
source app/base/tests/health.sh
# shellcheck disable=SC1091
source app/accounts/tests/auth.sh
# shellcheck disable=SC1091
source app/access/tests/access.sh
# shellcheck disable=SC1091
source app/access/tests/authz_matrix.sh
# shellcheck disable=SC1091
source app/base/tests/security.sh
# shellcheck disable=SC1091
source app/records/tests/notifications.sh
# shellcheck disable=SC1091
source app/accounts/tests/deletion.sh
api_print_summary
