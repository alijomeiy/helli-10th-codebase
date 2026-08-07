#!/bin/sh
# Container entrypoint: ensure the management SSH keypair exists (persisted in
# the data volume), print the public key once, then hand off to the WSGI server.
set -e
mkdir -p /var/lib/studentctl
if [ ! -f /var/lib/studentctl/panel_key ]; then
    echo "[studentctl] generating management SSH keypair..."
    ssh-keygen -q -t ed25519 -N "" -f /var/lib/studentctl/panel_key -C studentctl-panel
    echo "=============================================================="
    echo " Put this on the LINUX PLAYGROUND box as the 'studentctl' user's"
    echo " authorized key (run ONCE on the playground box):"
    echo
    cat /var/lib/studentctl/panel_key.pub
    echo
    echo "   echo '<above key>' | sudo -u studentctl tee -a /home/studentctl/.ssh/authorized_keys"
    echo "=============================================================="
fi
exec "$@"
