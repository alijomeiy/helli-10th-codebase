# studentctl — student Linux playground + web panel

A single-box setup for a computer class, on one **8 GB / 4 vCPU** Linux machine
(Ubuntu 22.04/24.04 or Debian 12):

- **Linux playground**: ~100 students get limited accounts (max **30
  concurrent**), each able to run one simple service (e.g.
  `python3 -m http.server`) on an assigned port.
- **Web panel** (Persian / RTL UI, **mobile-friendly**): students self-register,
  get approved by an admin, and see their SSH credentials + live capacity. Runs
  in a **Docker container**. The admin area is split off under `/admin/*` and
  hidden from students.
- The panel drives the playground over SSH using a restricted, passwordless-sudo
  account.

> Persian setup guide: see [`SETUP.fa.md`](SETUP.fa.md). Full change history in
> Persian: see [`CHANGELOG.fa.md`](CHANGELOG.fa.md).

### Access model (resource-based, no scheduling)

There is **no scheduling** — any enabled student may log in whenever there is
free capacity:

- **Login allowed** as long as `logged_in < max_concurrent` (default 30).
- **Idle auto-kick**: sessions idle for longer than `idle_timeout` (default 1800s
  = 30 min) are logged out automatically, so slots are reclaimed for others.

Both `max_concurrent` and `idle_timeout` are editable from the admin UI (and have
env defaults). Enforced at SSH login time by a PAM hook (`pam_exec` →
`studentctl-check-login`) reading a JSON config the panel pushes; the idle
timeout is applied via `TMOUT` in the shell profile. Because the login check is
local, students can still log in even if the panel container is down — only
admin changes need the panel up.

---

## Layout

```
studentctld/
├── server/                      # runs on the Linux playground box (as root)
│   ├── setup_server.sh          # one-time bootstrap
│   ├── studentctl-check-login.sh# PAM open-hours/concurrency hook
│   ├── studentctl-provision.sh  # create account
│   ├── studentctl-disable.sh / enable.sh / delete.sh
│   ├── studentctl-push-config.sh# replace /etc/studentctl/config.json
│   └── studentctl-status.sh     # JSON {current,cap,open_now,...} for the panel
├── panel/                       # runs in a container (or bare-metal)
│   ├── app.py  config.py  models.py  server_api.py  sync.py
│   ├── templates/  static/  requirements.txt
│   ├── Dockerfile  entrypoint.sh  panel.env.example
│   └── studentctl-panel.service  # bare-metal alternative
├── docker-compose.yml           # container deployment
└── deploy/
    ├── deploy_panel.sh          # one-command container build+run
    └── install_panel.sh         # bare-metal systemd installer (alternative)
```

---

## 1. Linux playground box (8 GB / 4 vCPU)

As root:

```bash
# If you cloned/copied these files on Windows, normalise line endings first:
find server -name '*.sh' -exec sed -i 's/\r$//' {} +

cd server
bash setup_server.sh
```

What it does:
- installs `jq`, `quota`, `ufw`, `openssh-server`;
- **sets the timezone to `Asia/Tehran`** (open-hours matching uses server local time);
- installs the `studentctl-*` scripts and wires the PAM login check into
  `/etc/pam.d/sshd`;
- sets a **30-min idle auto-logout** (configurable) + process/file ulimits for student shells;
- applies **cgroup v2 limits** per student session: `MemoryMax=384M`,
  `CPUQuota=50%`, `TasksMax=128`;
- opens the firewall for SSH and the student service port range `10000–10100`;
- seeds `/etc/studentctl/config.json` (`max_concurrent:30, idle_timeout:1800, users:{}`);
- creates a locked-down `studentctl` management user with passwordless sudo
  **only** for the `studentctl-*` scripts.

**Manual one-time steps the script reminds you about:**

1. Enable quotas. Edit `/etc/fstab`, add `usrquota,grpquota` to the options for
   `/`, then:
   ```bash
   mount -o remount / && quotacheck -cum / && quotaon -v /
   ```
   (reboot if needed).
2. (Optional) Restrict SSH to the lab subnet:
   ```bash
   ufw delete allow 22/tcp
   ufw allow from 10.0.0.0/24 to any port 22
   ```

---

## 2. The web panel — container (recommended)

On the **same box** (or another host that can SSH to the playground), with
Docker installed:

```bash
bash deploy/deploy_panel.sh
```

This:
- creates `panel/panel.env` from the example with a random `STUDENTCTL_SECRET`
  (if not already present) — **edit it**: set `STUDENTCTL_SSH_HOST` (use
  `host.docker.internal` if the playground is this same host),
  `STUDENTCTL_SERVER_DOMAIN`, and change `STUDENTCTL_ADMIN_PASS`;
- builds the image and runs the container;
- on first start, **generates an SSH keypair** and prints the public key —
  install it on the playground box:
  ```bash
  # on the playground box:
  sudo -u studentctl mkdir -p /home/studentctl/.ssh
  echo '<printed pubkey>' | sudo -u studentctl tee -a /home/studentctl/.ssh/authorized_keys
  ```

The panel listens on `127.0.0.1:5000` (loopback only). The SQLite DB and the
generated SSH key persist in the `panel-data` Docker volume across rebuilds.

### Putting nginx in front (optional, for TLS)

If you want `https://panel.yourdomain.ir/`, run nginx on the same box and proxy
to the container:

