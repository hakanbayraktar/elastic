#!/usr/bin/env python3
"""
Generate a cascading failure microservice incident dataset for ES|QL Root Cause Analysis (RCA).
Services: storefront -> checkout-service -> payment-service -> ledger-service
Root cause: ledger-service DB connection pool exhaustion.
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "incident-events.ndjson")

def generate_incident(output_path=DEFAULT_OUTPUT):
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(minutes=15)

    services_chain = ["storefront", "checkout-service", "payment-service", "ledger-service"]
    
    events = []

    # 1. 200 normal traces before incident
    for i in range(100):
        t_id = uuid.uuid4().hex
        t_time = base_time + timedelta(seconds=i * 2)
        for s_idx, s_name in enumerate(services_chain):
            step_time = t_time + timedelta(milliseconds=s_idx * 35)
            upstream = services_chain[s_idx - 1] if s_idx > 0 else None
            events.append({
                "@timestamp": step_time.isoformat(),
                "service": {"name": s_name},
                "upstream": {"service": upstream},
                "trace": {"id": t_id},
                "log": {"level": "INFO"},
                "http": {"response": {"status_code": 200}},
                "deployment": {"environment": "production"},
                "message": f"Processed order component in {s_name} successfully"
            })

    # 2. Incident Window: ledger-service runs out of DB pool connections!
    incident_start = base_time + timedelta(seconds=250)
    for i in range(150):
        t_id = uuid.uuid4().hex
        t_time = incident_start + timedelta(seconds=i * 1.5)

        # First failure: ledger-service
        ledger_time = t_time + timedelta(milliseconds=10)
        events.append({
            "@timestamp": ledger_time.isoformat(),
            "service": {"name": "ledger-service"},
            "upstream": {"service": "payment-service"},
            "trace": {"id": t_id},
            "log": {"level": "ERROR"},
            "http": {"response": {"status_code": 500}},
            "deployment": {"environment": "production"},
            "error": {"kind": "db_connection_pool_exhausted"},
            "db": {
                "connection_pool": {
                    "size": 50,
                    "available": 0
                }
            },
            "message": "HikariPool-1 - Connection is not available, request timed out after 3000ms"
        })

        # Second failure: payment-service (fails because ledger returned 500)
        pay_time = ledger_time + timedelta(milliseconds=45)
        events.append({
            "@timestamp": pay_time.isoformat(),
            "service": {"name": "payment-service"},
            "upstream": {"service": "checkout-service"},
            "trace": {"id": t_id},
            "log": {"level": "ERROR"},
            "http": {"response": {"status_code": 502}},
            "deployment": {"environment": "production"},
            "error": {"kind": "upstream_service_error"},
            "message": "Downstream call to ledger-service failed with HTTP 500"
        })

        # Third failure: checkout-service
        checkout_time = pay_time + timedelta(milliseconds=30)
        events.append({
            "@timestamp": checkout_time.isoformat(),
            "service": {"name": "checkout-service"},
            "upstream": {"service": "storefront"},
            "trace": {"id": t_id},
            "log": {"level": "ERROR"},
            "http": {"response": {"status_code": 500}},
            "deployment": {"environment": "production"},
            "error": {"kind": "payment_failed"},
            "message": "Checkout transaction aborted: payment-service returned Bad Gateway"
        })

        # Fourth failure: storefront
        storefront_time = checkout_time + timedelta(milliseconds=20)
        events.append({
            "@timestamp": storefront_time.isoformat(),
            "service": {"name": "storefront"},
            "upstream": {"service": None},
            "trace": {"id": t_id},
            "log": {"level": "ERROR"},
            "http": {"response": {"status_code": 500}},
            "deployment": {"environment": "production"},
            "error": {"kind": "internal_server_error"},
            "message": "Failed to render user checkout completion page"
        })

    with open(output_path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps({"create": {"_index": "rca-olaylar"}}) + "\n")
            f.write(json.dumps(ev) + "\n")

    print(f"Başarıyla {len(events)} olay üretildi -> {output_path}")

if __name__ == "__main__":
    generate_incident()
