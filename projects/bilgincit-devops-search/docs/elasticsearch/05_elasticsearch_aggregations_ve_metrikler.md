# Elasticsearch Aggregations ve Analitik Metrikler Rehberi

Elasticsearch Aggregations, indekslenen veriler üzerinde SQL GROUP BY benzeri gerçek zamanlı analitik ve istatistik hesaplama motorudur.

## 1. Terms Aggregation (Kategorilere Göre Sayım)
Belirli bir alandaki benzersiz değerlerin frekansını bulur:

```json
GET /bilgincit_logs/_search
{
  "size": 0,
  "aggs": {
    "top_status_codes": {
      "terms": {
        "field": "http.response.status_code",
        "size": 5
      }
    }
  }
}
```

## 2. Date Histogram (Zaman Serisi Grafikleri)
Metrikleri zaman aralıklarına (dakika, saat, gün) göre bucket'lara böler:

```json
GET /bilgincit_logs/_search
{
  "size": 0,
  "aggs": {
    "traffic_per_hour": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "1h"
      },
      "aggs": {
        "avg_response_time": {
          "avg": {
            "field": "http.response_time_ms"
          }
        }
      }
    }
  }
}
```
