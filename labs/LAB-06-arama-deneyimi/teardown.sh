#!/usr/bin/env bash
# LAB-06 temizligi: yalniz bu labin index'ini ve es anlamli setini siler. Ana cluster'a dokunmaz.
set -u
A='elastic:DevOps2026!'
echo "index deneyim-urunler -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE http://127.0.0.1:9200/deneyim-urunler)"
echo "synonyms deneyim-esanlam -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE http://127.0.0.1:9200/_synonyms/deneyim-esanlam)"
