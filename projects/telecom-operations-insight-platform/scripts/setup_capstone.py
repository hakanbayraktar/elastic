#!/usr/bin/env python3
"""Install LAB-04-only pipeline, mappings, data stream and retention policy."""
import base64
import json
import os
import ssl
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
ELASTIC = ROOT / "elastic"
PIPELINE = "lab04-telecom-capstone-v1"
COMPONENT = "lab04-telecom-capstone-mappings"
TEMPLATE = "lab04-telecom-capstone-template"
POLICY = "lab04-telecom-capstone-retention"
STREAM = "logs-telecom.capstone-prod"


def api(method, path, body=None, allow=()):
    base = os.environ.get("ELASTIC_URL", "http://127.0.0.1:9200").rstrip("/")
    headers = {"Content-Type": "application/json"}
    # Omurga güvenlidir: kimlik bilgisi her istekte gönderilir (ortamdan ezilebilir).
    value = os.environ.get("ELASTIC_USER", "elastic") + ":" + os.environ.get("ELASTIC_PASSWORD", "DevOps2026!")
    headers["Authorization"] = "Basic " + base64.b64encode(value.encode()).decode()
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(base + path, data=payload, headers=headers, method=method)
    context = ssl.create_default_context(cafile=os.environ.get("ELASTIC_CA_FILE"))
    try:
        with request.urlopen(req, context=context, timeout=60) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        if exc.code not in allow:
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {exc.read().decode()}") from None
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def main():
    pipeline = json.loads((ELASTIC / "00-capstone-pipeline.json").read_text())
    component = json.loads((ELASTIC / "01-capstone-mappings.json").read_text())
    policy = json.loads((ELASTIC / "02-capstone-ilm-policy.json").read_text())
    template = json.loads((ELASTIC / "03-capstone-index-template.json").read_text())
    api("PUT", f"/_ingest/pipeline/{PIPELINE}", pipeline)
    print("PASS pipeline: " + PIPELINE, flush=True)
    api("PUT", f"/_component_template/{COMPONENT}", component)
    print("PASS component template: " + COMPONENT, flush=True)
    api("PUT", f"/_ilm/policy/{POLICY}", policy)
    print("PASS ILM policy: " + POLICY, flush=True)
    api("PUT", f"/_index_template/{TEMPLATE}", template)
    print("PASS composable template: " + TEMPLATE, flush=True)
    status, _ = api("GET", f"/_data_stream/{STREAM}", allow=(404,))
    if status == 404:
        api("PUT", f"/_data_stream/{STREAM}")
    else:
        api("PUT", f"/{STREAM}/_settings", {"index.default_pipeline": PIPELINE,
                                                "index.lifecycle.name": POLICY})
    print("PASS data stream: " + STREAM, flush=True)


if __name__ == "__main__":
    main()
