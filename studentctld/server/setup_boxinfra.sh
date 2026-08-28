#!/bin/bash
# setup_boxinfra.sh — install the student-lab (boxes) infrastructure on the VM.
# Safe to re-run (idempotent). Does NOT touch running services (ctfd/panel/nginx).
set -e
cd "$(dirname "$0")"

echo "==> building studentbox:1 image (first build ~2-4 min)..."
docker build -q -f ../docker/studentbox.Dockerfile -t studentbox:1 ../docker

echo "==> installing box manager + mybox"
install -m 0700 studentctl-box.sh /usr/local/sbin/studentctl-box
install -m 0755 mybox.sh          /usr/local/bin/mybox

echo "==> labstudents group"
getent group labstudents >/dev/null 2>&1 || groupadd labstudents

echo "==> sudoers (studentctl: box mgmt | labstudents: mybox only)"
cat >/etc/sudoers.d/studentctl-box <<'EOF'
studentctl ALL=(root) NOPASSWD: /usr/local/sbin/studentctl-box
EOF
cat >/etc/sudoers.d/mybox <<'EOF'
%labstudents ALL=(root) NOPASSWD: /usr/local/sbin/studentctl-box enter
EOF
chmod 440 /etc/sudoers.d/studentctl-box /etc/sudoers.d/mybox
visudo -c >/dev/null && echo "   sudoers OK"

echo "==> cron: idle autostop / nightly stopall / nightly disk report"
cat >/etc/cron.d/studentctl-boxes <<'EOF'
*/10 * * * * root /usr/local/sbin/studentctl-box autostop >>/var/log/studentctl-box.log 2>&1
30 2 * * * root /usr/local/sbin/studentctl-box stopall    >>/var/log/studentctl-box.log 2>&1
15 3 * * * root /usr/local/sbin/studentctl-box disk       >>/var/log/studentctl-box.log 2>&1
EOF
chmod 644 /etc/cron.d/studentctl-boxes
touch /var/log/studentctl-box.log

echo "==> per-student box flag scatter hook (used by 'studentctl-box reset')"
if [ -f ../ctf/box_scatter_one.py ]; then
  cat >/usr/local/sbin/studentctl-box-scatter <<'EOF'
#!/bin/bash
# re-scatter one student's box flags from the CTF manifest (root only)
exec python3 /root/helli-10th-codebase/studentctld/ctf/box_scatter_one.py "$1"
EOF
  chmod 700 /usr/local/sbin/studentctl-box-scatter
  echo "   installed"
else
  echo "   skipped (box_scatter_one.py not present yet)"
fi

echo "==> smoke: box create/start/enter/stop for a throwaway user"
docker rm -f box-zzselftest >/dev/null 2>&1 || true
/usr/local/sbin/studentctl-box create zzselftest
/usr/local/sbin/studentctl-box start zzselftest
docker exec box-zzselftest bash -c 'echo inside-ok: $(whoami) $(docker --version 2>/dev/null | head -1)'
/usr/local/sbin/studentctl-box stop zzselftest
/usr/local/sbin/studentctl-box remove zzselftest

echo
echo "All done. Running services untouched:"
docker ps --format '{{.Names}}  {{.Status}}'
