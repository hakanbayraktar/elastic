#!/usr/bin/env bash
# LAB-02 temizligi: yalniz bu labin index'lerini ve data view'larini siler. Ana cluster'a dokunmaz.
set -u
ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601; AUTH='elastic:DevOps2026!'
for idx in belge-urunler belge-talepler belge-stok belge-surum; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u "$AUTH" -X DELETE "$ES/$idx")
  echo "index $idx -> $code"
done
# Shard boyutu kutusu: rollover index'leri (adlari cozulur), sablon ve ILM politikasi.
# Politika kullanan index varken silinemez; once index'ler silinir.
for idx in $(curl -s -u "$AUTH" "$ES/_cat/indices/belge-loglar-*?h=index" | sort); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u "$AUTH" -X DELETE "$ES/$idx")
  echo "index $idx -> $code"
done
echo "sablon belge-loglar -> $(curl -s -o /dev/null -w '%{http_code}' -u "$AUTH" -X DELETE "$ES/_index_template/belge-loglar")"
echo "politika belge-shard-1gb -> $(curl -s -o /dev/null -w '%{http_code}' -u "$AUTH" -X DELETE "$ES/_ilm/policy/belge-shard-1gb")"
# Arayuzde olusturulan data view'larin id'si rastgeledir; adina (title) gore bulunur.
for id in $(curl -s -u "$AUTH" "$KB/api/data_views" | jq -r '.data_view[] | select(.title | startswith("belge-")) | .id'); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u "$AUTH" -X DELETE -H 'kbn-xsrf: true' "$KB/api/data_views/data_view/$id")
  echo "data view $id -> $code"
done
