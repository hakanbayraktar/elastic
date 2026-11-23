"""Adim 4: bozuk documentleri bulk icinde yakalamak ve olmayan documenti okumak."""
from elasticsearch import NotFoundError, helpers

from ortak import INDEX, istemci

es = istemci()
gelen = [
    {"urun_id": "Y1", "ad": "Yeni 1", "fiyat": 120.5},
    {"urun_id": "Y2", "ad": "Yeni 2", "fiyat": "ücretsiz"},   # fiyat sayi degil
    {"urun_id": "Y3", "ad": "Yeni 3", "fiyat": 99.9},
    {"urun_id": "Y4", "ad": "Yeni 4", "fiyat": "yok"},        # fiyat sayi degil
    {"urun_id": "Y5", "ad": "Yeni 5", "fiyat": 15.0},
]
eylemler = ({"_index": INDEX, "_id": b["urun_id"], "_source": b} for b in gelen)

# raise_on_error=False: bir document reddedilince istisna atilmaz, reddedilenler liste olarak doner.
basarili, hatalar = helpers.bulk(es, eylemler, raise_on_error=False, refresh="wait_for")
print("yazilan  :", basarili)
for h in hatalar:
    ayrinti = h["index"]
    print("reddedilen:", ayrinti["_id"], ayrinti["status"], ayrinti["error"]["type"])

try:
    es.get(index=INDEX, id="U9999")
except NotFoundError as hata:
    print("bulunamadi:", hata.meta.status, "U9999")
