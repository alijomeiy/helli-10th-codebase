#!/bin/bash
# studentctl-provision  <username> <uid> <port> <password>
# Creates a restricted student account able to run ONE simple service.
set -euo pipefail
U="$1"; UID_N="$2"; PORT="$3"; PW="$4"

if id "$U" >/dev/null 2>&1; then
    echo "user already exists" >&2; exit 0
fi

useradd -u "$UID_N" -m -k /etc/skel -s /bin/bash "$U"
echo "${U}:${PW}" | chpasswd
chage -M 180 -W 7 "$U"          # password max life 180d
passwd -u "$U" >/dev/null       # ensure unlocked

# 400 MB disk quota on / (hard cap; needs usrquota enabled in fstab).
if repquota / >/dev/null 2>&1; then
    setquota -u "$U" 409600 409600 0 0 / || true
fi

# Open the student's service port.
ufw allow "${PORT}/tcp" >/dev/null 2>&1 || true

# Per-user rc: document how to run a service on their assigned port.
cat >>"/home/${U}/.bashrc" <<EOF

# --- studentctl: your assigned service port is ${PORT} ---
# Example:  python3 -m http.server ${PORT}
# Then visit:  http://<server-ip>:${PORT}/
EOF
chown "$U:$U" "/home/${U}/.bashrc"

echo "provisioned $U uid=$UID_N port=$PORT"
