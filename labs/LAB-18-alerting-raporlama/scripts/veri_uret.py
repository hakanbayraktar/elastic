"""LAB-18 ornek verisi: son 7 gune yayilmis 6000 Apache erisim olayi (sabit tohum, her kosuda ayni sayilar).

--ariza ile cagrilirsa veriye dokunmadan son bir dakikaya 40 adet 500 (odeme sayfasi) olayi ekler;
alarm kuralini tetiklemek icindir.

alarm-apache index sablonunu kurar, olaylari _bulk ile yazar ve ozet yazdirir. Yalniz Python standart kutuphanesi.
Konum alanlari (source.geo.*) burada sabit bir IP -> sehir tablosundan yazilir; gercek sistemde bunlari
Elasticsearch'in geoip processor'i ya da Logstash'in geoip filtresi uretir.
"""
import base64, json, random, urllib.error, urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

ES = "http://127.0.0.1:9200"
AUTH = "Basic " + base64.b64encode(b"elastic:DevOps2026!").decode()
INDEX = "alarm-apache"

SEHIRLER = [  # (ulke, sehir, enlem, boylam, ip oneki, agirlik)
    ("Turkey", "Istanbul", 41.01, 28.98, "85.105", 30), ("Turkey", "Ankara", 39.93, 32.86, "88.230", 14),
    ("Turkey", "Izmir", 38.42, 27.14, "78.186", 9), ("Germany", "Berlin", 52.52, 13.40, "91.64", 8),
    ("Germany", "Frankfurt", 50.11, 8.68, "93.184", 6), ("Netherlands", "Amsterdam", 52.37, 4.90, "94.142", 6),
    ("United Kingdom", "London", 51.51, -0.13, "81.2", 7), ("France", "Paris", 48.86, 2.35, "90.84", 5),
    ("United States", "New York", 40.71, -74.01, "104.28", 9), ("Azerbaijan", "Baku", 40.41, 49.87, "185.81", 6),
]
YOLLAR = [("/", 30), ("/urunler", 22), ("/urun/detay", 18), ("/sepet", 10), ("/odeme", 6), ("/api/stok", 10), ("/giris", 4)]
TARAYICI = [("Chrome", 55), ("Safari", 20), ("Firefox", 12), ("Edge", 9), ("curl", 4)]


def sec(rng, liste):
    return rng.choices(liste, weights=[x[-1] for x in liste])[0]


