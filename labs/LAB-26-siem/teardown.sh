#!/usr/bin/env bash
# LAB-26 temizligi: yalniz bu labin konteynerlerini, siem-* index'lerini ve sablonlarini, enrich policy ve
# ingest pipeline'ini, siem-lab-* tespit kurallarini ve bu kurallarin urettigi alarmlari siler; senaryo logunu
# ve izlenen dosyayi baslangic haline getirir. Ana cluster'a ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601
docker compose down -v 2>&1 | grep -E "Removed" | sed 's/^ *//'
N=0
for r in siem-lab-ssh-brute-force siem-lab-successful-login-after-bruteforce siem-lab-new-user-created siem-lab-threat-intel-match siem-lab-config-changed; do
  [ "$(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/detection_engine/rules?rule_id=$r")" = 200 ] && N=$((N + 1))
done
echo "tespit kurali silindi -> $N"
echo "alarm silindi -> $(curl -s -u "$A" -X POST "$ES/.alerts-security.alerts-default/_delete_by_query?refresh=true&ignore_unavailable=true" \
  -H 'Content-Type: application/json' -d '{"query": {"prefix": {"kibana.alert.rule.rule_id": "siem-lab-"}}}' | jq -r '.deleted // 0')"
# Sira onemli: data stream -> index -> sablon -> pipeline -> enrich policy (her biri bir oncekine bagli).
DS=$(curl -s -u "$A" "$ES/_data_stream/siem-*" | jq -r '[.data_streams[].name] | join(",")')
echo "data stream (siem-*) -> $([ -n "$DS" ] && curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/$DS" || echo yok)"
IDX=$(curl -s -u "$A" "$ES/_cat/indices/siem-*?h=index" | tr -d ' ' | paste -sd, -)
echo "index (siem-*) -> $([ -n "$IDX" ] && curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/$IDX" || echo yok)"
for t in siem-auth siem-fim; do echo "sablon $t -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/$t")"; done
echo "ingest pipeline siem-enrich -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_ingest/pipeline/siem-enrich")"
echo "enrich policy siem-threat-ip -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_enrich/policy/siem-threat-ip")"
: > data/attack-scenario.log 2>/dev/null; rm -f data/attack-scenario.log
cp izlenen/sshd_config.orijinal izlenen/sshd_config
