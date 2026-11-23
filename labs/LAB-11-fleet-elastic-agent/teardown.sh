#!/usr/bin/env bash
# LAB-11 temizligi: yalniz bu labin konteynerlerini, Fleet'teki ajan kayitlarini, fleet-server-policy ve
# fleet-linux-policy politikalarini (icindeki system-lab ve nginx-lab integration'lariyla), servis token'ini,
# namespace'i fleetlab olan data stream'leri ve Adim 7'nin "Sunucu CPU (Fleet)" panosunu siler.
# Ana cluster'a, Fleet'in genel ayarlarina (output, sunucu adresi) ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601; H='kbn-xsrf: true'; J='Content-Type: application/json'
docker compose down -v 2>&1 | grep -E "Removed" | sed 's/^ *//'
N=0
for id in $(curl -s -u "$A" "$KB/api/fleet/agents?perPage=100&showInactive=true" | jq -r '.items[] | select(.policy_id=="fleet-server-policy" or .policy_id=="fleet-linux-policy") | .id'); do
  curl -s -u "$A" -H "$H" -H "$J" -X POST "$KB/api/fleet/agents/$id/unenroll" -d '{"revoke": true}' -o /dev/null
  N=$((N + 1))
done
echo "ajan kaydi kaldirildi -> $N"
for p in fleet-linux-policy fleet-server-policy; do
  echo "politika $p -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H "$H" -H "$J" -X POST "$KB/api/fleet/agent_policies/delete" -d "{\"agentPolicyId\": \"$p\", \"force\": true}")"
done
echo "servis token -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_security/service/elastic/fleet-server/credential/token/fleet-lab-token")"
DS=$(curl -s -u "$A" "$ES/_data_stream/*-fleetlab" | jq -r '[.data_streams[].name] | join(",")')
echo "data stream (fleetlab) -> $([ -n "$DS" ] && curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/$DS" || echo yok)"
N=0
for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=dashboard&search_fields=title&search=Sunucu&per_page=100" | jq -r '.saved_objects[] | select(.attributes.title == "Sunucu CPU (Fleet)") | .id'); do
  curl -s -o /dev/null -u "$A" -H "$H" -X DELETE "$KB/api/saved_objects/dashboard/$id"; N=$((N + 1))
done
echo "pano (Sunucu CPU (Fleet)) -> $N"
rm -f .env.fleet
