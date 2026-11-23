#!/usr/bin/env bash
# ==============================================================================
# ELK DevSecOps TLS projesinin YALNIZCA kendi kaynaklarini siler:
#   - devsecops-* konteynerleri, es_data ve nginx_logs volume'lari (compose down -v)
#   - uretilen sertifikalar: certs/ ve nginx/certs/*.pem, nginx/certbot-challenge/
# Dokunmaz: .env (sizin kopyaniz), imajlar, baska compose projeleri, host servisleri.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    source .env
fi
STACK_VERSION="${STACK_VERSION:-9.5.5}"

echo "--> Konteynerler ve volume'lar kaldiriliyor (yalniz bu compose projesi)..."
docker compose down -v --remove-orphans

# Sertifikalar konteyner icinde uid 1000 sahipligiyle yazildi; host kullanicisi uid 1000
# degilse rm reddedilir. Silme, zaten indirilmis Elasticsearch imajinda root olarak yapilir.
if [[ -d certs || -n "$(ls nginx/certs/*.pem 2>/dev/null)" || -d nginx/certbot-challenge ]]; then
    echo "--> Uretilen sertifikalar siliniyor (certs/, nginx/certs/*.pem)..."
    docker run --rm -u 0:0 -v "${SCRIPT_DIR}:/work" --entrypoint bash \
        "docker.elastic.co/elasticsearch/elasticsearch:${STACK_VERSION}" \
        -c 'rm -rf /work/certs /work/nginx/certbot-challenge; rm -f /work/nginx/certs/*.pem; rm -rf /work/nginx/certs/live /work/nginx/certs/archive /work/nginx/certs/renewal /work/nginx/certs/accounts'
fi

echo "[SONUC] Temizlik tamamlandi. .env ve Docker imajlari korundu."
