#!/usr/bin/env bash
# ==============================================================================
# FastAPI ELK: Doğrulama ve Test Scripti (verify.sh)
# ==============================================================================
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

SUCCESS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

check_pass() { echo -e "  [${GREEN}PASS${NC}] $1"; ((SUCCESS_COUNT+=1)) || true; }
check_warn() { echo -e "  [${YELLOW}WARN${NC}] $1"; ((WARN_COUNT+=1)) || true; }
check_fail() { echo -e "  [${RED}FAIL${NC}] $1"; ((FAIL_COUNT+=1)) || true; }

ELASTIC_URL="${ELASTIC_URL:-http://localhost:9200}"
ELASTIC_USER="${ELASTIC_USER:-elastic}"
ELASTIC_PASSWORD="${ELASTIC_PASSWORD:-DevOps2026!}"
API_URL="${API_URL:-http://localhost:19002}"
LOGSTASH_HOST="${LOGSTASH_HOST:-127.0.0.1}"
LOGSTASH_PORT="${LOGSTASH_PORT:-5010}"

echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}🔍 FastAPI ELK: FastAPI ELK Loglama ve Error Monitoring Doğrulaması${NC}"
echo -e "${BLUE}================================================================${NC}\n"

# 1. Elasticsearch Bağlantısı
echo -e "${YELLOW}1. Elasticsearch 9.x Bağlantı Kontrolü:${NC}"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" >/dev/null 2>&1; then
    STATUS=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    check_pass "Elasticsearch erişilebilir (Cluster Durumu: $STATUS)"
else
    check_fail "Elasticsearch (${ELASTIC_URL}) erişilemiyor! Lütfen LAB-01 cluster'ı başlatın."
fi

# 2. Logstash Pipeline Kontrolü
# Not: docker-proxy portu, Logstash hazır olmasa bile bağlantıyı kabul eder; bu yüzden
# port testi yerine Logstash API'sinin gerçek olay sayaçlarına bakılır.
echo -e "\n${YELLOW}2. Logstash Pipeline Kontrolü (logstash-app2):${NC}"
ls_counts() {
    LS_STATS=$(docker exec logstash-app2 curl -s localhost:9600/_node/stats/pipelines/main 2>/dev/null || true)
    LS_IN=$(echo "$LS_STATS" | jq -r '.pipelines.main.events.in // 0' 2>/dev/null || echo 0)
    LS_OUT=$(echo "$LS_STATS" | jq -r '.pipelines.main.events.out // 0' 2>/dev/null || echo 0)
}
ls_counts
# Yoldaki (henüz gönderilmemiş) olaylar için en fazla 10 sn bekle
for _ in 1 2 3 4 5; do
    [ -n "$LS_STATS" ] && [ "${LS_IN:-0}" -eq "${LS_OUT:-0}" ] && break
    sleep 2; ls_counts
done
if [ -z "$LS_STATS" ]; then
    check_fail "Logstash API'sine ulaşılamadı (logstash-app2 çalışıyor mu?)"
elif [ "${LS_OUT:-0}" -eq 0 ]; then
    check_fail "Logstash pipeline henüz olay iletmedi (giren: ${LS_IN}, çıkan: ${LS_OUT})"
elif [ "${LS_IN}" -ne "${LS_OUT}" ]; then
    check_fail "Logstash olay düşürüyor: giren ${LS_IN}, çıkan ${LS_OUT} (docker logs logstash-app2 | grep 'Event was dropped')"
else
    check_pass "Logstash pipeline 'main' kayıpsız çalışıyor (giren: ${LS_IN}, çıkan: ${LS_OUT})"
fi

# 3. FastAPI Servisi Sağlık Kontrolü (Port 19002)
echo -e "\n${YELLOW}3. FastAPI Mikroservisi (Port 19002 - App2):${NC}"
if curl -s -k "${API_URL}/api/v1/health" >/dev/null 2>&1; then
    HEALTH_RESP=$(curl -s -k "${API_URL}/api/v1/health")
    check_pass "FastAPI servisi çalışıyor ($HEALTH_RESP)"
else
    check_fail "FastAPI (${API_URL}) yanıt vermiyor. 'docker compose up -d' ile servisi başlatın."
