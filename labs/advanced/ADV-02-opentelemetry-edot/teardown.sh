#!/usr/bin/env bash
# ADV-02 temizligi: yalniz EDOT Collector container'i, bu labin *-otellab data stream'leri (gizli olanlar dahil)
# ve _meta.sahibi=ADV-02 olan traces/logs/metrics-otel@custom sablonlari silinir.
# Ana cluster ve diger lablar etkilenmez.
set -uo pipefail
cd "$(dirname "$0")"
ES=http://127.0.0.1:9200; A='elastic:DevOps2026!'
docker compose -f docker-compose.otel.yml down 2>&1 | grep -E "Removed" | sed 's/^ *//' || echo "collector container yok"
DS=$(curl -s -u "$A" "$ES/_data_stream/*-otellab?expand_wildcards=all" | jq -r '[.data_streams[]?.name] | join(",")')
if [ -n "$DS" ]; then
  echo "data stream'ler ($(echo "$DS" | tr ',' '\n' | wc -l | tr -d ' ')) -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/$DS")"
else
  echo "data stream yok"
fi
for t in traces logs metrics; do
  if [ "$(curl -s -u "$A" "$ES/_component_template/$t-otel@custom" | jq -r '.component_templates[0].component_template._meta.sahibi // empty')" = ADV-02 ]; then
    echo "sablon $t-otel@custom -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_component_template/$t-otel@custom")"
  else
    echo "sablon $t-otel@custom -> yok ya da bu labin degil"
  fi
done
