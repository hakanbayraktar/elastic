#!/usr/bin/env bash
# Ornek loglari Logstash TCP girdisine (5000) tek bir kalici baglanti uzerinden
# gonderir. Zaman damgalari "simdi"ye kadar uzanan bir zaman cizgisine yayilir;
# boylece Kibana'daki zaman serisi panelleri gercekci gorunur.
# Kullanim: ./scripts/send-logs.sh [tekrar_sayisi]   (varsayilan 1)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

REPEAT="${1:-1}"
STEP="${STEP:-5}"                       # iki satir arasindaki saniye
SRC="${SRC:-${LAB_DIR}/sample-data/raw-logs.txt}"

LINES=$(grep -c '[^[:space:]]' "${SRC}")
TOTAL=$((LINES * REPEAT))
START=$(( $(date -u +%s) - TOTAL * STEP ))

# Docker portu Logstash hazir olmadan acar; pipeline yuklenmeden yazilan satirlar
# "Broken pipe" ile kaybolur. Once API'den pipeline'in yuklendigini bekle (en fazla 120 sn).
for _ in $(seq 1 40); do
  # pipefail altinda "curl | grep -q" SIGPIPE (141) verir; ciktiyi once degiskene al.
  out=$(curl -s "http://${LOGSTASH_HOST}:9600/_node/pipelines/main" || true)
  case "${out}" in *'"main"'*) break ;; esac
  sleep 3
done

# Gonderimden onceki cikis sayaci: satirlar sokete yazilinca betik biter ama Logstash
# onlari birkac saniye sonra isler. Sonda bu sayac gonderilen satir kadar artana dek beklenir.
out_count() { curl -s "${LOGSTASH_API}/_node/stats/pipelines/main" | jq -r '.pipelines.main.events.out // 0'; }
BEFORE=$(out_count)

exec 3<>"/dev/tcp/${LOGSTASH_HOST}/${LOGSTASH_TCP_PORT}" || {
  echo "[!] ${LOGSTASH_HOST}:${LOGSTASH_TCP_PORT} kapali. 'docker compose up -d' calistirin." >&2
  exit 1
}

i=0
for ((r = 0; r < REPEAT; r++)); do
  while IFS= read -r line; do
    [ -z "${line//[[:space:]]/}" ] && continue
    TS=$(date -u -d "@$((START + i * STEP))" '+%Y-%m-%d %H:%M:%S')
    # Satirin ilk 19 karakteri zaman damgasidir; gerisi oldugu gibi korunur.
    printf '%s%s\n' "${TS}" "${line:19}" >&3
    i=$((i + 1))
  done < "${SRC}"
done
exec 3>&-

echo "[+] ${i} satir gonderildi -> ${LOGSTASH_HOST}:${LOGSTASH_TCP_PORT} (${SRC##*/}, ${STEP}s araliklarla)"

printf '[i] Logstash isliyor '
for _ in $(seq 1 30); do
  [ "$(out_count)" -ge $((BEFORE + i)) ] && { echo " ${i} olay Elasticsearch'e yazildi"; exit 0; }
  printf .; sleep 2
done
echo " zaman asimi: 'docker compose logs logstash' ile hatayi inceleyin" >&2; exit 1
