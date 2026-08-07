#!/bin/bash
# studentctl-status  - returns JSON {current, max, reserved} for the panel
set -euo pipefail
CONFIG="${STUDENTCTL_CONFIG:-/etc/studentctl/config.json}"
MAX=$(jq -r '.max_concurrent // 15' "$CONFIG")
RES=$(jq -r '.reserved_for_onday // 3' "$CONFIG")
CUR=$(who | awk '{print $1}' | sort -u | while read -r u; do
    [ "$(id -u "$u" 2>/dev/null || echo 0)" -ge 1000 ] && echo "$u"
done | sort -u | wc -l)
jq -nc --argjson cur "$CUR" --argjson max "$MAX" --argjson res "$RES" \
   '{current:$cur, max:$max, reserved:$res, available:(( $max - $cur ) | if . < 0 then 0 else . end)}'
