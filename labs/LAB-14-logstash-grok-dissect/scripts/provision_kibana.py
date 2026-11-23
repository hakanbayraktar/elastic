#!/usr/bin/env python3
"""LAB-14: 'grok-*' data view'ini ve Logstash log analizi panosunu kurar.

Paneller, bu labin pipeline'inin urettigi gercek alanlarla eslenmistir:
  service, loglevel, tags, payload.response_time_ms

Panonun kurulumu Kibana Saved Objects API'si uzerinden yapilir; ayni panelleri
Lens arayuzunde elle de kurabilirsiniz (README, Adim 7).
"""
import base64
import json
import os
import ssl
import sys
import time
from urllib import error, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lens_builder as lb

BASE = os.environ.get("KIBANA_URL", "http://localhost:5601").rstrip("/")
USER = os.environ.get("ES_USER", os.environ.get("ELASTIC_USER", "elastic"))
PWD = os.environ.get("ELASTIC_PASSWORD", "DevOps2026!")
HEADERS = {
    "Content-Type": "application/json",
    "kbn-xsrf": "grok-provision",
    "Authorization": "Basic " + base64.b64encode(f"{USER}:{PWD}".encode()).decode(),
}
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

VIEW_ID = "grok-logs"
VIEW = {"title": "grok-*", "name": "Logstash Grok Logları", "timeFieldName": "@timestamp"}
DASHBOARD_ID = "grok-logstash-overview"
DASHBOARD_TITLE = "Logstash Grok Ayrıştırma ve Log Analizi"

PARSED = 'not tags : "_grokparsefailure"'
UNPARSED = 'tags : "_grokparsefailure"'

# (panel_id, baslik, tur, argumanlar, konum)
PANELS = [
    ("grok-parsed-count", "Ayrıştırılan Olay Sayısı", "metric",
     {"metric": ("count", PARSED), "label": "Ayrıştırılan olay"},
     {"x": 0, "y": 0, "w": 16, "h": 10}),

    ("grok-unparsed-count", "Ayrıştırılamayan Olay (Karantina)", "metric",
     {"metric": ("count", UNPARSED), "label": "_grokparsefailure"},
     {"x": 16, "y": 0, "w": 16, "h": 10}),

    ("grok-error-count", "Hata Seviyesindeki Olay Sayısı", "metric",
     {"metric": ("count", 'loglevel : "error"'), "label": "ERROR olayları"},
     {"x": 32, "y": 0, "w": 16, "h": 10}),

    ("grok-errors-by-service", "Servis Bazında Hata Sayısı", "xy",
     {"bucket": ("terms", "service", 10),
      "metric": ("count", 'loglevel : "error"'),
      "label": "ERROR olayları",
      "series_type": "bar_horizontal"},
     {"x": 0, "y": 10, "w": 24, "h": 15}),

    ("grok-levels-over-time", "Zaman İçinde Log Seviyesi Dağılımı", "xy",
     {"bucket": ("date_histogram", "@timestamp"),
      "metric": ("count",),
      "split": ("terms", "loglevel", 5),
      "series_type": "bar_stacked"},
     {"x": 24, "y": 10, "w": 24, "h": 15}),

    ("grok-latency-by-service", "Servis Bazında Yanıt Süresi (p95) ve Olay Sayısı", "table",
     {"buckets": [("terms", "service", 10)],
      "metrics": [("count",), ("percentile", "payload.response_time_ms", 95)]},
     {"x": 0, "y": 25, "w": 48, "h": 15}),
]

BUILDERS = {"metric": lb.metric_panel, "xy": lb.xy_panel,
            "pie": lb.pie_panel, "table": lb.table_panel}


def api(method, path, body=None, allow=()):
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(BASE + path, data=payload, headers=HEADERS, method=method)
    try:
        with request.urlopen(req, context=CONTEXT, timeout=40) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        if exc.code not in allow:
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}: "
                               f"{exc.read().decode('utf-8', 'replace')}") from None
        return exc.code, {}


def main():
    print(f"Kibana bekleniyor ({BASE}) ...", flush=True)
    for _ in range(30):
        try:
            api("GET", "/api/status")
            break
        except (OSError, RuntimeError):
            time.sleep(2)
    else:
        raise SystemExit("Kibana'ya erisilemedi; KIBANA_URL ve servis durumunu kontrol edin.")

    status, _ = api("GET", f"/api/data_views/data_view/{VIEW_ID}", allow=(404,))
    if status == 404:
        api("POST", "/api/data_views/data_view", {"data_view": {"id": VIEW_ID, **VIEW}})
    else:
        api("POST", f"/api/data_views/data_view/{VIEW_ID}",
            {"data_view": VIEW, "refresh_fields": True})
    print(f"[+] Data view hazir: {VIEW['name']} ({VIEW['title']})", flush=True)

    panels, references = [], []
    for panel_id, title, kind, options, grid in PANELS:
        payload = BUILDERS[kind](panel_id, title, VIEW_ID, **options)
        lb.validate(payload)
        api("POST", f"/api/saved_objects/lens/{panel_id}?overwrite=true", payload)
        panel_spec, ref_spec = lb.dashboard_panel(panel_id, panel_id, grid)
        panels.append(panel_spec)
        references.append(ref_spec)
        print(f"[+] Panel hazir: {title}", flush=True)

    lb.validate_dashboard(panels, references)
    api("POST", f"/api/saved_objects/dashboard/{DASHBOARD_ID}?overwrite=true", {
        "attributes": {
            "title": DASHBOARD_TITLE,
            "description": "Logstash grok ayrıştırması, koşullu yönlendirme ve "
                           "ayrıştırma sağlığı",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "syncColors": True,
                                       "hidePanelTitles": False}),
            "timeRestore": True,
            "timeFrom": "now-30m",
            "timeTo": "now",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"},
                                                "filter": []})
            },
        },
        "references": references,
    })
    print(f"\n[+] Pano kuruldu: {DASHBOARD_TITLE}")
    print(f"    {BASE}/app/dashboards#/view/{DASHBOARD_ID}")


if __name__ == "__main__":
    main()
