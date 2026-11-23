#!/usr/bin/env python3
"""
Python ile Elasticsearch Query DSL, Aggregations ve SQL Sorgulama
------------------------------------------------------------------
Bu script;
1. Query DSL ile match ve bool filtre araması yapar.
2. Metric (avg) ve Bucket (terms) aggregations çalıştırır.
3. Elasticsearch SQL API'sini çağırarak sonuçları tablo gibi alır.
"""

from es_client_helper import get_es_client

def main():
    es = get_es_client()
    index_name = "training-python-crud"

    if not es.indices.exists(index=index_name):
        print(f"Hata: {index_name} index'i bulunamadı. Lütfen önce 01_verify_cluster_and_crud.py scriptini çalıştırın.")
        return

    print("==================================================")
    print("1. Query DSL: Bool Filtre ve Match Araması")
    print("==================================================")
    search_query = {
        "bool": {
            "must": [
                {"match": {"title": "kablosuz"}}
            ],
            "filter": [
                {"term": {"category": "Electronics"}},
                {"range": {"price": {"lte": 150.0}}}
            ]
        }
    }
    res = es.search(index=index_name, query=search_query)
    hits = res["hits"]["hits"]
    print(f"Bulunan Eşleşme Sayısı: {len(hits)}")
    for hit in hits:
        source = hit["_source"]
        print(f"  - [{hit['_id']}] {source['title']} (Fiyat: {source['price']} TL, Skor: {hit['_score']:.2f})")

    print("\n==================================================")
    print("2. Aggregations: Kategori Bazlı Ortalama Fiyat")
    print("==================================================")
    agg_query = {
        "by_category": {
            "terms": {
                "field": "category"
            },
            "aggs": {
                "average_price": {
                    "avg": {
                        "field": "price"
                    }
                }
            }
        }
    }
    agg_res = es.search(index=index_name, size=0, aggregations=agg_query)
    buckets = agg_res["aggregations"]["by_category"]["buckets"]
    for b in buckets:
        cat_name = b["key"]
        doc_count = b["doc_count"]
        avg_price = b["average_price"]["value"]
        print(f"  - Kategori: {cat_name:<12} | Ürün Sayısı: {doc_count} | Ort. Fiyat: {avg_price:.2f} TL")

    print("\n==================================================")
    print("3. Elasticsearch SQL API Çağrısı")
    print("==================================================")
    sql_query = f"SELECT category, count(*), ROUND(AVG(price), 2) AS avg_p FROM \"{index_name}\" GROUP BY category"
    try:
        sql_res = es.sql.query(query=sql_query, format="txt")
        print("SQL Sonuç Tablosu:")
        print(sql_res)
    except Exception as e:
        print(f"SQL API uyarısı/notu: {e}")

    print("\n🎉 Tüm Python Arama ve Analitik testleri tamamlandı!")

if __name__ == "__main__":
    main()
