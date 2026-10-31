#!/bin/bash
# restore_boxes.sh — bring back the per-student container lab (mybox).
# Run as root on 62.3.41.38 AFTER `git pull`. Idempotent; safe to re-run.
# Steps: panel rebuild -> box infra (image/manager/mybox/sudoers/cron)
#        -> create one box per student -> in-box artifacts (box_scatter)
#        -> unhide the box-dependent challenges -> hub sync -> backup.
set -e
cd ~/helli-10th-codebase/studentctld

echo "==> 1/6 panel rebuild + restart (dashboard card + box APIs restored)"
docker compose up -d --build panel
sleep 3
docker ps --format '{{.Names}} {{.Status}}' | grep studentctl-panel

echo "==> 2/6 box infrastructure (idempotent installer)"
bash server/setup_boxinfra.sh 2>&1 | tail -5
# studentctl-box expects the tag studentbox:2; the Dockerfile builds :1
docker tag studentbox:1 studentbox:2 2>/dev/null || \
  docker build -q -f docker/studentbox.Dockerfile -t studentbox:2 docker

echo "==> 3/6 creating one box per student (stopped, 0 RAM idle)"
python3 - <<'PY'
import json
import subprocess
c = json.load(open("/etc/studentctl/config.json"))
n = 0
for name, d in sorted(c["users"].items()):
    if d.get("enabled") and d.get("uid", 0) >= 2000:
        r = subprocess.run(["/usr/local/sbin/studentctl-box", "create", name],
                           capture_output=True, text=True)
        if r.returncode == 0:
            n += 1
        else:
            print("  FAIL", name, r.stderr.strip()[:100])
print(f"boxes created: {n}")
PY

echo "==> 4/6 in-box artifacts for every challenge (box_scatter fleet, ~15 min)"
cd ctf
nohup python3 box_scatter.py > /var/log/box_scatter_restore.log 2>&1 &
echo "   started in background: /var/log/box_scatter_restore.log"
echo "   WAIT for 'box scatter done' before step 5:"
echo "   tail -f /var/log/box_scatter_restore.log"
