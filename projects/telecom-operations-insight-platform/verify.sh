#!/usr/bin/env bash
# ==============================================================================
# Capstone: Doğrulama ve Test Scripti (verify.sh)
# Telecom Capstone Bitirme Projesi Doğrulaması
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
DATA_STREAM="logs-telecom.capstone-prod"

echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}🔍 Capstone: Telecom Operations Capstone Projesi Doğrulaması${NC}"
echo -e "${BLUE}================================================================${NC}\n"

# 1. Elasticsearch Bağlantısı
echo -e "${YELLOW}1. Elasticsearch 9.x Bağlantı Kontrolü:${NC}"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" >/dev/null 2>&1; then
    STATUS=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    check_pass "Elasticsearch erişilebilir (Cluster Durumu: $STATUS)"
else
    check_fail "Elasticsearch (${ELASTIC_URL}) erişilemiyor! Lütfen LAB-01 cluster'ı başlatın."
fi

# 2. Capstone Pipeline Kontrolü
echo -e "\n${YELLOW}2. Capstone Ingest Pipeline Kontrolü:${NC}"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_ingest/pipeline/lab04-telecom-capstone-v1" | grep -q "lab04-telecom-capstone-v1"; then
    check_pass "Ingest pipeline 'lab04-telecom-capstone-v1' tanımlı"
else
    check_fail "Pipeline bulunamadı. 'python3 scripts/setup_capstone.py' çalıştırın."
fi

# 3. Capstone Data Stream Kontrolü
echo -e "\n${YELLOW}3. Capstone Data Stream Kontrolü (${DATA_STREAM}):${NC}"
DS_CHECK=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_data_stream/${DATA_STREAM}" 2>/dev/null || true)
if echo "$DS_CHECK" | grep -q "${DATA_STREAM}"; then
    check_pass "Data Stream '${DATA_STREAM}' mevcut"
    
    DOC_COUNT=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/${DATA_STREAM}/_count" 2>/dev/null | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo 0)
    if [ "${DOC_COUNT:-0}" -gt 0 ]; then
        check_pass "Data Stream içindeki doküman sayısı: ${DOC_COUNT}"
    else
        check_fail "Data Stream boş"
    fi
else
    check_fail "Data Stream '${DATA_STREAM}' yok. 'python3 scripts/load_capstone.py --scenario normal --requests 100' çalıştırın."
fi

# 4. Kibana Panosu ve Uyarı Kuralı
echo -e "\n${YELLOW}4. Kibana Panosu ve Uyarı Kuralı:${NC}"
KB_URL="${KIBANA_URL:-http://localhost:5601}"
kb_code() { curl -s -o /dev/null -w "%{http_code}" -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${KB_URL}$1"; }
if [ "$(kb_code /api/status)" = "200" ]; then
    check_pass "Kibana erişilebilir (${KB_URL})"
    if [ "$(kb_code /api/saved_objects/dashboard/telecom-operations-capstone)" = "200" ]; then
        check_pass "Pano 'telecom-operations-capstone' kurulu"
    else
        check_fail "Pano yok. 'python3 scripts/provision_capstone.py --dashboard-only' çalıştırın."
    fi
    if [ "$(kb_code /api/alerting/rule/telecom-capstone-error-rate)" = "200" ]; then
        check_pass "Uyarı kuralı 'telecom-capstone-error-rate' tanımlı (tetiklenme: python3 tests/verify_alert.py)"
    else
        check_warn "Uyarı kuralı kurulmamış (opsiyonel): python3 scripts/provision_capstone.py"
    fi
else
    check_fail "Kibana (${KB_URL}) yanıt vermiyor"
fi

# Özet
echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}📋 Capstone DOĞRULAMA ÖZETİ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo -e "  ${GREEN}Başarılı Testler:${NC} $SUCCESS_COUNT"
echo -e "  ${YELLOW}Uyarılar:${NC} $WARN_COUNT"
echo -e "  ${RED}Hatalar:${NC} $FAIL_COUNT\n"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}🎉 TEBRİKLER! Capstone Telecom Capstone ortam doğrulaması başarılı.${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  Bazı kontroller başarısız oldu. Lütfen yukarıdaki adımları kontrol edin.${NC}\n"
    exit 1
fi
