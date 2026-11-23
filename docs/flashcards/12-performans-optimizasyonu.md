# Flashcard 12: Performans Optimizasyonu ve Tuning

---

### Soru 1: JVM Heap boyutu neden fiziksel RAM'in en fazla %50'si ve en çok 31 GB olmalıdır?
**Cevap:**
1. **%50 Kuralı:** Lucene, diskteki segmentleri okumak için işletim sisteminin dosya sistemi önbelleğini (OS Filesystem Cache) kullanır. Kalan %50 RAM işletim sistemine ve Lucene'e bırakılmazsa disk I/O darboğazı oluşur.
2. **31 GB Sınırı (Compressed Ordinary Object Pointers - Compressed OOPs):** Java 32 GB'ın altında 32-bit işaretçiler kullanır. 32 GB aşıldığı anda 64-bit işaretçilere geçer ve nesne referansları iki kat bellek kaplamaya başlar. Bu nedenle 31 GB heap, genellikle 40 GB heap'ten daha fazla kullanılabilir alan sağlar!

---

### Soru 2: Indexleme (Indexing / Bulk) performansını artırmak için hangi ayarlar yapılmalıdır?
**Cevap:**
1. **`refresh_interval` Artırılmalı:** Geçici olarak `-1` (kapalı) veya `30s` yapılmalıdır.
2. **Replicas Kapatılmalı:** Büyük ilk veri yüklemelerinde `number_of_replicas: 0` yapılır, yükleme bittiğinde `1` yapılır.
3. **Toplu İstekler (Bulk API):** 5-15 MB'lık paketler halinde paralel thread'lerle gönderilmelidir.
4. **Otomatik ID Kullanımı:** Mümkünse belgenin `_id` değeri Elasticsearch tarafından otomatik üretilmelidir (Kendi ID'nizi verirseniz Elasticsearch her belgede "bu ID var mı?" diye eski segmentleri kontrol etmek zorunda kalır).

---

### Soru 3: Arama (Search) performansını artırmak için hangi stratejiler uygulanır?
**Cevap:**
1. **Filter Context Kullanımı:** Puanlama gerekmeyen koşullar `filter` içine alınmalı (Cache avantajı).
2. **Force Merge (Salt Okunur index'ler İçin):** Artık yazılmayan index'ler tek bir segmente (`max_num_segments=1`) birleştirilmelidir.
3. **Pre-filter & Shard Routing:** İlgili veri belirli bir kullanıcıya veya ülkeye aitse `_routing` kullanılarak sadece 1 shard taranmalıdır.
4. **Kullanılmayan Alanlar İçin `_source` Filtreleme:** Sadece ihtiyaç duyulan alanlar (`_source_includes`) istenmelidir.
