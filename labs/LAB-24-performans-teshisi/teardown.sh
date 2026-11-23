#!/usr/bin/env bash
# LAB-24 temizligi: yalniz bu labin perf-urunler index'ini, Stack Monitoring icin actigi Metricbeat container'ini,
# .monitoring-es-8-mb data stream'ini ve izleme_mb kullanicisini siler.
# Ana cluster'a ve diger lablara dokunmaz.
set -u
cd "$(dirname "$0")"
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200
echo "index perf-urunler -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/perf-urunler")"
docker compose down 2>&1 | grep -E "Removed" | sed 's/^ *//'
echo "data stream .monitoring-es-8-mb -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/.monitoring-es-8-mb")"
echo "kullanici izleme_mb -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_security/user/izleme_mb")"
