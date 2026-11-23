#!/usr/bin/env python3
"""
NovaCommerce: Kibana E-Commerce Sample Data ETL & Autocomplete İndeksleyici
--------------------------------------------------------------------
Bu script:
1. Mevcut Elasticsearch cluster'ına bağlanır (ELASTIC_URL, ELASTIC_USER, ELASTIC_PASSWORD).
2. 'ecommerce_search_products' index'ini custom edge_ngram analyzer ve mapping ile oluşturur.
3. 'kibana_sample_data_ecommerce' index'indeki siparişlerden tekil ürünleri ayıklar.
4. Kurumsal arama mimarisine uygun olarak 'search_autocomplete' alanını hazırlar
   ve Elasticsearch'e toplu olarak (bulk) index'ler.
"""

import os
import sys
import logging
import urllib3
from elasticsearch import Elasticsearch, helpers

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ELASTIC_URL = os.getenv("ELASTIC_URL", "http://localhost:9200")
ELASTIC_USER = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "DevOps2026!")

SOURCE_INDEX = "kibana_sample_data_ecommerce"
TARGET_INDEX = "ecommerce_search_products"

INDEX_SETTINGS_MAPPINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "tokenizer": {
                "autocomplete_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"]
                }
            },
            "analyzer": {
                "autocomplete_index": {
                    "type": "custom",
                    "tokenizer": "autocomplete_tokenizer",
                    "filter": ["lowercase"]
                },
                "autocomplete_search": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "product_name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
            },
            "brand": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "category": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "price": {"type": "float"},
            "discount_percentage": {"type": "float"},
            "currency": {"type": "keyword"},
            "in_stock": {"type": "boolean"},
            "units_sold": {"type": "integer"},
            "search_autocomplete": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_index",
                        "search_analyzer": "autocomplete_search"
                    }
                }
            }
        }
    }
}

# Eğer kibana_sample_data_ecommerce henüz yüklenmediyse kullanılacak yüksek kaliteli yedek ürün kataloğu
FALLBACK_PRODUCTS = [
    {"product_id": "P001", "product_name": "Casual Summer Dress", "brand": "Elitelligence", "category": "Women's Clothing", "price": 49.99, "discount_percentage": 10.0, "currency": "EUR", "in_stock": True, "units_sold": 340},
    {"product_id": "P002", "product_name": "Maxi Floral Summer Dress", "brand": "Oceanavigations", "category": "Women's Clothing", "price": 79.90, "discount_percentage": 15.0, "currency": "EUR", "in_stock": True, "units_sold": 280},
    {"product_id": "P003", "product_name": "Classic Leather Oxford Shoes", "brand": "Elitelligence", "category": "Men's Shoes", "price": 129.50, "discount_percentage": 0.0, "currency": "EUR", "in_stock": True, "units_sold": 190},
    {"product_id": "P004", "product_name": "Breathable Running Sneakers Shoes", "brand": "Tornado", "category": "Men's Shoes", "price": 89.00, "discount_percentage": 20.0, "currency": "EUR", "in_stock": True, "units_sold": 520},
    {"product_id": "P005", "product_name": "Vintage Denim Jeans Trousers", "brand": "Oceanavigations", "category": "Men's Clothing", "price": 59.99, "discount_percentage": 5.0, "currency": "EUR", "in_stock": True, "units_sold": 410},
    {"product_id": "P006", "product_name": "Slim Fit Casual Chino Trousers", "brand": "Elitelligence", "category": "Men's Clothing", "price": 45.00, "discount_percentage": 0.0, "currency": "EUR", "in_stock": True, "units_sold": 230},
    {"product_id": "P007", "product_name": "Winter Warm Wool Knit Sweater", "brand": "Tornado", "category": "Women's Clothing", "price": 69.00, "discount_percentage": 25.0, "currency": "EUR", "in_stock": True, "units_sold": 160},
    {"product_id": "P008", "product_name": "Waterproof Outdoor Hiking Shoes", "brand": "Tornado", "category": "Men's Shoes", "price": 110.00, "discount_percentage": 10.0, "currency": "EUR", "in_stock": True, "units_sold": 310},
    {"product_id": "P009", "product_name": "Graphic Print Cotton T-Shirt", "brand": "Oceanavigations", "category": "Men's Clothing", "price": 24.99, "discount_percentage": 0.0, "currency": "EUR", "in_stock": True, "units_sold": 890},
    {"product_id": "P010", "product_name": "Elegant Silk Evening Dress", "brand": "Elitelligence", "category": "Women's Clothing", "price": 189.00, "discount_percentage": 5.0, "currency": "EUR", "in_stock": True, "units_sold": 95},
    {"product_id": "P011", "product_name": "Leather Handbag Shoulder Bag", "brand": "Elitelligence", "category": "Women's Accessories", "price": 145.00, "discount_percentage": 10.0, "currency": "EUR", "in_stock": True, "units_sold": 210},
    {"product_id": "P012", "product_name": "Polarized UV400 Sunglasses", "brand": "Tornado", "category": "Men's Accessories", "price": 39.90, "discount_percentage": 0.0, "currency": "EUR", "in_stock": True, "units_sold": 450}
]

