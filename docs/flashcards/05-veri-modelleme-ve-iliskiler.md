# Flashcard 05: Veri Modelleme, Nesneler ve İlişkiler (Nested vs Join)

---

### Soru 1: Elasticsearch'te dizi halindeki nesnelerde (array of objects) Düzleştirme (Flattening) sorunu nedir?
**Cevap:**
* **Sorun:** Elasticsearch standart bir nesne dizisini index'lerken nesne sınırlarını kaybeder ve tüm alt alanları düzleştirir:
  ```json
  "users": [
    { "name": "Ahmet", "role": "ADMIN" },
    { "name": "Mehmet", "role": "USER" }
  ]
  ```
  Lucene bunu arka planda şöyle saklar:
  * `users.name: ["Ahmet", "Mehmet"]`
  * `users.role: ["ADMIN", "USER"]`
* **Sonuç (False Positive):** Birisi "name: Ahmet AND role: USER" aradığında bu belge eşleşir! Oysa Ahmet ADMIN idi.

---

### Soru 2: `nested` veri tipi bu sorunu nasıl çözer?
**Cevap:**
* Her dizi elemanını Lucene seviyesinde **gizli, ayrı bir alt doküman** olarak index'ler.
* Nesne sınırları korunur.
* `nested` sorgusu ile arandığında, koşulların **aynı alt nesne içinde** sağlanması zorunlu tutulur.
* `inner_hits` özelliği ile sorguyu sağlayan tam alt nesne sonuçlarda tek başına gösterilebilir.
* **Dezavantajı:** Ana belgedeki tek bir alt nesne güncellense bile, ana belge ve tüm alt nesneler yeniden indexlenmek (reindex) zorundadır.

---

### Soru 3: Parent-Child (`join` field) ilişkisi nedir ve ne zaman `nested` yerine tercih edilir?
**Cevap:**
* **Tanım:** Ana belge (Parent) ile alt belgenin (Child) **tamamen bağımsız iki ayrı Elasticsearch belgesi** olarak tanımlandığı ilişkidir.
* **Ne Zaman Tercih Edilir?**
  1. Alt belgeler (örn: Ürüne gelen müşteri yorumları, bir şirketin çalışanları) çok sık ekleniyor veya güncelleniyorsa.
  2. Her yorum geldiğinde koskoca ürün belgesini reindex etmek istemiyorsanız.
  3. 1-to-N ilişkisinde N sayısı yüzlerce veya binlerce ise.
* **Kritik Kural (Routing Zorunluluğu):** Bir Parent ve ona bağlı tüm Child belgeler **kesinlikle aynı fiziksel shard üzerinde** bulunmak zorundadır. Bu yüzden Child belgeler indexlenirken `?routing=<parent_id>` parametresi verilmek zorundadır!

---

### Soru 4: `has_child` ve `has_parent` sorguları nasıl çalışır?
**Cevap:**
* **`has_child`:** Alt belgenin kriterine göre Üst belgeyi getirir.
  * *Örnek:* "5 yıldız almış değerlendirmesi olan ürünleri getir."
* **`has_parent`:** Üst belgenin kriterine göre Alt belgeleri getirir.
  * *Örnek:* "Fiyatı 1.000 TL üzeri olan ürünlerin tüm yorumlarını getir."
* **`parent_id`:** Belirli bir üst belgeye ait tüm alt belgeleri hızlıca filtreler.

---

### Soru 5: İlişkisel Modelleme Karşılaştırma Özeti
**Cevap:**
| Yöntem | Güncelleme Maliyeti | Sorgu Hızı | Ölçeklenebilirlik | Kullanım Senaryosu |
|---|---|---|---|---|
| **Denormalization (Düz Veri)** | Yüksek (veri tekrarı) | En Hızlı | Çok Yüksek | Statik veri, loglar, hızlı analitik |
| **Nested Objects** | Orta/Yüksek (tüm belge reindex) | Hızlı (lokal join) | Küçük/Orta listeler | Sepet kalemleri, ürün varyantları |
| **Parent-Child (`join`)** | **Düşük (sadece child güncellenir)** | Daha Yavaş (shard join) | Büyük veri setleri | Ürün-Yorum, Şirket-Çalışan |
