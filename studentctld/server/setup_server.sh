#!/bin/bash
# studentctl - one-time server bootstrap (run as root on the 8GB/4core box)
# Ubuntu 22.04 / 24.04 (Debian 12) assumed.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo bash setup_server.sh" >&2
    exit 1
fi

echo "==> Installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y jq quota ufw openssh-server curl ca-certificates

echo "==> Setting timezone (open-hours matching uses server local time)"
timedatectl set-timezone Asia/Tehran || true

echo "==> Enabling filesystem quotas (requires a reboot to take effect on /)"
if ! grep -qE '^[^#]*\busrquota\b' /etc/fstab; then
    echo "  Edit /etc/fstab and add 'usrquota,grpquota' to the options for /," >&2
    echo "  then run: mount -o remount / && quotacheck -cum / && quotaon -v /" >&2
else
    quotacheck -cum / 2>/dev/null || true
    quotaon -v / 2>/dev/null || true
fi

echo "==> Installing studentctl management scripts"
install -m 0750 studentctl-provision.sh     /usr/local/sbin/studentctl-provision
install -m 0750 studentctl-disable.sh       /usr/local/sbin/studentctl-disable
install -m 0750 studentctl-enable.sh        /usr/local/sbin/studentctl-enable
install -m 0750 studentctl-delete.sh        /usr/local/sbin/studentctl-delete
install -m 0750 studentctl-push-config.sh   /usr/local/sbin/studentctl-push-config
install -m 0750 studentctl-status.sh        /usr/local/sbin/studentctl-status
install -m 0755 studentctl-check-login.sh   /usr/local/bin/studentctl-check-login

echo "==> Wiring PAM login check into sshd"
PAM_FILE=/etc/pam.d/sshd
LINE="account required pam_exec.so /usr/local/bin/studentctl-check-login"
if ! grep -q "studentctl-check-login" "$PAM_FILE"; then
    echo "$LINE" >> "$PAM_FILE"
fi

echo "==> Idle-timeout + welcome banner for student shells"
cat >/etc/profile.d/studentctl-students.sh <<'PROFILE'
# Applies to interactive student shells. Root/admins unaffected in practice.
if [ "$(id -u)" -ge 2000 ]; then
    # Auto-logout after N seconds idle (default 1800s = 30min).
    # Value comes from the panel-pushed config; env STUDENTCTL_TMOUT overrides.
    _T=$(jq -r '.idle_timeout // 1800' /etc/studentctl/config.json 2>/dev/null || echo 1800)
    TMOUT=${STUDENTCTL_TMOUT:-$_T}
    readonly TMOUT
    export TMOUT
    # Friendly limits
    ulimit -u 256        # max processes
    ulimit -n 512        # max open files
fi
PROFILE

echo "==> cgroup v2 resource limits for all student sessions (systemd user slice)"
mkdir -p /etc/systemd/system/user-.slice.d
cat >/etc/systemd/system/user-.slice.d/50-students.conf <<'EOF'
[Slice]
MemoryMax=384M
CPUQuota=50%
TasksMax=128
IOWeight=20
EOF
systemctl daemon-reload

echo "==> SSH hardening"
SSHD=/etc/ssh/sshd_config
# Password auth ON (students log in with generated passwords) but we restrict
# who can connect + enforce the PAM schedule check.
sshd_set() {
    local key="$1"; local val="$2"
    if grep -qE "^\s*#?\s*${key}\b" "$SSHD"; then
        sed -i -E "s|^\s*#?\s*${key}\b.*|${key} ${val}|" "$SSHD"
    else
        echo "${key} ${val}" >> "$SSHD"
    fi
}
sshd_set UsePAM yes
sshd_set ClientAliveInterval 300
sshd_set ClientAliveCountMax 2
sshd_set MaxStartups 30:30:60
systemctl reload ssh || systemctl reload sshd || true

echo "==> Firewall baseline"
# Allow SSH. Student service ports are opened per-account at provision time
# (range 10000-10100). Tighten the SSH source below to your classroom/lab subnet.
ufw --force reset >/dev/null
ufw allow 22/tcp comment 'ssh'
ufw allow 10000:10100/tcp comment 'student services'
ufw --force enable

echo "==> Config directory"
install -d -m 0755 /etc/studentctl
[ -f /etc/studentctl/config.json ] || echo '{"max_concurrent":30,"idle_timeout":1800,"users":{}}' >/etc/studentctl/config.json

echo "==> Dedicated management user for the web panel (passwordless, restricted sudo)"
if ! id studentctl >/dev/null 2>&1; then
    useradd -m -s /bin/bash studentctl
fi
SUDOERS=/etc/sudoers.d/studentctl
cat >"$SUDOERS" <<'EOF'
studentctl ALL=(root) NOPASSWD: /usr/local/sbin/studentctl-provision, \
 /usr/local/sbin/studentctl-disable, \
 /usr/local/sbin/studentctl-enable, \
 /usr/local/sbin/studentctl-delete, \
 /usr/local/sbin/studentctl-push-config, \
 /usr/local/sbin/studentctl-status
EOF
chmod 0440 "$SUDOERS"
visudo -cf "$SUDOERS"

echo
echo "=============================================================="
echo " Server bootstrap done. Next steps:"
echo "  1. Add usrquota to / in /etc/fstab and reboot if not done."
echo "  2. Put the web panel's public key for management:"
echo "       install -m 600 panel_key.pub /home/studentctl/.ssh/authorized_keys"
echo "       chown -R studentctl:studentctl /home/studentctl/.ssh"
echo "  3. Tighten 'ufw allow 22/tcp' to your lab subnet if desired."
echo "=============================================================="
