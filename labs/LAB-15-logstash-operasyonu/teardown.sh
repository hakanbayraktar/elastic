#!/usr/bin/env bash
# LAB-15 temizligi: yalniz bu labin Logstash container'i ve volume'u (kuyruk, DLQ), ops-app index'i
# ve ops-logs sablonu. Ana cluster ve diger lablar etkilenmez.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200
docker compose down -v 2>&1 | grep -E "Removed" | sed 's/^ *//'
echo "index ops-app -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/ops-app")"
echo "sablon ops-logs -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/ops-logs")"
