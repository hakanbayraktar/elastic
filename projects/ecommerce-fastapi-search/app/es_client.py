"""
Elasticsearch Python İstemci Katmanı ve Bağlantı Rehberi
=========================================================
Bu modül, resmi 'elasticsearch' Python SDK (v8 ve v9 uyumlu) kullanarak
cluster bağlantısını kurar, yapılandırır ve yönetir.

Nasıl Bağlanılır? Adım Adım Rehber:
-----------------------------------
1. Kütüphane Kurulumu:
   pip install elasticsearch

2. Bağlantı Yöntemleri:
   a) Geliştirme Ortamı (HTTP, Temel Kimlik Doğrulama):
      client = Elasticsearch(
          hosts=["http://localhost:9200"],
          basic_auth=("elastic", "DevOps2026!")
      )

   b) Üretim Ortamı (HTTPS, TLS Sertifika Doğrulaması):
      client = Elasticsearch(
          hosts=["https://elastic.devopsatolyesi.com:9200"],
          ca_certs="/etc/ssl/certs/ca.crt",
          basic_auth=("elastic", "GuvendigiSifre!")
      )

   c) API Key ile Bağlantı:
      client = Elasticsearch(
          hosts=["https://localhost:9200"],
          api_key=("id", "api_key_secret")
      )

3. Dayanıklılık (Resilience) Ayarları:
   - request_timeout: Sorguların sonsuza kadar beklemesini önler (örn: 30 sn).
   - max_retries: Ağ kopmalarında 3 defaya kadar tekrar dener.
   - retry_on_status: 502, 503, 504 gibi geçici gateway hatalarında otomatik yeniden dener.
"""

import logging
import urllib3
from elasticsearch import Elasticsearch
from app.config import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("es-client")

_client_instance = None

def get_elasticsearch_client() -> Elasticsearch:
    """
    Singleton Elasticsearch istemci örneği üretir veya mevcut olanı döner.
    """
    global _client_instance
    if _client_instance is None:
        logger.info(f"Elasticsearch istemcisi başlatılıyor: {settings.ELASTIC_URL}")
        
        is_https = settings.ELASTIC_URL.startswith("https")
        
        _client_instance = Elasticsearch(
            hosts=[settings.ELASTIC_URL],
            basic_auth=(settings.ELASTIC_USER, settings.ELASTIC_PASSWORD) 
                       if settings.ELASTIC_PASSWORD else None,
            verify_certs=False if is_https else False,
            ssl_show_warn=False,
            request_timeout=30,
            max_retries=3,
            retry_on_status=(502, 503, 504)
        )
    return _client_instance

def check_cluster_health() -> dict:
    """Cluster sağlık durumunu sorgular."""
    client = get_elasticsearch_client()
    return client.cluster.health()
