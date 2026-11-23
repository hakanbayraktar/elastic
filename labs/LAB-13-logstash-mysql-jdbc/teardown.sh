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
