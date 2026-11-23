#!/usr/bin/env bash
# ==============================================================================
# NovaCommerce: Doğrulama ve Test Scripti (verify.sh)
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
API_URL="${API_URL:-http://localhost:19001}"

echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}🔍 NovaCommerce: E-Ticaret Arama ve FastAPI Servisi Doğrulaması${NC}"
echo -e "${BLUE}================================================================${NC}\n"

# 1. Elasticsearch Bağlantısı
echo -e "${YELLOW}1. Elasticsearch 9.x Bağlantı Kontrolü:${NC}"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" >/dev/null 2>&1; then
    STATUS=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    check_pass "Elasticsearch erişilebilir (Cluster Durumu: $STATUS)"
else
    check_fail "Elasticsearch (${ELASTIC_URL}) erişilemiyor! Lütfen LAB-01 cluster'ını başlatın."
fi

# 2. Index ve Mapping Kontrolü
echo -e "\n${YELLOW}2. Index ve Edge N-Gram Mapping Kontrolü:${NC}"
TARGET_INDEX="ecommerce_search_products"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" -I "${ELASTIC_URL}/${TARGET_INDEX}" | grep -q "200 OK"; then
    check_pass "'${TARGET_INDEX}' index'i mevcut"
    
    # Mapping kontrolü
    MAPPING_JSON=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/${TARGET_INDEX}/_mapping")
    if echo "$MAPPING_JSON" | grep -q "autocomplete_index"; then
        check_pass "Custom 'autocomplete_index' analyzer mapping'de tanımlı"
    else
        check_fail "'autocomplete_index' analyzer mapping'de bulunamadı!"
    fi
    
    DOC_COUNT=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/${TARGET_INDEX}/_count" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    if [ "${DOC_COUNT:-0}" -gt 0 ]; then
        check_pass "İndekslenmiş ürün sayısı: ${DOC_COUNT}"
    else
        check_fail "Index boş (0 ürün)"
    fi
else
    check_fail "'${TARGET_INDEX}' yok! (README Adım 2: python3 scripts/ingest_from_kibana_sample.py)"
fi

# 3. Port 19001 (App1) Servis Kontrolü
echo -e "\n${YELLOW}3. FastAPI Arama Servisi (Port 19001 - App1):${NC}"
if curl -s -k "${API_URL}/api/v1/health" >/dev/null 2>&1; then
    HEALTH=$(curl -s -k "${API_URL}/api/v1/health")
    check_pass "FastAPI servisi port 19001 üzerinde çalışıyor ($HEALTH)"
else
    check_fail "Port 19001 yanıt vermiyor. (README Adım 4: docker compose -f docker-compose.app1.yml up -d --build)"
fi

# 4. Çift Erişim ve DNS Kontrolü
echo -e "\n${YELLOW}4. Çift Erişim Modeli (DNS ve PIP Kontrolü):${NC}"
HOSTNAME_VAL=$(hostname)
STUDENT_ID=$(echo "$HOSTNAME_VAL" | grep -o "student[0-9]*" || echo "")

if [ -n "$STUDENT_ID" ]; then
    FQDN="${STUDENT_ID}-app1.devopsatolyesi.com"
    IP=$(dig +short "$FQDN" 2>/dev/null | head -n1 || true)
    if [ -n "$IP" ]; then
        check_pass "DNS Çözümlendi: $FQDN -> $IP"
    else
        check_warn "DNS Henüz Çözümlenemedi: $FQDN (Cloudflare senkronizasyonu bekleniyor olabilir)"
    fi
else
    check_warn "Hostname üzerinden student kimliği tespit edilemedi. 'studentXX-app1.devopsatolyesi.com' adresinizi kontrol edin."
fi

# Özet
echo -e "\n${BLUE}================================================================${NC}"
echo -e "Başarılı: ${GREEN}$SUCCESS_COUNT${NC} | Uyarı: ${YELLOW}$WARN_COUNT${NC} | Hata: ${RED}$FAIL_COUNT${NC}"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}Tebrikler! NovaCommerce doğrulama testleri başarıyla tamamlandı.${NC}"
else
    echo -e "${RED}Lütfen yukarıdaki hataları giderdikten sonra tekrar deneyin.${NC}"
fi
echo -e "${BLUE}================================================================${NC}\n"

[ "$FAIL_COUNT" -eq 0 ]
