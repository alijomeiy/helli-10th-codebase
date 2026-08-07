# studentctl — student Linux playground + scheduling panel

A two-box setup for a computer class:

- **Big-ish box** (4 GB RAM / 2 vCPU): the Linux playground where ~100 students
  have limited accounts, max **15 concurrent**, each able to run one simple
  service (e.g. `python3 -m http.server`) on an assigned port.
- **Small VM**: a Flask web panel (**Persian / RTL UI**) where students
  self-register, get approved by an admin, see their SSH credentials, and pick a
  **preferred day**. The panel drives the Linux box over SSH using a restricted,
  passwordless-sudo account.
- **nginx on the 4GB box** reverse-proxies `panel.domain` (DNS → 4GB box) to the
  panel on the small VM.

### Access model you asked for

Each student picks a preferred weekday.

- **On their day** → priority access. Denied only if the server is genuinely
  full (15/15).
- **On another day** → still allowed **if** the server has spare capacity beyond
  a reserved buffer (default `max − reserved = 15 − 3 = 12`). So off-day
  students never steal the last slots from scheduled students, but idle
  capacity is not wasted.

Enforced at SSH login time by a PAM hook (`pam_exec` → `studentctl-check-login`)
reading a JSON config the panel pushes. Nothing relies on the panel being up at
login time.

---

## Layout

```
studentctld/
├── server/                      # runs on the Linux playground box (as root)
│   ├── setup_server.sh          # one-time bootstrap
│   ├── studentctl-check-login.sh# PAM scheduling/concurrency hook
│   ├── studentctl-provision.sh  # create account
│   ├── studentctl-disable.sh
│   ├── studentctl-enable.sh
│   ├── studentctl-delete.sh
│   ├── studentctl-push-config.sh# replace /etc/studentctl/config.json
│   └── studentctl-status.sh     # JSON {current,max,...} for the panel
├── panel/                       # runs on the small VM
│   ├── app.py  config.py  models.py  server_api.py  sync.py
│   ├── templates/  static/  requirements.txt
│   └── studentctl-panel.service
└── deploy/
    └── install_panel.sh         # installs the panel on the small VM
```

---

## 1. Linux playground box (4 GB / 2 vCPU)

Ubuntu 22.04/24.04 or Debian 12. As root:

```bash
# If you cloned/copied these files on Windows, normalise line endings first:
find server -name '*.sh' -exec sed -i 's/\r$//' {} +

cd server
bash setup_server.sh
```

What it does:
- installs `jq`, `quota`, `ufw`, `openssh-server`;
- installs the `studentctl-*` scripts and wires the PAM login check into
  `/etc/pam.d/sshd`;
- sets a **2-hour idle auto-logout** + process/file ulimits for student shells
  (`/etc/profile.d/studentctl-students.sh`);
- applies **cgroup v2 limits** for every student session via a systemd
  `user-.slice` drop-in: `MemoryMax=300M`, `CPUQuota=20%`, `TasksMax=128`;
- opens the firewall for SSH and the student service port range `10000–10100`;
- creates a locked-down `studentctl` management user with passwordless sudo
  **only** for the `studentctl-*` scripts.

**Manual one-time steps the script reminds you about:**

1. Enable quotas. Edit `/etc/fstab`, add `usrquota,grpquota` to the options for
   `/`, then:
   ```bash
   mount -o remount / && quotacheck -cum / && quotaon -v /
   ```
   (reboot if needed).
2. (Optional, recommended) Restrict SSH to the lab subnet:
   ```bash
   uwfm  # n/a — edit with ufw: replace `ufw allow 22/tcp` with a source rule
   ufw delete allow 22/tcp
   ufw allow from 10.0.0.0/24 to any port 22
   ```

---

## 2. Small VM — the web panel

On the small VM, as root:

```bash
find panel -name '*.py' -exec sed -i 's/\r$//' {} +
bash deploy/install_panel.sh
```

This:
- creates a `studentctl-panel` system user and a venv with the Python deps;
- **generates an SSH keypair** and prints the public key — install it on the
  **Linux box** as the `studentctl` user's authorized key:
  ```bash
  # on the Linux box:
  sudo -u studentctl mkdir -p /home/studentctl/.ssh
  sudo -u studentctl tee /home/studentctl/.ssh/authorized_keys <<< '<printed pubkey>'
  ```
- writes `/opt/studentctl/panel/panel.env` — **edit it**: set
  `STUDENTCTL_SSH_HOST`, `STUDENTCTL_SERVER_DOMAIN`, and especially change
  `STUDENTCTL_ADMIN_PASS`;
- enables the `studentctl-panel` systemd service (listening on `:5000`);
- installs a cron job that re-pushes the config every 2 min as a safety net.

Put nginx/Caddy in front for TLS if you expose it beyond the lab.

---

## 2b. Reverse proxy — nginx on the 4GB box

Topology you asked for: DNS resolves `panel.domain` to the **4GB playground
box**, but the panel itself runs on the **small VM**. So nginx lives on the
4GB box and reverse-proxies `panel.domain` → the small VM's `:5000`.

