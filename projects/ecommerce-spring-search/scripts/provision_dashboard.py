#!/usr/bin/env python3
"""Create NovaShop e-commerce Data Views, Lens panels, and the sales analytics dashboard."""
import base64
import json
import os
import ssl
import sys
import sys
import time
from urllib import error, request

BASE = os.environ.get("KIBANA_URL", "http://127.0.0.1:5601").rstrip("/")
HEADERS = {"Content-Type": "application/json", "kbn-xsrf": "novashop-dashboard"}
kuser = os.environ.get("KIBANA_USER", os.environ.get("ELASTIC_USER", "elastic"))
kpwd = os.environ.get("KIBANA_PASSWORD", os.environ.get("ELASTIC_PASSWORD", "DevOps2026!"))
if kuser:
    secret = f"{kuser}:{kpwd}"
    HEADERS["Authorization"] = "Basic " + base64.b64encode(secret.encode()).decode()

CONTEXT = ssl.create_default_context(cafile=os.environ.get("KIBANA_CA_FILE"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lens_builder as lb

DATA_VIEW_ID = "novashop-orders"
DATA_VIEW_PATTERN = "kibana_sample_data_ecommerce,ecommerce-orders*"
DATA_VIEW_NAME = "NovaShop E-Ticaret Siparişleri"
TIME_FIELD = "order_date"

DASHBOARD_ID = "novashop-ecommerce-analytics"
DASHBOARD_TITLE = "NovaShop E-Commerce Sales & Analytics"


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


# (panel_id, baslik, tur, argumanlar, grid)
PANELS_DEF = [
    ("novashop-revenue", "NovaShop | Toplam Satış Cirosu ($)", "metric",
     {"metric": ("sum", "taxful_total_price"), "label": "Toplam Ciro"},
     {"x": 0, "y": 0, "w": 12, "h": 7}),

    ("novashop-order-count", "NovaShop | Toplam Sipariş Sayısı", "metric",
     {"metric": ("count",), "label": "Sipariş"},
     {"x": 12, "y": 0, "w": 12, "h": 7}),

    ("novashop-category-share", "NovaShop | Kategori Satış Payı ($)", "pie",
     {"slice_by": "category.keyword", "size": 10,
      "metric": ("sum", "taxful_total_price"), "label": "Ciro"},
     {"x": 24, "y": 0, "w": 24, "h": 14}),

    ("novashop-daily-trend", "NovaShop | Günlük Satış ve Ciro Trendi ($)", "xy",
     {"bucket": ("date_histogram", TIME_FIELD),
      "metrics": [("count",), ("sum", "taxful_total_price")],
      "labels": ["Sipariş", "Ciro ($)"], "series_type": "bar"},
     {"x": 0, "y": 7, "w": 24, "h": 14}),

    ("novashop-top-products", "NovaShop | En Çok Ciro Getiren 10 Ürün", "xy",
     {"bucket": ("terms", "products.product_name.keyword", 10),
      "metric": ("sum", "taxful_total_price"), "label": "Ciro ($)",
      "series_type": "bar_horizontal"},
     {"x": 0, "y": 21, "w": 24, "h": 14}),

    ("novashop-city-table", "NovaShop | Şehir Bazında Sipariş ve Gelir Tablosu", "table",
     {"buckets": [("terms", "geoip.city_name", 10)],
      "metrics": [("count",), ("sum", "taxful_total_price")],
      "query": "geoip.city_name: *"},
     {"x": 24, "y": 14, "w": 24, "h": 21}),
]

BUILDERS = {"metric": lb.metric_panel, "xy": lb.xy_panel,
            "pie": lb.pie_panel, "table": lb.table_panel}


def main():
    print(f"Connecting to Kibana at {BASE} ...")
    for _ in range(30):
        try:
            api("GET", "/api/status")
            break
        except (OSError, RuntimeError):
            time.sleep(2)
    else:
        raise SystemExit("Kibana is not reachable; check KIBANA_URL and container status.")

    # 1. Create or Refresh Data View
    status, _ = api("GET", f"/api/data_views/data_view/{DATA_VIEW_ID}", allow=(404,))
    dv_body = {"title": DATA_VIEW_PATTERN, "name": DATA_VIEW_NAME, "timeFieldName": TIME_FIELD}
    if status == 404:
        api("POST", "/api/data_views/data_view", {"data_view": {**dv_body, "id": DATA_VIEW_ID}})
    else:
        api("POST", f"/api/data_views/data_view/{DATA_VIEW_ID}", {"data_view": dv_body, "refresh_fields": True})
    print(f"PASS Data View: {DATA_VIEW_NAME} ({DATA_VIEW_PATTERN})", flush=True)


    panels, references = [], []
    for i, (panel_id, title, kind, options, grid) in enumerate(PANELS_DEF):
        payload = BUILDERS[kind](panel_id, title, DATA_VIEW_ID, **options)
        lb.validate(payload)
        api("POST", f"/api/saved_objects/lens/{panel_id}?overwrite=true", payload)
        panel, reference = lb.dashboard_panel(panel_id, panel_id, grid,
                                              ref_name="novashop_panel_" + str(i))
        panels.append(panel)
        references.append(reference)
        print(f"PASS Lens: {title}", flush=True)
    lb.validate_dashboard(panels, references)
    dashboard_payload = {
        "attributes": {
            "title": DASHBOARD_TITLE,
            "description": "NovaShop e-ticaret satış cirosu, sipariş hacmi, kategori dağılımı ve çok satan ürünler panosu.",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
            "timeRestore": True,
            "timeFrom": "now-90d",
            "timeTo": "now",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"language": "kuery", "query": ""},
                    "filter": []
                })
            },
        },
        "references": references,
    }
    api("POST", f"/api/saved_objects/dashboard/{DASHBOARD_ID}?overwrite=true", dashboard_payload)
    print(f"PASS Dashboard: {DASHBOARD_ID} ({len(panels)} Lens panels)", flush=True)


if __name__ == "__main__":
    main()
