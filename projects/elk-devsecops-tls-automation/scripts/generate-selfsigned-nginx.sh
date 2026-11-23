#!/usr/bin/env bash
# ==============================================================================
# Generate Self-Signed SSL Certificates for Nginx Reverse Proxy (Offline/Local)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load .env if present
if [[ -f "${PROJECT_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    source "${PROJECT_DIR}/.env"
fi

CERTS_DIR="${PROJECT_DIR}/nginx/certs"
mkdir -p "${CERTS_DIR}"

STUDENT_ID="${STUDENT_ID:-student101}"
DOMAIN_BASE="${DOMAIN_BASE:-devopsatolyesi.com}"
ELASTIC_FQDN="${ELASTIC_FQDN:-${STUDENT_ID}-elastic.${DOMAIN_BASE}}"
KIBANA_FQDN="${KIBANA_FQDN:-${STUDENT_ID}-kibana.${DOMAIN_BASE}}"
LOGSTASH_FQDN="${LOGSTASH_FQDN:-${STUDENT_ID}-logstash.${DOMAIN_BASE}}"

echo "🔐 Nginx için Self-Signed SSL sertifikası üretiliyor..."
echo "   Domainler: ${ELASTIC_FQDN}, ${KIBANA_FQDN}, ${LOGSTASH_FQDN}, localhost"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "${CERTS_DIR}/privkey.pem" \
  -out "${CERTS_DIR}/fullchain.pem" \
  -subj "/C=TR/ST=Istanbul/L=DevOps/O=DevOpsAtolyesi/OU=ELK/CN=${ELASTIC_FQDN}" \
  -addext "subjectAltName=DNS:${ELASTIC_FQDN},DNS:${KIBANA_FQDN},DNS:${LOGSTASH_FQDN},DNS:localhost,IP:127.0.0.1"

echo "✅ Sertifikalar hazırlandı:"
echo "   - Private Key: ${CERTS_DIR}/privkey.pem"
echo "   - Certificate: ${CERTS_DIR}/fullchain.pem"
