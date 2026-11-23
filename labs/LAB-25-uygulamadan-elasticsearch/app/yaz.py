"""Adim 3: index'i ac, 1000 urunu bulk yardimcisiyla tek seferde yaz."""
from elasticsearch import helpers

from ortak import INDEX, istemci

KATEGORI = ["Bilgisayar", "Ses", "Giyilebilir", "Mobilya", "Mutfak"]

es = istemci()
es.indices.create(index=INDEX, settings={"number_of_shards": 1, "number_of_replicas": 0}, mappings={
    "properties": {
        "urun_id": {"type": "keyword"}, "kategori": {"type": "keyword"},
        "ad": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "fiyat": {"type": "scaled_float", "scaling_factor": 100}, "stok": {"type": "integer"},
    }})


def urunler():
    # Uretec (generator): 1000 document bellekte liste olarak tutulmaz, bulk yardimcisi parca parca gonderir.
    for i in range(1, 1001):
        yield {"_index": INDEX, "_id": f"U{i:04d}", "_source": {
            "urun_id": f"U{i:04d}", "ad": f"Ürün {i}", "kategori": KATEGORI[i % 5],
            "fiyat": round(50 + (i * 37) % 4950 + (i % 100) / 100, 2), "stok": (i * 7) % 120}}


basarili, hatalar = helpers.bulk(es, urunler(), chunk_size=250, refresh="wait_for")
print("yazilan  :", basarili, "| hata:", len(hatalar))
print("sayim    :", es.count(index=INDEX)["count"])
