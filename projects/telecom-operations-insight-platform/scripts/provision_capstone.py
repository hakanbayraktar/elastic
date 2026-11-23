#!/usr/bin/env python3
"""Create isolated Kibana assets and a five-minute capstone 5xx alert."""
import base64
import json
import os
from pathlib import Path
import ssl
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
DAY2 = ROOT / "kibana"
VIEW_ID = "telecom-capstone-view"
DASHBOARD_ID = "telecom-operations-capstone"
CONNECTOR_ID = "telecom-capstone-log"
RULE_ID = "telecom-capstone-error-rate"
PANELS = [
    ("telecom-day2-requests.json", "capstone-requests", "Capstone | İstek sayısı"),
    ("telecom-day2-error-rate.json", "capstone-error-rate", "Capstone | 5xx oranı"),
    ("telecom-day2-p95.json", "capstone-p95", "Capstone | p95 response time"),
    ("telecom-day2-endpoints.json", "capstone-endpoints", "Capstone | En sorunlu endpoint'ler"),
    ("telecom-day2-clients.json", "capstone-clients", "Capstone | Kaynak IP dağılımı"),
]


def api(method, path, body=None, allow=()):
    base = os.environ.get("KIBANA_URL", "http://127.0.0.1:5601").rstrip("/")
    headers = {"Content-Type": "application/json", "kbn-xsrf": "telecom-capstone"}
    value = os.environ.get("KIBANA_USER", "elastic") + ":" + os.environ.get("KIBANA_PASSWORD", "DevOps2026!")
    headers["Authorization"] = "Basic " + base64.b64encode(value.encode()).decode()
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(base + path, data=payload, headers=headers, method=method)
    context = ssl.create_default_context(cafile=os.environ.get("KIBANA_CA_FILE"))
    try:
        with request.urlopen(req, context=context, timeout=60) as response:
            data = response.read()
            return response.status, json.loads(data) if data else {}
    except error.HTTPError as exc:
        if exc.code not in allow:
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {exc.read().decode()}") from None
        return exc.code, {}


def ensure_view():
    status, _ = api("GET", f"/api/data_views/data_view/{VIEW_ID}", allow=(404,))
    body = {"data_view": {"id": VIEW_ID, "name": "Telecom Capstone Events",
                           "title": "logs-telecom.capstone-prod", "timeFieldName": "@timestamp"}}
    if status == 404:
        api("POST", "/api/data_views/data_view", body)
    else:
        api("POST", f"/api/data_views/data_view/{VIEW_ID}", {"data_view": {"name": body["data_view"]["name"],
                                                                            "title": body["data_view"]["title"],
                                                                            "timeFieldName": body["data_view"]["timeFieldName"]}})
    print("PASS Data View: " + VIEW_ID, flush=True)


def ensure_dashboard():
    panels, refs = [], []
    # labels is flattened by this lab's ECS contract and its subkeys do not
    # appear in Kibana field caps. Use the mapped trace.id keyword prefix.
    query = 'trace.id: capstone-trace-* AND service.name: "edge-proxy"'
    for i, (filename, saved_id, title) in enumerate(PANELS):
        panel = json.loads((DAY2 / filename).read_text())
        panel["title"] = title
        panel["query"]["expression"] = query
        if "data_source" in panel:
            panel["data_source"]["ref_id"] = VIEW_ID
        for layer in panel.get("layers", []):
            layer["data_source"]["ref_id"] = VIEW_ID
        api("PUT", f"/api/visualizations/{saved_id}", panel)
        # embeddableConfig atlanamaz: Kibana 9.x panel referanslarini cozerken
        # `panel.embeddableConfig.enhancements` ifadesini korumasiz okur ve
        # anahtar yoksa dashboard HTTP 500 ile acilmaz.
        panels.append({"version": "9.5.5", "type": "lens", "panelIndex": str(i),
                       "gridData": {"x": (i % 2) * 24, "y": (i // 2) * 15, "w": 24, "h": 15, "i": str(i)},
                       "embeddableConfig": {"enhancements": {}},
                       "panelRefName": "capstone_panel_" + str(i)})
        refs.append({"name": "capstone_panel_" + str(i), "type": "lens", "id": saved_id})
        print("PASS Lens: " + saved_id, flush=True)
    api("POST", f"/api/saved_objects/dashboard/{DASHBOARD_ID}?overwrite=true", {
        "attributes": {"title": "Telecom Operations | Incident Overview",
                       "description": "Synthetic-only capstone. Panels scope to capstone proxy events.",
                       "panelsJSON": json.dumps(panels),
                       "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
                       "timeRestore": True, "timeFrom": "now-24h", "timeTo": "now",
                       "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({"query": {"language": "kuery", "query": query}, "filter": []})}},
        "references": refs})
    print("PASS Dashboard: " + DASHBOARD_ID, flush=True)


def ensure_alert():
    connector = {"name": "Capstone synthetic incident log", "connector_type_id": ".server-log", "config": {}, "secrets": {}}
    status, _ = api("GET", f"/api/actions/connector/{CONNECTOR_ID}", allow=(404,))
    if status == 404:
        api("POST", f"/api/actions/connector/{CONNECTOR_ID}", connector)
    else:
        api("PUT", f"/api/actions/connector/{CONNECTOR_ID}", {"name": connector["name"], "config": {}, "secrets": {}})
    status, _ = api("GET", f"/api/alerting/rule/{RULE_ID}", allow=(404,))
    rule = {
        "name": "Capstone proxy 5xx oranı > %5 (5 dakika)", "rule_type_id": ".es-query", "consumer": "alerts", "enabled": True,
        "tags": ["telecom-capstone", "synthetic-only"], "schedule": {"interval": "10s"},
        "params": {"searchType": "esqlQuery", "esqlQuery": {"esql":
            'FROM logs-telecom.capstone-prod | WHERE trace.id LIKE "capstone-trace-*" AND service.name == "edge-proxy" | STATS requests = COUNT(*), errors = COUNT(*) WHERE http.response.status_code >= 500 AND http.response.status_code < 600 | EVAL error_percent = errors * 100.0 / requests | WHERE requests > 0 AND error_percent > 5'},
            "timeField": "@timestamp", "timeWindowSize": 5, "timeWindowUnit": "m", "threshold": [0], "thresholdComparator": ">",
            "size": 100, "aggType": "count", "groupBy": "all", "excludeHitsFromPreviousRun": False},
        "actions": [{"id": CONNECTOR_ID, "group": "query matched", "params": {"level": "error", "message": "Capstone proxy 5xx > 5%: {{rule.name}} | {{context.message}}"},
                     "frequency": {"summary": False, "notify_when": "onActionGroupChange", "throttle": None}}]}
    if status == 404:
        api("POST", f"/api/alerting/rule/{RULE_ID}", rule)
    else:
        for key in ("rule_type_id", "consumer", "enabled"):
            rule.pop(key, None)
        api("PUT", f"/api/alerting/rule/{RULE_ID}", rule)
    print("PASS Alert: " + RULE_ID, flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard-only", action="store_true", help="skip scheduled alert prerequisites")
    args = parser.parse_args()
    ensure_view()
    ensure_dashboard()
    if not args.dashboard_only:
        ensure_alert()
