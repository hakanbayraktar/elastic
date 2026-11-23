# ECS Veri Sözleşmesi — Telecom Operations Insight Platform

Bu dosyayı uygulanan pipeline ve mapping ile doldurun. Aynı iş kavramı için farklı kaynaklarda farklı alan adı üretmeyin.

| Kaynak değeri | ECS hedef alanı | Elasticsearch tipi | Dönüşüm / doğrulama | Gerekçe |
|---|---|---|---|---|
| Proxy HTTP status | `http.response.status_code` | `short` | Sayıya dönüştür, 500–599 filter ile kontrol et | Hata oranı ve range sorgusu |
| Uygulama süre (ms) | `event.duration` | `long` (ns) | `ms × 1_000_000` | p95 aggregation |
| Correlation ID | `trace.id` | `keyword` | Exact değer | Servisler arası korelasyon |
| İstemci adresi | `client.ip` | `ip` | GeoIP enrichment | IP filtre ve konum analizi |
| Uygulama adı | `service.name` | `keyword` | Sabit sözlük | Service filter/dashboard |
| Kaynak ailesi | `event.dataset` | `keyword` | `novashop.access` vb. | Kaynak karşılaştırması |
| Pod adı | `kubernetes.pod.name` | `keyword` | Kubernetes metadata | Workload bağlamı |

## Sözleşme kontrolleri

- [ ] `@timestamp` UTC ve `date` tipinde.
- [ ] IP, status ve duration string olarak kalmıyor.
- [ ] Dashboard alanları aggregatable (`keyword` veya sayısal) durumda.
- [ ] Ham mesaj gerektiğinde korunuyor; PII maskelenmeden indexlenmiyor.
- [ ] Yeni alan eklemeden önce mapping/cardinality etkisi değerlendirilmiş.
