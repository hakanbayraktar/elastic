#!/usr/bin/env python3
"""LAB-27 isteğe bağlı: IP başına istek sayısında anomali arayan ML işi ve iki örnek SLO kurar.
ML ve SLO ücretli özelliklerdir; trial lisans gerekir. Tekrar çalıştırılabilir: var olanı yeniden kurmaz.
Silmek için: ./teardown.sh
"""
import base64
import json
from urllib import error, request

ES = "http://127.0.0.1:9200"
KB = "http://127.0.0.1:5601"
YETKI = "Basic " + base64.b64encode(b"elastic:DevOps2026!").decode()
ACCESS = {"term": {"event.dataset": "apache.access"}}
IS = "apache-ip-istek-anomali"


def call(base, method, path, body=None, allow=()):
    headers = {"Content-Type": "application/json", "Authorization": YETKI, "kbn-xsrf": "true"}
    req = request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                          headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        if exc.code in allow:
            return exc.code, {}
        raise SystemExit(f"HATA {method} {path}: HTTP {exc.code}: {exc.read().decode()[:300]}")


def ml():
    if call(ES, "GET", f"/_ml/anomaly_detectors/{IS}", allow=(404,))[0] == 404:
        call(ES, "PUT", f"/_ml/anomaly_detectors/{IS}", {
            "description": "Bir IP'den gelen Apache istek sayısında olağandışı artış",
            "analysis_config": {"bucket_span": "5m", "detectors": [
                {"function": "high_count", "partition_field_name": "source.ip",
                 "detector_description": "Bir IP'den olağandışı çok istek"}],
                "influencers": ["source.ip", "source.geo.country_iso_code", "url.path"]},
            "analysis_limits": {"model_memory_limit": "32mb"},
            "data_description": {"time_field": "@timestamp"},
            "datafeed_config": {"datafeed_id": IS + "-feed", "indices": ["apache-web-*"],
                                "query": {"bool": {"filter": [ACCESS]}}}})
    durum = call(ES, "GET", f"/_ml/anomaly_detectors/{IS}/_stats")[1]["jobs"][0]["state"]
    if durum != "opened":
        call(ES, "POST", f"/_ml/anomaly_detectors/{IS}/_open", {})
    feed = call(ES, "GET", f"/_ml/datafeeds/{IS}-feed/_stats")[1]["datafeeds"][0]["state"]
    if feed != "started":
        call(ES, "POST", f"/_ml/datafeeds/{IS}-feed/_start", {"start": "now-1h"})
    print(f"ML işi: {IS} (açık, veri akışı başladı)")


def slo(slo_id, ad, iyi, hedef):
    if call(KB, "GET", f"/api/observability/slos/{slo_id}", allow=(404,))[0] == 200:
        print(f"SLO zaten var: {slo_id}")
        return
    call(KB, "POST", "/api/observability/slos", {
        "id": slo_id, "name": ad, "description": "Örnek hedef; sözleşmeye bağlı bir SLA değildir.",
        "indicator": {"type": "sli.kql.custom", "params": {
            "index": "apache-web-*", "dataViewId": "apache-web-logs", "timestampField": "@timestamp",
            "good": f'event.dataset: "apache.access" and {iyi}', "total": 'event.dataset: "apache.access"'}},
        "timeWindow": {"duration": "30d", "type": "rolling"}, "budgetingMethod": "occurrences",
        "objective": {"target": hedef}, "settings": {"frequency": "1m", "syncDelay": "1m"},
        "tags": ["apache-web"]})
    print(f"SLO: {slo_id}")


ml()
slo("apache-web-erisilebilirlik", "Apache erişilebilirlik %99,9 / 30 gün", "http.response.status_code < 500", 0.999)
slo("apache-web-gecikme-500ms", "Apache isteklerinin %95'i 500 ms altında / 30 gün", "event.duration <= 500000000", 0.95)
