#!/usr/bin/env bash
# SIEM'in en cok ihmal edilen isi: KURAL AYARI (tuning).
# Mesru bir otomasyon ya da kendi erisim IP'niz surekli brute force alarmi
# uretiyorsa kurali kapatmak yerine o kaynagi istisnaya alirsiniz.
#
# Kullanim: ./scripts/tune-false-positive.sh 159.146.73.4
set -euo pipefail
ES_URL="${ES_URL:-http://127.0.0.1:9200}"
KIBANA_URL="${KIBANA_URL:-http://127.0.0.1:5601}"
es() { curl -s -u 'elastic:DevOps2026!' "$@"; }
kbn() { curl -s -u 'elastic:DevOps2026!' -H 'kbn-xsrf: true' "$@"; }

IP="${1:-}"
RULE_ID="siem-lab-ssh-brute-force"
if [ -z "${IP}" ]; then
  echo "Kullanim: $0 <istisnaya_alinacak_ip>" >&2
  echo "Oneri: once asagidaki sorguyla aday bulun (cok denemesi ama cok da" >&2
  echo "basarili girisi olan kaynaklar genelde mesrudur):" >&2
  echo '  FROM siem-auth-* | STATS b=COUNT(*) WHERE event.outcome=="failure", s=COUNT(*) WHERE event.action=="ssh_login_success" BY source.ip | WHERE s > 100' >&2
  exit 2
fi

CURRENT=$(kbn "${KIBANA_URL}/api/detection_engine/rules?rule_id=${RULE_ID}" | jq -r '.query')
if [ "${CURRENT}" = "null" ]; then
  echo "[!] Kural bulunamadi: ${RULE_ID} (once python3 scripts/provision_detections.py)" >&2
  exit 1
fi
echo "[1/2] Mevcut kural sorgusu: ${CURRENT}"

NEW_QUERY="${CURRENT} and not source.ip : \"${IP}\""
kbn -X PATCH "${KIBANA_URL}/api/detection_engine/rules" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg id "${RULE_ID}" --arg q "${NEW_QUERY}" '{rule_id:$id, query:$q}')" \
  | jq -c '{name, query}'

echo "[2/2] ${IP} artik brute force kuralini tetiklemeyecek."
echo "      Not: istisna KURAL duzeyindedir; olay verisi silinmez, panolarda gorunmeye devam eder."
