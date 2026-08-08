#!/bin/bash
# studentctl-deploy-task1  — reads JSON array from stdin, creates a random
# directory tree per student with result.txt (clue) and a hidden answer file.
#
# Input: [{"username":"ali","uid":2000,"answer":5}, ...]
set -euo pipefail

DIR_NAMES=(alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu
           nu xi omicron pi rho sigma tau upsilon phi chi psi omega
           data files tmp var opt src lib bin etc run sys proc log cache)

ANSWER_FILES=(notes.txt config.dat readme.md info.log cache.tmp data.bin
              memo.txt record.csv settings.cfg backup.bak index.dat
              .hidden store.db local.conf)

_generate_tree() {
    local base="$1"
    local nn=${#DIR_NAMES[@]}
    local prev=("$base")

    for level in 1 2 3 4; do
        local n=$(( RANDOM % 2 + 4 ))   # 4 or 5 dirs at this level
        local level_dirs=()
        for (( i=0; i<n; i++ )); do
            local name="${DIR_NAMES[$(( RANDOM % nn ))]}"
            local parent="${prev[$(( RANDOM % ${#prev[@]} ))]}"
            local d="$parent/$name"
            while [ -d "$d" ]; do
                d="$parent/${name}_$(( RANDOM % 90 + 10 ))"
            done
            mkdir -p "$d"
            level_dirs+=("$d")

            # scatter decoy files
            if (( RANDOM % 2 == 0 )); then
                echo "ref: $RANDOM.$(( RANDOM % 1000 ))" > "$d/.cache"
            fi
            if (( RANDOM % 3 == 0 )); then
                head -c $(( RANDOM % 64 + 16 )) /dev/urandom | base64 > "$d/.lock"
            fi
        done
        prev=("${level_dirs[@]}")
    done
}

echo "=== task1 deployment ==="
jq -c '.[]' | while IFS= read -r entry; do
    USERNAME=$(echo "$entry" | jq -r '.username')
    ANSWER=$(echo "$entry" | jq -r '.answer')
    HOME_DIR=$(getent passwd "$USERNAME" | cut -d: -f6)

    if [ ! -d "$HOME_DIR" ]; then
        echo "  SKIP $USERNAME — home dir missing" >&2
        continue
    fi

    TASK_DIR="$HOME_DIR/task1"
    rm -rf "$TASK_DIR"
    mkdir -p "$TASK_DIR"

    _generate_tree "$TASK_DIR"

    # collect all dirs (shuffled)
    mapfile -t ALL_DIRS < <(find "$TASK_DIR" -type d | tail -n +2 | shuf)

    if [ "${#ALL_DIRS[@]}" -lt 2 ]; then
        echo "  SKIP $USERNAME — tree too small" >&2
        continue
    fi

    # place result.txt (clue) at random location
    RESULT_DIR="${ALL_DIRS[0]}"
    cat > "$RESULT_DIR/result.txt" <<'CLUE'
آیا این همان فایلی بود که دنبالش می‌گشتید؟
احتمالاً نه! فایل واقعی عددی است که در فایلی با نام معنادار
پنهان شده است. آن را پیدا کنید!
CLUE

    # place answer file at a different random location
    AF="${ANSWER_FILES[$(( RANDOM % ${#ANSWER_FILES[@]} ))]}"
    ANSWER_DIR="${ALL_DIRS[1]}"
    echo "$ANSWER" > "$ANSWER_DIR/$AF"

    # clean up any stale answer
    rm -f "$HOME_DIR/answer.txt"

    chown -R "$USERNAME:$USERNAME" "$TASK_DIR"
    echo "  OK  $USERNAME  answer=$ANSWER  file=$AF  in=$(basename "$ANSWER_DIR")"
done

echo "=== task1 done ==="
