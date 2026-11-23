#!/usr/bin/env bash
# ==============================================================================
# FastAPI ELK: Lab Başlatıcı Scripti (run-lab.sh)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo "🚀 FastAPI ELK: FastAPI + Logstash TCP + Elasticsearch Başlatılıyor"
echo "=================================================================="

# Docker compose ile Logstash ve FastAPI servisini ayağa kaldır
echo "1. Docker container'ları derleniyor ve başlatılıyor..."
docker compose up -d --build

echo ""
echo "2. Logstash pipeline'ının açılması bekleniyor (JVM açılışı ~45 sn)..."
for _ in $(seq 1 36); do
    docker logs logstash-app2 2>&1 | grep -q "Pipelines running" && break
    sleep 5
done
docker logs logstash-app2 2>&1 | grep -q "Pipelines running" || { echo "❌ Logstash pipeline açılmadı: docker logs logstash-app2"; exit 1; }
echo "   FastAPI sağlık uç noktası bekleniyor..."
for _ in $(seq 1 24); do
    curl -sf http://localhost:19002/api/v1/health >/dev/null && break
    sleep 5
done

echo ""
echo "3. Sağlık kontrolü yapılıyor..."
curl -sf http://localhost:19002/api/v1/health || { echo "❌ FastAPI yanıt vermiyor: docker logs fastapi-observability-app2"; exit 1; }
echo ""

echo "=================================================================="
echo "✅ Kurulum Tamamlandı!"
echo "   - FastAPI Servisi:  http://localhost:19002 (Docs: http://localhost:19002/docs)"
echo "   - Logstash TCP:     127.0.0.1:5010 (konteyner içi 5000)"
echo "   - Elasticsearch:    http://localhost:9200"
echo ""
echo "👉 Şimdi sentetik trafik ve hata logları üretmek için:"
echo "   python3 scripts/simulate-traffic.py"
echo ""
echo "👉 Durumu doğrulamak için:"
echo "   ./verify.sh"
echo "=================================================================="
