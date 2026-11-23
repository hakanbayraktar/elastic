#!/usr/bin/env bash
# ADV-07 temizligi: yalniz rca-olaylar index'i silinir. Ana cluster ve diger lablar etkilenmez.
set -uo pipefail
echo "index rca-olaylar -> $(curl -s -o /dev/null -w '%{http_code}' -u 'elastic:DevOps2026!' -X DELETE http://127.0.0.1:9200/rca-olaylar)"
