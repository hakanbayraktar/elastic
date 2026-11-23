#!/usr/bin/env bash
# ecommerce-fastapi-search temizligi: yalnizca bu projenin kaynaklari.
# Omurga (elasticsearch-lab00 / kibana-lab00) ve kibana_sample_data_ecommerce silinmez.
set -uo pipefail
cd "$(dirname "$0")"
ES_URL="${ELASTIC_URL:-http://localhost:9200}"
AUTH="${ELASTIC_USER:-elastic}:${ELASTIC_PASSWORD:-DevOps2026!}"

echo "[+] Arama servisi konteyneri ve imaji kaldiriliyor..."
docker compose -f docker-compose.app1.yml down --rmi local 2>&1 | tail -3

echo "[+] ecommerce_search_products index'i siliniyor..."
curl -s -u "$AUTH" -X DELETE "${ES_URL}/ecommerce_search_products?ignore_unavailable=true"
echo
echo "[+] Temizlik tamam. Omurga ve ornek veri etkilenmedi."