```
  browser ── panel.domain ──► 4GB box:80/443 (nginx) ──► small-VM:5000 (Flask)
```

On the **4GB box**:

```bash
find server -name '*.conf' -exec sed -i 's/\r$//' {} +
sudo apt-get install -y nginx
sudo cp server/nginx_panel.conf /etc/nginx/sites-available/panel.conf
# Replace placeholders with your real values:
sudo sed -i 's/PANEL_DOMAIN/panel.yourdomain.ir/g; s/SMALL_VM_IP/10.0.0.20/g' \
     /etc/nginx/sites-available/panel.conf
sudo ln -s /etc/nginx/sites-available/panel.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo ufw allow 80/tcp && sudo ufw allow 443/tcp
```

For HTTPS:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d panel.yourdomain.ir
```

The panel already applies `werkzeug.ProxyFix`, so behind nginx it sees the
correct scheme/host. **Lock down the small VM** so `:5000` is reachable only
from the 4GB box (students never hit it directly):

```bash
# on the small VM:
sudo ufw allow from 10.0.0.10 to any port 5000   # 4GB box IP only
sudo ufw deny 5000
```

---

## 3. Using it

1. Open `https://panel.yourdomain.ir/` → **ثبت‌نام** as a student, pick a day.
   (The whole UI is in **Persian / RTL**.)
2. **Admin** (`/admin/login`, default `admin`/`changeme123` — change it via the
   DB or by editing `STUDENTCTL_ADMIN_PASS` and restarting) → approve requests.
   Approving provisions the Linux account and assigns a UID + service port;
   the password is shown on the student's dashboard.
3. Student SSHes in on their day (or off-day if capacity allows):
   ```bash
   ssh alice@<linux-box-ip>
   # then run a service on their port:
   python3 -m http.server 10000
   ```
   and opens `http://<linux-box-ip>:10000/` in a browser.

Admins can also **disable / re-enable / delete** accounts and tune
`max_concurrent` and `reserved_onday` live.

---

## How scheduling is actually enforced

`studentctl-check-login.sh` runs in the PAM **account** phase of every SSH
login. Logic (UID ≥ 1000 only; root/admins unaffected):

```
if today == student.preferred_day:
    allow, unless logged_in >= max_concurrent   # priority, only hard-capped
else:
    allow only if logged_in < (max_concurrent - reserved_onday)
```

`logged_in` = count of unique non-system users currently in `who`. The config it
reads (`/etc/studentctl/config.json`) is the single source of truth and is
written by the panel via `studentctl-push-config`. Because the check is purely
local, **students can still log in on their scheduled day even if the panel VM
is down** — only admin changes need the panel up.

---

## Resource budget (4 GB / 2 cores ÷ 15 concurrent)

| Resource   | Per student        | Mechanism                      |
|------------|--------------------|--------------------------------|
| RAM        | 300 MB max         | cgroup v2 `MemoryMax`          |
| CPU        | 20% of one core    | cgroup v2 `CPUQuota`           |
| Processes  | 128                | cgroup `TasksMax` + `ulimit`   |
| Open files | 512                | `ulimit -n`                    |
| Disk       | 1 GB soft / 1.1 GB | ext4 `usrquota`                |
| Idle time  | 2 h auto-logout    | `TMOUT` in profile             |
| Network    | one service port   | `ufw` per-account + 10000–10100|

Plenty of headroom for 15 students each running a small Python/web service.

---

## Tuning knobs

- `max_concurrent`, `reserved_onday` → admin UI (saved to DB + pushed).
- Per-student RAM/CPU → edit `/etc/systemd/system/user-.slice.d/50-students.conf`
  on the Linux box, then `systemctl daemon-reload`.
- Idle timeout → `TMOUT` in `/etc/profile.d/studentctl-students.sh`, or set
  `STUDENTCTL_TMOUT` per environment.
- Outbound internet is **not** blocked by default so `pip`/`apt` work for
  learning. To lock it down, add per-UID owner rules in `ufw`/`iptables`.

---

## Security notes

- The panel never holds root on the Linux box: it SSHes as `studentctl`, which
  can only run the whitelisted scripts (sudoers file).
- Panel login passwords are hashed (werkzeug). The generated **SSH password** is
  stored in the panel DB in plaintext so students can re-read it on their
  dashboard — acceptable for a classroom, but treat the panel DB as sensitive
  and back it up. To avoid that, remove `ssh_password` from the dashboard and
  have students reset via the admin instead.
- Rotate `STUDENTCTL_SECRET` and the admin password before real use.

---

## Quick troubleshooting

- **Student can't log in on their day** → check `/etc/studentctl/config.json`
  has them with `enabled:true` and the right `day`; check the PAM line exists in
  `/etc/pam.d/sshd`; the deny reason is printed to the SSH client.
- **Panel shows “can't reach Linux server”** → verify the panel's key is in
  `/home/studentctl/.ssh/authorized_keys` on the Linux box and that
  `studentctl` can run `sudo /usr/local/sbin/studentctl-status` without a
  password.
- **Quotas not applied** → `usrquota` not enabled on `/`; run the fstab/remount
  steps above.
