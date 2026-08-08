"""SSH bridge: the panel drives the Linux box as the restricted 'studentctl' user.

Each server action is an idempotent sudo call from the whitelist set up in
setup_server.sh. Config is pushed as a JSON blob read by the PAM login hook.
"""
import json
import logging
import paramiko
from flask import current_app

log = logging.getLogger("studentctl.server_api")


def _client():
    cfg = current_app.config
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        hostname=cfg["SSH_HOST"],
        port=cfg["SSH_PORT"],
        username=cfg["SSH_USER"],
        key_filename=cfg["SSH_KEY"],
        timeout=10,
        allow_agent=False,
        look_for_keys=False,
    )
    return c


def _run(cmd):
    """Run a command over SSH, return (rc, stdout, stderr)."""
    try:
        with _client() as c:
            stdin, stdout, stderr = c.exec_command(cmd, timeout=30)
            rc = stdout.channel.recv_exit_status()
            out = stdout.read().decode(errors="replace").strip()
            err = stderr.read().decode(errors="replace").strip()
            return rc, out, err
    except Exception as e:  # pragma: no cover - operational
        log.exception("SSH command failed: %s", cmd)
        return 99, "", str(e)


def _sudo(script, *args):
    safe = " ".join('"' + str(a).replace('"', '\\"') + '"' for a in args)
    rc, out, err = _run(f"sudo /usr/local/sbin/{script} {safe}")
    if rc != 0:
        raise RuntimeError(err or out or f"{script} exit {rc}")
    return out


# ---- public actions ----------------------------------------------------------

def provision(username, uid, port, password):
    return _sudo("studentctl-provision", username, uid, port, password)


def disable(username):
    return _sudo("studentctl-disable", username)


def enable(username):
    return _sudo("studentctl-enable", username)


def delete(username):
    return _sudo("studentctl-delete", username)


def status():
    rc, out, err = _run("sudo /usr/local/sbin/studentctl-status")
    if rc != 0:
        raise RuntimeError(err or out)
    return json.loads(out)


def deploy_task1(student_data):
    """SSH to server, pipe JSON to studentctl-deploy-task1 which creates
    a random tree + answer files per student."""
    payload = json.dumps(student_data)
    try:
        with _client() as c:
            cmd = "sudo /usr/local/sbin/studentctl-deploy-task1"
            stdin, stdout, stderr = c.exec_command(cmd, timeout=120)
            stdin.write(payload)
            stdin.channel.shutdown_write()
            rc = stdout.channel.recv_exit_status()
            out = stdout.read().decode(errors="replace").strip()
            err = stderr.read().decode(errors="replace").strip()
            if rc != 0:
                raise RuntimeError(err or out)
            return out
    except Exception as e:
        log.exception("deploy_task1 failed")
        raise RuntimeError(str(e))


def push_config(max_concurrent, idle_timeout, users):
    """users: dict username -> {enabled, uid, port}"""
    payload = json.dumps({
        "max_concurrent": int(max_concurrent),
        "idle_timeout": int(idle_timeout),
        "users": {
            u: {
                "enabled": bool(d["enabled"]),
                "uid": int(d["uid"]),
                "port": int(d["port"]),
            }
            for u, d in users.items()
        },
    })
    # Stream the JSON to the server via stdin of the push-config script.
    try:
        with _client() as c:
            cmd = "sudo /usr/local/sbin/studentctl-push-config"
            stdin, stdout, stderr = c.exec_command(cmd, timeout=30)
            stdin.write(payload)
            stdin.channel.shutdown_write()
            rc = stdout.channel.recv_exit_status()
            out = stdout.read().decode(errors="replace").strip()
            err = stderr.read().decode(errors="replace").strip()
            if rc != 0:
                raise RuntimeError(err or out)
            return out
    except Exception as e:
        log.exception("push_config failed")
        raise RuntimeError(str(e))
