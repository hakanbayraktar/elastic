#!/usr/bin/env bash
# ==============================================================================
# Initialize Let's Encrypt SSL Certificates with Certbot
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load .env
if [[ -f "${PROJECT_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    source "${PROJECT_DIR}/.env"
fi

STUDENT_ID="${STUDENT_ID:-student101}"
DOMAIN_BASE="${DOMAIN_BASE:-devopsatolyesi.com}"
ELASTIC_FQDN="${ELASTIC_FQDN:-${STUDENT_ID}-elastic.${DOMAIN_BASE}}"
KIBANA_FQDN="${KIBANA_FQDN:-${STUDENT_ID}-kibana.${DOMAIN_BASE}}"
EMAIL="${LETSENCRYPT_EMAIL:-admin@${DOMAIN_BASE}}"
STAGING="${LETSENCRYPT_STAGING:-0}"

# Logstash adi yok: 5044 Nginx'ten gecmez, Beats Logstash'in dahili CA sertifikasini dogrular.
# Bu sertifikayi yalnizca Nginx (Elasticsearch ve Kibana girisi) sunar.
DOMAINS=("-d" "${ELASTIC_FQDN}" "-d" "${KIBANA_FQDN}")

echo "======================================================================"
echo "🌐 Let's Encrypt SSL Sertifika Talebi Başlatılıyor"
echo "   Domainler: ${ELASTIC_FQDN}, ${KIBANA_FQDN}"
echo "   E-Posta:   ${EMAIL}"
echo "======================================================================"

# Determine staging flag
STAGING_FLAG=""
if [[ "${STAGING}" != "0" ]]; then
    STAGING_FLAG="--staging"
    echo "⚠️  UYARI: Let's Encrypt STAGING modunda çalışıyor (Limit aşımını önlemek için)."
fi

# Ensure directories exist
mkdir -p "${PROJECT_DIR}/nginx/certs"
mkdir -p "${PROJECT_DIR}/nginx/certbot-challenge"

# Run certbot via docker. Sertifika /etc/letsencrypt/live/<ilk-domain>/ altina yazilir;
# Nginx ise /etc/nginx/certs/fullchain.pem ve privkey.pem okur. Bu yuzden alinan sertifika
# ayni konteynerde (dosyalar root'a ait, host kullanicisi okuyamaz) ust dizine kopyalanir.
docker run --rm \
  -v "${PROJECT_DIR}/nginx/certbot-challenge:/var/www/certbot" \
  -v "${PROJECT_DIR}/nginx/certs:/etc/letsencrypt" \
  --entrypoint sh \
  certbot/certbot -c "certbot certonly --webroot --webroot-path=/var/www/certbot \
      ${STAGING_FLAG} --email '${EMAIL}' --agree-tos --no-eff-email --force-renewal \
      ${DOMAINS[*]} \
    && cp -L '/etc/letsencrypt/live/${ELASTIC_FQDN}/fullchain.pem' /etc/letsencrypt/fullchain.pem \
    && cp -L '/etc/letsencrypt/live/${ELASTIC_FQDN}/privkey.pem' /etc/letsencrypt/privkey.pem"

echo "✅ Let's Encrypt sertifikaları alındı ve nginx/certs/ altına kopyalandı."
echo "   Nginx'in yüklemesi için: docker compose exec nginx nginx -s reload"
