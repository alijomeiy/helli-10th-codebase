#!/bin/bash
# studentctl-check-login.sh
# Invoked by pam_exec (account phase) on every SSH login.
# Enforces: global concurrent cap + preferred-day priority with off-day overflow.
#
# Reads: /etc/studentctl/config.json
#   { "max_concurrent": 15, "reserved_for_onday": 3,
#     "users": { "alice": { "day": 1, "enabled": true } , ... } }
#   day is ISO weekday: 1=Mon .. 7=Sun
set -euo pipefail

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

MAX_CONC=$(jq -r '.max_concurrent // 15' "$CONFIG")
RESERVED=$(jq -r '.reserved_for_onday // 3' "$CONFIG")
MY_DAY=$(jq -r --arg u "$USER" '.users[$u].day // 1' "$CONFIG")
TODAY=$(date +%u)   # 1=Mon .. 7=Sun

# Count currently-logged-in unique users (excluding pure system accounts).
COUNT=$(who | awk '{print $1}' | sort -u | while read -r u; do
    [ "$(id -u "$u" 2>/dev/null || echo 0)" -ge 1000 ] && echo "$u"
done | sort -u | wc -l)

deny() { echo "studentctl: $1" >&2; exit 1; }

if [ "$TODAY" -eq "$MY_DAY" ]; then
    # On-day: priority access, denied only if server genuinely full.
    [ "$COUNT" -ge "$MAX_CONC" ] && deny "Server full ($COUNT/$MAX_CONC). Please try again shortly."
    exit 0
fi

# Off-day: allowed only if spare capacity beyond the reserved on-day buffer.
AVAIL=$(( MAX_CONC - RESERVED ))
if [ "$COUNT" -ge "$AVAIL" ]; then
    deny "Today is not your scheduled day and capacity is reserved (used $COUNT, threshold $AVAIL)."
fi
exit 0
