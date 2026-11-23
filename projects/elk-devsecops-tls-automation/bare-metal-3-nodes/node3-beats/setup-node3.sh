#!/usr/bin/env bash
# ==============================================================================
# Node 3: Install and Configure 5x Beats with TLS/SSL
# ==============================================================================
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "Bu betik root (sudo) olarak çalıştırılmalıdır." 
   exit 1
fi

ES_HOST="${1:-192.168.1.10}"
LS_HOST="${2:-192.168.1.11}"

echo "0. Elastic GPG Anahtarı ve Deposu Ekleniyor (temiz Ubuntu'da paketler varsayılan depoda yok)..."
apt-get update && apt-get install -y wget curl gnupg apt-transport-https
mkdir -p /etc/apt/keyrings
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /etc/apt/keyrings/elasticsearch-keyring.gpg --yes
echo "deb [signed-by=/etc/apt/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/9.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-9.x.list

echo "1. 5x Beats Kuruluyor (Filebeat, Metricbeat, Heartbeat, Packetbeat, Auditbeat)..."

apt-get update && apt-get install -y filebeat=9.5.5 metricbeat=9.5.5 heartbeat-elastic=9.5.5 packetbeat=9.5.5 auditbeat=9.5.5
apt-mark hold filebeat metricbeat heartbeat-elastic packetbeat auditbeat

echo "1b. Sertifikalar Yerleştiriliyor (Node 1'den scp ile /tmp/elk-certs-bundle'a kopyalandı)..."
BUNDLE=/tmp/elk-certs-bundle
[ -f "${BUNDLE}/ca/ca.crt" ] || { echo "HATA: ${BUNDLE}/ca/ca.crt yok; README'deki scp adımını uygulayın."; exit 1; }
mkdir -p /etc/beats/certs
cp -r "${BUNDLE}/ca" "${BUNDLE}/node3-beats" /etc/beats/certs/
chmod -R a+rX /etc/beats/certs

echo "2. Filebeat Yapılandırılıyor..."
cat <<EOF > /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: filestream
    id: system-logs
    paths:
      - /var/log/syslog
      - /var/log/auth.log

output.logstash:
  hosts: ["${LS_HOST}:5044"]
  ssl.enabled: true
  ssl.certificate_authorities: ["/etc/beats/certs/ca/ca.crt"]
  ssl.certificate: "/etc/beats/certs/node3-beats/node3-beats.crt"
  ssl.key: "/etc/beats/certs/node3-beats/node3-beats.key"
EOF

echo "3. Metricbeat Yapılandırılıyor..."
cat <<EOF > /etc/metricbeat/metricbeat.yml
metricbeat.modules:
  - module: system
    metricsets: ["cpu", "memory", "network", "process_summary"]
    period: 10s

output.elasticsearch:
  hosts: ["https://${ES_HOST}:9200"]
  ssl.enabled: true
  ssl.certificate_authorities: ["/etc/beats/certs/ca/ca.crt"]
  username: "elastic"
  password: "DevOps2026!"
EOF

echo "4. Heartbeat Yapılandırılıyor..."
# Paket ve servis adı heartbeat-elastic, config dizini ise /etc/heartbeat
cat <<EOF > /etc/heartbeat/heartbeat.yml
heartbeat.monitors:
  - type: http
    id: es-monitor
    # schedule zorunludur; yoksa heartbeat "missing required field ... schedule" ile çıkar
    schedule: '@every 10s'
    urls: ["https://${ES_HOST}:9200"]
    ssl.certificate_authorities: ["/etc/beats/certs/ca/ca.crt"]
    check.response.status: [200, 401]

output.elasticsearch:
  hosts: ["https://${ES_HOST}:9200"]
  ssl.enabled: true
  ssl.certificate_authorities: ["/etc/beats/certs/ca/ca.crt"]
  username: "elastic"
  password: "DevOps2026!"
EOF

echo "5. Auditbeat ve Packetbeat Yapılandırılıyor..."
cat <<EOF > /etc/auditbeat/auditbeat.yml
auditbeat.modules:
  - module: file_integrity
    paths:
      - /bin
      - /usr/bin

output.elasticsearch:
  hosts: ["https://${ES_HOST}:9200"]
  ssl.enabled: true
  ssl.certificate_authorities: ["/etc/beats/certs/ca/ca.crt"]
  username: "elastic"
  password: "DevOps2026!"
EOF

cat <<EOF > /etc/packetbeat/packetbeat.yml
packetbeat.interfaces.device: any
packetbeat.protocols:
  - type: dns
    ports: [53]

output.elasticsearch:
  hosts: ["https://${ES_HOST}:9200"]
  ssl.enabled: true
  ssl.certificate_authorities: ["/etc/beats/certs/ca/ca.crt"]
  username: "elastic"
  password: "DevOps2026!"
EOF

echo "6. Servisler Başlatılıyor..."
systemctl daemon-reload
systemctl enable --now filebeat metricbeat heartbeat-elastic packetbeat auditbeat

# Hatalı config'te Beat birkaç saniye içinde çıkar; enable --now bunu yakalamaz.
sleep 15
FAILED=""
for svc in filebeat metricbeat heartbeat-elastic packetbeat auditbeat; do
  systemctl is-active --quiet "$svc" || FAILED="${FAILED} ${svc}"
done
if [ -n "${FAILED}" ]; then
  echo "HATA: çalışmayan servis(ler):${FAILED}  ->  journalctl -u <servis> -n 20"
  exit 1
fi

echo "✅ Node 3 kurulumu tamamlandı. 5 Beat servisi çalışıyor."
