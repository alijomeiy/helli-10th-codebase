#!/bin/bash
# studentctl-box — root-only manager for per-student lab boxes (docker).
#
# Usage: studentctl-box <command> [username]
#   create <u>     create the box (stopped, 0 RAM)
#   start <u>      wake the box (honours MAX_AWAKE)
#   stop  <u>      sleep the box
#   enter          open a root shell in the CALLER's own box (via mybox only)
#   reset <u>      destroy + recreate (all data in the box is lost)
#   remove <u>     destroy the box
#   status <u>     JSON: {exists, running, mem}
#   list           table of all boxes
#   autostop       stop boxes with no interactive sessions (cron, every 10 min)
#   stopall        stop every box (cron, nightly)
#   disk           append a disk report to the log (cron, nightly)
set -u

IMAGE=studentbox:2
MEM=384m
CPUS=0.5
PIDS=128
MAX_AWAKE=30            # refuse to wake more than this many boxes at once
IDLE_STRIKES=3          # autostop: 3 consecutive idle checks (10 min apart)
IDLE_DIR=/var/tmp/studentctl-box-idle
LOG=/var/log/studentctl-box.log

bname(){ printf 'box-%s' "$1"; }
ok_user(){ printf '%s' "$1" | grep -qE '^[a-z0-9][a-z0-9_-]{0,31}$'; }
exists(){ docker inspect "$(bname "$1")" >/dev/null 2>&1; }
running(){ [ "$(docker inspect -f '{{.State.Running}}' "$(bname "$1")" 2>/dev/null)" = "true" ]; }
awake_count(){ docker ps -q --filter label=studentctl=box | wc -l; }

# students reach this script ONLY via the sudoers rule for 'enter';
# if invoked under sudo with any other command, refuse hard.
if [ -n "${SUDO_USER:-}" ] && [ "${1:-}" != "enter" ]; then
  echo "not allowed"; exit 1
fi

cmd_create(){
  local u=${1:-} b
  ok_user "$u" || { echo "bad username"; exit 1; }
  b=$(bname "$u")
  exists "$u" && { echo "$b exists"; return 0; }
  docker create -it --name "$b" --hostname "$b" --label studentctl=box \
    --memory "$MEM" --cpus "$CPUS" --pids-limit "$PIDS" \
    --security-opt seccomp=unconfined \
    --security-opt apparmor=unconfined \
    --security-opt systempaths=unconfined \
    --device /dev/fuse --device /dev/net/tun \
    --stop-timeout 30 "$IMAGE" >/dev/null && echo "created $b"
}

cmd_start(){
  local u=${1:-}
  ok_user "$u" || exit 1
  exists "$u" || cmd_create "$u" >/dev/null
  running "$u" && return 0
  local n; n=$(awake_count)
  if [ "$n" -ge "$MAX_AWAKE" ]; then
    echo "فعلاً آزمایشگاه‌های فعال زیاد است ($n/$MAX_AWAKE). کمی بعد تلاش کنید."
    exit 2
  fi
  docker start "$(bname "$u")" >/dev/null
  rm -f "$IDLE_DIR/$(bname "$u")"
}

cmd_enter(){
  # only reachable through mybox (sudo sets SUDO_USER to the real student)
  local u=${SUDO_USER:-}
  [ -n "$u" ] && [ "$u" != "root" ] || { echo "use: mybox"; exit 1; }
  ok_user "$u" || exit 1
  cmd_start "$u" || exit 2
  exec docker exec -it "$(bname "$u")" env TERM="${TERM:-xterm-256color}" bash --rcfile /etc/bash.bashrc
}

cmd_stop(){
  local u=${1:-}
  ok_user "$u" || exit 1
  if running "$u"; then docker stop "$(bname "$u")" >/dev/null; fi
  rm -f "$IDLE_DIR/$(bname "$u")"
  echo "stopped $(bname "$u")"
}

cmd_remove(){
  local u=${1:-}
  ok_user "$u" || exit 1
  docker rm -f "$(bname "$u")" >/dev/null 2>&1
  rm -f "$IDLE_DIR/$(bname "$u")"
  echo "removed $(bname "$u")"
}

cmd_reset(){
  local u=${1:-}
  cmd_remove "$u"
  cmd_create "$u"
  # re-scatter this student's box flags if the hook is installed (no-op otherwise)
  if [ -x /usr/local/sbin/studentctl-box-scatter ]; then
    /usr/local/sbin/studentctl-box-scatter "$u" || true
  fi
  echo "reset $(bname "$u")"
}

cmd_status(){
  local u=${1:-} b
  ok_user "$u" || { echo '{"exists":false}'; exit 1; }
  b=$(bname "$u")
  if ! exists "$u"; then
    echo '{"exists":false,"running":false}'
    return 0
  fi
  if running "$u"; then
    local mem
    mem=$(docker stats --no-stream --format '{{.MemUsage}}' "$b" 2>/dev/null | head -1)
    printf '{"exists":true,"running":true,"mem":"%s"}\n' "${mem:-?}"
  else
    echo '{"exists":true,"running":false}'
  fi
}

cmd_list(){
  docker ps -a --filter label=studentctl=box --format 'table {{.Names}}\t{{.Status}}\t{{.Size}}'
}

cmd_autostop(){
  mkdir -p "$IDLE_DIR"
  local b active n
  for b in $(docker ps --filter label=studentctl=box --format '{{.Names}}'); do
    # active = processes beyond the box's own background set (PID1 sleep + cron)
    active=$(docker top "$b" -o pid,comm 2>/dev/null | tail -n +2 |
             awk '{print $2}' | grep -cvE '^(sleep|cron|CRON|sh)$')
    [ -n "$active" ] || active=0
    if [ "$active" -eq 0 ]; then
      n=$(( $(cat "$IDLE_DIR/$b" 2>/dev/null || echo 0) + 1 ))
      echo "$n" > "$IDLE_DIR/$b"
      if [ "$n" -ge "$IDLE_STRIKES" ]; then
        docker stop "$b" >/dev/null && rm -f "$IDLE_DIR/$b"
        echo "$(date -Is) stopped idle $b" >> "$LOG"
      fi
    else
      rm -f "$IDLE_DIR/$b"
    fi
  done
}

cmd_stopall(){
  local b
  for b in $(docker ps -q --filter label=studentctl=box); do
    docker stop "$b" >/dev/null
  done
  echo "$(date -Is) stopall: done" >> "$LOG"
  echo "all boxes stopped"
}

cmd_disk(){
  {
    date -Is
    docker system df
    docker ps -as --filter label=studentctl=box --format '{{.Names}} {{.Size}}'
  } >> "$LOG"
  echo "disk report appended to $LOG"
}

case "${1:-}" in
  create)  cmd_create  "${2:-}" ;;
  start)   cmd_start   "${2:-}" ;;
  stop)    cmd_stop    "${2:-}" ;;
  enter)   cmd_enter ;;
  reset)   cmd_reset   "${2:-}" ;;
  remove)  cmd_remove  "${2:-}" ;;
  status)  cmd_status  "${2:-}" ;;
  list)    cmd_list ;;
  autostop) cmd_autostop ;;
  stopall) cmd_stopall ;;
  disk)    cmd_disk ;;
  *)
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
