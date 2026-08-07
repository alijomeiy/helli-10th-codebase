#!/bin/bash
# deploy/deploy_panel.sh — build & run the panel container (one command).
# Run on the host that will run the panel (same host as the playground is fine).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR%/deploy}"
ENV_FILE="$ROOT/panel/panel.env"

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: 'docker' not found. Install Docker (or podman + the compose plugin)." >&2
    exit 1
fi

# Create panel.env from the example with a freshly generated secret.
if [ ! -f "$ENV_FILE" ]; then
    SECRET="$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | cut -c1-32)"
    sed "s|__GENERATE_A_RANDOM_SECRET__|$SECRET|" \
        "$ROOT/panel/panel.env.example" >"$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "==> Created $ENV_FILE with a random secret."
    echo "    EDIT it now: set STUDENTCTL_SSH_HOST / STUDENTCTL_SERVER_DOMAIN"
    echo "    (use host.docker.internal if the playground is this same host)."
    echo
fi

echo "==> Building & starting the panel container..."
cd "$ROOT"
docker compose up -d --build

sleep 3
echo
echo "==> Status:"
docker compose ps
echo
if docker compose ps | grep -q "studentctl-panel.*Up\|studentctl-panel.*running\|healthy"; then
    echo "Panel up at http://127.0.0.1:5000/  (admin at /admin/login)"
else
    echo "Container did not report healthy. Logs:" >&2
    docker compose logs --tail=40 panel >&2
    exit 1
fi
echo
echo "First build prints the SSH public key — copy it to the playground box:"
echo "  echo '<key>' | sudo -u studentctl tee -a /home/studentctl/.ssh/authorized_keys"
