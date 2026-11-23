#!/usr/bin/env python3
"""Ingest a fresh incident and prove the scheduled Kibana alert activates."""
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import time
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = Path(os.environ.get("CAPSTONE_REPORT_DIR", str(ROOT / "reports")))
REPORT = REPORT_DIR / "capstone-alert-runtime-report.json"
RULE_ID = "telecom-capstone-error-rate"


def resolve_kibana_url():
    explicit = os.environ.get("KIBANA_URL")
    if explicit:
        return explicit.rstrip("/")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for scheme in ("http", "https"):
        url = f"{scheme}://127.0.0.1:5601"
        try:
            req = request.Request(f"{url}/api/status")
            with request.urlopen(req, timeout=1, context=ctx):
                return url
        except Exception:
            pass
    return "http://127.0.0.1:5601"

def kibana_rule():
    base = resolve_kibana_url()
    headers = {"kbn-xsrf": "capstone-alert-verify"}
    credential = os.environ.get("KIBANA_USER", "elastic") + ":" + os.environ.get("KIBANA_PASSWORD", "DevOps2026!")
    headers["Authorization"] = "Basic " + base64.b64encode(credential.encode()).decode()
    req = request.Request(base + f"/api/alerting/rule/{RULE_ID}", headers=headers)
    context = ssl.create_default_context(cafile=os.environ.get("KIBANA_CA_FILE"))
    if not os.environ.get("KIBANA_CA_FILE"):
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    with request.urlopen(req, context=context, timeout=20) as response:
        return json.load(response)


def main():
    started = datetime.now(timezone.utc)
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/load_capstone.py"),
                           "--scenario", "high-5xx", "--requests", "100"],
                          check=True, capture_output=True, text=True)
    # setup_capstone.py prints resource status before the loader's JSON report.
    # Read the deterministic report artifact instead of assuming stdout is JSON-only.
    load_report_path = REPORT_DIR / "capstone-high-5xx-runtime-report.json"
    load_report = json.loads(load_report_path.read_text())
    assert load_report["proxy_5xx_percent"] > 5
    latest = None
    for _ in range(18):
        latest = kibana_rule()
        execution = latest.get("execution_status", {}).get("last_execution_date")
        last_run = latest.get("last_run", {})
        active = last_run.get("alerts_count", {}).get("active", 0)
        executed_after_ingest = execution and datetime.fromisoformat(execution.replace("Z", "+00:00")) >= started
        if latest.get("enabled") and last_run.get("outcome") == "succeeded" and active > 0 and executed_after_ingest:
            break
        time.sleep(10)
    else:
        raise SystemExit("Scheduled capstone alert did not activate on the fresh synthetic high-5xx run.")

    report = {"passed": True, "rule_id": RULE_ID, "enabled": latest["enabled"],
              "execution_status": latest.get("execution_status", {}).get("status"),
              "last_run_outcome": latest["last_run"]["outcome"],
              "active_alerts": latest["last_run"]["alerts_count"]["active"],
              "last_execution_date": latest.get("execution_status", {}).get("last_execution_date"),
              "scenario": load_report["scenario"], "run_id": load_report["run_id"],
              "proxy_5xx_percent": load_report["proxy_5xx_percent"]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
