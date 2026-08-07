#!/bin/bash
# studentctl-delete <username>    - permanently remove account + data
set -euo pipefail
U="$1"
id "$U" >/dev/null 2>&1 || { echo "no such user"; exit 0; }
loginctl terminate-user "$U" 2>/dev/null || true
userdel -r "$U" 2>/dev/null || userdel "$U"
# Quota cleanup
quotaoff -uv "$U" 2>/dev/null || true
echo "deleted $U"
