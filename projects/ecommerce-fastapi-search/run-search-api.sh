#!/usr/bin/env bash
# ==============================================================================
# NovaCommerce: NovaCommerce FastAPI Arama Servisini Başlatma Scripti
# Port: 19001 (App1 Slotu)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-19001}"
HOST="${HOST:-0.0.0.0}"
ELASTIC_URL="${ELASTIC_URL:-http://localhost:9200}"
ELASTIC_USER="${ELASTIC_USER:-elastic}"
ELASTIC_PASSWORD="${ELASTIC_PASSWORD:-DevOps2026!}"

echo "=================================================================="
echo "🚀 NovaCommerce: NovaCommerce Arama Servisi Başlatılıyor..."
echo "=================================================================="

# 1. Python Sanal Ortamı
# Sistem Python'u (Ubuntu 24.04) PEP 668 ile korunur: global `pip install` reddedilir.
# Bu yüzden paketler proje içindeki .venv'e kurulur; root yetkisi gerekmez.
if [ ! -x ".venv/bin/python3" ]; then
    echo "📦 Proje sanal ortamı oluşturuluyor (.venv)..."
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python3 -c "import fastapi, uvicorn, elasticsearch, pydantic_settings" 2>/dev/null || {
    echo "📦 Python paketleri .venv içine kuruluyor (app/requirements.txt)..."
    pip install -q -r app/requirements.txt
}

# 2. Elasticsearch ve Veri Index Kontrolü
echo "🔍 Elasticsearch cluster'ı kontrol ediliyor ($ELASTIC_URL)..."
EXIT_CODE=0
python3 - << 'EOF' || EXIT_CODE=$?
import os, sys, urllib3
from elasticsearch import Elasticsearch
urllib3.disable_warnings()

url = os.getenv("ELASTIC_URL", "http://localhost:9200")
user = os.getenv("ELASTIC_USER", "elastic")
pwd = os.getenv("ELASTIC_PASSWORD", "DevOps2026!")

try:
    es = Elasticsearch(hosts=[url], basic_auth=(user, pwd) if pwd else None, verify_certs=False)
    if not es.ping():
        print(f"❌ Elasticsearch erişilemiyor: {url}")
        sys.exit(1)
    
    target_idx = "ecommerce_search_products"
    if not es.indices.exists(index=target_idx):
        print(f"ℹ️ '{target_idx}' index'i bulunamadı. ETL scripti çalıştırılacak...")
        sys.exit(2)
    else:
        cnt = es.count(index=target_idx).get("count", 0)
        print(f"✅ '{target_idx}' index'i hazır ({cnt} ürün kayıtlı).")
except Exception as e:
    print(f"❌ Hata: {e}")
    sys.exit(1)
EOF

if [ "$EXIT_CODE" -eq 1 ]; then
    exit 1
elif [ "$EXIT_CODE" -eq 2 ]; then
    echo "🔄 Kibana Sample Data'dan ürün kataloğu üretiliyor..."
    python3 scripts/ingest_from_kibana_sample.py
fi

# 3. Dış IP ve Hostname Bilgileri
PUBLIC_IP=$(curl -s -m 2 https://ifconfig.me 2>/dev/null || curl -s -m 2 https://api.ipify.org 2>/dev/null || echo "SUNUCU_PUBLIC_IP")
HOSTNAME_VAL=$(hostname)
STUDENT_ID=$(echo "$HOSTNAME_VAL" | grep -o "student[0-9]*" || echo "studentXX")

echo ""
echo "=================================================================="
echo "🎉 ARAMA SERVİSİ YAYIN ADRESLERİ (Çift Erişim Modeli):"
echo "=================================================================="
echo "1. 🌐 Cloudflare DNS (HTTPS):"
echo "   - API Root    : https://${STUDENT_ID}-app1.devopsatolyesi.com"
echo "   - Swagger UI  : https://${STUDENT_ID}-app1.devopsatolyesi.com/docs"
echo "   - Autocomplete: https://${STUDENT_ID}-app1.devopsatolyesi.com/api/v1/search/autocomplete?q=cas"
echo ""
echo "2. 📡 Doğrudan IP (PIP Yol Erişimi - Port 80):"
echo "   - API Root    : http://${PUBLIC_IP}/app1"
echo "   - Swagger UI  : http://${PUBLIC_IP}/app1/docs"
echo ""
echo "3. ⚡ Doğrudan IP (PIP Port Erişimi - Port 19001):"
echo "   - API Root    : http://${PUBLIC_IP}:19001"
echo "   - Swagger UI  : http://${PUBLIC_IP}:19001/docs"
echo ""
echo "4. 💻 Yerel (Localhost):"
echo "   - Swagger UI  : http://localhost:19001/docs"
echo "=================================================================="
echo ""

# 4. Servisi Başlat
exec uvicorn app.main:app --host "$HOST" --port "$PORT"
