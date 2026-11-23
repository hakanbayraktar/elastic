#!/usr/bin/env bash
# LAB-03 temizligi: yalniz bu labin mapping-* index'lerini siler. Ana cluster'a dokunmaz.
set -u
for idx in mapping-dinamik mapping-urunler mapping-urunler-v2; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u 'elastic:DevOps2026!' -X DELETE "http://127.0.0.1:9200/$idx")
  echo "index $idx -> $code"
done
# <details> bloklarindaki deneme index'leri kendi sonlarinda silinir; adim yarida kaldiysa burada silinir.
for idx in mapping-kopya mapping-normalizer mapping-tolerans mapping-coerce mapping-ascii; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u 'elastic:DevOps2026!' -X DELETE "http://127.0.0.1:9200/$idx")
  [ "$code" = 200 ] && echo "index $idx -> $code"
done
exit 0
