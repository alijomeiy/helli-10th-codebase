#!/bin/bash
# submit — student task submission command
# Runs locally on the server, checks files, calls the panel API.
# Usage:  submit [answer]
#   If no argument given, reads ~/answer.txt
PANEL_URL="${STUDENTCTL_PANEL_URL:-http://127.0.0.1:5000}"
USERNAME="$(whoami)"

# --- gather answer -----------------------------------------------------------
ANSWER=""
if [ -n "$1" ]; then
    ANSWER="$1"
elif [ -f "$HOME/answer.txt" ]; then
    ANSWER="$(head -1 "$HOME/answer.txt" | tr -dc '0-9')"
fi

# --- check local task state --------------------------------------------------
TASK1_EXISTS=false
[ -d "$HOME/task1" ] && TASK1_EXISTS=true

TASK2_OK=false
if [ -d "$HOME/school/computer/first-project" ] \
   && [ -d "$HOME/school/computer/second-project" ] \
   && [ -d "$HOME/school/physic" ] \
   && [ -d "$HOME/school/math" ]; then
    TASK2_OK=true
fi

# --- POST to panel -----------------------------------------------------------
RESPONSE=$(curl -sf -X POST "$PANEL_URL/api/tasks/submit" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"$USERNAME\",
        \"answer\": \"$ANSWER\",
        \"task1_exists\": $TASK1_EXISTS,
        \"task2_ok\": $TASK2_OK
    }" 2>&1)

if [ $? -ne 0 ]; then
    echo "❌ ارتباط با پنل برقرار نشد. بعداً دوباره تلاش کنید."
    exit 1
fi

if command -v jq >/dev/null 2>&1; then
    MSG=$(echo "$RESPONSE" | jq -r '.message // "انجام شد."')
    echo "$MSG"
    echo "$RESPONSE" | jq -c '.details[]?' 2>/dev/null \
        | while IFS= read -r line; do
            S=$(echo "$line" | jq -r '.status')
            M=$(echo "$line" | jq -r '.message')
            if [ "$S" = "correct" ]; then
                echo "  ✅ $M"
            elif [ "$S" = "wrong" ]; then
                echo "  ❌ $M"
            elif [ "$S" = "done" ]; then
                echo "  ⏭️  $M"
            fi
        done
else
    echo "$RESPONSE"
fi
