#!/usr/bin/env python3
"""Load e-commerce products, customers, and orders into Elasticsearch."""
import base64
import json
import os
from pathlib import Path
import ssl
from urllib import request, error

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / 'sample-data'

ELASTIC_USER = os.environ.get('ELASTIC_USER', 'elastic')
ELASTIC_PASSWORD = os.environ.get('ELASTIC_PASSWORD', 'DevOps2026!')
AUTH_HEADER = 'Basic ' + base64.b64encode(f"{ELASTIC_USER}:{ELASTIC_PASSWORD}".encode()).decode()

def resolve_elastic_url():
    explicit = os.environ.get('ELASTIC_URL') or os.environ.get('ELASTICSEARCH_URL')
    if explicit:
        return explicit.rstrip('/')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for scheme in ('http', 'https'):
        url = f"{scheme}://127.0.0.1:9200"
        try:
            req = request.Request(f"{url}/_cluster/health", headers={'Authorization': AUTH_HEADER})
            with request.urlopen(req, timeout=2, context=ctx):
                return url
        except error.HTTPError:
            # Cluster cevap veriyor (örn. 401) -> adres doğru, kimlik bilgisi ayrıca kontrol edilir
            return url
        except Exception:
            pass
    return 'http://127.0.0.1:9200'

ELASTIC_URL = resolve_elastic_url()
HEADERS = {'Content-Type': 'application/x-ndjson', 'Authorization': AUTH_HEADER}
CONTEXT = ssl.create_default_context(cafile=os.environ.get('ELASTIC_CA_FILE'))
if not os.environ.get('ELASTIC_CA_FILE'):
    CONTEXT.check_hostname = False
    CONTEXT.verify_mode = ssl.CERT_NONE

def load_ndjson(filename):
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(path)
    payload = path.read_bytes()
    req = request.Request(f"{ELASTIC_URL}/_bulk?refresh=true", data=payload, headers=HEADERS, method='POST')
    try:
        res = request.urlopen(req, timeout=30, context=CONTEXT)
        with res:
            data = json.loads(res.read().decode())
            items = len(data.get('items', []))
            if data.get('errors') or items != 20:
                raise RuntimeError(f"Bulk load failed for {filename}: {items} items, errors={data.get('errors')}")
            print(f"Loaded {filename}: {items} items")
    except error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')[:300]
        hint = ''
        if exc.code == 401:
            hint = (f"\nKimlik doğrulaması başarısız. Kullanılan kullanıcı: '{ELASTIC_USER}'. "
                    "Farklı bir parola kullanıyorsanız: "
                    "ELASTIC_USER=elastic ELASTIC_PASSWORD='<parola>' python3 scripts/load_ecommerce_data.py")
        raise RuntimeError(f"Failed to load {filename}: HTTP {exc.code}: {detail}{hint}") from None

if __name__ == '__main__':
    print(f"Connecting to Elasticsearch at {ELASTIC_URL}...")
    load_ndjson('products.ndjson')
    load_ndjson('customers.ndjson')
    load_ndjson('orders.ndjson')
    print("E-commerce datasets loaded successfully.")
