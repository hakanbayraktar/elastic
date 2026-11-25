#!/usr/bin/env bash
# LAB-27 temizligi: yalniz bu labin container'lari ve volume'leri, apache-web-* index'leri ve sablonu,
# Metricbeat data stream'i ve sablonu, apache-5xx kurali, uc connector'i, data view'lari, panosu ve haritasi,
# istege bagli ML isi ve iki SLO.
# Kurulmamis connector'lar (Resend, Slack) 404 yazar.
# Ana cluster'a dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601
k() { curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' "$@"; }
docker compose down -v --remove-orphans 2>&1 | grep -E "Removed" | sed 's/^ *//' | sort | uniq -c | awk '{$1=""; print substr($0,2)}' | head -20
echo "kural apache-5xx -> $(k -X DELETE "$KB/api/alerting/rule/apache-5xx")"
curl -s -o /dev/null -u "$A" -X POST "$ES/_ml/datafeeds/apache-ip-istek-anomali-feed/_stop?force=true"
echo "ML isi -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_ml/anomaly_detectors/apache-ip-istek-anomali?force=true")"
for S in apache-web-erisilebilirlik apache-web-gecikme-500ms; do echo "SLO $S -> $(k -X DELETE "$KB/api/observability/slos/$S")"; done
for C in apache-mailpit apache-eposta apache-slack; do echo "connector $C -> $(k -X DELETE "$KB/api/actions/connector/$C")"; done
N=0
for t in map lens dashboard search; do
  for v in apache-web-logs apache-web-metrics; do
    for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=$t&per_page=1000&has_reference=%7B%22type%22%3A%22index-pattern%22%2C%22id%22%3A%22$v%22%7D" | jq -r '.saved_objects[].id'); do
      k -X DELETE "$KB/api/saved_objects/$t/$id?force=true" >/dev/null; N=$((N + 1))
    done
  done
done
echo "Kibana nesneleri -> $N silindi"
for v in apache-web-logs apache-web-metrics; do echo "data view $v -> $(k -X DELETE "$KB/api/data_views/data_view/$v")"; done
IDX=$(curl -s -u "$A" "$ES/_cat/indices/apache-web-*?h=index" | tr -d ' ' | paste -sd, -)
[ -n "$IDX" ] && echo "index'ler -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/$IDX")"
echo "sablon apache-web -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/apache-web")"
echo "metricbeat data stream -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/metricbeat-9.5.5")"
echo "metricbeat sablonu -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/metricbeat-9.5.5")"
