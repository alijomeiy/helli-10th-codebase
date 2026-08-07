#!/bin/bash
# studentctl-disable <username>   - lock a student out (kill sessions + lock)
set -euo pipefail
U="$1"
id "$U" >/dev/null 2>&1 || { echo "no such user"; exit 0; }
passwd -l "$U" >/dev/null 2>&1 || true
# Kill any active sessions for this user
loginctl terminate-user "$U" 2>/dev/null || true
pkill -KILL -u "$U" 2>/dev/null || true
echo "disabled $U"
