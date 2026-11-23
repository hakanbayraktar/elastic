#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}    E-Commerce Arama Servisi Başlatıcı                         ${NC}"
echo -e "${BLUE}================================================================${NC}"

export ELASTIC_USER="${ELASTIC_USER:-elastic}"
export ELASTIC_PASSWORD="${ELASTIC_PASSWORD:-DevOps2026!}"

# Elasticsearch Protokol ve URL Otomatik Tespiti (HTTP veya HTTPS/SSL)
if [[ -z "${ELASTICSEARCH_URL:-}" && -z "${ELASTIC_URL:-}" ]]; then
  if curl -s -k --connect-timeout 2 "http://127.0.0.1:9200/_cluster/health" >/dev/null 2>&1 || \
     curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" --connect-timeout 2 "http://127.0.0.1:9200/_cluster/health" >/dev/null 2>&1; then
    export ELASTICSEARCH_URL="http://127.0.0.1:9200"
  elif curl -s -k --connect-timeout 2 "https://127.0.0.1:9200/_cluster/health" >/dev/null 2>&1 || \
       curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" --connect-timeout 2 "https://127.0.0.1:9200/_cluster/health" >/dev/null 2>&1; then
    export ELASTICSEARCH_URL="https://127.0.0.1:9200"
  else
    export ELASTICSEARCH_URL="http://127.0.0.1:9200"
  fi
else
  export ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-${ELASTIC_URL:-http://127.0.0.1:9200}}"
fi
export ELASTIC_URL="$ELASTICSEARCH_URL"

# 1. Elasticsearch Kontrolü
echo -e "\n${YELLOW}1. Elasticsearch Bağlantısı Kontrol Ediliyor (${ELASTICSEARCH_URL})...${NC}"
if ! curl -k -fsS -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" "${ELASTICSEARCH_URL}/_cluster/health" >/dev/null 2>&1 && ! curl -k -fsS "${ELASTICSEARCH_URL}/_cluster/health" >/dev/null 2>&1; then
    echo -e "${RED}HATA: Elasticsearch (${ELASTICSEARCH_URL}) erişilemiyor!${NC}"
    echo -e "Lütfen önce LAB-01 veya LAB-01'deki Elasticsearch servisini başlatın."
    exit 1
fi
echo -e "${GREEN}✓ Elasticsearch bağlantısı aktif.${NC}"

# 2. Şema ve Ürün Verisinin Kontrolü / Yüklenmesi
echo -e "\n${YELLOW}2. E-Ticaret Ürün Kataloğu ve Şema Kontrol Ediliyor...${NC}"
INDEX_EXISTS=$(curl -k -s -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" -o /dev/null -w "%{http_code}" "${ELASTICSEARCH_URL}/ecommerce-products-v1" || echo "000")

if [ "$INDEX_EXISTS" != "200" ]; then
    echo -e "  'ecommerce-products-v1' index'i bulunamadı. Otomatik yükleniyor..."
    python3 scripts/load_ecommerce_data.py
    echo -e "${GREEN}✓ 20 ürün, 20 müşteri ve 20 sipariş başarıyla yüklendi.${NC}"
else
    echo -e "${GREEN}✓ 'ecommerce-products-v1' index'i zaten mevcut.${NC}"
fi

# 3. Port 8080 Kontrolü
if ss -tulpn 2>/dev/null | grep -q ":8080 "; then
    echo -e "${YELLOW}Port 8080 zaten dinleniyor. Mevcut servis test edilecek...${NC}"
else
    echo -e "\n${YELLOW}3. Spring Boot Arama Servisi Başlatılıyor (Port 8080)...${NC}"
    JAR_PATH="$SCRIPT_DIR/adapter/target/product-search-adapter-1.0.0-SNAPSHOT.jar"
    
    if [ -f "$JAR_PATH" ] && command -v java >/dev/null 2>&1; then
        echo -e "  Java 21 ile yerel arka plan servisi olarak başlatılıyor..."
        nohup java -jar "$JAR_PATH" > /tmp/search-service.log 2>&1 &
        ADAPTER_PID=$!
        echo $ADAPTER_PID > /tmp/search-service.pid
        echo -e "  PID: $ADAPTER_PID (Log: /tmp/search-service.log)"
    elif command -v docker >/dev/null 2>&1; then
        echo -e "  Docker Compose ile başlatılıyor..."
        if [ -z "${ELASTICSEARCH_API_KEY:-}" ]; then
            API_KEY=$(curl -s -k -u "${ELASTIC_USER}:${ELASTIC_PASSWORD}" -X POST "${ELASTICSEARCH_URL}/_security/api_key" -H 'Content-Type: application/json' -d '{"name":"novashop-adapter","role_descriptors":{"novashop_search":{"indices":[{"names":["ecommerce-products-v1"],"privileges":["read","view_index_metadata"]}]}}}' | jq -r '.encoded // empty' 2>/dev/null || true)
            export ELASTICSEARCH_API_KEY="${API_KEY:-}"
        fi
        docker compose -f docker-compose.novashop.yml up -d --build
    else
        echo -e "${RED}HATA: Ne Java ne de Docker bulundu!${NC}"
        exit 1
    fi

    # Servisin hazır olmasını bekle (en fazla 30 saniye)
    echo -n "  Arama servisi ayağa kalkıyor"
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8080/api/products/search?q=test >/dev/null 2>&1; then
            echo -e " ${GREEN}[HAZIR]${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
fi

# 4. Canlı Arama Doğrulaması
echo -e "\n${YELLOW}4. Canlı Arama Testi Gerçekleştiriliyor...${NC}"
SEARCH_RES=$(curl -s "http://127.0.0.1:8080/api/products/search?q=wireless")

if echo "$SEARCH_RES" | grep -q "P1001"; then
    echo -e "${GREEN}✓ Canlı Arama Başarılı!${NC}"
    echo -e "  Bulunan Ürünler: $(echo "$SEARCH_RES" | jq -r '.hits[] | "\(.id): \(.name) (\(.category)) - $\(.price)"' 2>/dev/null || echo "$SEARCH_RES")"
else
    echo -e "${RED}UYARI: Arama yanıtı beklenenden farklı döndü:${NC}"
    echo "$SEARCH_RES"
fi

# 5. Kibana Dashboard Kontrolü ve Yüklenmesi
if command -v python3 >/dev/null 2>&1 && [ -f "$SCRIPT_DIR/scripts/provision_dashboard.py" ]; then
    echo -e "\n${YELLOW}5. NovaShop Kibana Dashboard'u Kontrol Ediliyor...${NC}"
    KIBANA_URL="${KIBANA_URL:-http://127.0.0.1:5601}" python3 "$SCRIPT_DIR/scripts/provision_dashboard.py" || true
fi

# 6. Dış Erişim Bilgisi
HOST_NAME=$(hostname)
INSTANCE_ID=$(echo "$HOST_NAME" | grep -o "[a-zA-Z0-9-]*" | head -n1 || echo "lab")
echo -e "\n${BLUE}================================================================${NC}"
echo -e "${GREEN} E-Commerce Arama Servisi Başarıyla Çalışıyor!                  ${NC}"
echo -e " Yerel URL : http://127.0.0.1:8080/api/products/search?q=wireless"
echo -e " Ağ URL    : http://${HOST_NAME}:8080/api/products/search?q=wireless"
echo -e "${BLUE}================================================================${NC}"
