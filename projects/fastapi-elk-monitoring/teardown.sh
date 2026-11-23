#!/usr/bin/env bash
# fastapi-elk-monitoring temizligi: yalnizca bu projenin kaynaklari.
set -uo pipefail
cd "$(dirname "$0")"
ES_URL="${ELASTIC_URL:-http://localhost:9200}"
AUTH="${ELASTIC_USER:-elastic}:${ELASTIC_PASSWORD:-DevOps2026!}"
es() { curl -s -u "$AUTH" -H 'Content-Type: application/json' "$@"; echo; }

echo "[+] Logstash ve FastAPI konteynerleri kaldiriliyor..."
docker compose down -v --rmi local 2>&1 | tail -3
echo "[+] logs-fastapi-production data stream'i siliniyor..."
es -X DELETE "${ES_URL}/_data_stream/logs-fastapi-production"
echo "[+] logs-fastapi-template sablonu siliniyor..."
es -X DELETE "${ES_URL}/_index_template/logs-fastapi-template"
echo "[+] logstash-fastapi-writer API key'leri gecersiz kiliniyor..."
es -X DELETE "${ES_URL}/_security/api_key" -d '{"name":"logstash-fastapi-writer"}' | jq -c '{invalidated: (.invalidated_api_keys|length)}' 2>/dev/null || true
echo "[+] Temizlik tamam. Omurga ve diger lablar etkilenmedi."
