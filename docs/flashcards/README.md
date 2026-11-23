# 📚 Elasticsearch & Kibana Pratik Öğrenme ve Mülakat Kartları (Flashcards)

Bu bölüm, Elastic Stack 9.x eğitiminde öğrenilen teorik ve pratik bilgileri pekiştirmek, günlük operasyonlarda hızlı başvuru (cheat-sheet) yapmak ve teknik mülakatlara hazırlanmak için hazırlanmış soru-cevap kartlarını içerir.

---

## 🗂️ Konu Dizini

| # | Konu Başlığı | Kapsam | Bağlantı |
|---|---|---|---|
| 01 | **Genel Kavramlar & Mimari** | Segment merge, bellek (JVM Heap / OS Cache), replica'lar, refresh_interval | [01-genel-kavramlar.md](01-genel-kavramlar.md) |
| 02 | **Temel Terminoloji** | Cluster, node rolleri, shard, inverted index (Inverted Index), `_source` | [02-temel-terminoloji.md](02-temel-terminoloji.md) |
| 03 | **REST API ve İstekler** | CRUD metotları, OCC (`_seq_no`), CAT API, `_update_by_query` | [03-api-ve-istekler.md](03-api-ve-istekler.md) |
| 04 | **Index Yönetimi & ILM** | Dynamic vs Explicit mapping, alias mimarisi, ILM yaşam döngüsü, Data Streams | [04-index-yonetimi.md](04-index-yonetimi.md) |
| 05 | **İlişkisel Veri & Modelleme** | Düzleştirme sorunu, `nested` objects, parent-child (`join` field), routing | [05-veri-modelleme-ve-iliskiler.md](05-veri-modelleme-ve-iliskiler.md) |
| 06 | **Metin Analizi & Analyzer'lar**| Tokenizer, token filter, `text` vs `keyword`, multi-field, edge n-gram | [06-metin-analizi-ve-analyzerlar.md](06-metin-analizi-ve-analyzerlar.md) |
| 07 | **Arama & Query DSL** | `match` vs `term`, `bool` mantığı, BM25 skorlama, `dis_max`, derin sayfalama | [07-arama-sorgulari-query-dsl.md](07-arama-sorgulari-query-dsl.md) |
| 08 | **Aggregations & Analitik** | Metric, bucket ve pipeline agg'ler, HLL++ cardinality, Doc Values | [08-aggregations-analitik.md](08-aggregations-analitik.md) |
| 09 | **Veri Toplama (Ingestion)** | Beats vs Logstash vs Ingest Pipelines, ECS standardı, DLQ, Dissect vs Grok | [09-veri-toplama-ingestion.md](09-veri-toplama-ingestion.md) |
| 10 | **Cluster Yönetimi & Kurtarma** | Cluster health (Green/Yellow/Red), `allocation/explain`, Split-Brain, Watermarks | [10-cluster-yonetimi-ve-mimari.md](10-cluster-yonetimi-ve-mimari.md) |
| 11 | **Güvenlik & Erişim Kontrolü** | TLS/SSL (Transport vs HTTP), RBAC, FLS/DLS, API Key güvenliği | [11-guvenlik-ve-erisim-kontrolu.md](11-guvenlik-ve-erisim-kontrolu.md) |
| 12 | **Performans Optimizasyonu** | Heap boyutlandırma, bulk hızlandırma, force merge, search slow logs | [12-performans-optimizasyonu.md](12-performans-optimizasyonu.md) |
| 13 | **Kibana, ES\|QL & SQL** | KQL sözdizimi, Lens panelleri, ES\|QL boru hattı, SQL API ve `_sql/translate` | [13-kibana-ve-sql.md](13-kibana-ve-sql.md) |

---

## 🎯 Nasıl Çalışılmalı?
1. **Kendinizi Test Edin:** Her kartta önce soruyu okuyun ve zihninizde cevabını verin.
2. **Kavramı Doğrulayın:** Cevabı açıp temel anahtar kelimeleri ve pratik gerekçeleri inceleyin.
3. **Lablarla Pekiştirin:** Öğrendiğiniz kavramın ilgili labını (`labs/LAB-XX`) açıp terminal veya Kibana Console üzerinde canlı uygulayın.
