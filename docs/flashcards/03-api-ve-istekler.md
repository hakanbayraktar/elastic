# Flashcard 03: REST API Standartları ve İstek Yönetimi

---

### Soru 1: CRUD işlemlerinde kullanılan temel HTTP metotları nelerdir?
**Cevap:**
* **`POST /index/_doc`**: Otomatik üretilen `_id` ile yeni belge ekler.
* **`PUT /index/_doc/<id>`**: Belirtilen `_id` ile yeni belge ekler veya mevcut belgenin tamamını ezer (upsert).
* **`POST /index/_create/<id>`**: Sadece belge yoksa ekler; eğer aynı `_id` varsa `409 Conflict` hatası fırlatır.
* **`GET /index/_doc/<id>`**: Belgeyi `_source` alanıyla birlikte getirir.
* **`POST /index/_update/<id>`**: Belgenin tamamını ezmeden yalnızca belirtilen alanları kısmi günceller (partial update).
* **`DELETE /index/_doc/<id>`**: Belgeyi silinmek üzere işaretler (tombstone).

---

### Soru 2: Optimistic Concurrency Control (OCC) nasıl çalışır?
**Cevap:**
* **Sorun:** İki farklı işlem aynı anda aynı belgeyi güncellemeye çalıştığında veri kaybı (race condition) oluşabilir.
* **Çözüm:** Elasticsearch her belgede `_seq_no` (sıra numarası) ve `_primary_term` (yazma dönemi) değerlerini saklar.
* **Uygulama:**
  ```json
  POST /products/_update/101?if_seq_no=4&if_primary_term=1
  {
    "doc": { "stock": 49 }
  }
  ```
  Eğer araya başka bir işlem girip `_seq_no` değerini 5 yapmışsa, Elasticsearch isteği reddeder ve `409 Conflict (version_conflict_engine_exception)` döner.

---

### Soru 3: CAT API nedir ve ne zaman kullanılır?
**Cevap:**
* **Tanım:** "Compact and Aligned Text" anlamına gelir. İnsanlar ve terminal yöneticileri tarafından kolay okunabilecek tablo formatında metin çıktısı üretir.
* **Önemli CAT Komutları:**
  * `GET /_cat/health?v`: Cluster sağlığını (green/yellow/red) ve node/shard sayılarını gösterir.
  * `GET /_cat/nodes?v`: Node'ların IP, rol, CPU ve RAM kullanımını listeler.
  * `GET /_cat/indices?v`: index'lerin durumunu, belge sayısını ve boyutunu listeler.
  * `GET /_cat/shards?v`: Hangi shard'ın hangi node'da olduğunu veya neden atanamadığını (`UNASSIGNED`) gösterir.
* **İpucu:** `?v` parametresi başlıkları (headers), `?s=store.size:desc` sıralamayı sağlar.

---

### Soru 4: `_update_by_query` ve `_delete_by_query` ne işe yarar?
**Cevap:**
* Tek bir `_id` yerine bir arama sorgusu kriterine uyan tüm belgeleri toplu olarak güncellemek veya silmek için kullanılır.
* **Örnek:**
  ```json
  POST /orders/_update_by_query
  {
    "script": { "source": "ctx._source.status = 'ARCHIVED'" },
    "query": { "range": { "order_date": { "lt": "now-1y" } } }
  }
  ```
* **Önemli Not:** Arka planda Scroll API ve Bulk API çalıştırır. Büyük veri setlerinde zaman alabilir; `wait_for_completion=false` ile asenkron task (`_tasks/ID`) olarak çalıştırılabilir.
