# studentbox:1 — per-student Linux lab image.
# The student is root inside his box; podman (with a `docker` command shim)
# is preinstalled so each student can pull/run/deploy his own containers.
# Build (on the VM):  docker build -t studentbox:1 -f docker/studentbox.Dockerfile docker/
FROM ubuntu:latest

# --- same apt mirror + same trust config the VM itself uses:
# repo.abrha.net with /etc/apt/apt.conf.d/99-disable-ssl-verify
# (copied from the host, which relies on apt GPG signature verification)
RUN rm -f /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list && \
    printf '%s\n' \
      'deb https://repo.abrha.net/ubuntu resolute main restricted universe multiverse' \
      'deb https://repo.abrha.net/ubuntu resolute-updates main restricted universe multiverse' \
      'deb https://repo.abrha.net/ubuntu resolute-security main restricted universe multiverse' \
      'deb https://repo.abrha.net/ubuntu resolute-backports main restricted universe multiverse' \
      > /etc/apt/sources.list && \
    printf 'Acquire::https::Verify-Peer "false";\n' \
      > /etc/apt/apt.conf.d/99-disable-ssl-verify

ENV DEBIAN_FRONTEND=noninteractive TZ=Asia/Tehran
RUN ln -fs /usr/share/zoneinfo/$TZ /etc/localtime

# teaching tools + podman + the `docker` command shim (podman-docker)
RUN apt-get update && apt-get install -y --no-install-recommends \
        vim curl wget less file tree procps psmisc iproute2 cron sudo \
        ca-certificates tzdata bash-completion \
        podman podman-docker uidmap fuse-overlayfs passt slirp4netns \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# subuid/subgid ranges so rootless podman works for root and for the lab user
RUN echo 'root:100000:65536'  >> /etc/subuid && echo 'root:100000:65536'  >> /etc/subgid && \
    echo 'lab:200000:65536'   >> /etc/subuid && echo 'lab:200000:65536'   >> /etc/subgid

# the `lab` user — used by the users/su lessons
RUN useradd -m -s /bin/bash lab && echo 'lab:lab12345' | chpasswd

# podman defaults for running INSIDE a container: no systemd, file events,
# and silence the "Emulate Docker CLI" notice
RUN mkdir -p /etc/containers && printf '%s\n' \
      '[containers]' \
      'cgroup_manager = "cgroupfs"' \
      'events_logger = "file"' \
      > /etc/containers/containers.conf && \
    touch /etc/containers/nodocker

# PID 1: bring up cron, then idle (boxes are entered via `docker exec`)
COPY box-init /usr/local/bin/box-init
RUN chmod 755 /usr/local/bin/box-init && \
    printf '%s\n' \
      '== آزمایشگاه لینوکس شما ==' \
      'شما root این سیستم هستید.' \
      'دستور docker (podman) برای کشیدن و اجرای کانتینرها در دسترس است.' \
      '' > /etc/motd

CMD ["/usr/local/bin/box-init"]
