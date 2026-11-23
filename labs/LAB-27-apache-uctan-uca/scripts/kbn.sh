#!/usr/bin/env bash
# Kibana API'sine kimlik ve gerekli basliklarla istek atar.
# Kullanim: ./scripts/kbn.sh METHOD /api/yol ['json govde' | @- (stdin)]
set -euo pipefail
M="$1"; P="$2"; shift 2
ARGS=(-s -u 'elastic:DevOps2026!' -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X "$M")
[ $# -gt 0 ] && ARGS+=(-d "$1")
curl "${ARGS[@]}" "http://127.0.0.1:5601$P"
