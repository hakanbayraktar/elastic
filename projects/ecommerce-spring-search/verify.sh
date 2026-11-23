#!/usr/bin/env bash
# ==============================================================================
# NovaShop: Doğrulama ve Test Scripti (verify.sh)
# NovaShop E-Commerce Arama Servisi ve Şema Doğrulaması
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
NOVASHOP_URL="${NOVASHOP_URL:-http://localhost:8080}"

echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}🔍 NovaShop: NovaShop E-Ticaret Arama Servisi Doğrulaması${NC}"
echo -e "${BLUE}================================================================${NC}\n"

# 1. Elasticsearch Bağlantısı
echo -e "${YELLOW}1. Elasticsearch 9.x Bağlantı Kontrolü:${NC}"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" >/dev/null 2>&1; then
    STATUS=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    check_pass "Elasticsearch erişilebilir (Cluster Durumu: $STATUS)"
else
    check_fail "Elasticsearch (${ELASTIC_URL}) erişilemiyor! Lütfen LAB-01 cluster'ı başlatın."
fi

# 2. Ürün ve Müşteri Indexleri
echo -e "\n${YELLOW}2. NovaShop Indexleri ve Veri Kontrolü:${NC}"
for IDX in "ecommerce-products-v1" "ecommerce-customers-v1" "ecommerce-orders-v1"; do
    if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" -I "${ELASTIC_URL}/${IDX}" | grep -q "200 OK"; then
        CNT=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/${IDX}/_count" 2>/dev/null | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo 0)
        check_pass "'${IDX}' index'i mevcut (Doküman: ${CNT})"
    else
        check_fail "'${IDX}' index'i bulunamadı! 'python3 scripts/load_ecommerce_data.py' çalıştırın."
    fi
done

# 3. Relevance & Boosting Arama Testi
echo -e "\n${YELLOW}3. Relevance & Field Boosting Arama Testi:${NC}"
SEARCH_PAYLOAD='{"query":{"multi_match":{"query":"kulaklik","fields":["name^3","description"]}},"size":1}'
SEARCH_RESP=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" -H "Content-Type: application/json" -X POST "${ELASTIC_URL}/ecommerce-products-v1/_search" -d "$SEARCH_PAYLOAD" 2>/dev/null || true)

if echo "$SEARCH_RESP" | grep -q '"hits"'; then
    check_pass "Ürün araması multi_match ve boosting ile başarıyla çalıştı"
else
    check_fail "Arama sorgusu sonuç döndürmedi"
fi

# 4. Spring Boot NovaShop REST Servis Kontrolü (Port 8080)
echo -e "\n${YELLOW}4. NovaShop Canlı REST Servisi (Port 8080):${NC}"
if curl -s -k "${NOVASHOP_URL}/actuator/health" >/dev/null 2>&1 || curl -s -k "${NOVASHOP_URL}/api/products/search?q=test" >/dev/null 2>&1; then
    check_pass "NovaShop Spring Boot servisi port 8080 üzerinde çalışıyor"
else
    check_fail "NovaShop servisi port 8080 dinlemiyor. './run-novashop.sh' ile başlatabilirsiniz."
fi

# 5. NovaShop Kibana Dashboard Kontrolü
KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
echo -e "\n${YELLOW}5. NovaShop Kibana Dashboard Kontrolü:${NC}"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${KIBANA_URL}/api/saved_objects/dashboard/novashop-ecommerce-analytics" 2>/dev/null | grep -q '"attributes"'; then
    check_pass "NovaShop Satış Analitiği Dashboard'u ('novashop-ecommerce-analytics') Kibana üzerinde aktif"
else
    check_fail "Dashboard henüz yüklenmemiş. 'python3 scripts/provision_dashboard.py' çalıştırın."
fi

# 6. Annotation Groups Olayları (novashop-events) Kontrolü (Opsiyonel)
echo -e "\n${YELLOW}6. Annotation Groups Olayları (novashop-events) Kontrolü:${NC}"
if curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" -I "${ELASTIC_URL}/novashop-events" 2>/dev/null | grep -q "200 OK"; then
    EVT_CNT=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTIC_URL}/novashop-events/_count" 2>/dev/null | grep -o '"count":[0-9]*' | cut -d':' -f2 || echo 0)
    check_pass "'novashop-events' index'i mevcut ve olaylar yüklü (Olay sayısı: ${EVT_CNT})"
else
    check_warn "'novashop-events' index'i henüz oluşturulmamış (Opsiyonel). 'python3 scripts/seed_annotation_events.py' çalıştırabilirsiniz."
fi

# Özet
echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE}📋 NovaShop DOĞRULAMA ÖZETİ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo -e "  ${GREEN}Başarılı Testler:${NC} $SUCCESS_COUNT"
echo -e "  ${YELLOW}Uyarılar:${NC} $WARN_COUNT"
echo -e "  ${RED}Hatalar:${NC} $FAIL_COUNT\n"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}🎉 TEBRİKLER! NovaShop NovaShop E-Commerce Arama doğrulaması başarılı.${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  Bazı kontroller başarısız oldu. Lütfen yukarıdaki adımları kontrol edin.${NC}\n"
    exit 1
fi