```bash
sudo apt-get install -y nginx
# proxy panel.yourdomain.ir -> 127.0.0.1:5000
sudo tee /etc/nginx/sites-available/panel.conf >/dev/null <<'EOF'
server {
    server_name panel.yourdomain.ir;
    location / { proxy_pass http://127.0.0.1:5000; proxy_set_header Host $host; proxy_set_header X-Forwarded-Proto $scheme; }
}
EOF
sudo ln -s /etc/nginx/sites-available/panel.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo apt-get install -y certbot python3-certbot-nginx && sudo certbot --nginx -d panel.yourdomain.ir
```

The panel already applies `werkzeug.ProxyFix`, so behind nginx it sees the
correct scheme/host.

### Bare-metal alternative (no Docker)

If you prefer systemd over containers:

```bash
find panel -name '*.py' -exec sed -i 's/\r$//' {} +
bash deploy/install_panel.sh
```

This installs the panel under `/opt/studentctl/panel` with a venv, enables the
`studentctl-panel` service, and adds a 2-minute cron re-sync.

---

## 3. Using it

1. Open `https://panel.yourdomain.ir/` → **ثبت‌نام** as a student. (Whole UI is
   Persian / RTL, mobile-friendly.)
2. **Admin** → go to `/admin/login` (default `admin`/`changeme123` — **change it
   immediately**). Approve requests; approving provisions the Linux account and
   assigns a UID + service port (the password is shown on the student's
   dashboard). Set `max_concurrent` and `idle_timeout`.
3. Student SSHes in whenever capacity is free:
   ```bash
   ssh alice@<linux-box-ip>
   # then run a service on their port:
   python3 -m http.server 10000
   ```
   and opens `http://<linux-box-ip>:10000/` in a browser. Idle sessions are
   logged out after `idle_timeout`.

Admins can also **disable / re-enable / delete** accounts and tune the limits
live.

---

## How access is enforced

`studentctl-check-login.sh` runs in the PAM **account** phase of every SSH login
(UID ≥ 1000 only; root/admins unaffected):

```
allow, unless logged_in >= max_concurrent   # default 30
```

`logged_in` = count of unique non-system users currently in `who`. Idle sessions
are auto-logged-out after `idle_timeout` seconds via `TMOUT` in
`/etc/profile.d/studentctl-students.sh` (the value is read from the pushed config
at login). The config (`/etc/studentctl/config.json`) is the single source of
truth, written by the panel via `studentctl-push-config`.

---

## Resource budget (8 GB / 4 cores ÷ 30 concurrent)

| Resource   | Per student        | Mechanism                      |
|------------|--------------------|--------------------------------|
| RAM        | 384 MB max         | cgroup v2 `MemoryMax`          |
| CPU        | 50% of one core    | cgroup v2 `CPUQuota`           |
| Processes  | 128                | cgroup `TasksMax` + `ulimit`   |
| Open files | 512                | `ulimit -n`                    |
| Disk       | 400 MB hard cap    | ext4 `usrquota`                |
| Idle time  | 2 h auto-logout    | `TMOUT` in profile             |
| Network    | one service port   | `ufw` per-account + 10000–10100|

Comfortable headroom for 30 students each running a small Python/web service.

---

## Tuning knobs

- `max_concurrent`, `idle_timeout` → admin UI (saved to DB + pushed), or env
  `STUDENTCTL_MAX_CONCURRENT` / `STUDENTCTL_IDLE_TIMEOUT`.
- Per-student RAM/CPU → edit
  `/etc/systemd/system/user-.slice.d/50-students.conf` on the playground box,
  then `systemctl daemon-reload`.
- Idle timeout override → `STUDENTCTL_TMOUT` env per shell (overrides the pushed
  value).
- Outbound internet is **not** blocked by default so `pip`/`apt` work for
  learning. To lock it down, add per-UID owner rules in `ufw`/`iptables`.

---

## Security notes

- The panel never holds root on the playground: it SSHes as `studentctl`, which
  can only run the whitelisted scripts (sudoers file).
- Panel login passwords are hashed (werkzeug). The generated **SSH password** is
  stored in the panel DB in plaintext so students can re-read it on their
  dashboard — acceptable for a classroom, but treat the panel DB (the Docker
  volume) as sensitive and back it up.
- Rotate `STUDENTCTL_SECRET` and the admin password before real use.
- Admin is reachable only at `/admin/login`; no link appears in the student UI.

---

## Quick troubleshooting

- **Student can't log in** → check `/etc/studentctl/config.json` has them with
  `enabled:true` and that `logged_in < max_concurrent`; check the PAM line exists
  in `/etc/pam.d/sshd`; the deny reason is printed to the SSH client.
- **Panel shows "can't reach Linux server"** → verify the panel's key is in
  `/home/studentctl/.ssh/authorized_keys` on the playground and that
  `studentctl` can run `sudo /usr/local/sbin/studentctl-status` without a
  password. If the panel is in a container and the playground is the host, set
  `STUDENTCTL_SSH_HOST=host.docker.internal`.
- **Idle timeout not working** → ensure the student's shell sources
  `/etc/profile.d/studentctl-students.sh` (interactive bash does by default); the
  `TMOUT` value comes from config.json at login.
- **Quotas not applied** → `usrquota` not enabled on `/`; run the fstab/remount
  steps above.