fi

# 4. Elasticsearch 'logs-fastapi-*' Data Stream ve Doküman Kontrolü
echo -e "\n${YELLOW}4. Elasticsearch Data Stream ve Doküman Kontrolü:${NC}"
INDICES=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cat/indices/logs-fastapi-*?h=index,docs.count" 2>/dev/null || true)

if [ -n "$INDICES" ]; then
    check_pass "'logs-fastapi-*' data stream / index mevcut:"
    echo "$INDICES" | while read -r line; do
        echo -e "      -> $line"
    done

    # Toplam doküman sayısı kontrolü
    TOTAL_DOCS=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/logs-fastapi-*/_count" 2>/dev/null | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo 0)
    if [ "${TOTAL_DOCS:-0}" -gt 0 ]; then
        check_pass "Toplam kaydedilmiş log sayısı: ${TOTAL_DOCS}"
    else
        check_fail "index'te doküman yok. 'python3 scripts/simulate-traffic.py' çalıştırın."
    fi
else
    check_fail "'logs-fastapi-*' data stream'i yok: uygulama logları Logstash üzerinden Elasticsearch'e ulaşmamış."
fi

# 5. Hata Logları ve Stack Trace İncelemesi
echo -e "\n${YELLOW}5. Hata Seviyesi (ERROR) ve Stack Trace Indexleme Kontrolü:${NC}"
ERROR_COUNT=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" \
    -H "Content-Type: application/json" \
    -X POST "${ELASTIC_URL}/logs-fastapi-*/_count" \
    -d '{"query":{"term":{"log.level":"ERROR"}}}' 2>/dev/null | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo 0)

if [ "${ERROR_COUNT:-0}" -gt 0 ]; then
    check_pass "İndekslenmiş ERROR log adedi: ${ERROR_COUNT}"
    
    # Stack trace kontrolü
    HAS_TRACE=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" \
        -H "Content-Type: application/json" \
        -X POST "${ELASTIC_URL}/logs-fastapi-*/_search" \
        -d '{"query":{"exists":{"field":"error.stack_trace"}},"size":1}' 2>/dev/null | grep -o '"total":{"value":[0-9]*' | cut -d':' -f3 || echo 0)
    
    if [ "${HAS_TRACE:-0}" -gt 0 ]; then
        check_pass "Python Exception Stack Trace başarıyla yakalanmış ve ayrıştırılmış"
    else
        check_fail "Stack trace alanı tespit edilemedi."
    fi
else
    check_fail "ERROR logu yok. README Adım 5'teki hata isteklerini veya 'python3 scripts/simulate-traffic.py' çalıştırın."
fi

# 6. ES|QL Sorgulama Doğrulaması
echo -e "\n${YELLOW}6. ES|QL Hata Analitiği Sorgusu:${NC}"
ESQL_PAYLOAD='{"query":"FROM logs-fastapi-* | WHERE log.level == \"ERROR\" | STATS cnt = count() BY error.class | LIMIT 5"}'
ESQL_RESP=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" \
    -H "Content-Type: application/json" \
    -X POST "${ELASTIC_URL}/_query" \
    -d "$ESQL_PAYLOAD" 2>/dev/null || true)

if echo "$ESQL_RESP" | grep -q "values"; then
    check_pass "ES|QL sorgusu başarıyla çalıştı ve hata sınıflarını grupladı"
else
    check_fail "ES|QL sorgusu veri döndürmedi"
fi

# Özet Raporu
echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}📋 FastAPI ELK DOĞRULAMA ÖZETİ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo -e "  ${GREEN}Başarılı Testler:${NC} $SUCCESS_COUNT"
echo -e "  ${YELLOW}Uyarılar / İpuçları:${NC} $WARN_COUNT"
echo -e "  ${RED}Kritik Hatalar:${NC} $FAIL_COUNT\n"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}🎉 TEBRİKLER! FastAPI ELK FastAPI ELK Error Monitoring altyapısı eksiksiz çalışıyor.${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  Bazı kontroller başarısız oldu. Lütfen yukarıdaki adımları kontrol edin.${NC}\n"
    exit 1
fi
