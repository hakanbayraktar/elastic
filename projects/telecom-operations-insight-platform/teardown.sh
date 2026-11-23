#!/usr/bin/env bash
# telecom-operations-insight-platform temizligi: yalnizca bu capstone'un kaynaklari.
set -uo pipefail
cd "$(dirname "$0")"
ES_URL="${ELASTIC_URL:-http://localhost:9200}"
KB_URL="${KIBANA_URL:-http://localhost:5601}"
AUTH="${ELASTIC_USER:-elastic}:${ELASTIC_PASSWORD:-DevOps2026!}"
es() { printf '    %-55s %s\n' "$2" "$(curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -X "$1" "${ES_URL}$2")"; }
kb() { printf '    %-55s %s\n' "$2" "$(curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -H 'kbn-xsrf: telecom-teardown' -X "$1" "${KB_URL}$2")"; }

echo "[+] Kibana nesneleri (200/204 silindi, 404 zaten yok):"
kb DELETE /api/alerting/rule/telecom-capstone-error-rate
kb DELETE /api/actions/connector/telecom-capstone-log
kb DELETE /api/saved_objects/dashboard/telecom-operations-capstone
for id in capstone-requests capstone-error-rate capstone-p95 capstone-endpoints capstone-clients; do
  kb DELETE "/api/saved_objects/lens/${id}"
done
kb DELETE /api/data_views/data_view/telecom-capstone-view

echo "[+] Elasticsearch varliklari:"
es DELETE /_data_stream/logs-telecom.capstone-prod
es DELETE /_index_template/lab04-telecom-capstone-template
es DELETE /_component_template/lab04-telecom-capstone-mappings
es DELETE /_ilm/policy/lab04-telecom-capstone-retention
es DELETE /_ingest/pipeline/lab04-telecom-capstone-v1

rm -rf reports
echo "[+] Temizlik tamam. Omurga ve diger lablar etkilenmedi."
