"""Adim 2: API key ile baglan, kim oldugunu sor, yetki disi bir index'e yazmayi dene."""
from elasticsearch import AuthorizationException

from ortak import istemci

es = istemci()
info = es.info()
kim = es.security.authenticate()
print("cluster  :", info["cluster_name"], info["version"]["number"])
print("kimlik   :", kim["authentication_type"], kim["api_key"]["name"])

try:
    es.index(index="belge-deneme", document={"deneme": 1})
except AuthorizationException as hata:
    print("yetkisiz :", hata.meta.status, hata.body["error"]["type"])
