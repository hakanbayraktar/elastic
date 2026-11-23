#!/usr/bin/env bash
# SIEM veri katmani:
#   1) siem-auth-*      index sablonu (ECS tipleri: ip, keyword, geo_point)
#   2) siem-threat-intel tehdit istihbarati listesi + enrich policy
#   3) siem-enrich      ingest pipeline: GeoIP + ASN + IOC eslesmesi + risk skoru
set -euo pipefail
ES_URL="${ES_URL:-http://127.0.0.1:9200}"
KIBANA_URL="${KIBANA_URL:-http://127.0.0.1:5601}"
es() { curl -s -u 'elastic:DevOps2026!' "$@"; }
kbn() { curl -s -u 'elastic:DevOps2026!' -H 'kbn-xsrf: true' "$@"; }

echo "[1/4] siem-auth-* index sablonu"
es -X PUT "${ES_URL}/_index_template/siem-auth" -H 'Content-Type: application/json' -d '{
  "index_patterns": ["siem-auth-*"],
  "priority": 200,
  "template": {
    "settings": { "number_of_shards": 1, "number_of_replicas": 0,
                  "index.default_pipeline": "siem-enrich" },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "event": {
          "properties": {
            "kind": { "type": "keyword" }, "dataset": { "type": "keyword" },
            "category": { "type": "keyword" }, "action": { "type": "keyword" },
            "outcome": { "type": "keyword" }, "risk_score": { "type": "integer" }
          }
        },
        "user":   { "properties": { "name": { "type": "keyword" } } },
        "source": {
          "properties": {
            "ip":   { "type": "ip" },
            "port": { "type": "integer" },
            "geo":  { "properties": { "location": { "type": "geo_point" },
                                      "country_name": { "type": "keyword" },
                                      "country_iso_code": { "type": "keyword" },
                                      "city_name": { "type": "keyword" } } },
            "as":   { "properties": { "number": { "type": "long" },
                                      "organization": { "properties": { "name": { "type": "keyword" } } } } }
          }
        },
        "threat": {
          "properties": {
            "indicator": {
              "properties": {
                "ip": { "type": "ip" },
                "type": { "type": "keyword" },
                "description": { "type": "text" },
                "provider": { "type": "keyword" },
                "confidence": { "type": "keyword" },
                "matched": { "properties": { "field": { "type": "keyword" } } }
              }
            }
          }
        },
        "host":    { "properties": { "name": { "type": "keyword" } } },
        "process": { "properties": { "name": { "type": "keyword" }, "pid": { "type": "long" },
                                     "command_line": { "type": "text" } } },
        "authentication": { "properties": { "method": { "type": "keyword" } } },
        "log": { "properties": { "detail": { "type": "text" },
                                 "file": { "properties": { "path": { "type": "keyword" } } } } },
        "message": { "type": "text" },
        "tags": { "type": "keyword" }
      }
    }
  }
}' >/dev/null
echo "      ok (source.ip -> ip, source.geo.location -> geo_point, default_pipeline -> siem-enrich)"

echo "[2/4] Tehdit istihbarati listesi (siem-threat-intel)"
es -X PUT "${ES_URL}/siem-threat-intel" -H 'Content-Type: application/json' -d '{
  "settings": { "number_of_replicas": 0 },
  "mappings": { "properties": {
    "ip": { "type": "ip" }, "type": { "type": "keyword" },
    "description": { "type": "text" }, "provider": { "type": "keyword" },
    "confidence": { "type": "keyword" } } }
}' >/dev/null 2>&1 || true

# Lab icin kucuk bir IOC listesi. Gercek hayatta bu index MISP/AbuseIPDB gibi
# bir beslemeden periyodik olarak guncellenir.
es -X POST "${ES_URL}/siem-threat-intel/_bulk?refresh=true" -H 'Content-Type: application/json' --data-binary '
{"index":{"_id":"203.0.113.77"}}
{"ip":"203.0.113.77","type":"ipv4-addr","provider":"lab-ioc-feed","confidence":"high","description":"Lab senaryosu: brute force sonrasi basarili giris yapan kaynak"}
{"index":{"_id":"203.0.113.9"}}
{"ip":"203.0.113.9","type":"ipv4-addr","provider":"lab-ioc-feed","confidence":"medium","description":"Bilinen tarama altyapisi (ornek IOC)"}
{"index":{"_id":"198.51.100.23"}}
{"ip":"198.51.100.23","type":"ipv4-addr","provider":"lab-ioc-feed","confidence":"low","description":"Supheli cikis dugumu (ornek IOC)"}
' >/dev/null
echo "      ok ($(es "${ES_URL}/siem-threat-intel/_count" | jq -r .count) gosterge)"

echo "[3/4] Enrich policy: IOC listesini bellekte arama tablosuna cevir"
es -X PUT "${ES_URL}/_enrich/policy/siem-threat-ip" -H 'Content-Type: application/json' -d '{
  "match": { "indices": "siem-threat-intel", "match_field": "ip",
             "enrich_fields": ["type", "description", "provider", "confidence"] }
}' >/dev/null 2>&1 || true
es -X POST "${ES_URL}/_enrich/policy/siem-threat-ip/_execute?wait_for_completion=true" >/dev/null
echo "      ok (policy derlendi)"

echo "[4/4] Ingest pipeline: siem-enrich (GeoIP + ASN + IOC + risk skoru)"
es -X PUT "${ES_URL}/_ingest/pipeline/siem-enrich" -H 'Content-Type: application/json' -d '{
  "description": "SIEM zenginlestirme: cografya, ag sahibi, tehdit istihbarati eslesmesi ve risk skoru",
  "processors": [
    { "geoip": { "field": "source.ip", "target_field": "source.geo", "ignore_missing": true, "ignore_failure": true } },
    { "geoip": { "field": "source.ip", "target_field": "source.as", "database_file": "GeoLite2-ASN.mmdb",
                 "properties": ["asn", "organization_name"], "ignore_missing": true, "ignore_failure": true } },
    { "rename": { "field": "source.as.asn", "target_field": "source.as.number", "ignore_missing": true } },
    { "rename": { "field": "source.as.organization_name", "target_field": "source.as.organization.name", "ignore_missing": true } },
    { "enrich": { "policy_name": "siem-threat-ip", "field": "source.ip", "target_field": "threat.indicator",
                  "max_matches": 1, "ignore_missing": true, "ignore_failure": true } },
    { "set": { "if": "ctx.threat?.indicator?.ip != null", "field": "threat.indicator.matched.field", "value": "source.ip" } },
    { "script": {
        "description": "Basit risk skoru: olay turu ve IOC eslesmesine gore 0-100",
        "source": "int r = 0; def e = ctx.event; if (e != null) { if (e.outcome == \"failure\") { r += 10; } if (e.action == \"ssh_invalid_user\") { r += 15; } if (e.action == \"user_created\") { r += 50; } if (e.action == \"sudo_command\") { r += 20; } if (e.action == \"ssh_login_success\") { r += 5; } } if (ctx.threat?.indicator?.matched?.field != null) { r += 40; } if (r > 100) { r = 100; } if (ctx.event == null) { ctx.event = [:]; } ctx.event.risk_score = r;"
    } }
  ],
  "on_failure": [
    { "append": { "field": "tags", "value": "siem_enrich_failure" } },
    { "set": { "field": "error.message", "value": "{{ _ingest.on_failure_message }}" } }
  ]
}' >/dev/null
echo "      ok"
echo
echo "[+] SIEM veri katmani hazir."
