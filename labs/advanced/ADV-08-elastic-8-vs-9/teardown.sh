#!/usr/bin/env bash
# ADV-08 temizligi: yalniz bu labin compose projesi (es-v8-lab: 8.19 Elasticsearch/Kibana ve volume'leri) ve ana
# cluster'da kalmissa Adim 3'un surum-eski / surum-yeni deneme sablonlari silinir. Ana cluster ve diger lablar etkilenmez.
set -uo pipefail
cd "$(dirname "$0")"
docker compose down -v 2>&1 | grep -cE "Removed" | sed 's/^/kaldirilan nesne: /'
A='elastic:DevOps2026!'
echo "ana cluster _template/surum-eski -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE http://127.0.0.1:9200/_template/surum-eski)"
echo "ana cluster _index_template/surum-yeni -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE http://127.0.0.1:9200/_index_template/surum-yeni)"
