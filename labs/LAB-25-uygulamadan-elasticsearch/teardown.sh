#!/usr/bin/env bash
# LAB-25 temizligi: yalniz bu labin py-urunler ve py-tek index'lerini ve py-uygulama API key'lerini siler, venv'i kaldirir.
# Ana cluster'a ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200
for I in py-urunler py-tek; do echo "index $I -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/$I")"; done
echo "api key py-uygulama -> $(curl -s -u "$A" -X DELETE "$ES/_security/api_key" -H 'Content-Type: application/json' -d '{"name": "py-uygulama"}' | jq -c '{invalidated: (.invalidated_api_keys | length)}')"
rm -rf .venv && echo ".venv silindi"
