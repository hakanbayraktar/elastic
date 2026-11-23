"""Butun betiklerin kullandigi istemci: adres ve API key ortam degiskeninden gelir, parola kodda yoktur."""
import os

from elasticsearch import Elasticsearch

ES_URL = os.environ.get("ES_URL", "http://127.0.0.1:9200")
INDEX = "py-urunler"


def istemci(**ayar):
    anahtar = os.environ.get("ES_API_KEY")
    if not anahtar:
        raise SystemExit("ES_API_KEY tanimli degil (Adim 2).")
    # request_timeout: tek istegin en fazla bekleme suresi; max_retries: baglanti/zaman asimi hatasinda tekrar
    return Elasticsearch(ES_URL, api_key=anahtar, request_timeout=10, max_retries=3, retry_on_timeout=True, **ayar)
