"""Dev Tools (.http) dosyasindaki istekleri sirayla Elasticsearch'e gonderir; Kibana Console'a yapistirmanin terminal karsiligi.

Kullanim: python3 scripts/apply_http.py dev-tools/01-create-ecommerce-schema.http
Istekler '###' ile ayrilir; '#' ile baslayan satirlar yorumdur. Her istek icin 'METOT yol -> HTTP kod' yazilir.
"""
import base64
import json
import os
import sys
from urllib import error, request

ES = os.environ.get("ELASTICSEARCH_URL", "http://127.0.0.1:9200")
AUTH = base64.b64encode(f"{os.environ.get('ELASTIC_USER', 'elastic')}:{os.environ.get('ELASTIC_PASSWORD', 'DevOps2026!')}".encode()).decode()


def gonder(metot, yol, govde):
    veri = json.dumps(govde).encode() if govde is not None else None
    req = request.Request(f"{ES}/{yol.lstrip('/')}", data=veri, method=metot,
                          headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"})
    try:
        with request.urlopen(req) as r:
            return r.status
    except error.HTTPError as e:
        return e.code


def main(dosya):
    hata = 0
    for parca in open(dosya, encoding="utf-8").read().split("###"):
        satirlar = [s for s in parca.splitlines() if s.strip() and not s.lstrip().startswith("#")]
        if not satirlar:
            continue
        metot, yol = satirlar[0].split(None, 1)
        govde = json.loads("\n".join(satirlar[1:])) if len(satirlar) > 1 else None
        kod = gonder(metot.upper(), yol.strip(), govde)
        print(f"{metot.upper()} {yol.strip()} -> {kod}")
        hata += kod >= 400 and metot.upper() != "DELETE"
    sys.exit(1 if hata else 0)


if __name__ == "__main__":
    main(sys.argv[1])
