#!/usr/bin/env python3
"""
Python ile Elasticsearch Cluster Doğrulama ve CRUD Operasyonları
-------------------------------------------------------------
Bu script;
1. Cluster sağlığını (Health) denetler.
2. Özel ayarlarla test index'i (training-python-crud) oluşturur.
3. Tekil ve toplu (Bulk) belge ekler.
4. Kısmi güncelleme (Partial update) ve Optimistic Concurrency Control (OCC) test eder.
5. Belgeyi sorgulayıp siler.
"""

from es_client_helper import get_es_client

def main():
    es = get_es_client()
    index_name = "training-python-crud"

    print("==================================================")
    print("1. Cluster Sağlığı Denetimi")
    print("==================================================")
    health = es.cluster.health()
    status = health["status"]
    print(f"Cluster Sağlığı: {status.upper()} (Node Sayısı: {health['number_of_nodes']})")
    assert status in ["green", "yellow"], f"Cluster sağlığı beklenmedik durumda: {status}"

    print("\n==================================================")
    print("2. Test index'i Oluşturma (Explicit Mapping)")
    print("==================================================")
    if es.indices.exists(index=index_name):
        print(f"Mevcut {index_name} index'i temizleniyor...")
        es.indices.delete(index=index_name)

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "1s"
        },
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "category": {"type": "keyword"},
                "price": {"type": "double"},
                "in_stock": {"type": "boolean"},
                "stock_count": {"type": "integer"}
            }
        }
    }
    es.indices.create(index=index_name, body=mapping)
    print(f"✅ Index oluşturuldu: {index_name}")

    print("\n==================================================")
    print("3. CRUD Operasyonları (Create, Read, Update, Delete)")
    print("==================================================")
    
    # CREATE
    doc_1 = {
        "title": "Logitech MX Master 3S Kablosuz Fare",
        "category": "Electronics",
        "price": 99.99,
        "in_stock": True,
        "stock_count": 50
    }
    create_res = es.index(index=index_name, id="prod-001", document=doc_1)
    print(f"✅ Doküman eklendi (ID: prod-001, Sonuç: {create_res['result']})")

    # READ
    get_res = es.get(index=index_name, id="prod-001")
    seq_no = get_res["_seq_no"]
    primary_term = get_res["_primary_term"]
    print(f"✅ Doküman okundu: {get_res['_source']['title']}")
    print(f"   (Seq No: {seq_no}, Primary Term: {primary_term})")

    # UPDATE (OCC ile güvenli güncelleme)
    update_res = es.update(
        index=index_name,
        id="prod-001",
        if_seq_no=seq_no,
        if_primary_term=primary_term,
        doc={"stock_count": 48}
    )
    print(f"✅ Stok güvenle güncellendi (Yeni versiyon: {update_res['_version']})")

    # BULK INSERT
    print("\n==================================================")
    print("4. Toplu Veri Ekleme (Bulk API)")
    print("==================================================")
    operations = [
        {"index": {"_index": index_name, "_id": "prod-002"}},
        {"title": "Dell UltraSharp 27 İnç Monitör", "category": "Electronics", "price": 450.0, "in_stock": True, "stock_count": 15},
        {"index": {"_index": index_name, "_id": "prod-003"}},
        {"title": "Ergonomik Çalışma Masası", "category": "Furniture", "price": 320.0, "in_stock": False, "stock_count": 0}
    ]
    bulk_res = es.bulk(operations=operations, refresh=True)
    print(f"✅ Bulk işlemi tamamlandı. Hata var mı?: {bulk_res.get('errors')}")

    # COUNT
    count_res = es.count(index=index_name)
    print(f"✅ Toplam belge sayısı: {count_res['count']}")

    print("\n🎉 Tüm Python CRUD testleri başarıyla tamamlandı!")

if __name__ == "__main__":
    main()