def get_client() -> Elasticsearch:
    return Elasticsearch(
        hosts=[ELASTIC_URL],
        basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD) if ELASTIC_PASSWORD else None,
        verify_certs=False,
        ssl_show_warn=False,
        request_timeout=30
    )

def recreate_target_index(client: Elasticsearch):
    if client.indices.exists(index=TARGET_INDEX):
        logging.info(f"Mevcut '{TARGET_INDEX}' index'i siliniyor...")
        client.indices.delete(index=TARGET_INDEX)
    logging.info(f"'{TARGET_INDEX}' index'i custom edge_ngram analyzer ile oluşturuluyor...")
    client.indices.create(index=TARGET_INDEX, body=INDEX_SETTINGS_MAPPINGS)
    logging.info(f"'{TARGET_INDEX}' index'i başarıyla hazırlandı.")

def extract_products_from_sample_data(client: Elasticsearch):
    products_map = {}
    
    if not client.indices.exists(index=SOURCE_INDEX):
        logging.warning(f"'{SOURCE_INDEX}' bulunamadı! Yedek örnek ürün kataloğu yükleniyor...")
        for p in FALLBACK_PRODUCTS:
            pid = p["product_id"]
            p["search_autocomplete"] = f"{p['brand']} {p['product_name']}"
            products_map[pid] = p
        return list(products_map.values())

    logging.info(f"'{SOURCE_INDEX}' kaynağından siparişler okunuyor ve ürünler tekilleştiriliyor...")
    
    # 500 sipariş dokümanı çekerek ürün havuzunu topla
    resp = client.search(
        index=SOURCE_INDEX,
        size=500,
        _source=["products", "currency"]
    )
    
    hits = resp.get("hits", {}).get("hits", [])
    logging.info(f"{len(hits)} adet sipariş inceleniyor...")

    for hit in hits:
        source = hit.get("_source", {})
        currency = source.get("currency", "EUR")
        for prod in source.get("products", []):
            prod_id = str(prod.get("product_id") or "")
            prod_name = prod.get("product_name") or ""
            if not prod_id or not prod_name:
                continue
            
            if prod_id not in products_map:
                brand = prod.get("manufacturer") or "General"
                cat = prod.get("category") or "General"
                price = float(prod.get("base_price") or prod.get("price") or 0.0)
                discount = float(prod.get("discount_percentage") or 0.0)
                
                # Makaledeki kurgu: search_autocomplete alanı marka ve model/ürün adını kapsar
                search_autocomplete_text = f"{brand} {prod_name}"
                
                products_map[prod_id] = {
                    "product_id": prod_id,
                    "product_name": prod_name,
                    "brand": brand,
                    "category": cat,
                    "price": round(price, 2),
                    "discount_percentage": discount,
                    "currency": currency,
                    "in_stock": True,
                    "units_sold": int(prod.get("quantity", 1)),
                    "search_autocomplete": search_autocomplete_text
                }
            else:
                products_map[prod_id]["units_sold"] += int(prod.get("quantity", 1))

    logging.info(f"Toplam {len(products_map)} adet tekil ürün tespit edildi.")
    return list(products_map.values())

def bulk_index_products(client: Elasticsearch, products: list):
    actions = [
        {
            "_index": TARGET_INDEX,
            "_id": p["product_id"],
            "_source": p
        }
        for p in products
    ]
    success_count, errors = helpers.bulk(client, actions, refresh=True)
    logging.info(f"✅ Başarıyla indexlenen ürün sayısı: {success_count}")
    if errors:
        logging.error(f"Hatalar: {errors}")

def main():
    try:
        client = get_client()
        if not client.ping():
            logging.error(f"Elasticsearch sunucusuna erişilemedi: {ELASTIC_URL}")
            sys.exit(1)
        
        info = client.info()
        logging.info(f"Elasticsearch Bağlantısı Başarılı: Sürüm {info.get('version', {}).get('number')}")
        
        recreate_target_index(client)
        products = extract_products_from_sample_data(client)
        bulk_index_products(client, products)
        
        count = client.count(index=TARGET_INDEX).get("count", 0)
        print("\n" + "=" * 60)
        print(f"🎉 ETL Başarıyla Tamamlandı!")
        print(f"   Hedef Index : {TARGET_INDEX}")
        print(f"   Toplam Ürün  : {count}")
        print(f"   Hazır Sorgu  : GET /{TARGET_INDEX}/_search")
        print("=" * 60 + "\n")
    except Exception as e:
        logging.exception(f"ETL sırasında hata meydana geldi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
