#!/usr/bin/env bash
# Bir NDJSON dosyasini Logstash TCP girdisine (127.0.0.1:5001) gonderir ve ingest pipeline'inin
# cikis sayaci gonderilen olay kadar artana dek bekler. Satirlar sokete yazilinca betik biterdi;
# Logstash onlari birkac saniye sonra isler.
# Kullanim: ./scripts/gonder.sh <dosya.ndjson> [--beklemeden]
set -euo pipefail
API=http://127.0.0.1:9601
FILE="$1"
N=$(grep -c . "${FILE}")
out() { curl -s "${API}/_node/stats/pipelines/ingest" | jq -r '.pipelines.ingest.events.out // 0'; }
BEFORE=$(out)

# TCP girdisi pipeline ile birlikte acilir; acilana dek en fazla 60 sn dene.
for _ in $(seq 1 30); do
  if exec 3<>/dev/tcp/127.0.0.1/5001; then break; fi 2>/dev/null
  sleep 2
done
cat "${FILE}" >&3
exec 3>&-
echo "[+] ${N} olay gonderildi (${FILE##*/})"

[ "${2:-}" = "--beklemeden" ] && exit 0
printf '[i] Logstash isliyor '
for _ in $(seq 1 30); do
  [ "$(out)" -ge $((BEFORE + N)) ] && { echo " ${N} olay cikisa ulasti"; exit 0; }
  printf .; sleep 2
done
echo " zaman asimi: 'docker compose logs logstash' ile inceleyin" >&2
exit 1
