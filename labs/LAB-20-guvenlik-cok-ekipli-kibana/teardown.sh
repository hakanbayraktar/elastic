#!/usr/bin/env bash
# LAB-20 temizligi: yalniz bu labin guvenlik-talepler index'ini, gvn-* rollerini, gvn_* kullanicilarini,
# gvn-form API key'ini ve gvn-destek Space'ini (icindeki data view'la) adiyla siler.
# elastic kullanicisina, default Space'e ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601
del() { echo "$1 -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' -X DELETE "$2")"; }
for s in gvn-destek; do del "space $s" "$KB/api/spaces/space/$s"; done
for u in gvn_okuyucu gvn_destek gvn_izleyici gvn_rapor; do del "kullanici $u" "$ES/_security/user/$u"; done
for r in gvn-okuyucu gvn-destek gvn-rapor; do del "rol $r" "$ES/_security/role/$r"; done
echo "api key gvn-form -> $(curl -s -u "$A" -X DELETE "$ES/_security/api_key" -H 'Content-Type: application/json' -d '{"name": "gvn-form"}' | jq -c '{invalidated: (.invalidated_api_keys | length)}')"
del "index guvenlik-talepler" "$ES/guvenlik-talepler"
