#!/usr/bin/env bash
# LAB-21 temizligi: yalniz bu labin saglik-* index'ini siler. Ana cluster'a ve ornek veriye dokunmaz.
set -u
echo "index saglik-arizali -> $(curl -s -o /dev/null -w '%{http_code}' -u 'elastic:DevOps2026!' -X DELETE http://127.0.0.1:9200/saglik-arizali)"
