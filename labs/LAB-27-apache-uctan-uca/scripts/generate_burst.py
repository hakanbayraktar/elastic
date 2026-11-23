#!/usr/bin/env python3
"""Generate a bounded same-IP request burst against the local Apache lab only."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import urllib.error
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8088")
    parser.add_argument("--ip", default="195.175.39.39", help="Synthetic X-Forwarded-For profile")
    parser.add_argument("--path", default="/", help="Istek yolu; ariza icin /cgi-bin/unavailable.sh (503)")
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()
    if not (1 <= args.requests <= 500) or not (1 <= args.concurrency <= 20):
        parser.error("requests must be 1..500 and concurrency 1..20")

    def send(_):
        req = urllib.request.Request(args.url.rstrip("/") + args.path, headers={
            "X-Forwarded-For": args.ip,
            "X-Request-ID": "burst-" + str(uuid.uuid4()),
            "User-Agent": "ElasticLab-Burst/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        statuses = [future.result() for future in as_completed(
            [pool.submit(send, i) for i in range(args.requests)])]
    elapsed = time.monotonic() - started
    print(f"requests={len(statuses)} concurrency={args.concurrency} ip={args.ip} "
          f"elapsed_seconds={elapsed:.2f} statuses={dict((code, statuses.count(code)) for code in sorted(set(statuses)))}")


if __name__ == "__main__":
    main()
