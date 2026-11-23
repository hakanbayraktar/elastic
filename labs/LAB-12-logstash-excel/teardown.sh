#!/usr/bin/env bash
# LAB-12 temizligi: yalniz bu labin Logstash konteynerini, excel-* index'ini, sablonunu, data view'ini,
# rolunu ve kullanicisini siler. Ana cluster'a ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601
docker compose down -v 2>&1 | grep -E "Removed|removed" | sed 's/^ *//'
del() { echo "$1 -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$2")"; }
del "index excel-satislar" "$ES/excel-satislar"
del "index excel-uygulama-loglari" "$ES/excel-uygulama-loglari"
del "sablon excel-satislar" "$ES/_index_template/excel-satislar"
del "kullanici excel_logstash" "$ES/_security/user/excel_logstash"
del "rol excel-logstash-writer" "$ES/_security/role/excel-logstash-writer"
for id in $(curl -s -u "$A" "$KB/api/data_views" | jq -r '.data_view[] | select(.title == "excel-satislar" or .title == "excel-uygulama-loglari") | .id'); do
  echo "data view $id -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE -H 'kbn-xsrf: true' "$KB/api/data_views/data_view/$id")"
done
rm -f data/satislar.csv
