#!/usr/bin/env bash
# ==============================================================================
# Node 2: Logstash, Kibana and Nginx Gateway Setup
# ==============================================================================
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "Bu betik root (sudo) olarak çalıştırılmalıdır." 
   exit 1
fi

ES_HOST="${1:-192.168.1.10}"

echo "0. Elastic GPG Anahtarı ve Deposu Ekleniyor (temiz Ubuntu'da paketler varsayılan depoda yok)..."
apt-get update && apt-get install -y wget curl gnupg apt-transport-https
mkdir -p /etc/apt/keyrings
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /etc/apt/keyrings/elasticsearch-keyring.gpg --yes
echo "deb [signed-by=/etc/apt/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/9.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-9.x.list

echo "1. Logstash, Kibana ve Nginx Kuruluyor..."
apt-get update && apt-get install -y logstash=1:9.5.5-1 kibana=9.5.5 nginx certbot python3-certbot-nginx
apt-mark hold logstash kibana

echo "1b. Sertifikalar Yerleştiriliyor (Node 1'den scp ile /tmp/elk-certs-bundle'a kopyalandı)..."
BUNDLE=/tmp/elk-certs-bundle
[ -f "${BUNDLE}/ca/ca.crt" ] || { echo "HATA: ${BUNDLE}/ca/ca.crt yok; README'deki scp adımını uygulayın."; exit 1; }
for svc in kibana logstash; do
  mkdir -p "/etc/${svc}/certs"
  cp -r "${BUNDLE}/ca" "${BUNDLE}/node2-kibana-logstash" "/etc/${svc}/certs/"
done

echo "2. Kibana TLS Yapılandırılıyor..."
cat <<EOF > /etc/kibana/kibana.yml
server.port: 5601
server.host: "0.0.0.0"
elasticsearch.hosts: ["https://${ES_HOST}:9200"]
# Kibana 8+ 'elastic' süper kullanıcısını reddeder; parolası Node 1'de atanan kibana_system kullanılır
elasticsearch.username: "kibana_system"
elasticsearch.password: "DevOps2026!"
elasticsearch.ssl.certificateAuthorities: [ "/etc/kibana/certs/ca/ca.crt" ]

server.ssl.enabled: true
server.ssl.certificate: /etc/kibana/certs/node2-kibana-logstash/node2-kibana-logstash.crt
server.ssl.key: /etc/kibana/certs/node2-kibana-logstash/node2-kibana-logstash.key
EOF

chown -R kibana:kibana /etc/kibana

echo "3. Logstash SSL Pipeline Yapılandırılıyor..."
mkdir -p /etc/logstash/certs
# Beats girdisi PKCS#8 anahtar ister; certutil PKCS#1 üretir
openssl pkcs8 -in /etc/logstash/certs/node2-kibana-logstash/node2-kibana-logstash.key -topk8 -nocrypt -out /etc/logstash/certs/logstash.pk8

cat <<EOF > /etc/logstash/conf.d/devsecops-pipeline.conf
input {
  beats {
    port => 5044
    # Logstash 9.x: ssl kaldırıldı -> ssl_enabled
    ssl_enabled => true
    ssl_certificate => "/etc/logstash/certs/node2-kibana-logstash/node2-kibana-logstash.crt"
    ssl_key => "/etc/logstash/certs/logstash.pk8"
    ssl_certificate_authorities => ["/etc/logstash/certs/ca/ca.crt"]
    ssl_client_authentication => "optional"
  }
}

output {
  elasticsearch {
    hosts => ["https://${ES_HOST}:9200"]
    # Logstash 9.x: ssl ve cacert kaldırıldı
    ssl_enabled => true
    ssl_certificate_authorities => ["/etc/logstash/certs/ca/ca.crt"]
    user => "elastic"
    password => "DevOps2026!"
    index => "devsecops-baremetal-%{+YYYY.MM.dd}"
  }
}
EOF

chown -R logstash:logstash /etc/logstash

echo "4. Servisler Başlatılıyor..."
systemctl daemon-reload
systemctl enable --now kibana logstash nginx

echo "✅ Node 2 kurulumu tamamlandı. Kibana: Port 5601 HTTPS, Logstash: Port 5044 SSL."
