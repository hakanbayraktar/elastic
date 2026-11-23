"""Adim 6: zaman asimi ve yeniden deneme. Hangi hata tekrar denenir, hangisi denenmez?"""
import logging

from elasticsearch import ConnectionError, ConnectionTimeout, Elasticsearch

from ortak import INDEX, istemci


class Sayac(logging.Handler):
    """elastic_transport her denemeyi WARNING olarak loglar; denemeleri sayariz."""
    def __init__(self):
        super().__init__(); self.n = 0

    def emit(self, kayit):
        if "Retrying" in kayit.getMessage():
            self.n += 1


s = Sayac()
logging.getLogger("elastic_transport.transport").addHandler(s)

# 1) Cok kisa zaman asimi: istek yetismez, istemci 3 kez tekrar dener.
es = istemci()
try:
    es.options(request_timeout=0.001).search(index=INDEX, query={"match_all": {}})
except ConnectionTimeout:
    print("zaman asimi :", "ConnectionTimeout, tekrar deneme =", s.n)

# 2) Kapali port: baglanti kurulamaz, yine tekrar denenir ve sonunda vazgecilir.
s.n = 0
kapali = Elasticsearch("http://127.0.0.1:9299", api_key="x", request_timeout=2, max_retries=2)
try:
    kapali.info()
except ConnectionError:
    print("kapali port :", "ConnectionError, tekrar deneme =", s.n)

# 3) Mantik hatasi (404) tekrar denenmez: ayni istek ayni cevabi verir.
s.n = 0
print("404         :", es.options(ignore_status=404).get(index=INDEX, id="U9999").meta.status, "tekrar deneme =", s.n)
