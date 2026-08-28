#!/bin/bash
# run_contest.sh — one-shot: scatter flags + register everything in CTFd
#   sudo CTFD_TOKEN=<admin-api-token> ./run_contest.sh
set -euo pipefail
cd "$(dirname "$0")"

: "${CTFD_TOKEN:?export CTFD_TOKEN=<your admin token>}"
URL="${CTFD_URL:-http://127.0.0.1:8000}"
MANIFEST="${1:-manifest.json}"

[ "$(id -u)" -eq 0 ] || { echo "run as root: sudo CTFD_TOKEN=... ./run_contest.sh"; exit 1; }

echo "==> scattering flags into student homes"
python3 ctf_scatter.py --manifest "$MANIFEST"

echo "==> scattering root-lab flags into student boxes"
python3 box_scatter.py --manifest "$MANIFEST"

echo "==> creating challenges & flags in CTFd"
python3 ctf_setup.py --url "$URL" --token "$CTFD_TOKEN" \
    --manifest "$MANIFEST" --fresh

echo "==> done. now take a pristine snapshot:"
echo "    ./classroom.sh backup"
