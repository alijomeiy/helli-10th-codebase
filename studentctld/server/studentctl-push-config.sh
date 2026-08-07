#!/bin/bash
# studentctl-push-config
# Reads a new JSON config from STDIN, atomically replaces /etc/studentctl/config.json.
# The login-check hook reads this file on every login, so no reload is needed.
set -euo pipefail
DEST="${STUDENTCTL_CONFIG:-/etc/studentctl/config.json}"
TMP="$(mktemp)"
cat >"$TMP"
# Validate it is JSON
jq empty "$TMP"
install -m 0644 -o root -g root "$TMP" "$DEST"
rm -f "$TMP"
echo "config updated"
