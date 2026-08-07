#!/bin/bash
# studentctl-status  - returns JSON {current, max, available} for the panel.
set -uo pipefail
CONFIG="${STUDENTCTL_CONFIG:-/etc/studentctl/config.json}"
MAX=$(jq -r '.max_concurrent // 30' "$CONFIG")

CUR=$(who | awk '{print $1}' | sort -u | while read -r u; do
    [ "$(id -u "$u" 2>/dev/null || echo 0)" -ge 1000 ] && echo "$u"
done | sort -u | wc -l)

jq -nc --argjson cur "$CUR" --argjson max "$MAX" \
  '{current:$cur, max:$max,
    available:(( $max - $cur ) | if . < 0 then 0 else . end)}'
