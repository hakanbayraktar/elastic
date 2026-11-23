#!/usr/bin/env bash
# ADV-03 temizligi: yalniz bu labin kind cluster'i (k8s-loglar; DaemonSet ve demo uygulama icinde) ve ana cluster'daki
# k8s-pod-logs data stream'i ile sablonu silinir. Ana cluster'in kendisi ve diger lablar etkilenmez.
set -uo pipefail
ES=http://127.0.0.1:9200; A='elastic:DevOps2026!'
if kind get clusters 2>/dev/null | grep -qx k8s-loglar; then
  kind delete cluster --name k8s-loglar 2>&1 | tail -1
else
  echo "kind cluster k8s-loglar yok"
fi
echo "data stream k8s-pod-logs -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_data_stream/k8s-pod-logs")"
echo "sablon k8s-pod-logs -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/k8s-pod-logs")"
