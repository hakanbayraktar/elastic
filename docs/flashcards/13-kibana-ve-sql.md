# Flashcard 13: Kibana, KQL, ES|QL ve Elasticsearch SQL Uyumluluğu

---

### Soru 1: KQL (Kibana Query Language) ile Lucene Query Syntax farkı nedir?
**Cevap:**
* **KQL:** Kibana Discover için tasarlanmış modern, sade, otomatik tamamlama ve tip denetimi olan filtreleme dilidir (Örn: `response: 200 and extension: (php or html)`).
* **Lucene Syntax:** Eski, katı ve regex/wildcard destekleyen sözdizimidir (Örn: `response:200 AND (extension:php OR extension:html)`).
* **Fark:** KQL'de arama terimi yazdığınızda Kibana arkada mapping'i kontrol eder, `*` wildcard'larını güvenle işler ve yazımı kolaylaştırır.

---

### Soru 2: Elasticsearch SQL API nedir, ne amaçla kullanılır?
**Cevap:**
* Elasticsearch'e geleneksel ANSI SQL sözdizimi ile sorgu atmanızı sağlayan REST API (`POST /_sql`) katmanıdır.
* **Kullanım Alanları:**
  1. SQL bilen analistlerin hızlıca veri çekebilmesi.
  2. BI araçlarının (Tableau, PowerBI) JDBC/ODBC sürücüleriyle Elasticsearch'e bağlanabilmesi.
  3. **`_sql/translate` Endpoint'i:** Yazılan SQL'in arkada hangi Query DSL ve Aggregation koduna karşılık geldiğini öğrenmek ve doğrulamak için mükemmel bir araçtır.
* **Sınır:** Elasticsearch bir RDBMS değildir; tablolar arası geleneksel `JOIN` desteklemez.

---

### Soru 3: ES|QL (Elasticsearch Query Language) nedir ve farkı nedir?
**Cevap:**
* Elastic Stack 8.11 ve 9.x ile gelen, boru hattı (pipelined `|`) tabanlı, yeni nesil veri sorgulama ve dönüştürme motorudur.
* **Örnek:**
  ```text
  FROM kibana_sample_data_ecommerce
  | WHERE taxful_total_price > 100
  | STATS avg_price = AVG(taxful_total_price) BY category
  | SORT avg_price DESC
  | LIMIT 5
  ```
* **Avantajı:** Hem filtreleme, hem hesaplama (`EVAL`), hem zenginleştirme (`ENRICH`), hem de özetlemeyi tek bir satırda çalıştırır; klasik DSL'e göre %30-50 daha az bellek harcar ve inanılmaz hızlıdır.

---

### Soru 4: Kibana Lens paneli oluştururken nelere dikkat edilmelidir?
**Cevap:**
1. **Data View Seçimi:** Doğru zaman damgasına (`@timestamp`) sahip Data View seçilmelidir.
2. **Break Down By (Gruplama):** `text` alanları yerine her zaman `.keyword` alanları seçilmelidir.
3. **Zaman Aralığı Uyumu:** Örnek veri (sample data) kullanılıyorsa, global zaman filtresi verinin olduğu tarihlere ayarlanmalıdır.
