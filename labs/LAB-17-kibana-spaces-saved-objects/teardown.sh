#!/usr/bin/env bash
# LAB-17 temizligi: yalniz bu labin satis-ekibi ve pazarlama Space'lerini (icindeki pano kopyalariyla) ve
# API ornegindeki export dosyasini siler. Default Space'e, ornek panoya ve veriye dokunmaz.
set -u
cd "$(dirname "$0")"
for s in satis-ekibi pazarlama; do
  echo "space $s -> $(curl -s -o /dev/null -w '%{http_code}' -u 'elastic:DevOps2026!' -H 'kbn-xsrf: true' -X DELETE "http://127.0.0.1:5601/api/spaces/space/$s")"
done
rm -f spaces-export.ndjson
