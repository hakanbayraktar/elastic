#!/usr/bin/env bash
# Gerçek Logstash üzerinde dissect ve grok filtre maliyetini ölçer.
# Aynı satır generator girdisiyle N kez üretilir; üç geçiş yapılır:
#   referans (filtre yok) / yalnız dissect / yalnız grok
# Her geçiş aynı JVM açılış maliyetini taşıdığı için anlamlı olan FARKLARDIR.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

COUNT="${BENCH_COUNT:-300000}"
NOISE="${BENCH_NOISE:-1.5}"   # JVM açılışından gelen ölçüm gürültüsü (saniye)
cd "${LAB_DIR}"

run_pass() {
  local conf="$1" start end
  start=$(date +%s.%N)
  docker compose --profile tools run --rm --no-TTY -e BENCH_COUNT="${COUNT}" logstash-tools \
    -f "/usr/share/logstash/pipeline/${conf}" >/dev/null 2>&1
  end=$(date +%s.%N)
  awk -v s="${start}" -v e="${end}" 'BEGIN { printf "%.2f", e - s }'
}

printf '[+] %s olay x 3 gecis (her gecis ayri, tek seferlik konteynerde)\n' "${COUNT}"
BASE=$(run_pass bench-baseline.conf); printf '    referans (filtre yok) : %s s\n' "${BASE}"
DIS=$(run_pass bench-dissect.conf);   printf '    yalniz dissect        : %s s\n' "${DIS}"
GRK=$(run_pass bench-grok.conf);      printf '    yalniz grok           : %s s\n' "${GRK}"

awk -v c="${COUNT}" -v b="${BASE}" -v d="${DIS}" -v g="${GRK}" -v n="${NOISE}" 'BEGIN {
  gd = g - d; dd = d - b;
  printf "\n    grok - dissect        : %+.2f s  ->  olay basina %+.1f us ek CPU\n", gd, gd * 1e6 / c;
  # Fark iki yonde de olculur: dissect referanstan hizli cikamaz, -n altindaki deger de gurultudur.
  if (dd < n && dd > -n)
    printf "    dissect - referans    : %+.2f s  ->  olcum gurultusu (<%.1f s) icinde: dissect pratikte bedava\n", dd, n;
  else if (dd <= -n)
    printf "    dissect - referans    : %+.2f s  ->  dissect referanstan hizli olamaz: gurultu esigini (%.1f s) asan dalgalanma, betigi tekrar calistirin\n", dd, n;
  else
    printf "    dissect - referans    : %+.2f s  ->  olay basina %+.1f us ek CPU\n", dd, dd * 1e6 / c;
}'
