#!/usr/bin/env bash
# ADV-06 temizligi: yalniz shop-v1 ve shop-v2 index'leri (alias'lari onlarla birlikte duser).
# Ana cluster ve diger lablar etkilenmez.
set -uo pipefail
ES=http://127.0.0.1:9200; A='elastic:DevOps2026!'
for i in shop-v1 shop-v2; do
  echo "index $i -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/$i")"
done
