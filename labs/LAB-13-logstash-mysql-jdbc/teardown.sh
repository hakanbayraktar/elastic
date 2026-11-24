#!/usr/bin/env bash
# LAB-13 temizligi: yalniz bu labin MySQL ve Logstash konteynerlerini (volume'leriyle), mysql-siparisler
# index'ini, sablonunu, rolunu ve kullanicisini siler. Ana cluster'a ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200
docker compose down -v 2>&1 | grep -E "Removed" | sed 's/^ *//'
del() { echo "$1 -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$2")"; }
del "index mysql-siparisler" "$ES/mysql-siparisler"
del "sablon mysql-siparisler" "$ES/_index_template/mysql-siparisler"
del "kullanici mysql_logstash" "$ES/_security/user/mysql_logstash"
del "rol mysql-logstash-writer" "$ES/_security/role/mysql-logstash-writer"
# Adim 7: data view'a bagli Kibana nesneleri (Lens, pano) ve data view
KB=http://127.0.0.1:5601; N=0
for t in dashboard lens search visualization; do
  for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=$t&per_page=1000&has_reference=%7B%22type%22%3A%22index-pattern%22%2C%22id%22%3A%22mysql-siparisler%22%7D" | jq -r '.saved_objects[].id'); do
    curl -s -o /dev/null -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/saved_objects/$t/$id?force=true"; N=$((N + 1))
  done
done
for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=dashboard&search_fields=title&search=%22MySQL%20sipari%C5%9Fleri%22" | jq -r '.saved_objects[].id'); do
  curl -s -o /dev/null -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/saved_objects/dashboard/$id?force=true"; N=$((N + 1))
done
echo "Kibana nesneleri -> $N silindi"
echo "data view mysql-siparisler -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/data_views/data_view/mysql-siparisler")"
