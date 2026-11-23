#!/usr/bin/env bash
# LAB-19 temizligi: yalniz bu labin 3-node cluster'ini ve (varsa) Kibana'sini, volume'larini (veri, sertifika,
# snapshot deposu), CA kopyasini ve Python sanal ortamini siler. LAB-23 de ayni cluster'i kullanir; LAB-23'ü
# yapacaksaniz bu betigi sonra calistirin. LAB-01 ana cluster'i (9200) ve diger lablar etkilenmez.
set -uo pipefail
cd "$(dirname "$0")"
ENV_ARGS=(); [ -f starter/.env ] && ENV_ARGS=(--env-file starter/.env)
docker compose "${ENV_ARGS[@]}" -f starter/docker-compose.yml -f starter/docker-compose.kibana.yml down -v --remove-orphans 2>&1 \
  | grep -E "Removed" | sed 's/^ *//'
rm -rf .ca .venv && echo ".ca ve .venv silindi"
LEFT=$(docker ps -a --format '{{.Names}}' | grep -E '^elastic-cluster-|^kibana-cluster$' || true)
[ -z "$LEFT" ] && echo "konteyner kalmadi" || echo "KALDI: $LEFT"
