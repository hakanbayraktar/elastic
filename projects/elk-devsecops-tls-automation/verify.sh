#!/usr/bin/env bash
# ==============================================================================
# Project: ELK DevSecOps Full TLS/SSL Automation Verification Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

check_pass() {
    echo -e "  [${GREEN}PASS${NC}] $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

check_fail() {
    echo -e "  [${RED}FAIL${NC}] $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

check_warn() {
    echo -e "  [${YELLOW}WARN${NC}] $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/.env"
fi

ELASTIC_PASSWORD="${ELASTIC_PASSWORD:-DevOps2026!}"
STUDENT_ID="${STUDENT_ID:-student101}"
DOMAIN_BASE="${DOMAIN_BASE:-devopsatolyesi.com}"
ELASTIC_FQDN="${ELASTIC_FQDN:-${STUDENT_ID}-elastic.${DOMAIN_BASE}}"
KIBANA_FQDN="${KIBANA_FQDN:-${STUDENT_ID}-kibana.${DOMAIN_BASE}}"

echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}🔍 ELK DevSecOps TLS/SSL Altyapı ve Güvenlik Doğrulaması${NC}"
echo -e "${BLUE}======================================================================${NC}\n"

# 1. Dahili Sertifikaların Varlığı
echo "1. Sertifika Dosyaları Kontrol Ediliyor..."
if [[ -f "${SCRIPT_DIR}/nginx/certs/fullchain.pem" && -f "${SCRIPT_DIR}/nginx/certs/privkey.pem" ]]; then
    check_pass "Nginx SSL sertifikaları mevcut (${SCRIPT_DIR}/nginx/certs/)"
    EXPIRY=$(openssl x509 -enddate -noout -in "${SCRIPT_DIR}/nginx/certs/fullchain.pem" | cut -d= -f2)
    check_pass "Nginx SSL Bitiş Tarihi: ${EXPIRY}"
else
    check_warn "Nginx sertifikaları henüz üretilmemiş. 'bash scripts/generate-selfsigned-nginx.sh' veya docker compose başlatın."
fi

# 2. Elasticsearch HTTPS Sağlık Durumu
echo "2. Elasticsearch HTTPS Erişilebilirliği Test Ediliyor..."
ES_HEALTH=$(curl -sf -k -u "elastic:${ELASTIC_PASSWORD}" "https://localhost:9200/_cluster/health" 2>/dev/null || true)
if [ -n "$ES_HEALTH" ]; then
    STATUS=$(echo "$ES_HEALTH" | grep -o '"status":"[^"]*' | cut -d'"' -f4 || echo "unknown")
    CLUSTER_NAME=$(echo "$ES_HEALTH" | grep -o '"cluster_name":"[^"]*' | cut -d'"' -f4 || echo "unknown")
    check_pass "Elasticsearch HTTPS gateway (9200) erişilebilir (Cluster: ${CLUSTER_NAME}, Durum: ${STATUS})"
else
    check_fail "Elasticsearch HTTPS (port 9200) yanıt vermiyor! Docker compose durumunu kontrol edin."
fi
# Dahili CA zinciri: -k OLMADAN, certs/ca/ca.crt ile doğrudan Elasticsearch (127.0.0.1:9201)
if curl -sf --cacert "${SCRIPT_DIR}/certs/ca/ca.crt" -u "elastic:${ELASTIC_PASSWORD}" "https://localhost:${ELASTIC_DIRECT_PORT:-9201}/" >/dev/null 2>&1; then
    check_pass "Elasticsearch sertifikası dahili CA ile doğrulandı (localhost:${ELASTIC_DIRECT_PORT:-9201})"
else
    check_fail "Dahili CA ile doğrulama başarısız (certs/ca/ca.crt, localhost:${ELASTIC_DIRECT_PORT:-9201})"
fi

# 3. Kibana HTTPS Yanıtı
echo "3. Kibana HTTPS Servisi Test Ediliyor..."
if curl -s -k -I "https://localhost:5601/login" | grep -E "HTTP/.* (200|302)" > /dev/null 2>&1; then
    check_pass "Kibana HTTPS (5601) aktif ve giriş sayfası yanıt veriyor."
else
    check_fail "Kibana HTTPS (port 5601) yanıt vermiyor: docker compose logs kibana"
fi

# 4. Logstash 5044 TLS el sıkışması (port açık olması yetmez; sertifika dahili CA ile doğrulanmalı)
echo "4. Logstash Beats TLS (5044) Portu Test Ediliyor..."
if openssl s_client -connect localhost:5044 -CAfile "${SCRIPT_DIR}/certs/ca/ca.crt" </dev/null 2>/dev/null \
     | grep -q "Verify return code: 0 (ok)"; then
    check_pass "Logstash 5044 TLS el sıkışması dahili CA ile doğrulandı."
else
    check_fail "Logstash 5044 TLS el sıkışması başarısız: docker compose logs logstash"
fi

# 5. Her Beat'in ve Logstash hattının verisi ayrı ayrı (biri çalışıp diğerleri çökmüşse yakalanır)
echo "5. Beats ve TLS Index Verileri Kontrol Ediliyor..."
es_direct() {
    curl -s --cacert "${SCRIPT_DIR}/certs/ca/ca.crt" -u "elastic:${ELASTIC_PASSWORD}" \
        -H 'Content-Type: application/json' "https://localhost:${ELASTIC_DIRECT_PORT:-9201}$1" "${@:2}"
}
for idx in devsecops metricbeat heartbeat packetbeat auditbeat; do
    COUNT=$(es_direct "/${idx}-*/_count" | jq -r '.count // 0' 2>/dev/null || echo 0)
    if [[ "${COUNT}" =~ ^[0-9]+$ && "${COUNT}" -gt 0 ]]; then
        check_pass "${idx}-* : ${COUNT} belge"
    else
        if [[ "${idx}" == "devsecops" ]]; then
            check_fail "devsecops-* boş: Filebeat -> Logstash (mTLS) hattı veri taşımıyor (gateway'e en az bir istek atın)"
        else
            check_fail "${idx}-* boş: docker compose logs ${idx}"
        fi
    fi
done

# 6. Heartbeat monitörleri: ES, Kibana ve Logstash TLS uçları son 2 dakikada 'up' mı?
echo "6. Heartbeat TLS Monitörleri Kontrol Ediliyor..."
for mon in es-tls-monitor kb-tls-monitor ls-tls-monitor; do
    LAST=$(es_direct "/heartbeat-*/_search?size=1&filter_path=hits.hits._source.monitor.status" \
        -d "{\"query\":{\"bool\":{\"filter\":[{\"term\":{\"monitor.id\":\"${mon}\"}},{\"range\":{\"@timestamp\":{\"gte\":\"now-2m\"}}}]}},\"sort\":[{\"@timestamp\":\"desc\"}]}" \
        | jq -r '.hits.hits[0]._source.monitor.status // "yok"' 2>/dev/null || echo yok)
    if [[ "${LAST}" == "up" ]]; then
        check_pass "${mon}: up"
    else
        check_fail "${mon}: ${LAST} (son 2 dakikada 'up' kaydı yok)"
    fi
done

echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}📋 DEVSECOPS TLS DOĞRULAMA ÖZETİ${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "  Başarılı : ${GREEN}${PASS_COUNT}${NC}"
echo -e "  Uyarı    : ${YELLOW}${WARN_COUNT}${NC}"
echo -e "  Hata     : ${RED}${FAIL_COUNT}${NC}"

if [[ ${FAIL_COUNT} -eq 0 ]]; then
    echo -e "\n${GREEN}🎉 TEBRİKLER! ELK DevSecOps TLS/SSL Altyapısı başarıyla doğrulandı.${NC}\n"
    exit 0
else
    echo -e "\n${RED}❌ BAZI KONTROLLER BAŞARISIZ OLDU. Lütfen logları inceleyin.${NC}\n"
    exit 1
fi
