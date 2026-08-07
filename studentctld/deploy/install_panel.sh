#!/bin/bash
# Install the web panel on the SMALL VM (the controller box, not the Linux playground).
# Ubuntu 22.04/24.04 or Debian 12. Run as root.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${STUDENTCTL_PANEL_SRC:-$SCRIPT_DIR/../panel}"
DEST=/opt/studentctl/panel
DATA=/var/lib/studentctl

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo bash install_panel.sh" >&2
    exit 1
fi
if [ ! -d "$SRC" ]; then
    echo "ERROR: panel source dir not found at: $SRC" >&2
    echo "Run from the repo, or set STUDENTCTL_PANEL_SRC=/abs/path/to/panel" >&2
    exit 1
fi

echo "==> Creating panel system user"
id studentctl-panel >/dev/null 2>&1 || useradd -r -m -d "$DATA" -s /usr/sbin/nologin studentctl-panel

echo "==> Creating writable data dir ($DATA)"
install -d -o studentctl-panel -g studentctl-panel "$DATA"

echo "==> Installing system Python + deps"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip ca-certificates dos2unix

echo "==> Deploying files to $DEST (normalising CRLF -> LF)"
install -d -o studentctl-panel -g studentctl-panel "$DEST"
cp -r "$SRC"/. "$DEST"/
# Strip Windows line endings so Python + systemd parse cleanly.
find "$DEST" \( -name '*.py' -o -name '*.service' -o -name '*.conf' \
             -o -name '*.txt' -o -name '*.sh' -o -name '*.css' \) \
     -exec sed -i 's/\r$//' {} +
chown -R studentctl-panel:studentctl-panel "$DEST"

echo "==> Virtualenv + python deps"
if [ ! -x "$DEST/venv/bin/python" ]; then
    sudo -u studentctl-panel python3 -m venv "$DEST/venv"
fi
sudo -u studentctl-panel "$DEST/venv/bin/pip" install --upgrade pip
sudo -u studentctl-panel "$DEST/venv/bin/pip" install -r "$DEST/requirements.txt"
WAITRESS="$DEST/venv/bin/waitress-serve"
if [ ! -x "$WAITRESS" ]; then
    echo "ERROR: $WAITRESS missing — pip install failed (no network?)." >&2
    exit 1
fi

echo "==> Smoke test: can the app actually import?"
if ! sudo -u studentctl-panel "$DEST/venv/bin/python" -c "import sys; sys.path.insert(0,'$DEST'); import app" 2>"$DEST/.import_err"; then
    echo "ERROR: the panel app failed to import. Error:" >&2
    cat "$DEST/.import_err" >&2
    exit 1
fi

echo "==> Generating a management SSH keypair (panel -> linux box)"
install -d -m 700 -o studentctl-panel -g studentctl-panel "$DEST/.ssh"
if [ ! -f "$DEST/panel_key" ]; then
    sudo -u studentctl-panel ssh-keygen -t ed25519 -N "" \
        -f "$DEST/panel_key" -C "studentctl-panel" >/dev/null
fi
PUB="$(cat "$DEST/panel_key.pub")"
echo
echo "  >>> Put this on the LINUX box as the studentctl user's authorized key:"
echo
echo "      sudo -u studentctl tee /home/studentctl/.ssh/authorized_keys <<< '$PUB'"
echo

echo "==> Writing env file. EDIT $DEST/panel.env with your values."
if [ ! -f "$DEST/panel.env" ]; then
cat >"$DEST/panel.env" <<EOF
STUDENTCTL_SECRET=$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | cut -c1-32)
STUDENTCTL_DB=$DATA/panel.db
STUDENTCTL_SSH_HOST=10.0.0.10
STUDENTCTL_SSH_PORT=22
STUDENTCTL_SSH_USER=studentctl
STUDENTCTL_SSH_KEY=$DEST/panel_key
STUDENTCTL_SERVER_DOMAIN=10.0.0.10
STUDENTCTL_ADMIN_USER=admin
STUDENTCTL_ADMIN_PASS=changeme123
EOF
fi
chown studentctl-panel:studentctl-panel "$DEST/panel.env"
chmod 600 "$DEST/panel.env"

echo "==> Installing systemd service"
install -m 644 "$DEST/studentctl-panel.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable studentctl-panel
systemctl restart studentctl-panel

echo "==> Checking that it came up..."
sleep 2
if systemctl is-active --quiet studentctl-panel; then
    echo "  OK: studentctl-panel is active."
else
    echo "  !! service did NOT start. Recent logs:" >&2
    journalctl -u studentctl-panel -n 40 --no-pager >&2 || true
    echo "  Run for more:  journalctl -u studentctl-panel -n 80 --no-pager" >&2
    exit 1
fi

echo "==> Listening sockets for the panel:"
ss -tlnp 2>/dev/null | grep -E ':5000' || echo "  (port 5000 not found — check cloud firewall / 0.0.0.0 bind)"

echo "==> Optional: periodic config re-sync (every 2 min)"
cat >/etc/cron.d/studentctl-sync <<EOF
*/2 * * * * studentctl-panel $DEST/venv/bin/python $DEST/sync.py >>/var/log/studentctl-sync.log 2>&1
EOF

echo
echo "Panel running on :5000. Default admin: admin / changeme123  -> CHANGE IT NOW."
echo "Test:   curl -I http://127.0.0.1:5000/"
