#!/bin/bash
# classroom.sh — teacher controls for the CTF contest
#   start   : bring CTFd up (contest accessible)
#   stop    : take CTFd down (contest closed)
#   status  : show container state
#   backup  : snapshot pristine DB (run once AFTER setup, BEFORE first class)
#   reset   : restore DB snapshot (wipes teams/solves between classrooms)
set -euo pipefail
cd "$(dirname "$0")"

cmd="${1:-}"
case "$cmd" in
  start)
    docker compose up -d
    echo "CTF is UP  -> http://<server-ip>:8000"
    ;;
  stop)
    docker compose stop ctfd
    echo "CTF is DOWN"
    ;;
  status)
    docker compose ps
    ;;
  backup)
    mkdir -p backups
    docker compose exec -T db sh -c \
      'exec mysqldump -uroot -p"$MARIADB_ROOT_PASSWORD" ctfd' \
      | gzip > backups/ctfd-pristine.sql.gz
    echo "snapshot saved: backups/ctfd-pristine.sql.gz"
    ;;
  reset)
    if [ ! -f backups/ctfd-pristine.sql.gz ]; then
      echo "no snapshot found — run './classroom.sh backup' first" >&2
      exit 1
    fi
    docker compose stop ctfd
    gunzip -c backups/ctfd-pristine.sql.gz | \
      docker compose exec -T db sh -c \
        'exec mysql -uroot -p"$MARIADB_ROOT_PASSWORD" ctfd'
    docker compose start ctfd
    echo "CTF reset to pristine state (all teams/solves wiped)"
    ;;
  *)
    echo "usage: $0 {start|stop|status|backup|reset}"
    exit 1
    ;;
esac
