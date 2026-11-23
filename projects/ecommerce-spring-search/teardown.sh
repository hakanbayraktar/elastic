#!/usr/bin/env bash
# ecommerce-spring-search temizligi: yalnizca bu projenin kaynaklari.
# Omurga (elasticsearch-lab00 / kibana-lab00) ve kibana_sample_data_ecommerce silinmez.
set -uo pipefail
cd "$(dirname "$0")"
ES_URL="${ELASTIC_URL:-http://localhost:9200}"
KB_URL="${KIBANA_URL:-http://localhost:5601}"
AUTH="${ELASTIC_USER:-elastic}:${ELASTIC_PASSWORD:-DevOps2026!}"
es() { curl -s -u "$AUTH" -H 'Content-Type: application/json' "$@"; echo; }
kb() { curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -H 'kbn-xsrf: novashop-teardown' "$@"; }

echo "[+] Arama servisi durduruluyor..."
if [ -f /tmp/search-service.pid ]; then
  kill "$(cat /tmp/search-service.pid)" 2>/dev/null && echo "    Java sureci durduruldu"
  rm -f /tmp/search-service.pid
fi
docker compose -f docker-compose.novashop.yml down --rmi local 2>&1 | tail -2

echo "[+] Index'ler siliniyor..."
es -X DELETE "${ES_URL}/ecommerce-products-v1,ecommerce-customers-v1,ecommerce-orders-v1,novashop-events?ignore_unavailable=true"

echo "[+] Kibana nesneleri siliniyor (id ile)..."
printf '    dashboard novashop-ecommerce-analytics: %s\n' "$(kb -X DELETE "${KB_URL}/api/saved_objects/dashboard/novashop-ecommerce-analytics")"
for id in novashop-revenue novashop-order-count novashop-category-share novashop-daily-trend novashop-top-products novashop-city-table; do
  printf '    lens %s: %s\n' "$id" "$(kb -X DELETE "${KB_URL}/api/saved_objects/lens/${id}")"
done
for id in novashop-orders novashop-events-dataview; do
  printf '    data view %s: %s\n' "$id" "$(kb -X DELETE "${KB_URL}/api/data_views/data_view/${id}")"
done

echo "[+] novashop-adapter API key'leri gecersiz kiliniyor..."
es -X DELETE "${ES_URL}/_security/api_key" -d '{"name":"novashop-adapter"}' | jq -c '{invalidated: (.invalidated_api_keys|length)}' 2>/dev/null || true
rm -f novashop-yonetim-satisi.pdf
echo "[+] Temizlik tamam. Omurga ve ornek veri etkilenmedi."
