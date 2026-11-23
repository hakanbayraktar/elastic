# Flashcard 08: Aggregations (Toplama) ve Analitik

---

### Soru 1: Elasticsearch'te 3 temel Aggregation türü nelerdir?
**Cevap:**
1. **Metric Aggregations:** Bir dizi sayısal değer üzerinden tek bir metrik hesaplar (`avg`, `sum`, `min`, `max`, `stats`, `cardinality` vb.).
2. **Bucket Aggregations:** Belgeleri belirli kriterlere göre sepetlere (buckets) ayırır (`terms`, `range`, `date_histogram`, `filter`, `geo_distance` vb.). Her sepet kendi içinde alt-aggregasyonlar (sub-aggregations) içerebilir.
3. **Pipeline Aggregations:** Doğrudan belgeler üzerinde değil, diğer aggregasyonların çıktıları (sepet sonuçları) üzerinde işlem yapar (`derivative`, `moving_avg`, `bucket_script`, `cumulative_sum` vb.).

---

### Soru 2: `cardinality` aggregasyonu neden yaklaşık (approximate) sonuç döner?
**Cevap:**
* Milyonlarca tekil değeri (unique count) tam olarak saymak shard'lar üzerinde devasa bellek (RAM) gerektirir.
* Elasticsearch, bellek tasarrufu sağlamak için **HyperLogLog++ (HLL++)** algoritmasını kullanır.
* `precision_threshold` ayarı ile (örn: 10000) doğruluk ile bellek tüketimi arasında denge kurulur. Küçük sayılarda %100 doğrudur, büyük sayılarda standart hata payı genellikle %1-2 civarındadır.

---

### Soru 3: Doc Values nedir ve Aggregation performansıyla ilişkisi nedir?
**Cevap:**
* **Doc Values:** Indexleme sırasında oluşturulan **sütun bazlı (columnar)** disk veri yapısıdır.
* Inverted Index (Inverted Index) arama için mükemmelken, sıralama (sorting) ve gruplama (aggregation) için berbattır. Doc Values, her belgenin ilgili alandaki değerini sütunsal olarak sıralı tutarak aggregasyonların doğrudan OS filesystem cache üzerinden ışık hızında çalışmasını sağlar.
* `text` alanlarında doc values kapalıdır (bunun yerine `fielddata` gerekir ki belleği şişirir); bu nedenle aggregasyonlar mutlaka `keyword` veya sayısal alanlarda yapılmalıdır.

---

### Soru 4: Date Histogram ile Histogram arasındaki fark nedir?
**Cevap:**
* **Histogram:** Sayısal aralıklara göre (örn: her 50 TL'lik fiyat dilimi: 0-50, 50-100, 100-150) gruplar.
* **Date Histogram:** Zaman serisi verilerini takvimsel veya sabit zaman dilimlerine göre (örn: `calendar_interval: "1d"` (günlük), `fixed_interval: "1h"` (saatlik)) gruplar. Zaman serisi dashboard'larının kalbidir.
