#!/usr/bin/env bash
# ==============================================================================
# Node 1: Elasticsearch 9.x Installation and CA/Cert Generation
# ==============================================================================
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "Bu betik root (sudo) olarak çalıştırılmalıdır." 
   exit 1
fi

CERTS_DIR="/etc/elasticsearch/certs"
NODE1_IP="$(hostname -I | awk '{print $1}')"
# Diğer düğümlerin IP'leri sertifika SAN'ına yazılır: Beats Logstash'e, tarayıcı Kibana'ya
# IP ile bağlandığında hostname doğrulaması bu IP'leri sertifikada arar.
NODE2_IP="${1:?Kullanım: sudo bash setup-node1.sh <node2-ip> <node3-ip>}"
NODE3_IP="${2:?Kullanım: sudo bash setup-node1.sh <node2-ip> <node3-ip>}"
ELASTIC_PASSWORD="${ELASTIC_PASSWORD:-DevOps2026!}"
KIBANA_PASSWORD="${KIBANA_PASSWORD:-DevOps2026!}"

echo "1. Elastic GPG Anahtarı ve Deposu Ekleniyor..."
apt-get update && apt-get install -y wget curl gnupg unzip lsb-release apt-transport-https

mkdir -p /etc/apt/keyrings
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /etc/apt/keyrings/elasticsearch-keyring.gpg --yes
echo "deb [signed-by=/etc/apt/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/9.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-9.x.list

echo "2. Elasticsearch Kuruluyor..."
apt-get update && apt-get install -y elasticsearch=9.5.5
apt-mark hold elasticsearch

echo "3. Sertifikalar Üretiliyor..."
mkdir -p "${CERTS_DIR}"

cat <<EOF > /tmp/instances.yml
instances:
  - name: node1-elasticsearch
    dns:
      - node1-elasticsearch
      - localhost
    ip:
      - 127.0.0.1
      - ${NODE1_IP}
  - name: node2-kibana-logstash
    dns:
      - node2-kibana-logstash
      - localhost
    ip:
      - 127.0.0.1
      - ${NODE2_IP}
  - name: node3-beats
    dns:
      - node3-beats
      - localhost
    ip:
      - 127.0.0.1
      - ${NODE3_IP}
EOF

cd /usr/share/elasticsearch
# Betik ikinci kez çalıştırılırsa certutil var olan zip'in üzerine yazmayı reddeder
rm -f /tmp/ca.zip /tmp/bundle.zip
bin/elasticsearch-certutil ca --silent --pem -out /tmp/ca.zip
unzip -q -o /tmp/ca.zip -d "${CERTS_DIR}"
bin/elasticsearch-certutil cert --silent --pem --in /tmp/instances.yml --ca-cert "${CERTS_DIR}/ca/ca.crt" --ca-key "${CERTS_DIR}/ca/ca.key" -out /tmp/bundle.zip
unzip -q -o /tmp/bundle.zip -d "${CERTS_DIR}"

# Dağıtım için paketle. CA'nın ÖZEL anahtarı (ca.key) Node 1'de kalır; diğer düğümlere
# yalnızca ca.crt ve kendi sertifika/anahtarları gider.
rm -rf /tmp/elk-certs-bundle
mkdir -p /tmp/elk-certs-bundle/ca
cp "${CERTS_DIR}/ca/ca.crt" /tmp/elk-certs-bundle/ca/
cp -r "${CERTS_DIR}/node2-kibana-logstash" "${CERTS_DIR}/node3-beats" /tmp/elk-certs-bundle/
# Paket düğüm özel anahtarlarını içerir: herkese okunur bırakılmaz. Diğer düğümler scp ile
# sudo'yu çağıran kullanıcı olarak çeker; bu yüzden sahibi o kullanıcıdır, izni 700/600.
chown -R "${SUDO_USER:-root}:" /tmp/elk-certs-bundle
chmod -R u=rwX,go= /tmp/elk-certs-bundle

echo "4. elasticsearch.yml Yapılandırılıyor..."
cat <<EOF > /etc/elasticsearch/elasticsearch.yml
cluster.name: devsecops-cluster
node.name: node1-elasticsearch
network.host: 0.0.0.0
http.port: 9200
# Dosya baştan yazıldığı için paketin varsayılan yolları da yazılmalı; yoksa Elasticsearch
# /usr/share/elasticsearch/logs dizinine yazmaya çalışır ve AccessDeniedException ile açılmaz.
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

discovery.type: single-node

xpack.security.enabled: true
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.key: ${CERTS_DIR}/node1-elasticsearch/node1-elasticsearch.key
xpack.security.http.ssl.certificate: ${CERTS_DIR}/node1-elasticsearch/node1-elasticsearch.crt
xpack.security.http.ssl.certificate_authorities: ${CERTS_DIR}/ca/ca.crt

xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.key: ${CERTS_DIR}/node1-elasticsearch/node1-elasticsearch.key
xpack.security.transport.ssl.certificate: ${CERTS_DIR}/node1-elasticsearch/node1-elasticsearch.crt
xpack.security.transport.ssl.certificate_authorities: ${CERTS_DIR}/ca/ca.crt
EOF

# Paket kurulumundaki otomatik güvenlik yapılandırması keystore'a kendi SSL keystore
# parolalarını yazar. elasticsearch.yml'i yukarıda PEM sertifikalarla değiştirdiğimiz için
# bu girdiler artık karşılıksızdır ve kalırsa Elasticsearch açılmaz.
for key in xpack.security.http.ssl.keystore.secure_password \
           xpack.security.transport.ssl.keystore.secure_password \
           xpack.security.transport.ssl.truststore.secure_password; do
  /usr/share/elasticsearch/bin/elasticsearch-keystore remove "$key" 2>/dev/null || true
done

chown -R elasticsearch:elasticsearch /etc/elasticsearch

echo "5. Elasticsearch Servisi Başlatılıyor..."
systemctl daemon-reload
systemctl enable --now elasticsearch

echo "6. elastic ve kibana_system Parolaları Atanıyor..."
for _ in $(seq 1 40); do
  curl -s --cacert "${CERTS_DIR}/ca/ca.crt" "https://localhost:9200" -o /dev/null && break
  sleep 3
done
curl -s --cacert "${CERTS_DIR}/ca/ca.crt" "https://localhost:9200" -o /dev/null \
  || { echo "HATA: Elasticsearch 2 dakikada açılmadı: journalctl -u elasticsearch"; exit 1; }
# Paket kurulumunun rastgele ürettiği parola bilinmediği için önce yeni bir rastgele parola
# alınır (-a otomatik, -b onaysız, -s yalnızca parolayı yazdır), sonra API ile sabitlenir.
GENERATED=$(/usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic -a -b -s)
curl -sf --cacert "${CERTS_DIR}/ca/ca.crt" -u "elastic:${GENERATED}" -H 'Content-Type: application/json' \
  -X POST "https://localhost:9200/_security/user/elastic/_password" -d "{\"password\":\"${ELASTIC_PASSWORD}\"}"
# Kibana 8+ 'elastic' süper kullanıcısıyla bağlanmayı reddeder; kibana_system kullanılır.
curl -sf --cacert "${CERTS_DIR}/ca/ca.crt" -u "elastic:${ELASTIC_PASSWORD}" -H 'Content-Type: application/json' \
  -X POST "https://localhost:9200/_security/user/kibana_system/_password" -d "{\"password\":\"${KIBANA_PASSWORD}\"}"
echo

echo "✅ Node 1 kurulumu tamamlandı. Sertifikalar /tmp/elk-certs-bundle altında hazırlandı."
