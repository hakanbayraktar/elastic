#!/usr/bin/env bash
# Logstash imajında (openssl içerir) çalışır; setup-certs.sh'tan sonra.
set -euo pipefail

# 1. Logstash beats girdisi PKCS#8 anahtar ister; certutil PKCS#1 ("BEGIN RSA PRIVATE KEY") üretir.
if [ ! -f /certs/logstash/logstash.pk8 ]; then
  echo "--> [Convert] Logstash anahtarı PKCS#8 biçimine çevriliyor..."
  openssl pkcs8 -in /certs/logstash/logstash.key -topk8 -nocrypt -out /certs/logstash/logstash.pk8
fi

# 2. Nginx için geçici (self-signed) sertifika; Let's Encrypt sertifikası varsa dokunulmaz.
mkdir -p /nginx/certs
if [ ! -f /nginx/certs/fullchain.pem ]; then
  echo "--> [Convert] Nginx için geçici SSL sertifikası üretiliyor..."
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /nginx/certs/privkey.pem \
    -out /nginx/certs/fullchain.pem \
    -subj "/CN=${ELASTIC_FQDN}" \
    -addext "subjectAltName=DNS:${ELASTIC_FQDN},DNS:${KIBANA_FQDN},DNS:${LOGSTASH_FQDN},DNS:localhost,IP:127.0.0.1"
fi

# Elastic imajları uid 1000 ile çalışır
chown -R 1000:1000 /certs
find /certs -type d -exec chmod 755 {} +
find /certs -type f -exec chmod 644 {} +
echo "--> [Convert] Tamamlandı."
