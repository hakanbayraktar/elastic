#!/usr/bin/env python3
"""
Elasticsearch 9.x İstemci Bağlantı Yardımcısı (Helper)
------------------------------------------------------
Bu modül, Elasticsearch 9.5.5 cluster'ına bağlantı sağlar.
Lab ortamında Elasticsearch yerel olarak düz HTTP (9200) çalışır;
dış dünya SSL sonlandırması Nginx/Cloudflare katmanında yapılır.
İstemci hem doğrudan HTTP'yi hem de olası HTTPS (self-signed/proxy)
bağlantılarını destekleyecek şekilde esnek yapılandırılmıştır.

Ortam Değişkenleri:
- ELASTIC_URL      : Varsayılan "http://localhost:9200" veya "https://localhost:9200"
- ELASTIC_USER     : Varsayılan "elastic"
- ELASTIC_PASSWORD : Varsayılan "DevOps2026!"
"""

import os
import urllib3
from elasticsearch import Elasticsearch

# Lab ortamlarındaki self-signed TLS sertifika uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_es_client() -> Elasticsearch:
    """
    Elasticsearch istemcisini ortam değişkenlerine göre başlatır ve döndürür.
    """
    es_url = os.getenv("ELASTIC_URL", "http://localhost:9200")
    es_user = os.getenv("ELASTIC_USER", "elastic")
    es_password = os.getenv("ELASTIC_PASSWORD", "DevOps2026!")

    # URL https ile başlıyorsa SSL doğrulamayı lab ortamı için esnet
    is_https = es_url.startswith("https")

    client = Elasticsearch(
        hosts=[es_url],
        basic_auth=(es_user, es_password) if es_password else None,
        verify_certs=False if is_https else False,
        ssl_show_warn=False,
        request_timeout=30
    )
    return client

if __name__ == "__main__":
    es = get_es_client()
    info = es.info()
    print("✅ Elasticsearch Bağlantısı Başarılı!")
    print(f"   Cluster Adı : {info.get('cluster_name')}")
    print(f"   Elastic Sürüm: {info.get('version', {}).get('number')}")
