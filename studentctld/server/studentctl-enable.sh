#!/bin/bash
# studentctl-enable <username>    - re-enable a previously disabled student
set -euo pipefail
U="$1"
id "$U" >/dev/null 2>&1 || { echo "no such user"; exit 0; }
passwd -u "$U" >/dev/null 2>&1 || true
echo "enabled $U"
