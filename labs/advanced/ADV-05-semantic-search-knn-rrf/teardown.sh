#!/usr/bin/env bash
# ADV-05 temizligi: vektor-runbook index'i ve vektor-e5 inference endpoint'i silinir; endpoint'le birlikte modelin
# dagitimi kalkar (yaklasik 1 GB bellek bosalir). Indirilmis model cluster'da kalir. Ana cluster ve diger lablar etkilenmez.
set -uo pipefail
ES=http://127.0.0.1:9200; A='elastic:DevOps2026!'
echo "index vektor-runbook -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/vektor-runbook")"
echo "endpoint vektor-e5 -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_inference/text_embedding/vektor-e5")"
