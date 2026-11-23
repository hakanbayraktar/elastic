#!/usr/bin/env python3
"""Install a mapping template; data indices are created automatically on first event."""
import base64
import json
import os
import ssl
import time
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("ELASTIC_URL", "http://elasticsearch:9200").rstrip("/")


def api(method, path, body=None):
    headers = {"Content-Type": "application/json"}
    user = os.environ.get("ELASTIC_USER")
    if user:
        token = base64.b64encode(f"{user}:{os.environ.get('ELASTIC_PASSWORD', '')}".encode()).decode()
        headers["Authorization"] = "Basic " + token
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(URL + path, data=payload, headers=headers, method=method)
    context = ssl.create_default_context(cafile=os.environ.get("ELASTIC_CA_FILE"))
    try:
        with request.urlopen(req, context=context, timeout=15) as response:
            return response.status, json.loads(response.read())
    except error.HTTPError as exc:
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}") from None


def main():
    template = json.loads((ROOT / "elastic/apache-index-template.json").read_text())
    for attempt in range(60):
        try:
            api("PUT", "/_index_template/apache-web", template)
            print("PASS index template: apache-web", flush=True)
            print("Index auto-creation is enabled; no index was pre-created.", flush=True)
            return
        except (OSError, RuntimeError):
            if attempt == 59:
                raise
            time.sleep(2)


if __name__ == "__main__":
    main()
