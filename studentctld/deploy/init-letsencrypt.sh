#!/bin/bash
# init-letsencrypt.sh — one-time bootstrap to obtain a Let's Encrypt certificate.
#
# Prerequisites:
#   * A domain (e.g. panel.yourdomain.ir) with DNS A-record pointing to THIS server.
#   * Ports 80 + 443 open in any cloud firewall.
#
# Usage:
#   sudo DOMAIN=panel.yourdomain.ir EMAIL=you@example.com bash deploy/init-letsencrypt.sh
#
# It creates a temporary self-signed cert so nginx can start, requests the real
# cert via the HTTP-01 challenge, then leaves everything ready for `docker compose up -d`.
set -euo pipefail

DOMAIN="${DOMAIN:?set DOMAIN=panel.yourdomain.ir}"
EMAIL="${EMAIL:?set EMAIL=you@example.com}"
RSA_KEY_SIZE=4096
COMPOSE="docker compose"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WW="$(pwd)/certbot/www"
CONF="$(pwd)/certbot/conf"
mkdir -p "$WWW" "$CONF"

echo "==> 1/5  starting nginx with a temporary self-signed certificate"
if [ ! -e "$CONF/live/$DOMAIN/fullchain.pem" ]; then
    mkdir -p "$CONF/live/$DOMAIN"
    docker run --rm \
        -v "$CONF:/etc/letsencrypt" \
        --entrypoint openssl \
        certbot/certbot \
        req -x509 -nodes -newkey "rsa:$RSA_KEY_SIZE" -days 1 \
            -keyout "/etc/letsencrypt/live/$DOMAIN/privkey.pem" \
            -out    "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
            -subj "/CN=localhost" >/dev/null 2>&1
fi

$COMPOSE up -d nginx
sleep 3

echo "==> 2/5  deleting the temporary certificate"
docker run --rm \
    -v "$CONF:/etc/letsencrypt" \
    --entrypoint rm \
    certbot/certbot \
    -Rf "/etc/letsencrypt/live/$DOMAIN" \
          "/etc/letsencrypt/archive/$DOMAIN" \
          "/etc/letsencrypt/renewal/$DOMAIN.conf" >/dev/null 2>&1 || true

echo "==> 3/5  requesting the real certificate from Let's Encrypt"
docker run --rm \
    -v "$WWW:/var/www/certbot" \
    -v "$CONF:/etc/letsencrypt" \
    certbot/certbot \
    certonly --webroot -w /var/www/certbot \
        --email "$EMAIL" --agree-tos --no-eff-email --non-interactive \
        -d "$DOMAIN" --rsa-key-size "$RSA_KEY_SIZE"

echo "==> 4/5  starting all services"
$COMPOSE up -d

echo "==> 5/5  reloading nginx to pick up the real certificate"
$COMPOSE exec nginx nginx -s reload || true

echo
echo "Done. The panel is live at https://$DOMAIN/  (admin at /admin/login)"
