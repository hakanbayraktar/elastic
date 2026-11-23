#!/usr/bin/env bash
set -euo pipefail

mkdir -p /certs/ca /certs/elasticsearch /certs/kibana /certs/logstash /certs/beats

# 1. Dahili Elastic CA ve Bileşen Sertifikaları
if [ ! -f /certs/ca/ca.crt ]; then
  echo "--> [Setup] Root CA oluşturuluyor..."
  bin/elasticsearch-certutil ca --silent --pem -out /certs/ca.zip
  unzip -q /certs/ca.zip -d /certs/
  rm /certs/ca.zip
fi

if [ ! -f /certs/elasticsearch/elasticsearch.crt ]; then
  echo "--> [Setup] instances.yml hazırlanıyor..."
  cat <<EOF > /certs/instances.yml
instances:
  - name: elasticsearch
    dns:
      - elasticsearch
      - ${ELASTIC_FQDN:-student101-elastic.devopsatolyesi.com}
      - localhost
    ip:
      - 127.0.0.1
  - name: kibana
    dns:
      - kibana
      - ${KIBANA_FQDN:-student101-kibana.devopsatolyesi.com}
      - localhost
    ip:
      - 127.0.0.1
  - name: logstash
    dns:
      - logstash
      - ${LOGSTASH_FQDN:-student101-logstash.devopsatolyesi.com}
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
  echo "--> [Setup] Node ve istemci sertifikaları üretiliyor..."
  bin/elasticsearch-certutil cert --silent --pem --in /certs/instances.yml --ca-cert /certs/ca/ca.crt --ca-key /certs/ca/ca.key -out /certs/bundle.zip
  unzip -q -o /certs/bundle.zip -d /certs/
  rm /certs/bundle.zip

fi

# PKCS#8 dönüşümü ve Nginx geçici sertifikası openssl ister; Elasticsearch 9.x imajında
# openssl bulunmadığı için bu adımlar scripts/setup-tls-convert.sh ile Logstash imajında yapılır.
echo "--> [Setup] Sertifika üretimi tamamlandı (dönüşüm: setup-tls-convert)."
