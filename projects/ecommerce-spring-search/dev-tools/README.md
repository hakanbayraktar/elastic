# 🧭 NovaShop: E-Commerce Search Service Dev Tools Sorgu Rehberi

Bu klasör, e-ticaret arama mimarisi, ürün şeması tasarımı, alaka puanlaması (relevance), faceted search aggregations ve Parent-Child ilişkisel modellemesini adım adım Dev Tools Console üzerinde uygulamanız için hazırlanmıştır.

---

## 📚 Sorgu Dosyaları ve Uygulama Sırası

| Sıra | Dosya | Öğrenilecek Konular |
|:---:|---|---|
| **01** | [`01-create-ecommerce-schema.http`](01-create-ecommerce-schema.http) | Ürün, müşteri ve sipariş şemaları (Multi-fields `text` + `keyword`, `scaled_float`, object address ve Alias tanımları) |
| **02** | [`02-bulk-ecommerce-data.http`](02-bulk-ecommerce-data.http) | `_bulk` API ile 20 ürün, 20 müşteri ve 20 sipariş dokümanının indexlenmesi |
| **03** | [`03-ecommerce-search-and-filtering.http`](03-ecommerce-search-and-filtering.http) | Multi-match, field boosting (`name^2`), fuzzy search (`fuzziness: "AUTO"`), `match_phrase` (`slop: 2`) ve Bool filtresi |
| **04** | [`04-ecommerce-aggregations-and-analytics.http`](04-ecommerce-aggregations-and-analytics.http) | Fiyat aralıkları (`range`), kategori bazında ortalama fiyat (`terms` + `avg`), aylık ciro (`date_histogram`) |
| **05** | [`05-relational-join-parent-child.http`](05-relational-join-parent-child.http) | Parent-Child (`join` type), zorunlu `?routing=<parent_id>`, `has_child`, `has_parent` ve `parent_id` sorguları |
| **06** | [`06-telecom-catalog-relevance-benchmarks.http`](06-telecom-catalog-relevance-benchmarks.http) | Alakadarlık kıyaslamaları, puan ağırlıklandırma ve arama optimizasyonu |

---

## 🚀 Nasıl Çalışmalısınız?

1. Kibana sol navigasyon menüsünden **Management ➔ Dev Tools (Console)** sekmesini açın.
2. Sırayla `01` dosyasından başlayarak sorguları Console'a yapıştırıp `Ctrl + Enter` (veya sağdaki yeşil üçgen buton) ile çalıştırın.
3. Her adımın dönen HTTP durum kodunu (`200 OK`) ve JSON yanıtındaki `_score` / `hits` alanlarını inceleyin.
