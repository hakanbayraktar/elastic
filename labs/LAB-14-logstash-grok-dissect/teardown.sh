#!/usr/bin/env bash
# LAB-14 temizligi: yalnizca bu labin konteyneri, volume'u, index'leri,
# sablonu ve Kibana nesneleri. LAB-01 ana cluster etkilenmez.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/scripts/common.sh"
KBN_AUTH=(-u "${ES_USER}:${ELASTIC_PASSWORD}" -H "kbn-xsrf: grok")
cd "${SCRIPT_DIR}"

echo "[1/4] Konteyner ve veri volume'u siliniyor"
docker compose --profile tools down -v

echo "[2/4] grok-* index'leri siliniyor"
# ES varsayilan olarak joker karakterle silmeye izin vermez
# (action.destructive_requires_name); once gercek adlari cozuyoruz.
INDICES=$(es "${ES_URL}/_cat/indices/grok-*?h=index" | tr -d ' ' | paste -sd, -)
if [ -n "${INDICES}" ]; then es -X DELETE "${ES_URL}/${INDICES}"; echo; echo "  -> ${INDICES}"; else echo "  -> index yok"; fi

echo "[3/4] Index sablonu siliniyor"
es -X DELETE "${ES_URL}/_index_template/grok-logs"; echo

for P in grok-ayristir grok-temizle grok-ayristir-arayuz; do
  es -X DELETE "${ES_URL}/_ingest/pipeline/${P}" >/dev/null; echo "  -> pipeline ${P}"
done
echo "[4/4] Kibana nesneleri siliniyor (pano, paneller, data view)"
for P in grok-parsed-count grok-unparsed-count grok-error-count \
         grok-errors-by-service grok-levels-over-time grok-latency-by-service; do
  curl -s -X DELETE "${KBN_AUTH[@]}" "${KIBANA_URL}/api/saved_objects/lens/${P}" >/dev/null
done
curl -s -X DELETE "${KBN_AUTH[@]}" "${KIBANA_URL}/api/saved_objects/dashboard/grok-logstash-overview" >/dev/null
curl -s -X DELETE "${KBN_AUTH[@]}" "${KIBANA_URL}/api/data_views/data_view/grok-logs" >/dev/null
echo "  -> pano, 6 panel ve data view kaldirildi"
echo "[+] Temizlik tamam."
