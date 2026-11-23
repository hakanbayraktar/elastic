#!/usr/bin/env python3
"""Send low-rate synthetic HTTP traffic only to the local Docker Apache service."""
import argparse
from datetime import datetime, timezone
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

CLIENTS = [
    {"name": "uk-profile-a", "ip": "81.2.69.142"},
    {"name": "sweden-profile", "ip": "89.160.20.128"},
    {"name": "us-profile", "ip": "216.160.83.56"},
    {"name": "uk-profile-b", "ip": "2.125.160.216"},
    {"name": "germany-profile", "ip": "5.9.0.1"},
    # Public Turk Telekom DNS IP, used only as a synthetic X-Forwarded-For value.
    {"name": "turkey-istanbul", "ip": "195.175.39.39"},
]
PATHS = [
    ("/", 35),
    ("/products/sku-100", 20),
    ("/api/search?q=elastic+observability", 20),
    ("/cgi-bin/slow.sh", 10),
    ("/cgi-bin/unavailable.sh", 8),
    ("/missing/training-page", 7),
]
AGENTS = ["LabBrowser/1.0", "SyntheticMobile/1.0", "SyntheticBot/1.0"]


def choose_path(rng):
    values, weights = zip(*PATHS)
    return rng.choices(values, weights=weights, k=1)[0]


def request_once(base_url, path, client, use_forwarded_ip, log_file, rng):
    request_id = str(uuid.uuid4())
    headers = {"User-Agent": rng.choice(AGENTS), "X-Request-ID": request_id}
    if use_forwarded_ip:
        headers["X-Forwarded-For"] = client["ip"]

    started_ns = time.time_ns()
    status = 0
    try:
        req = urllib.request.Request(base_url.rstrip("/") + path, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            response.read(4096)
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.read(4096)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"request failed: {type(exc).__name__}", flush=True)
        return
    duration_ns = time.time_ns() - started_ns
    event = {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "event": {"dataset": "apache.traffic", "duration": duration_ns, "kind": "event"},
        "http": {
            "request": {"id": request_id, "method": "GET"},
            "response": {"status_code": status},
        },
        "url": {"path": urllib.parse.urlsplit(path).path, "original": path},
        "labels": {"synthetic_client_profile": client["name"], "forwarded_ip_used": use_forwarded_ip},
    }
    if use_forwarded_ip:
        event["source"] = {"ip": client["ip"]}
    log_file.write(json.dumps(event, separators=(",", ":")) + "\n")
    log_file.flush()
    print(f"{status} {path} client={client['name']} xff={use_forwarded_ip} duration_ms={duration_ns / 1_000_000:.1f}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://apache")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--requests", type=int, default=0, help="0 means continue until the container is stopped")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if args.interval < 0.2:
        parser.error("interval must be at least 0.2 seconds for this low-rate lab")
    if args.requests < 0:
        parser.error("requests cannot be negative")

    rng = random.Random(args.seed)
    output = open("/var/log/traffic/traffic.jsonl", "a", encoding="utf-8", buffering=1)
    count = 0
    while args.requests == 0 or count < args.requests:
        client = CLIENTS[count % len(CLIENTS)]
        path = choose_path(rng)
        # One request in ten models a direct client with no forwarded-proxy header.
        request_once(args.url, path, client, (count + 1) % 10 != 0, output, rng)
        count += 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
