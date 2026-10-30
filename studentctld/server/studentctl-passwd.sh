#!/bin/bash
# studentctl-passwd <username> <new_password>
set -euo pipefail
U="$1"
PW="$2"
id "$U" >/dev/null 2>&1 || { echo "no such user" >&2; exit 1; }
echo "${U}:${PW}" | chpasswd
echo "password updated for $U"
