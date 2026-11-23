#!/usr/bin/env bash
# LAB-16 temizligi: pano-apache index'i ve sablonu, bu labda kurulan Kibana nesneleri (data view, pano,
# Library'deki gorsellestirmeler, kayitli arama, harita). Ana cluster ve diger lablar etkilenmez.
set -u
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601
echo "index pano-apache -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/pano-apache")"
echo "sablon pano-apache -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/pano-apache")"
# Arayuzde kurulan nesnelerin id'leri rastgeledir; bu labin data view'ina bagli olanlar bulunup silinir.
N=0
for t in dashboard lens search map visualization; do
  for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=$t&per_page=1000&has_reference=%7B%22type%22%3A%22index-pattern%22%2C%22id%22%3A%22pano-apache%22%7D" | jq -r '.saved_objects[].id'); do
    curl -s -o /dev/null -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/saved_objects/$t/$id?force=true"; N=$((N + 1))
  done
done
for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=dashboard&search_fields=title&search=%22Apache%20at%C3%B6lye%22" | jq -r '.saved_objects[].id'); do
  curl -s -o /dev/null -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/saved_objects/dashboard/$id?force=true"; N=$((N + 1))
done
echo "Kibana nesneleri -> $N silindi"
echo "data view pano-apache -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/data_views/data_view/pano-apache")"
