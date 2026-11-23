"""Adim 5: fiyata gore sirala, search_after ile butun sonuclari sayfa sayfa oku."""
from elasticsearch import BadRequestError

from ortak import INDEX, istemci

es = istemci()
# Son siralama alani benzersiz olmali (urun_id); ayni fiyatli urunlerde sira sabit kalir.
SIRA = [{"fiyat": "desc"}, {"urun_id": "asc"}]

sonraki, sayfa, toplam = None, 0, 0
while True:
    yanit = es.search(index=INDEX, size=300, sort=SIRA, source=["urun_id", "fiyat"],
                      query={"match_all": {}}, search_after=sonraki)
    isabetler = yanit["hits"]["hits"]
    if not isabetler:
        break
    sayfa += 1
    toplam += len(isabetler)
    sonraki = isabetler[-1]["sort"]              # bir sonraki sayfa bu degerden sonra baslar
    print(f"sayfa {sayfa}: {len(isabetler):3d} document, ilk {isabetler[0]['_id']}, son {isabetler[-1]['_id']}, search_after={sonraki}")
print("toplam   :", toplam)

try:
    es.search(index=INDEX, from_=9990, size=20, query={"match_all": {}})
except BadRequestError as hata:
    print("from+size:", hata.meta.status, hata.body["error"]["root_cause"][0]["reason"][:60])
