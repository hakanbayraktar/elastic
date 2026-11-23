#!/usr/bin/env bash
# LAB-01 dogrulama: ana cluster (Elasticsearch + Kibana) kurulu, erisilebilir ve trial lisansli mi?
set -u
ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601; AUTH='elastic:DevOps2026!'
FAIL=0
ok()   { echo "  [OK]   $1"; }
bad()  { echo "  [HATA] $1"; FAIL=$((FAIL + 1)); }
info() { echo "  [i]    $1"; }

echo "1. Sunucu"
[ "$(cat /proc/sys/vm/max_map_count)" -ge 262144 ] && ok "vm.max_map_count >= 262144" || bad "vm.max_map_count dusuk"

echo "2. Container'lar"
for c in elasticsearch-lab00 kibana-lab00; do
  [ "$(docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null)" = "true" ] && ok "$c calisiyor" || bad "$c calismiyor"
done
[ "$(docker inspect -f '{{.State.ExitCode}}' setup-lab00 2>/dev/null)" = "0" ] && ok "setup-lab00 Exited (0)" || bad "setup-lab00 basarisiz"

echo "3. Elasticsearch"
[ "$(curl -s -o /dev/null -w '%{http_code}' $ES)" = "401" ] && ok "parolasiz istek 401" || bad "guvenlik kapali olabilir"
V=$(curl -s -u "$AUTH" "$ES?filter_path=version.number" | jq -r .version.number)
[ "$V" = "9.5.5" ] && ok "surum $V" || bad "surum beklenen degil: $V"
H=$(curl -s -u "$AUTH" "$ES/_cluster/health" | jq -r .status)
case "$H" in green) ok "cluster green";; yellow) info "cluster yellow (replica isteyen index varsa normal)";; *) bad "cluster $H";; esac
L=$(curl -s -u "$AUTH" "$ES/_license" | jq -r '.license.type + "/" + .license.status')
[ "$L" = "trial/active" ] && ok "lisans $L" || bad "lisans $L (Adim 5)"

echo "4. Kibana"
K=$(curl -s -u "$AUTH" "$KB/api/status" | jq -r .status.overall.level)
[ "$K" = "available" ] && ok "Kibana available" || bad "Kibana $K"
PUB=$(docker inspect kibana-lab00 -f '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^SERVER_PUBLICBASEURL=//p')
case "$PUB" in *localhost*|"") bad "SERVER_PUBLICBASEURL localhost (Adim 2 export)";; *) ok "SERVER_PUBLICBASEURL $PUB";; esac

echo "5. Dis erisim"
HOST=$(hostname -s)
for sub in kibana elastic; do
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "https://$HOST-$sub.devopsatolyesi.com/")
  case "$code" in 200|302|401) ok "https://$HOST-$sub.devopsatolyesi.com -> $code";; *) bad "https://$HOST-$sub.devopsatolyesi.com -> $code";; esac
done

echo
[ "$FAIL" -eq 0 ] && { echo "[SONUC] LAB-01 tamam"; exit 0; } || { echo "[SONUC] $FAIL hata"; exit 1; }
