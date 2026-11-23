#!/usr/bin/env python3
"""Generate synthetic, trace-correlated Telecom Operations capstone events."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

KINDS = {
    "proxy": "edge-proxy",
    "api": "subscriber-api",
    "application": "novashop-checkout",
    "subscriber-db": "subscriber-registry",
    "5g": "5g-core",
}
INFRA = {
    "linux": "lab-linux-host",
    "docker": "novashop-container-runtime",
    "kind": "novashop-kubernetes",
    "nginx": "nginx-gateway",
}
SCENARIOS = ("normal", "surge", "high-5xx", "high-latency", "bad-auth", "suspicious-ip")


def event(ts, kind, service, request_id, trace_id, subscriber_id, run_id, status, duration, ip, scenario, number):
    doc = {
        "@timestamp": ts,
        "service": {"name": service},
        "temp": {"timestamp": ts, "status": str(status), "duration_ms": duration},
        "client": {"ip": ip},
        "trace": {"id": trace_id},
        "url": {"path": "/api/checkout" if kind != "5g" else "/5g/session"},
        "http": {"request": {"method": "POST" if kind in ("proxy", "api", "application") else "GET"}},
        "labels": {
            "training_profile": "capstone",
            "source_kind": kind,
            "scenario": scenario,
            "run_id": run_id,
            "request_id": request_id,
            "subscriber_id": subscriber_id,
            "sequence": str(number),
        },
        "log": {"level": "ERROR" if status >= 500 else "WARN" if status == 401 else "INFO"},
        "message": f"Synthetic {kind} event for {scenario}; trace {trace_id}",
        # Deliberate synthetic PII proves that the shared ingest PII pipeline removes it.
        "user": {"email": f"subscriber-{number}@example.test"},
    }
    if status >= 500:
        doc["error"] = {"type": "upstream_failure", "message": "Synthetic upstream failure"}
    if kind == "docker":
        doc["container"] = {"id": f"container-{number:06d}", "name": "novashop-checkout"}
    if kind in ("kind", "nginx"):
        doc["labels"]["kubernetes_pod_name"] = f"novashop-checkout-{number % 3}"
    if kind == "linux":
        doc["host"] = {"name": "lab-linux-01"}
    return doc


def build_events(scenario="normal", count=100, run_id=None, start=None):
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")
    if count < 10 or count > 10000:
        raise ValueError("requests must be between 10 and 10000")
    run_id = run_id or uuid.uuid4().hex[:10]
    start = start or datetime.now(timezone.utc)
    events = []
    for number in range(1, count + 1):
        stamp = (start.timestamp() + number / 10)
        ts = datetime.fromtimestamp(stamp, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        request_id = f"capstone-{run_id}-{number:06d}"
        trace_id = f"capstone-trace-{run_id}-{number:06d}"
        subscriber_id = f"sub-sim-{number % 37:04d}"
        status, duration, ip = 200, 42, "81.2.69.142"
        if scenario == "normal" and number % 100 == 0:
            status, duration = 503, 890
        elif scenario in ("surge", "high-5xx") and number % 4 == 0:
            status, duration = 503, 1250
        elif scenario == "high-latency" and number % 3 == 0:
            duration = 4200
        elif scenario == "bad-auth" and number % 5 == 0:
            status, duration, ip = 401, 85, "203.0.113.10"
        elif scenario == "suspicious-ip" and number % 2 == 0:
            status, duration, ip = 429, 125, "203.0.113.77"
        for kind, service in KINDS.items():
            events.append(event(ts, kind, service, request_id, trace_id, subscriber_id, run_id, status, duration, ip, scenario, number))
        # Emit each infrastructure source once per ten requests to keep the
        # event count distinct from request count and avoid double-counting panels.
        if number % 10 == 0:
            for kind, service in INFRA.items():
                infra_id = f"capstone-{run_id}-infra-{kind}-{number:06d}"
                events.append(event(ts, kind, service, infra_id, trace_id, subscriber_id, run_id, status, duration, ip, scenario, number))
    return run_id, events


def iter_bulk(events, target):
    for doc in events:
        yield json.dumps({"create": {"_index": target}}, separators=(",", ":"))
        yield json.dumps(doc, separators=(",", ":"), ensure_ascii=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="normal")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--bulk-data-stream", default="logs-telecom.capstone-prod")
    parser.add_argument("--output", default="/tmp/telecom-capstone.ndjson")
    args = parser.parse_args()
    run_id, docs = build_events(args.scenario, args.requests, args.run_id)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for line in iter_bulk(docs, args.bulk_data_stream):
            handle.write(line + "\n")
    print(json.dumps({"scenario": args.scenario, "run_id": run_id, "requests": args.requests, "documents": len(docs), "output": str(output)}))
