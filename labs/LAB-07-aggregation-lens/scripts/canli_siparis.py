"""Canli siparis akisi (sentetik): analiz-canli index'ine saniyede bir siparis yazar.

  python3 scripts/canli_siparis.py gecmis        # son 15 dakikayi saniyede bir siparisle doldurur (_bulk)
  python3 scripts/canli_siparis.py canli 600     # 600 saniye boyunca her saniye yeni siparis yazar
"""
import base64, json, os, random, sys, time
from datetime import datetime, timedelta, timezone
from urllib import request

ES = os.environ.get("ES_URL", "http://127.0.0.1:9200")
AUTH = base64.b64encode(f"elastic:{os.environ.get('ELASTIC_PASSWORD', 'DevOps2026!')}".encode()).decode()
KATEGORI = ["Giyim", "Ayakkabı", "Elektronik", "Kozmetik"]


def istek(yol, govde, tip="application/json"):
    req = request.Request(f"{ES}/{yol}", data=govde.encode(), method="POST",
                          headers={"Authorization": f"Basic {AUTH}", "Content-Type": tip})
    with request.urlopen(req) as r:
        return json.load(r)


def siparis(zaman):
    return {"@timestamp": zaman.strftime("%Y-%m-%dT%H:%M:%SZ"), "kategori": random.choice(KATEGORI),
            "tutar": round(random.uniform(20, 400), 2)}


if __name__ == "__main__":
    simdi = datetime.now(timezone.utc)
    if sys.argv[1] == "gecmis":
        satirlar = []
        for s in range(900, 0, -1):
            satirlar += ['{"index":{}}', json.dumps(siparis(simdi - timedelta(seconds=s)), ensure_ascii=False)]
        r = istek("analiz-canli/_bulk?refresh=true", "\n".join(satirlar) + "\n", "application/x-ndjson")
        print("gecmis 15 dakika:", len(r["items"]), "siparis, hata:", r["errors"])
    else:
        bitis = time.time() + int(sys.argv[2])
        while time.time() < bitis:
            istek("analiz-canli/_doc", json.dumps(siparis(datetime.now(timezone.utc)), ensure_ascii=False))
            time.sleep(1)
