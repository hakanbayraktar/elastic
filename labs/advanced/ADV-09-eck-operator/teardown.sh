#!/usr/bin/env bash
# ADV-09 temizligi: yalniz bu labin kind cluster'i (k8s-eck; operator, Elasticsearch, Kibana, PVC icinde) ve indirilen
# CA dosyasi silinir. Ana cluster ve diger lablar (ADV-03'un k8s-loglar cluster'i dahil) etkilenmez.
set -uo pipefail
cd "$(dirname "$0")"
if kind get clusters 2>/dev/null | grep -qx k8s-eck; then
  kind delete cluster --name k8s-eck 2>&1 | tail -1
else
  echo "kind cluster k8s-eck yok"
fi
rm -f eck-ca.crt && echo "eck-ca.crt silindi"