def es(method, path, body=None, ndjson=False):
    data = None if body is None else (body if ndjson else json.dumps(body)).encode()
    req = urllib.request.Request(ES + path, data=data, method=method, headers={
        "Authorization": AUTH, "Content-Type": "application/x-ndjson" if ndjson else "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def main():
    # Betik tekrar calistirilinca veri ikiye katlanmasin: index varsa once silinir.
    try:
        es("DELETE", f"/{INDEX}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    es("PUT", "/_index_template/alarm-apache", {
        "index_patterns": [INDEX],
        "template": {"settings": {"number_of_shards": 1, "number_of_replicas": 0},
                     "mappings": {"properties": {
                         "@timestamp": {"type": "date"}, "source.ip": {"type": "ip"},
                         "source.geo.location": {"type": "geo_point"},
                         "source.geo.country_name": {"type": "keyword"}, "source.geo.city_name": {"type": "keyword"},
                         "url.path": {"type": "keyword"}, "http.request.method": {"type": "keyword"},
                         "http.response.status_code": {"type": "integer"}, "http.response.status_class": {"type": "keyword"}, "http.response.bytes": {"type": "long"},
                         "response_time_ms": {"type": "integer"}, "user_agent.name": {"type": "keyword"}}}}})
    # Index connector alarm-gecmisi index'ini kendisi acar; sablon olmazsa 1 replica alir ve tek node'lu
    # cluster yellow kalir. Replica 0 sablonu bunu onler.
    es("PUT", "/_index_template/alarm-gecmisi", {"index_patterns": ["alarm-gecmisi"], "template": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0}}})
    rng = random.Random(14)
    simdi = datetime.now(timezone.utc).replace(microsecond=0)
    satirlar, durum, ulke = [], Counter(), Counter()
    for i in range(6000):
        # Gunduz trafigi daha yogun: saat, 07-23 arasina daha cok agirlik verilerek secilir.
        gun = rng.randrange(7)
        saat = rng.choices(range(24), weights=[1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 6, 5, 3, 2])[0]
        t = simdi - timedelta(days=gun, hours=simdi.hour - saat, minutes=rng.randrange(60), seconds=rng.randrange(60))
        if t > simdi:
            t -= timedelta(days=1)
        ulke_, sehir, lat, lon, onek, _ = sec(rng, SEHIRLER)
        yol = sec(rng, YOLLAR)[0]
        kod, ms = 200, int(rng.lognormvariate(4.3, 0.5))
        if rng.random() < 0.06:
            kod = 404
        # 2 gun once 14:00-16:00 arasi odeme servisinde ariza: /odeme istekleri 500 ve yavas.
        if yol == "/odeme" and gun == 2 and 14 <= saat < 16:
            kod, ms = 500, ms * 20
        elif rng.random() < 0.01:
            kod = 500
        doc = {"@timestamp": t.isoformat().replace("+00:00", "Z"),
               "source": {"ip": f"{onek}.{rng.randrange(1, 255)}.{rng.randrange(1, 255)}",
                          "geo": {"country_name": ulke_, "city_name": sehir,
                                  "location": {"lat": round(lat + rng.uniform(-0.05, 0.05), 4),
                                               "lon": round(lon + rng.uniform(-0.05, 0.05), 4)}}},
               "url": {"path": yol}, "http": {"request": {"method": "POST" if yol in ("/sepet", "/odeme", "/giris") else "GET"},
                                              "response": {"status_code": kod, "status_class": f"{kod // 100}xx", "bytes": rng.randrange(300, 60000)}},
               "response_time_ms": ms, "user_agent": {"name": sec(rng, TARAYICI)[0]}}
        satirlar += [json.dumps({"index": {"_index": INDEX}}), json.dumps(doc)]
        durum[kod] += 1
        ulke[ulke_] += 1
    sonuc = es("POST", "/_bulk?refresh=true&filter_path=errors,items.*.error", "\n".join(satirlar) + "\n", ndjson=True)
    sayim = es("GET", f"/{INDEX}/_count")["count"]
    print(f"[+] {sayim} olay yazildi ({INDEX}), hata: {sonuc.get('errors')}")
    print("    durum kodu :", ", ".join(f"{k}={v}" for k, v in sorted(durum.items())))
    print("    ilk 3 ulke :", ", ".join(f"{k}={v}" for k, v in ulke.most_common(3)))


def ariza():
    simdi = datetime.now(timezone.utc).replace(microsecond=0)
    satirlar = []
    for i in range(40):
        t = simdi - timedelta(seconds=60 - i)
        doc = {"@timestamp": t.isoformat().replace("+00:00", "Z"),
               "source": {"ip": f"85.105.{i + 1}.{i + 7}", "geo": {"country_name": "Turkey", "city_name": "Istanbul",
                                                                     "location": {"lat": 41.01, "lon": 28.98}}},
               "url": {"path": "/odeme"}, "http": {"request": {"method": "POST"},
                                                  "response": {"status_code": 500, "status_class": "5xx", "bytes": 512}},
               "response_time_ms": 4000 + i, "user_agent": {"name": "Chrome"}}
        satirlar += [json.dumps({"index": {"_index": INDEX}}), json.dumps(doc)]
    es("POST", "/_bulk?refresh=true&filter_path=errors", "\n".join(satirlar) + "\n", ndjson=True)
    print(f"[+] 40 adet 500 olayi yazildi (/odeme, son 1 dakika) -> {INDEX}")


if __name__ == "__main__":
    import sys
    ariza() if "--ariza" in sys.argv else main()
