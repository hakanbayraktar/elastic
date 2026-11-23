#!/usr/bin/env bash
# LAB-07 temizligi: yalniz bu labda olusturulan pano ve Lens gorsellestirmesini (basliga gore), canli siparis
# akisini, analiz-canli index'ini ve data view'ini, ornek data view'a eklenen siparis_saati runtime field'ini siler.
# Ornek e-ticaret verisine ve ana cluster'a dokunmaz.
set -u
cd "$(dirname "$0")"
KB=http://127.0.0.1:5601; ES=http://127.0.0.1:9200; A='elastic:DevOps2026!'
for pair in "dashboard:Satış özeti" "lens:Kategori bazında sipariş"; do
  type=${pair%%:*}; title=${pair#*:}
  for id in $(curl -s -u "$A" -G "$KB/api/saved_objects/_find" --data-urlencode "type=$type" --data-urlencode "search_fields=title" --data-urlencode "search=\"$title\"" | jq -r --arg t "$title" '.saved_objects[] | select(.attributes.title == $t) | .id'); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE -H 'kbn-xsrf: true' "$KB/api/saved_objects/$type/$id")
    echo "$type '$title' -> $code"
  done
done
if pgrep -f "scripts/canli_siparis.py canli" >/dev/null; then pkill -f "scripts/canli_siparis.py canli"; echo "canli siparis akisi -> durduruldu"; fi
echo "runtime field siparis_saati -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE -H 'kbn-xsrf: true' "$KB/api/data_views/data_view/ff959d40-b880-11e8-a6d9-e546fe2bba5f/runtime_field/siparis_saati")"
echo "data view analiz-canli -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE -H 'kbn-xsrf: true' "$KB/api/data_views/data_view/analiz-canli")"
echo "index analiz-canli -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/analiz-canli")"
