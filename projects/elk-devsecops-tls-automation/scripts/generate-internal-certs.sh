#!/usr/bin/env bash
# ==============================================================================
# Generate Internal Elastic Stack CA & Component Certificates (Zero-Trust mTLS)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -f "${PROJECT_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    source "${PROJECT_DIR}/.env"
fi

STACK_VERSION="${STACK_VERSION:-9.5.5}"
STUDENT_ID="${STUDENT_ID:-student101}"
DOMAIN_BASE="${DOMAIN_BASE:-devopsatolyesi.com}"
CERTS_DIR="${PROJECT_DIR}/certs"

mkdir -p "${CERTS_DIR}"

echo "======================================================================"
echo "🔐 Elastic Stack Dahili CA ve Sertifikaları Üretiliyor"
echo "   Sürüm: ${STACK_VERSION}"
echo "   Hedef Dizin: ${CERTS_DIR}"
echo "======================================================================"

# Prepare instances.yml for elasticsearch-certutil
cat <<EOF > "${CERTS_DIR}/instances.yml"
instances:
  - name: elasticsearch
    dns:
      - elasticsearch
      - ${STUDENT_ID}-elastic.${DOMAIN_BASE}
      - localhost
    ip:
      - 127.0.0.1
  - name: kibana
    dns:
      - kibana
      - ${STUDENT_ID}-kibana.${DOMAIN_BASE}
      - localhost
    ip:
      - 127.0.0.1
  - name: logstash
    dns:
      - logstash
      - ${STUDENT_ID}-logstash.${DOMAIN_BASE}
      - localhost
    ip:
      - 127.0.0.1
  - name: beats
    dns:
      - beats
      - localhost
    ip:
      - 127.0.0.1
EOF

# Run elasticsearch container to generate CA and certificates
docker run --rm \
  -v "${CERTS_DIR}:/certs" \
  -u 0:0 \
  "docker.elastic.co/elasticsearch/elasticsearch:${STACK_VERSION}" \
  bash -c "
    set -e
    cd /certs
    # certutil goreli -out/--in yollarini kendi ana dizinine (/usr/share/elasticsearch) gore
    # cozer; bu yuzden tum yollar mutlak verilir.
    CERTUTIL=/usr/share/elasticsearch/bin/elasticsearch-certutil
    if [ ! -f /certs/ca/ca.crt ]; then
      echo '--> Root CA oluşturuluyor...'
      \$CERTUTIL ca --silent --pem -out /certs/ca.zip
      unzip -q /certs/ca.zip -d /certs
      rm /certs/ca.zip
    fi

    echo '--> Node ve servis sertifikaları üretiliyor...'
    \$CERTUTIL cert --silent --pem --in /certs/instances.yml --ca-cert /certs/ca/ca.crt --ca-key /certs/ca/ca.key -out /certs/bundle.zip
    unzip -q -o /certs/bundle.zip -d /certs
    rm /certs/bundle.zip
    chown -R 1000:1000 /certs
    echo '--> Sertifika üretimi tamamlandı.'
  "

# Elasticsearch 9.x imajinda openssl yok; PKCS#8 donusumu Logstash imajinda (openssl var)
# root olarak yapilir. Host openssl'i kullanilmaz: dosyalar uid 1000'e ait oldugu icin
# host kullanicisi (uid 1000 degilse) certs/ altina yazamaz.
docker run --rm \
  -v "${CERTS_DIR}:/certs" \
  -u 0:0 \
  --entrypoint bash \
  "docker.elastic.co/logstash/logstash:${STACK_VERSION}" \
  -c "openssl pkcs8 -in /certs/logstash/logstash.key -topk8 -nocrypt -out /certs/logstash/logstash.pk8 \
      && chown -R 1000:1000 /certs \
      && find /certs -type d -exec chmod 755 {} + && find /certs -type f -exec chmod 644 {} + \
      && echo '--> Logstash anahtari PKCS#8 bicimine cevrildi.'"

echo "✅ Tüm dahili mTLS sertifikaları başarıyla üretildi:"
echo "   - CA:          ${CERTS_DIR}/ca/ca.crt"
echo "   - Elastic:     ${CERTS_DIR}/elasticsearch/"
echo "   - Kibana:      ${CERTS_DIR}/kibana/"
echo "   - Logstash:    ${CERTS_DIR}/logstash/"
echo "   - Beats:       ${CERTS_DIR}/beats/"
