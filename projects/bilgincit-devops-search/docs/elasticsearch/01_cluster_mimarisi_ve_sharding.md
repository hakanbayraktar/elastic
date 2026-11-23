# Elasticsearch Cluster Mimarisi ve Sharding Rehberi

Bu dokümanda kurumsal Elasticsearch küme (cluster) mimarisi, master-node, data-node ayrımı, primary shard ve replica shard yapılandırması detaylı olarak açıklanmıştır.

## 1. Elasticsearch Node Türleri
Elasticsearch kümesinde her sunucu (node) farklı görevleri üstlenebilir:
- **Master-Eligible Node:** Küme durumunu (cluster state), indekslerin oluşturulmasını ve shard dağıtımını yönetir.
- **Data Node:** Doküman verilerini diskte tutar, CRUD operasyonlarını ve arama (search/aggregation) sorgularını icra eder.
- **Ingest Node:** Doküman indekslenmeden önce pipeline işlemlerini (grok, date, set, drop) yürütür.
- **Coordinating Node:** İstemciden gelen istekleri karşılar, ilgili data node'lara dağıtır ve gelen sonuçları birleştirip istemciye döner.

## 2. Shard ve Replica Yönetimi
Bir indeks fiziksel olarak Lucene indeks parçalarına (shard) bölünür.

```json
PUT /bilgincit_logs
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "routing.allocation.total_shards_per_node": 2
  }
}
```

### Önemli Kurallar:
- **Primary Shard Sayısı:** İndeks oluşturulduktan sonra doğrudan artırılamaz (split API gerekir).
- **Replica Shard Sayısı:** Dinamik olarak çalışma zamanında artırılabilir veya azaltılabilir.
- **Split Brain Önlemi:** Çift sayılı master node yerine tek sayılı (3, 5) master node kurulmalıdır.

```bash
# Küme sağlığını (Cluster Health) kontrol etme komutu
curl -X GET "http://localhost:9200/_cluster/health?pretty"
```

## 3. Shard Boyutlandırma Best Practice
- Shard boyutlarının 20 GB ile 50 GB arasında tutulması tavsiye edilir.
- Bir gigabyte JVM Heap başına en fazla 20-25 shard hedeflenmelidir.
