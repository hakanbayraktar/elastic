#!/usr/bin/env python3
"""Create Apache log/metric Data Views, Lens panels and the operations dashboard."""
import base64
import json
import os
from pathlib import Path
import ssl
import sys
import time
from urllib import error, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lens_builder as lb

BASE = os.environ.get("KIBANA_URL", "http://127.0.0.1:5601").rstrip("/")
HEADERS = {"Content-Type": "application/json", "kbn-xsrf": "apache-web-observability"}
kuser = os.environ.get("KIBANA_USER", os.environ.get("ELASTIC_USER", "elastic"))
kpwd = os.environ.get("KIBANA_PASSWORD", os.environ.get("ELASTIC_PASSWORD", "DevOps2026!"))
if kuser:
    secret = f"{kuser}:{kpwd}"
    HEADERS["Authorization"] = "Basic " + base64.b64encode(secret.encode()).decode()
CONTEXT = ssl.create_default_context(cafile=os.environ.get("KIBANA_CA_FILE"))
VIEWS = [
    ("apache-web-logs", "apache-web-*", "Apache Web İstek ve Hata Logları"),
    ("apache-web-metrics", "metricbeat-*", "Apache ve Docker Metrikleri"),
]
DASHBOARD_ID = "apache-web-operations"

ACCESS = "event.dataset: apache.access"

# (panel_id, baslik, tur, argumanlar, grid)
PANELS = [
    ("apache-web-requests", "Apache | İstek sayısı", "xy",
     {"bucket": ("date_histogram", "@timestamp"), "metric": ("count",),
      "series_type": "line", "query": ACCESS},
     {"x": 0, "y": 0, "w": 24, "h": 14}),

    ("apache-web-error-count", "Apache | 5xx istek sayısı", "metric",
     {"metric": ("count", "http.response.status_code >= 500"), "label": "5xx istek",
      "query": ACCESS},
     {"x": 24, "y": 0, "w": 24, "h": 14}),

    ("apache-web-endpoints", "Apache | En sorunlu 10 endpoint", "xy",
     {"bucket": ("terms", "url.path", 10), "metric": ("count",),
      "series_type": "bar_horizontal",
      "query": f"{ACCESS} and http.response.status_code >= 500"},
     {"x": 0, "y": 14, "w": 24, "h": 14}),

    # event.duration ECS'te NANOSANIYE tutulur (olculen p95 ~1.8e8 ns = ~185 ms).
    # Panel donusum yapmadigi icin etiket de nanosaniye demek zorunda; "ms"
    # yazmak degeri 1.000.000 kat yanlis gosterir. Milisaniye gostermek isteyen
    # kullanici Lens arayuzunden kolonun formatini Duration > nanoseconds ->
    # Milliseconds olarak degistirip panoyu yeniden kaydedebilir (README bolum 5).
    ("apache-web-latency", "Apache | Yanıt süresi (p95, nanosaniye)", "xy",
     {"bucket": ("date_histogram", "@timestamp"),
      "metric": ("percentile", "event.duration", 95), "label": "p95 (ns)",
      "series_type": "line", "query": ACCESS},
     {"x": 24, "y": 14, "w": 24, "h": 14}),

    ("apache-web-geo", "Apache | Ülke ve şehir dağılımı", "table",
     {"buckets": [("terms", "source.geo.country_name", 10),
                  ("terms", "source.geo.city_name", 10)],
      "metrics": [("count",)],
      "query": f"{ACCESS} and source.geo.country_name: *"},
     {"x": 0, "y": 28, "w": 48, "h": 12}),
]

builders = {"metric": lb.metric_panel, "xy": lb.xy_panel,
            "pie": lb.pie_panel, "table": lb.table_panel}


def api(method, path, body=None, allow=()):
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(BASE + path, data=payload, headers=HEADERS, method=method)
    try:
        with request.urlopen(req, context=CONTEXT, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        if exc.code not in allow:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {details}") from None
        return exc.code, {}


def main():
    for _ in range(60):
        try:
            api("GET", "/api/status")
            break
        except (OSError, RuntimeError):
            time.sleep(2)
    else:
        raise SystemExit("Kibana is not reachable; check KIBANA_URL and container status.")

    for view_id, title, name in VIEWS:
        # 'id' yalnizca olusturmada verilir; guncelleme ucunun govde semasi onu
        # reddeder. Guncellemede de tam spec gonderilir, aksi halde onceki
        # calistirmadan kalan yanlis title/timeFieldName hic duzelmez.
        spec = {"title": title, "name": name, "timeFieldName": "@timestamp"}
        status, _ = api("GET", f"/api/data_views/data_view/{view_id}", allow=(404,))
        if status == 404:
            api("POST", "/api/data_views/data_view", {"data_view": {"id": view_id, **spec}})
        else:
            api("POST", f"/api/data_views/data_view/{view_id}",
                {"data_view": spec, "refresh_fields": True})
        print(f"PASS Data View: {name} ({title})", flush=True)

    panels, references = [], []
    for i, (panel_id, title, kind, options, grid) in enumerate(PANELS):
        payload = builders[kind](panel_id, title, "apache-web-logs", **options)
        lb.validate(payload)
        api("POST", f"/api/saved_objects/lens/{panel_id}?overwrite=true", payload)
        panel, reference = lb.dashboard_panel(panel_id, panel_id, grid,
                                              ref_name="apache_panel_" + str(i))
        panels.append(panel)
        references.append(reference)
        print(f"PASS Lens: {panel_id}", flush=True)

    lb.validate_dashboard(panels, references)
    api("POST", f"/api/saved_objects/dashboard/{DASHBOARD_ID}?overwrite=true", {
        "attributes": {
            "title": "Apache Web Trafiği ve GeoIP",
            "description": "Sentetik Apache access/error logları, 5xx, p95 ve GeoIP analizi.",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
            "timeRestore": True, "timeFrom": "now-1h", "timeTo": "now",
            "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({
                "query": {"language": "kuery", "query": ""}, "filter": []})},
        },
        "references": references,
    })
    print(f"PASS Dashboard: {DASHBOARD_ID} ({len(panels)} Lens panels)", flush=True)


if __name__ == "__main__":
    main()
