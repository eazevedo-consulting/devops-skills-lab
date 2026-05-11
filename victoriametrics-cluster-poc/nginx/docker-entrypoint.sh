#!/bin/sh
# docker-entrypoint.sh
#
# Strategy:
#   1. If the real Let's Encrypt cert is not yet available, generate a temporary
#      self-signed cert in /tmp (always writable) and symlink into
#      /etc/letsencrypt/live/<domain>/ so nginx can start without error.
#   2. Start nginx in the background.
#   3. Poll until the real cert appears (certbot wrote cert.pem alongside
#      fullchain.pem and privkey.pem).
#   4. Remove the dummy symlinks and reload nginx gracefully.
#   5. Wait on nginx PID to keep the container alive.

set -e

DOMAIN="monitor-poc.eazevedo.online"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
FULLCHAIN="${CERT_DIR}/fullchain.pem"
PRIVKEY="${CERT_DIR}/privkey.pem"

# /tmp is always writable regardless of volume mount options
DUMMY_DIR="/tmp/nginx-dummy-cert/${DOMAIN}"

# ── Step 1: Ensure nginx can start ──────────────────────────────────────────
if [ ! -s "${FULLCHAIN}" ] || [ ! -s "${PRIVKEY}" ]; then
    echo "[entrypoint] Real cert not found — generating temporary self-signed cert in /tmp..."

    mkdir -p "${DUMMY_DIR}"
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout "${DUMMY_DIR}/privkey.pem" \
        -out    "${DUMMY_DIR}/fullchain.pem" \
        -subj   "/CN=${DOMAIN}" \
        2>/dev/null

    # Create the cert dir inside the mounted letsencrypt volume (rw)
    mkdir -p "${CERT_DIR}"

    # Symlink to the tmp dummy so nginx finds the expected paths
    ln -sf "${DUMMY_DIR}/fullchain.pem" "${FULLCHAIN}"
    ln -sf "${DUMMY_DIR}/privkey.pem"   "${PRIVKEY}"

    USING_DUMMY=true
else
    echo "[entrypoint] Real cert found — starting normally."
    USING_DUMMY=false
fi

# ── Step 2: Start nginx in background ───────────────────────────────────────
echo "[entrypoint] Starting nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

# ── Steps 3 & 4: Wait for real cert then reload ─────────────────────────────
if [ "${USING_DUMMY}" = "true" ]; then
    echo "[entrypoint] Waiting for certbot to issue the real certificate..."
    while true; do
        sleep 10
        # certbot writes cert.pem, chain.pem, fullchain.pem, privkey.pem
        # We check cert.pem as the signal that certbot completed successfully
        if [ -f "${CERT_DIR}/cert.pem" ]; then
            # Verify fullchain and privkey are real files (not our dummy symlinks)
            CHAIN_TARGET=$(readlink -f "${FULLCHAIN}" 2>/dev/null || echo "")
            if ! echo "${CHAIN_TARGET}" | grep -q "${DUMMY_DIR}"; then
                echo "[entrypoint] Real cert already in place. Skipping symlink removal."
            else
                echo "[entrypoint] Real cert detected — removing dummy symlinks..."
                rm -f "${FULLCHAIN}" "${PRIVKEY}"
                # certbot already wrote the real fullchain.pem and privkey.pem
            fi
            echo "[entrypoint] Reloading nginx with valid certificate..."
            nginx -s reload
            echo "[entrypoint] nginx reloaded successfully."
            break
        fi
    done
fi

# ── Step 5: Keep container alive ────────────────────────────────────────────
wait "${NGINX_PID}"
