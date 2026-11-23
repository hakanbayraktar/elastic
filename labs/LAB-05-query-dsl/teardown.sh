#!/usr/bin/env bash
# LAB-05 temizligi: yalniz bu labin skor index'ini siler. Ornek e-ticaret verisi sonraki
# lablarda kullanildigi icin silinmez. Ana cluster'a dokunmaz.
set -u
code=$(curl -s -o /dev/null -w '%{http_code}' -u 'elastic:DevOps2026!' -X DELETE http://127.0.0.1:9200/arama-skor)
echo "index arama-skor -> $code"
