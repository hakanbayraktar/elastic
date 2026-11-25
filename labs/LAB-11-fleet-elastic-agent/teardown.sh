#!/usr/bin/env bash
# LAB-11 temizligi: yalniz bu labin konteynerlerini, Fleet'teki ajan kayitlarini, "Fleet Server Policy" ve
# "Lab Linux sunucu" politikalarini (icindeki integration'larla), Fleet Server'in service token'larini,
# labin Fleet Server adresini (https://fleet-server:8220), labin data stream'lerini ve Adim 7'nin
# "Sunucu CPU (Fleet)" panosunu siler. Ana cluster'a, Fleet output ayarina ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601; H='kbn-xsrf: true'; J='Content-Type: application/json'
docker compose down -v 2>&1 | grep -E "Removed" | sed 's/^ *//'
# Politikalar adla bulunur: arayuzde acilan politikanin id'si rastgeledir.
POLS=$(curl -s -u "$A" "$KB/api/fleet/agent_policies?perPage=100" \
  | jq -r '.items[] | select(.name == "Fleet Server Policy" or .name == "Lab Linux sunucu") | .id')
N=0
for id in $(curl -s -u "$A" "$KB/api/fleet/agents?perPage=100&showInactive=true" \
  | jq -r --arg p "$(echo $POLS)" '.items[] | select(.policy_id as $i | ($p | split(" ") | index($i))) | .id'); do
  curl -s -u "$A" -H "$H" -H "$J" -X POST "$KB/api/fleet/agents/$id/unenroll" -d '{"revoke": true}' -o /dev/null
  N=$((N + 1))
done
echo "ajan kaydi kaldirildi -> $N"
for p in $POLS; do
  AD=$(curl -s -u "$A" "$KB/api/fleet/agent_policies/$p" | jq -r '.item.name')
  echo "politika $AD -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H "$H" -H "$J" -X POST "$KB/api/fleet/agent_policies/delete" -d "{\"agentPolicyId\": \"$p\", \"force\": true}")"
done
N=0
for t in $(curl -s -u "$A" "$ES/_security/service/elastic/fleet-server/credential" | jq -r '.tokens | keys[]'); do
  curl -s -o /dev/null -u "$A" -X DELETE "$ES/_security/service/elastic/fleet-server/credential/token/$t"; N=$((N + 1))
done
echo "service token -> $N silindi"
for id in $(curl -s -u "$A" "$KB/api/fleet/fleet_server_hosts" | jq -r '.items[] | select(.host_urls | index("https://fleet-server:8220")) | .id'); do
  curl -s -o /dev/null -u "$A" -H "$H" -H "$J" -X PUT "$KB/api/fleet/fleet_server_hosts/$id" -d '{"is_default": false}'
  echo "fleet server adresi -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H "$H" -X DELETE "$KB/api/fleet/fleet_server_hosts/$id")"
done
# fleetlab: Linux politikasi. default: Fleet Server Policy'nin ajan izleme ve System verisi (yalniz Fleet ajanlari yazar).
DS=$(curl -s -u "$A" "$ES/_data_stream/*-fleetlab,*-elastic_agent*-default,metrics-fleet_server.*-default,logs-system.*-default,metrics-system.*-default" \
  | jq -r '[.data_streams[].name] | join(",")')
echo "data stream -> $([ -n "$DS" ] && curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/$DS" || echo yok)"
N=0
for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=dashboard&search_fields=title&search=Sunucu&per_page=100" | jq -r '.saved_objects[] | select(.attributes.title == "Sunucu CPU (Fleet)") | .id'); do
  curl -s -o /dev/null -u "$A" -H "$H" -X DELETE "$KB/api/saved_objects/dashboard/$id"; N=$((N + 1))
done
echo "pano (Sunucu CPU (Fleet)) -> $N"
# Labin kurdugu integration paketleri: hazir panolari, index sablonlari ve ingest pipeline'lari paketle gider.
# Politikalar yukarida silindigi icin paketleri kullanan kalmaz; bir sonraki kurulum onlari yeniden yukler.
N=0
for p in nginx system fleet_server elastic_agent; do
  V=$(curl -s -u "$A" "$KB/api/fleet/epm/packages/$p" | jq -r '.item.installationInfo.version // empty')
  [ -n "$V" ] && [ "$(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H "$H" -X DELETE "$KB/api/fleet/epm/packages/$p/$V")" = 200 ] && N=$((N + 1))
done
echo "integration paketi -> $N kaldirildi"
# elastic_agent paketi kurulurken Fleet "[Elastic Agent] ..." alerting kurallarini da acar (kapali); paket
# kaldirilinca kurallar kalir. Id'leri fleet-default-elastic_agent- ile baslar; yalniz Fleet kullanan bu lab kurar.
N=0
for id in $(curl -s -u "$A" "$KB/api/alerting/rules/_find?per_page=100&search_fields=name&search=%22Elastic%20Agent%22" \
  | jq -r '.data[] | select(.id | startswith("fleet-default-elastic_agent-")) | .id'); do
  curl -s -o /dev/null -u "$A" -H "$H" -X DELETE "$KB/api/alerting/rule/$id"; N=$((N + 1))
done
echo "Elastic Agent kurali -> $N silindi"
rm -f .env .env.fleet
