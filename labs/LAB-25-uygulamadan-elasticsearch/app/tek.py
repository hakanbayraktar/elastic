"""Adim 7: tek document yaz (es.index), id ile oku (es.get), match ile ara (es.search)."""
from ortak import istemci

es = istemci()
TEK = "py-tek"                      # Adim 3-6'daki py-urunler'e dokunmaz; API key py-* icin yetkilidir

# Index'i once kendimiz aciyoruz: mapping'i API key'in "index" yetkisine biraktirmak (otomatik mapping guncellemesi)
# bir sonraki surumde yetkisiz kalacak. Tek node oldugu icin replica 0.
if not es.indices.exists(index=TEK):
    es.indices.create(index=TEK, settings={"number_of_replicas": 0},
                      mappings={"properties": {"urun_id": {"type": "keyword"}, "ad": {"type": "text"}, "fiyat": {"type": "float"}}})

URUNLER = [
    ("T1", "Kablosuz Kulaklık", 1149.5),
    ("T2", "Kablolu Kulaklık", 399.9),
    ("T3", "Termos 750 ml", 349.0),
]
for urun_id, ad, fiyat in URUNLER:
    # refresh="wait_for": document aramada gorunene kadar bekler; uygulamada genelde gerekmez
    sonuc = es.index(index=TEK, id=urun_id, document={"urun_id": urun_id, "ad": ad, "fiyat": fiyat}, refresh="wait_for")
    print(f"index  : {urun_id} {sonuc['result']} (surum {sonuc['_version']})")

belge = es.get(index=TEK, id="T1")
print("get    :", belge["found"], belge["_source"])

yanit = es.search(index=TEK, query={"match": {"ad": "kulaklık"}})
print("match  :", yanit["hits"]["total"]["value"], "sonuc")
for hit in yanit["hits"]["hits"]:
    print(f"  {hit['_source']['ad']:20s} {hit['_source']['fiyat']:8.2f}  skor {hit['_score']:.2f}")
