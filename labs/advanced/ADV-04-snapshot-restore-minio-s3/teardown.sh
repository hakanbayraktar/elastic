#!/usr/bin/env bash
# ADV-04 temizligi: yalniz bu labin index'leri, s3-yedek repository kaydi, ana cluster keystore'undaki
# s3.client.default.* anahtarlari ve MinIO (container + volume, bucket icerigiyle) silinir.
# Ana cluster'in kendisi ve diger lablar etkilenmez.
set -uo pipefail
cd "$(dirname "$0")"
ES=http://127.0.0.1:9200; A='elastic:DevOps2026!'
kod() { curl -s -o /dev/null -w '%{http_code}' -u "$A" "$@"; }
for i in s3-islemler-aranabilir s3-islemler; do echo "index $i -> $(kod -X DELETE "$ES/$i")"; done
echo "repository s3-yedek -> $(kod -X DELETE "$ES/_snapshot/s3-yedek")"
for k in access_key secret_key; do
  docker exec elasticsearch-lab00 ./bin/elasticsearch-keystore remove "s3.client.default.$k" >/dev/null 2>&1 \
    && echo "keystore s3.client.default.$k -> silindi" || echo "keystore s3.client.default.$k -> yok"
done
echo "reload_secure_settings -> $(kod -X POST "$ES/_nodes/reload_secure_settings")"
docker compose -f docker-compose.minio.yml down -v 2>&1 | grep -E "Removed" | sed 's/^ *//' || echo "MinIO container yok"
