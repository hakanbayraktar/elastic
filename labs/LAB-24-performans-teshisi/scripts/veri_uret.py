#!/usr/bin/env python3
"""perf-urunler index'ini acar ve 200.000 urun yazar (sabit tohum: her seferinde ayni veri).
Yalniz standart kutuphane. Kullanim: python3 scripts/veri_uret.py
"""
import base64
import json
import random
import urllib.request

ES = "http://127.0.0.1:9200"
AUTH = "Basic " + base64.b64encode(b"elastic:DevOps2026!").decode()
INDEX = "perf-urunler"
N = 200_000


def istek(method, path, body, ctype="application/json"):
    req = urllib.request.Request(ES + path, method=method, data=body)
    req.add_header("Authorization", AUTH)
    req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


istek("PUT", f"/{INDEX}", json.dumps({
    "settings": {"number_of_shards": 1, "number_of_replicas": 0, "refresh_interval": "-1"},
    "mappings": {"properties": {
        "urun_id": {"type": "keyword"},
        "ad": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "kategori": {"type": "keyword"},
        "fiyat": {"type": "float"},
        "stok": {"type": "integer"},
    }}}).encode())

r = random.Random(42)
MARKA = ["Nova", "Atlas", "Delta", "Orion", "Vega", "Kuzey", "Mavi", "Zirve"]
URUN = ["Kablosuz Kulaklık", "Akıllı Saat", "Dizüstü Bilgisayar", "Bluetooth Hoparlör", "Oyun Faresi",
        "Mekanik Klavye", "Tablet Kılıfı", "Şarj Aleti", "Ofis Sandalyesi", "Çelik Termos"]
KAT = ["Ses", "Giyilebilir", "Bilgisayar", "Aksesuar", "Mobilya", "Mutfak"]
hata = False
for bas in range(0, N, 10_000):
    satirlar = []
    for i in range(bas, bas + 10_000):
        satirlar.append(json.dumps({"index": {"_id": f"P{i:06d}"}}))
        satirlar.append(json.dumps({"urun_id": f"P{i:06d}", "ad": f"{r.choice(MARKA)} {r.choice(URUN)} {r.randint(100, 99999)}",
                                    "kategori": r.choice(KAT), "fiyat": round(r.uniform(50, 30000), 2), "stok": r.randint(0, 500)},
                                   ensure_ascii=False))
    sonuc = istek("POST", f"/{INDEX}/_bulk", ("\n".join(satirlar) + "\n").encode(), "application/x-ndjson")
    hata = hata or sonuc["errors"]
istek("PUT", f"/{INDEX}/_settings", json.dumps({"index": {"refresh_interval": None}}).encode())
istek("POST", f"/{INDEX}/_refresh", b"")
istek("POST", f"/{INDEX}/_forcemerge?max_num_segments=1", b"")
sayi = istek("GET", f"/{INDEX}/_count", None)["count"]
print(f"[+] {sayi} urun yazildi ({INDEX}), hata: {hata}")
