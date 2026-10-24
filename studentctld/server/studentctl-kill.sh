#!/bin/bash
# studentctl-kill <username>
set -euo pipefail
U="$1"
id "$U" >/dev/null 2>&1 || { echo "no such user" >&2; exit 0; }
loginctl terminate-user "$U" 2>/dev/null || true
pkill -KILL -u "$U" 2>/dev/null || true
echo "terminated sessions for $U"
