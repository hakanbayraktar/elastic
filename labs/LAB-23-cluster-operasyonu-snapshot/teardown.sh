#!/usr/bin/env bash
# LAB-23 temizligi: yalniz bu labin cluster icindeki kaynaklari silinir: SLM politikasi, snapshot'lar, repository,
# geri yuklenen index, cluster-arsiv (segment ornegi) ve node bosaltma ayari. 3-node cluster'in kendisi LAB-19'a aittir ve calismaya devam eder
# (kaldirmak icin ../LAB-19-3-node-tls-cluster/teardown.sh). LAB-01 ana cluster'i etkilenmez.
set -uo pipefail
cd "$(dirname "$0")"
L20=../LAB-19-3-node-tls-cluster
[ -f "$L20/.ca/ca.crt" ] || { echo "3-node cluster kurulu degil; silinecek kaynak yok"; exit 0; }
set -a; . "$L20/starter/.env"; set +a
es() { curl -s --cacert "$L20/.ca/ca.crt" -u "elastic:$CLUSTER_ELASTIC_PASSWORD" -H 'Content-Type: application/json' "$@"; }
U=https://127.0.0.1:19208
kod() { es -o /dev/null -w '%{http_code}' "$@"; }
echo "SLM politikasi cluster-gunluk -> $(kod -X DELETE "$U/_slm/policy/cluster-gunluk")"
SNAPS=$(es "$U/_snapshot/cluster-yedek/_all" | jq -r '[.snapshots[]?.snapshot] | join(",")')
[ -n "$SNAPS" ] && echo "snapshot'lar ($(echo "$SNAPS" | tr ',' '\n' | wc -l | tr -d ' ')) -> $(kod -X DELETE "$U/_snapshot/cluster-yedek/$SNAPS")"
echo "repository cluster-yedek -> $(kod -X DELETE "$U/_snapshot/cluster-yedek")"
echo "index geri-cluster-urunler -> $(kod -X DELETE "$U/geri-cluster-urunler")"
echo "index cluster-arsiv -> $(kod -X DELETE "$U/cluster-arsiv")"
echo "node bosaltma ayari -> $(kod -X PUT "$U/_cluster/settings" -d '{"persistent": {"cluster.routing.allocation.exclude._name": null}}')"
