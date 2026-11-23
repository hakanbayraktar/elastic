#!/usr/bin/env bash
# LAB-22 temizligi: yalniz bu labin ilm-uygulama data stream'ini (arka plan index'leriyle), index template'ini,
# component template'lerini ve ILM politikasini siler; ILM kontrol araligini varsayilana dondurur.
# Ana cluster'daki diger verilere dokunmaz.
set -u
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200
del() { echo "$1 -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$2")"; }
del "data stream ilm-uygulama" "$ES/_data_stream/ilm-uygulama"
del "index template ilm-uygulama" "$ES/_index_template/ilm-uygulama"
del "component template ilm-ayarlar" "$ES/_component_template/ilm-ayarlar"
del "component template ilm-mappings" "$ES/_component_template/ilm-mappings"
del "ILM politikasi ilm-politika" "$ES/_ilm/policy/ilm-politika"
echo "poll_interval varsayilan -> $(curl -s -u "$A" -X PUT "$ES/_cluster/settings" -H 'Content-Type: application/json' \
  -d '{"persistent": {"indices.lifecycle.poll_interval": null}}' | jq -c .acknowledged)"
