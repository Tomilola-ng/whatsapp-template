#!/usr/bin/env bash
set -euo pipefail

api_prereq_auth() {
  local existing
  existing="$(api_session_get CUSTOMER_TOKEN)"
  if [[ -n "${existing}" ]]; then
    return 0
  fi
  api_auth_register_and_login_customer
}
