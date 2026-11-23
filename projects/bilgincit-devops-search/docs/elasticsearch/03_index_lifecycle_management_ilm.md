# Elasticsearch Index Lifecycle Management (ILM)

Büyük veri ve log yönetimi projelerinde zaman serisi verilerin (time-series data) yaşam döngüsünü yönetmek için ILM kullanılır.

## 1. ILM Yaşam Döngüsü Fazları
1. **Hot (Sıcak):** Sürekli yazılan (write/ingest) ve yoğun aranan veriler. Hızlı NVMe diskler kullanılır.
2. **Warm (Ilık):** Artık yazılmayan, sadece okunan ve ara sıra sorgulanan veriler. Force merge ile segment sayısı 1'e düşürülür.
3. **Cold (Soğuk):** Nadiren sorgulanan veriler. Replica sayısı azaltılır veya Searchable Snapshots kullanılır.
4. **Frozen (Donuk):** Sadece arşiv niteliğinde, doğrudan S3/Blob storage üzerinden taranan veriler.
5. **Delete (Silme):** Belirli süre (örneğin 90 gün) sonra indeksin otomatik silindiği aşama.

## 2. ILM İlkesi Oluşturma Örneği

```json
PUT _ilm/policy/bilgincit_log_policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50GB",
            "max_age": "7d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "forcemerge": {
            "max_num_segments": 1
          }
        }
      },
      "delete": {
        "min_age": "60d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

```bash
# ILM durumunu kontrol etme komutu
curl -X GET "http://localhost:9200/bilgincit_logs-*/_ilm/explain?pretty"
```
