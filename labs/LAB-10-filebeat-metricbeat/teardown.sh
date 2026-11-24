#!/usr/bin/env bash
# LAB-10 temizligi: yalniz bu labin container'lari ve Filebeat registry volume'u, beats-* index'leri,
# beats-log / beats-metric sablonlari ve beats-log data view'i. Ana cluster ve diger lablar etkilenmez.
# Host'un /var/log/auth.log dosyasina yazilan 5 deneme satiri sistem logudur; silinmez.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601
docker compose down -v 2>&1 | grep -E "Removed" | sed 's/^ *//'
IDX=$(curl -s -u "$A" "$ES/_cat/indices/beats-*?h=index" | tr -d ' ' | paste -sd, -)
if [ -n "$IDX" ]; then echo "index'ler -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/$IDX")"; fi
for t in beats-log beats-metric; do
  echo "sablon $t -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/$t")"
done
echo "data view beats-log -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/data_views/data_view/beats-log")"
# Adim 6 kutusu: data view arayuzde kurulduysa id'si rastgeledir; adla bulunur
for id in $(curl -s -u "$A" "$KB/api/data_views" | jq -r '.data_view[] | select(.title == "beats-log-*" and .id != "beats-log") | .id'); do
  echo "data view $id -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/data_views/data_view/$id")"
done
