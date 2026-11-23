#!/usr/bin/env bash
# LAB-14 dogrulama: pipeline canli mi, grok iki formati da ayristirdi mi,
# ayristirilamayan satir karantinaya gitti mi, Kibana panosu kuruldu mu?
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/scripts/common.sh"
KBN_AUTH=(-u "${ES_USER}:${ELASTIC_PASSWORD}" -H "kbn-xsrf: grok")

FAIL=0
ok()  { echo "  [OK]   $1"; }
bad() { echo "  [HATA] $1"; FAIL=1; }
cnt() { es "${ES_URL}/$1/_count" | jq -r '.count // 0'; }

echo "== 1. Logstash servisi =="
STATS=$(curl -s --max-time 5 "${LOGSTASH_API}/_node/stats/pipelines/main")
if [ "$(echo "${STATS}" | jq -r '.pipelines.main.events.out // "null"')" != "null" ]; then
  ok "API 9600 yanit veriyor | islenen olay: $(echo "${STATS}" | jq -r '.pipelines.main.events.out')"
  QT=$(curl -s --max-time 5 "${LOGSTASH_API}/_node/stats/pipelines/main" | jq -r '.pipelines.main.queue.type')
  [ "${QT}" = "persisted" ] && ok "Persistent Queue etkin (queue.type=persisted)" || bad "queue.type=${QT} (persisted bekleniyor)"
else
  bad "Logstash API 9600 yanit vermiyor (docker compose up -d)"
fi

echo "== 2. Index sablonu =="
es "${ES_URL}/_index_template/grok-logs" | jq -e '.index_templates[0].name == "grok-logs"' >/dev/null 2>&1 \
  && ok "sablon grok-logs mevcut" || bad "sablon yok (./scripts/setup-indices.sh)"

echo "== 3. Kosullu yonlendirme =="
APP=$(cnt "grok-app-*"); ERR=$(cnt "grok-error-*"); UNP=$(cnt "grok-unparsed-*")
[ "${APP:-0}" -gt 0 ] && ok "grok-app-*      : ${APP} belge" || bad "grok-app-* bos (./scripts/send-logs.sh)"
[ "${ERR:-0}" -gt 0 ] && ok "grok-error-*    : ${ERR} belge" || bad "grok-error-* bos"
[ "${UNP:-0}" -gt 0 ] && ok "grok-unparsed-* : ${UNP} belge (karantina calisiyor)" || bad "grok-unparsed-* bos"

echo "== 4. grok: iki format da ayristi mi =="
B=$(es "${ES_URL}/grok-app-*,grok-error-*/_count?q=service:payment-gateway" | jq -r '.count // 0')
L=$(es "${ES_URL}/grok-app-*,grok-error-*/_count?q=service:legacy-batch" | jq -r '.count // 0')
[ "${B:-0}" -gt 0 ] && ok "1. desen (koseli parantezli): ${B} belge" || bad "1. desen ayristirilamadi"
[ "${L:-0}" -gt 0 ] && ok "2. desen (eski '-' formati)  : ${L} belge" || bad "2. desen ayristirilamadi"
GF=$(echo "${STATS}" | jq -r '[.pipelines.main.plugins.filters[] | select(.name=="grok")] | first | "eslesen: \(.matches), basarisiz: \(.failures)"')
echo "  [i]    grok sayaclari -> ${GF}"

echo "== 5. date + json + mutate =="
# JSON govdesi olan bir belge seciyoruz: duz metin mesajlarda payload zaten olmaz.
DOC=$(es "${ES_URL}/grok-error-*/_search?q=_exists_:payload&size=1" | jq -r '.hits.hits[0]._source // empty')
if [ -n "${DOC}" ]; then
  for F in service loglevel env '@timestamp' payload; do
    [ "$(echo "${DOC}" | jq -r --arg f "${F}" 'getpath([$f]) != null')" = "true" ] \
      && ok "alan ${F}: $(echo "${DOC}" | jq -rc --arg f "${F}" 'getpath([$f])' | cut -c1-55)" \
      || bad "alan ${F} bos"
  done
else
  bad "grok-error-* icinde belge yok"
fi

echo "== 6. Kibana panosu =="
curl -s "${KBN_AUTH[@]}" "${KIBANA_URL}/api/data_views/data_view/grok-logs" | jq -e '.data_view.id == "grok-logs"' >/dev/null 2>&1 \
  && ok "data view grok-logs hazir" || bad "data view yok (python3 scripts/provision_kibana.py)"
DASH=$(curl -s "${KBN_AUTH[@]}" "${KIBANA_URL}/api/saved_objects/dashboard/grok-logstash-overview")
if echo "${DASH}" | jq -e '.id == "grok-logstash-overview"' >/dev/null 2>&1; then
  ok "pano hazir: $(echo "${DASH}" | jq -r '.attributes.title') | panel: $(echo "${DASH}" | jq -r '[.references[] | select(.type=="lens")] | length')"
else
  bad "pano yok (python3 scripts/provision_kibana.py)"
fi

echo
[ "${FAIL}" -eq 0 ] && echo "[SONUC] LAB-14 dogrulamasi basarili." || echo "[SONUC] Eksik adim var (yukaridaki HATA satirlari)."
exit "${FAIL}"
