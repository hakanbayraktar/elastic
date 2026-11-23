#!/usr/bin/env python3
"""Generate, ingest and verify an isolated Telecom capstone scenario."""
import argparse
import base64
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generator/generate_capstone.py"
spec = importlib.util.spec_from_file_location("capstone_generator", GENERATOR)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
REPORT_DIR = Path(os.environ.get("CAPSTONE_REPORT_DIR", str(ROOT / "reports")))
TARGET = "logs-telecom.capstone-prod"
PIPELINE = "lab04-telecom-capstone-v1"


def resolve_elastic_url():
    explicit = os.environ.get("ELASTIC_URL")
    if explicit:
        return explicit.rstrip("/")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for scheme in ("http", "https"):
        url = f"{scheme}://127.0.0.1:9200"
        try:
            req = request.Request(f"{url}/_cluster/health")
            with request.urlopen(req, timeout=1, context=ctx):
                return url
        except Exception:
            pass
    return "http://127.0.0.1:9200"

def api(method, path, body=None, ndjson=False):
    base = resolve_elastic_url()
    headers = {"Content-Type": "application/x-ndjson" if ndjson else "application/json"}
    credential = f"{os.environ.get('ELASTIC_USER', 'elastic')}:{os.environ.get('ELASTIC_PASSWORD', 'DevOps2026!')}"
    headers["Authorization"] = "Basic " + base64.b64encode(credential.encode()).decode()
    payload = body.encode() if isinstance(body, str) else json.dumps(body).encode() if body is not None else None
    req = request.Request(base + path, data=payload, headers=headers, method=method)
    context = ssl.create_default_context(cafile=os.environ.get("ELASTIC_CA_FILE"))
    if not os.environ.get("ELASTIC_CA_FILE"):
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    try:
        with request.urlopen(req, context=context, timeout=90) as response:
            return json.loads(response.read())
    except error.HTTPError as exc:
        # Never expose authorization headers or user documents in a report.
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}") from None


def search(query, aggs=None, size=0, source=None):
    body = {"size": size, "track_total_hits": True, "query": query}
    if aggs:
        body["aggs"] = aggs
    if source is not None:
        body["_source"] = source
    return api("POST", f"/{TARGET}/_search", body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=generator.SCENARIOS, default="normal")
    parser.add_argument("--requests", type=int, default=100)
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / "scripts/setup_capstone.py")], check=True)
    run_id, docs = generator.build_events(args.scenario, args.requests)
    bulk = "\n".join(generator.iter_bulk(docs, TARGET)) + "\n"
    result = api("POST", f"/_bulk?pipeline={PIPELINE}&refresh=wait_for", bulk, ndjson=True)
    assert result.get("errors") is False, "Bulk API reported failed items"
    assert len(result.get("items", [])) == len(docs), "Bulk item count mismatch"

    scope = {"bool": {"filter": [
        {"term": {"labels.training_profile": "capstone"}},
        {"term": {"labels.run_id": run_id}},
    ]}}
    source_count = search(scope)["hits"]["total"]["value"]
    assert source_count == len(docs), (source_count, len(docs))

    proxy_scope = {"bool": {"filter": [scope, {"term": {"labels.source_kind": "proxy"}}]}}
    metrics = search(proxy_scope, {
        "requests": {"value_count": {"field": "trace.id"}},
        "errors": {"filter": {"range": {"http.response.status_code": {"gte": 500, "lt": 600}}}},
        "auth_failures": {"filter": {"term": {"http.response.status_code": 401}}},
        "suspicious_ip_events": {"filter": {"term": {"client.ip": "203.0.113.77"}}},
        "avg_duration_ns": {"avg": {"field": "event.duration"}},
        "p95_duration_ns": {"percentiles": {"field": "event.duration", "percents": [95]}},
        "sources": {"terms": {"field": "labels.source_kind", "size": 20}},
    })["aggregations"]
    requests = metrics["requests"]["value"]
    errors = metrics["errors"]["doc_count"]
    error_rate = errors * 100.0 / requests
    assert requests == args.requests, (requests, args.requests)
    if args.scenario in ("high-5xx", "surge"):
        assert error_rate > 5, error_rate
    if args.scenario == "normal":
        assert error_rate <= 5, error_rate
    if args.scenario == "bad-auth":
        assert metrics["auth_failures"]["doc_count"] == args.requests // 5, metrics["auth_failures"]
    if args.scenario == "suspicious-ip":
        assert metrics["suspicious_ip_events"]["doc_count"] == args.requests // 2, metrics["suspicious_ip_events"]
    if args.scenario == "high-latency":
        p95_ms = metrics["p95_duration_ns"]["values"]["95.0"] / 1_000_000
        assert p95_ms >= 4000, p95_ms

    trace_id = f"capstone-trace-{run_id}-000001"
    correlation = search({"term": {"trace.id": trace_id}}, {"by_service": {"terms": {"field": "service.name", "size": 10}}})
    services = sorted(bucket["key"] for bucket in correlation["aggregations"]["by_service"]["buckets"])
    assert len(services) == 5, services

    sample = search({"term": {"labels.run_id": run_id}}, size=1, source=True)["hits"]["hits"][0]["_source"]
    assert "user" not in sample and "temp" not in sample, "PII or temporary parser fields remained in source"
    assert "personal fields removed" in sample.get("message", ""), "PII-safe message was not applied"
    assert sample.get("event", {}).get("duration", 0) > 0, "duration was not converted to nanoseconds"
    assert sample.get("event", {}).get("dataset") == "telecom.capstone", "event dataset was not normalized"

    report = {
        "passed": True,
        "scenario": args.scenario,
        "run_id": run_id,
        "requests": requests,
        "documents": source_count,
        "proxy_5xx": errors,
        "proxy_5xx_percent": error_rate,
        "avg_duration_ns": metrics["avg_duration_ns"]["value"],
        "p95_duration_ns": metrics["p95_duration_ns"]["values"]["95.0"],
        "auth_failures": metrics["auth_failures"]["doc_count"],
        "suspicious_ip_events": metrics["suspicious_ip_events"]["doc_count"],
        "trace_services": services,
        "pii_removed": True,
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / f"capstone-{args.scenario}-runtime-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (REPORT_DIR / "capstone-runtime-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
