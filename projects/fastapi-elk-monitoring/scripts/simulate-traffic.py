#!/usr/bin/env python3
"""
simulate-traffic.py
FastAPI servisine gerçekçi trafik göndererek 2xx, 4xx ve 5xx hata logları üretir.
Sadece Python Standart Kütüphanesi (urllib) kullanır, harici bağımlılık gerektirmez.
"""

import json
import random
import sys
import time
import urllib.error
import urllib.request
from typing import Dict, Tuple

API_URL = "http://localhost:19002"
TOTAL_REQUESTS = 50


def send_request(method: str, path: str, payload: dict = None) -> Tuple[int, str]:
    url = f"{API_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def main():
    print("=" * 65)
    print("🚀 FastAPI ELK: FastAPI ELK Log & Error Simülatörü Başlatılıyor")
    print(f"Hedef Servis: {API_URL} | Toplam İstek: {TOTAL_REQUESTS}")
    print("=" * 65)

    stats: Dict[str, int] = {"2xx": 0, "4xx": 0, "5xx": 0, "fail": 0}

    scenarios = [
        # (Ağırlık, Metot, Path, Payload Açıklaması)
        ("HEALTH", "GET", "/api/v1/health", None),
        ("CREATE_ORDER", "POST", "/api/v1/orders", {
            "user_id": "usr-101",
            "items": [{"item_id": "prod-1", "item_name": "Kablosuz Kulaklık", "quantity": 1, "unit_price": 750.0}],
            "currency": "TRY"
        }),
        ("GET_EXISTING_ORDER", "GET", "/api/v1/orders/ord-1001", None),
        ("GET_NOT_FOUND_ORDER", "GET", "/api/v1/orders/ord-9999", None),  # 404
        ("PAYMENT_SUCCESS", "POST", "/api/v1/checkout/payment", {
            "order_id": "ord-1001",
            "amount": 750.0,
            "gateway": "iyzico_v1"
        }),
        ("PAYMENT_TIMEOUT_500", "POST", "/api/v1/checkout/payment", {
            "order_id": "ord-1002",
            "amount": 1450.0,
            "gateway": "timeout_gateway"  # 500 fırlatır
        }),
        ("ZERO_DIVISION_500", "GET", "/api/v1/calculate/discount?price=250&ratio=0", None),  # 500
        ("DB_DEADLOCK_500", "GET", "/api/v1/database/deadlock", None),  # 500
    ]

    # Ağırlıklı dağılım: %50 Normal 2xx, %20 4xx, %30 5xx Hata
    weights = [
        ("HEALTH", 10),
        ("CREATE_ORDER", 20),
        ("GET_EXISTING_ORDER", 15),
        ("GET_NOT_FOUND_ORDER", 15),
        ("PAYMENT_SUCCESS", 10),
        ("PAYMENT_TIMEOUT_500", 10),
        ("ZERO_DIVISION_500", 10),
        ("DB_DEADLOCK_500", 10),
    ]
    pool = [k for k, w in weights for _ in range(w)]

    for i in range(1, TOTAL_REQUESTS + 1):
        chosen_key = random.choice(pool)
        scenario = next(s for s in scenarios if s[0] == chosen_key)
        _, method, path, body = scenario

        code, resp = send_request(method, path, body)

        if 200 <= code < 300:
            stats["2xx"] += 1
            badge = "\033[32m[2xx OK]\033[0m"
        elif 400 <= code < 500:
            stats["4xx"] += 1
            badge = "\033[33m[4xx CLIENT ERROR]\033[0m"
        elif code >= 500:
            stats["5xx"] += 1
            badge = "\033[31m[5xx SERVER ERROR]\033[0m"
        else:
            stats["fail"] += 1
            badge = "\033[35m[CONNECT FAIL]\033[0m"

        print(f"[{i:02d}/{TOTAL_REQUESTS}] {badge} {method:4} {path[:40]:<40} -> Status {code}")
        time.sleep(0.08)  # Doğal trafik aralığı

    print("\n" + "=" * 65)
    print("📊 Trafik Simülasyon Özeti:")
    print(f"  ✅ Başarılı İstekler (2xx):     {stats['2xx']}")
    print(f"  ⚠️  İstemci Hataları (4xx):      {stats['4xx']}")
    print(f"  🔥 Sunucu Hataları (5xx):       {stats['5xx']}")
    if stats["fail"] > 0:
        print(f"  ❌ Ulaşılamayan İstekler:       {stats['fail']}")
    print("=" * 65)
    if stats["fail"] > 0:
        print("Bazı isteklere ulaşılamadı: servis hazır mı? (curl http://localhost:19002/api/v1/health)\n")
        sys.exit(1)
    print("Loglar Logstash TCP üzerinden Elasticsearch 'logs-fastapi-production' data stream'ine aktarılır.\n")


if __name__ == "__main__":
    main()
