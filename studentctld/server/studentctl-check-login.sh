#!/bin/bash
# studentctl-check-login.sh
# Invoked by pam_exec (account phase) on every SSH login.
#
# Access policy (resource-based, no scheduling):
#   An enabled student may log in as long as logged_in < max_concurrent.
#   Idle sessions are auto-logged-out after idle_timeout seconds (TMOUT in the
#   shell profile), so capacity is reclaimed automatically.
#
# Reads /etc/studentctl/config.json:
#   { "max_concurrent": 30, "idle_timeout": 1800,
#     "users": { "alice": { "enabled": true }, ... } }
set -uo pipefail

CONFIG="${STUDENTCTL_CONFIG:-/etc/studentctl/config.json}"
USER="${PAM_USER:-}"

# No user context -> allow (e.g. PAM service probes)
[ -z "$USER" ] && exit 0

# Root / system accounts are never limited by this hook.
if [ "$(id -u "$USER" 2>/dev/null || echo 0)" -lt 1000 ]; then
    exit 0
fi

# Not a managed student -> allow (admins, service users).
ENABLED=$(jq -r --arg u "$USER" '.users[$u].enabled // false' "$CONFIG" 2>/dev/null || echo false)
if [ "$ENABLED" != "true" ]; then
    exit 0
fi

MAX_CONC=$(jq -r '.max_concurrent // 30' "$CONFIG")

# Count currently-logged-in unique students (UID >= 1000).
COUNT=$(who | awk '{print $1}' | sort -u | while read -r u; do
    [ "$(id -u "$u" 2>/dev/null || echo 0)" -ge 1000 ] && echo "$u"
done | sort -u | wc -l)

if [ "$COUNT" -ge "$MAX_CONC" ]; then
    echo "studentctl: سرور پر است ($COUNT/$MAX_CONC). کمی بعد تلاش کنید." >&2
    exit 1
fi
exit 0
