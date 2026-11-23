# Flashcard 10: Cluster Yönetimi, Mimari ve Kurtarma (RCA)

---

### Soru 1: Cluster Sağlığı (Cluster Health) renkleri (Green, Yellow, Red) ne anlama gelir?
**Cevap:**
* 🟢 **GREEN (Yeşil):** Tüm primary ve tüm replica shard'lar başarıyla atanmış ve sağlıklı çalışıyor.
* 🟡 **YELLOW (Sarı):** Tüm primary shard'lar atanmış ve veri kaybı yoktur; ancak en az bir replica shard atanamamıştır (Örn: Tek node'lu bir cluster'da `number_of_replicas: 1` ayarlanırsa).
* 🔴 **RED (Kırmızı):** En az bir primary shard atanamamıştır! Bu shard'daki verilere erişilemez, veri kaybı veya hizmet kesintisi riski vardır. Acil müdahale gerekir.

---

### Soru 2: RED bir cluster'da arıza tanısı nasıl konur?
**Cevap:**
* **İlk Komut:** `GET /_cluster/allocation/explain`
* Bu API, Elasticsearch'e şu soruyu sorar: *"Neden bu shard'ı hiçbir node'a atayamıyorsun?"*
* **Dönen Yanıt:** Elasticsearch tüm node'ları tek tek inceler ve neden atanamadığını açıklar (Örn: disk doluluğu sınırı, node eşleşme filtreleri, bozuk index dosyası, sürüm uyumsuzluğu).

---

### Soru 3: Split-Brain (Bölünmüş Beyin) sorunu nedir ve nasıl önlenir?
**Cevap:**
* **Sorun:** Ağ kesintisi nedeniyle cluster'daki node'lar ikiye ayrıldığında, her iki tarafın da kendini bağımsız bir cluster sanıp ayrı bir master seçmesi durumudur. Her iki taraf da bağımsız yazma kabul ederse veri tutarlılığı kalıcı olarak bozulur.
* **Çözüm:**
  * Çift sayıda değil, **tek sayıda master adayı node (3 master-eligible node)** kullanılır.
  * Elasticsearch 7+ sürümündeki Raft benzeri oylama mekanizması ile bir master seçilebilmesi için **çoğunluk (quorom: (N/2)+1)** şartı aranır. İkiye bölünen taraflardan azınlıkta kalan taraf master seçemez ve yazma kabul etmez.

---

### Soru 4: Disk Su Seviyesi Eşikleri (Disk Watermarks) nelerdir?
**Cevap:**
Elasticsearch node disklerini korumak için üç kritik eşiğe sahiptir:
1. **Low Watermark (Varsayılan %85):** Yeni shard'ların bu node'a atanmasını durdurur.
2. **High Watermark (Varsayılan %90):** Mevcut shard'ları bu node'dan başka boş node'lara tahliye etmeye (relocate) başlar.
3. **Flood-Stage Watermark (Varsayılan %95):** Disk taşmasını önlemek için ilgili node'daki tüm index'leri zorla **Salt Okunur (Read-Only)** moda geçirir (`read_only_allow_delete: true`). Yeni veri yazılamaz!
