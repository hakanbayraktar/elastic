#!/usr/bin/env bash
# LAB-24 temizligi: yalniz bu labin perf-urunler index'ini, Stack Monitoring icin actigi iki Metricbeat container'ini,
# .monitoring-es-8-mb data stream'ini ve izleme_mb kullanicisini (3-node cluster aciksa orada da) siler.
# Ana cluster'a, 3-node cluster'in kendisine ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200
CA=../LAB-19-3-node-tls-cluster/.ca/ca.crt; C3=https://127.0.0.1:19208
echo "index perf-urunler -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/perf-urunler")"
docker compose --profile cluster3 down 2>&1 | grep -E "Removed" | sed 's/^ *//'
echo "data stream .monitoring-es-8-mb -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/.monitoring-es-8-mb")"
echo "kullanici izleme_mb -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_security/user/izleme_mb")"
# 7. adim: 3-node cluster aciksa oradaki izleme kullanicisi da silinir
if [ -f "$CA" ] && curl -s -o /dev/null --cacert "$CA" "$C3"; then
  echo "kullanici izleme_mb (3-node) -> $(curl -s -o /dev/null -w '%{http_code}' --cacert "$CA" -u "$A" -X DELETE "$C3/_security/user/izleme_mb")"
fi
