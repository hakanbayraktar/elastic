#!/usr/bin/env bash
# Demo servislere sabit sayida istek atar: nginx 20 x 200 + 5 x 404, API 10 x 200 + 3 x 500.
# Ayrica host'un auth.log'una 5 deneme satiri yazar (logger, auth tesisi). Satirlar kosuya ozel
# etiket tasir (RUN degiskeni, yoksa saat): onceki kosularin satirlariyla karismaz.
set -euo pipefail
ok() { curl -s -o /dev/null -w '%{http_code}\n' "$1"; }
for _ in $(seq 1 20); do ok http://127.0.0.1:8081/ ; done | sort | uniq -c | sed 's/^/  nginx /'
for _ in $(seq 1 5);  do ok http://127.0.0.1:8081/yok ; done | sort | uniq -c | sed 's/^/  nginx /'
for _ in $(seq 1 10); do ok http://127.0.0.1:3001/api/pay ; done | sort | uniq -c | sed 's/^/  api   /'
for _ in $(seq 1 3);  do ok http://127.0.0.1:3001/api/fail ; done | sort | uniq -c | sed 's/^/  api   /'
RUN="${RUN:-$(date +%H%M%S)}"
for i in $(seq 1 5); do logger -p auth.notice -t "beats-lab-${RUN}" "deneme oturumu $i"; done
echo "  auth.log: 5 satir (etiket beats-lab-${RUN})"
