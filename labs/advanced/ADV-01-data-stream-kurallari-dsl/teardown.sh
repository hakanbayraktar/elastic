#!/usr/bin/env bash
# ADV-01 temizligi: yalniz bu labin dsk-* data stream'leri, sablonlari ve dsk-ilm politikasi silinir;
# DSL kontrol araligi (data_streams.lifecycle.poll_interval) varsayilana doner. Ana cluster ve diger lablar etkilenmez.
set -uo pipefail
ES=http://127.0.0.1:9200; A='elastic:DevOps2026!'
kod() { curl -s -o /dev/null -w '%{http_code}' -u "$A" "$@"; }
for d in dsk-olaylar dsk-gecis; do echo "data stream $d -> $(kod -X DELETE "$ES/_data_stream/$d")"; done
for t in dsk-olaylar dsk-gecis; do echo "sablon $t -> $(kod -X DELETE "$ES/_index_template/$t")"; done
echo "ILM politikasi dsk-ilm -> $(kod -X DELETE "$ES/_ilm/policy/dsk-ilm")"
echo "DSL kontrol araligi -> $(kod -X PUT "$ES/_cluster/settings" -H 'Content-Type: application/json' -d '{"persistent": {"data_streams.lifecycle.poll_interval": null}}')"
