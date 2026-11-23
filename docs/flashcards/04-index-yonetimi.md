# Flashcard 04: Index Yönetimi, Mapping ve ILM

---

### Soru 1: Dynamic Mapping ile Explicit Mapping arasındaki fark nedir?
**Cevap:**
* **Dynamic Mapping:** Elasticsearch daha önce görmediği bir JSON alanıyla karşılaştığında alanın tipini otomatik tahmin eder (örn: sayı ise `long`, metin ise `text` + `keyword`).
  * *Tehlike:* Mapping Explosion'a yol açabilir veya yanlış tip seçebilir.
* **Explicit Mapping:** Index oluşturulurken alanların tiplerinin (`keyword`, `text`, `integer`, `date`, `boolean`) mühendis tarafından elle tanımlanmasıdır.
* **En İyi Pratik:** Üretim ortamlarında `dynamic: "strict"` veya `dynamic: false` yapılarak kontrolsüz alan türemesi engellenmelidir.

---

### Soru 2: Mevcut bir alanın (field) veri tipi değiştirilebilir mi?
**Cevap:**
* **Hayır.** Elasticsearch'te oluşturulmuş bir alanın tipi (örn: `integer` olan bir alanı `keyword` yapmak) doğrudan değiştirilemez. Çünkü Lucene Inverted Index'i bu tipe göre fiziksel olarak diske yazılmıştır.
* **Çözüm:**
  1. Doğru mapping ile yeni bir index (`v2`) oluşturulur.
  2. `_reindex` API kullanılarak veriler eski index'ten yeni index'e aktarılır.
  3. Index Alias yeni index'e yönlendirilir.

---

### Soru 3: Index Alias neden kritik bir mimari desendir?
**Cevap:**
* Uygulamalar asla doğrudan fiziksel index adına (`orders-v1`) bağlanmamalıdır; bir alias (`orders`) kullanmalıdır.
* **Avantajları:**
  1. **Sıfır Kesintiyle Geçiş (Zero-Downtime Reindex):** Veriler `orders-v2`'ye taşındığında, tek bir atomik `_aliases` işlemi ile alias `orders-v1`'den `orders-v2`'ye çevrilir. Uygulama hiçbir kesinti yaşamaz.
  2. **Index Birleştirme:** Birden fazla aylık index'i (`logs-2026-01`, `logs-2026-02`) tek bir `logs` alias'ı altında toplayıp tek seferde aratabilirsiniz.
  3. **Filtreli Alias (Security & Tenant):** Alias içine gizli bir `filter` gömerek kullanıcıların sadece kendi departmanlarına ait verileri görmesini sağlayabilirsiniz.

---

### Soru 4: Index Lifecycle Management (ILM) nedir ve aşamaları nelerdir?
**Cevap:**
* Zaman serisi verilerinin (log, metrik, izleme) yaşlandıkça otomatik olarak daha ucuz depolamaya taşınmasını ve silinmesini sağlayan politikadır.
* **4 Ana Aşama:**
  1. **Hot (Sıcak):** Aktif yazma ve yoğun aramanın yapıldığı aşama (Hızlı NVMe/SSD, birden fazla primary).
  2. **Warm (Ilık):** Artık yazma yapılmaz (Read-only). Sorgulanabilir. Shard'lar shrink edilebilir ve force-merge uygulanabilir.
  3. **Cold (Soğuk):** Nadiren sorgulanan veriler. Daha ucuz diskler, arama performansı ikincil plandadır.
  4. **Delete (Silme):** Saklama süresi (retention) dolan verinin (örn: 90 gün sonra) tamamen silindiği aşama.

---

### Soru 5: Data Stream nedir?
**Cevap:**
* Zaman serisi ve salt ekleme yapılan (append-only) log/metrik verilerini birden çok arka plan index'inde (`.ds-...`) saklayan, fakat dışarıya tek bir isimle görünen yapıdır.
* Data Stream arkasında otomatik ILM ve rollover kuralları çalışır. Her dokümanın `@timestamp` alanı olması zorunludur.
