#!/usr/bin/env bash
# grok-* index sablonu: alan tipleri sabitlenir, tek shard / sifir replika.
# Alan tipini sablonla sabitlemek dinamik eslemenin surpriz tip secmesini onler
# (ornek: response_time_ms alaninin ilk belgeye gore "long" yerine "text" olmasi).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

es -X PUT "${ES_URL}/_index_template/grok-logs" -H 'Content-Type: application/json' -d '{
  "index_patterns": ["grok-app-*", "grok-error-*", "grok-unparsed-*"],
  "priority": 200,
  "template": {
    "settings": { "number_of_shards": 1, "number_of_replicas": 0 },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "service":    { "type": "keyword" },
        "loglevel":   { "type": "keyword" },
        "env":        { "type": "keyword" },
        "tags":       { "type": "keyword" },
        "rest_msg":   { "type": "text" },
        "message":    { "type": "text" },
        "payload": {
          "properties": {
            "response_time_ms": { "type": "integer" },
            "user_id":          { "type": "long" },
            "product_id":       { "type": "long" },
            "active_conns":     { "type": "integer" },
            "order_id":         { "type": "keyword" },
            "event":            { "type": "keyword" },
            "error":            { "type": "text" }
          }
        }
      }
    }
  }
}'
echo
echo "[+] Sablon hazir: grok-logs (grok-app-*, grok-error-*, grok-unparsed-*)"
