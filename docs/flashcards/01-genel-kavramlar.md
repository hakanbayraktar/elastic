# Flashcard 01: Elasticsearch Genel Kavramlar ve Mimari

Bu kartlar, Elasticsearch'ün çalışma mantığını, bellek yönetimini ve temel operasyonel mekanizmalarını hızlıca kavramak ve mülakatlara/sınavlara hazırlanmak için tasarlanmıştır.

---

### Soru 1: Segment Merging (Segment Birleştirme) nedir, neden önemlidir?
**Cevap:**
* **Tanım:** Elasticsearch'e yeni belgeler yazıldıkça diskte küçük **segment** adı verilen Lucene veri dosyaları oluşur. Segment Merging, arka planda çalışan ve bu küçük segmentleri birleştirerek daha büyük ve optimize segmentlere dönüştüren süreçtir.
* **Faydaları:**
  1. **Silinen Belgelerin Temizlenmesi:** Elasticsearch'te silinen veya güncellenen belgeler anında diskten yok edilmez; üzerine "tombstone" (silindi işareti) konur. Segment merge sırasında bu silinmiş kayıtlar fiziksel olarak diskten atılır ve disk alanı geri kazanılır.
  2. **Arama Performansı:** Arama sorgusu her segmenti ayrı ayrı taramak zorundadır. Daha az segment = daha hızlı arama.
  3. **Dosya Tanımlayıcı (File Descriptor) Tasarrufu:** Açık dosya sayısını azaltır.

---

### Soru 2: Elasticsearch neden çok fazla bellek (RAM) tüketir?
**Cevap:**
Elasticsearch belleği iki ana katmanda kullanır:
1. **JVM Heap Belleği (Genellikle RAM'in %50'si, maks 31 GB):**
   * Shard durumları, cluster state ve metadata.
   * Devam eden arama ve indexleme işlemleri (In-flight requests).
   * Aggregation ve sorting için kullanılan bellek yapıları.
   * Segment birleştirme ara tamponları.
2. **İşletim Sistemi Dosya Sistemi Önbelleği (OS Filesystem Cache - Kalan %50):**
   * Lucene segmentleri diskte saklanır. Elasticsearch, disk I/O maliyetinden kaçınmak için bu segmentleri işletim sisteminin sayfa önbelleğinde (page cache) tutar. Hızlı aramaların sırrı buradadır.

---

### Soru 3: Replica Shard'ların rolü nedir?
**Cevap:**
* **Yüksek Erişilebilirlik (HA - Fault Tolerance):** Bir primary shard'ın bulunduğu node çökerse, Elasticsearch hemen bir replica shard'ı primary seviyesine yükseltir (promotes) ve veri kaybı önlenir.
* **Arama Yük Dengelemesi (Read Scale):** Arama (search) istekleri hem primary hem de replica shard'lara dağıtılarak paralel okunabilir. Bu da arama verimini katlar.
* **Not:** Replicas yazma (write/indexing) hızını artırmaz; aksine her replica'ya da yazılması gerektiği için yazma maliyetini bir miktar artırır.

---

### Soru 4: `refresh_interval` ayarı indexleme ve arama performansını nasıl etkiler?
**Cevap:**
* **İşlevi:** Bellekteki (indexing buffer) belgelerin diske Lucene segmenti olarak yazılıp aranabilir (searchable) hale gelme sıklığıdır (varsayılan: `1s`).
* **Near Real-Time (NRT):** 1 saniyelik refresh, bir belgenin yazıldıktan 1 saniye sonra aranabilmesini sağlar.
* **Toplu Veri Yükleme (Bulk) Optimizasyonu:** Yoğun veri yüklerken `refresh_interval: -1` veya `30s` yapılır. Böylece sürekli küçük segmentler üretilmez, CPU ve disk I/O tasarrufu sağlanır, indexleme %30-40 hızlanır. Yükleme bitince tekrar `1s` yapılır.

---

### Soru 5: Elasticsearch'te belge silindiğinde disk alanı neden hemen boşalmaz?
**Cevap:**
* Lucene segmentleri **değiştirilemez (immutable)** dosyalardır.
* Bir belge silindiğinde segment doğrudan değiştirilmez; belgenin ID'si bir `.del` dosyasına (tombstone) yazılır. Arama sırasında bu belgeler filtrelenir ancak diskte yer kaplamaya devam eder.
* Gerçek disk alanı temizliği yalnızca **Segment Merge** gerçekleştiğinde veya elle `_forcemerge?only_expunge_deletes=true` komutu tetiklendiğinde gerçekleşir.

---

### Soru 6: Bulk API kullanmak neden tekil isteklerden kat kat hızlıdır?
**Cevap:**
* **Ağ Maliyeti (Network Roundtrip):** 1.000 ayrı HTTP POST isteği atmak yerine tek bir HTTP isteğiyle 1.000 belge gönderilir.
* **İç Koordinasyon:** Elasticsearch Bulk isteğini aldığında belgeleri ilgili primary shard'lara göre clusterleyip tek seferde iletir.
* **Tavsiye Edilen Boyut:** Genellikle 5 MB – 15 MB arası bulk paketleri idealdir.

---

### Soru 7: Query Context ile Filter Context arasındaki fark nedir?
**Cevap:**
| Özellik | Query Context (`must`, `should`) | Filter Context (`filter`, `must_not`) |
|---|---|---|
| **Soru** | "Belge bu sorguya *ne kadar iyi* uyuyor?" | "Belge bu koşulu sağlıyor mu? (*Evet / Hayır*)" |
| **Puanlama (`_score`)** | Hesaplanır (TF/IDF, BM25 algoritmasıyla). | **Hesaplanmaz** (`_score = 0`). |
| **Önbellek (Caching)** | Önbelleğe alınmaz. | Sık kullanılan filtreler **Node Query Cache**'te saklanır. |
| **Hız** | Daha yavaş ve CPU tüketir. | **Çok daha hızlıdır.** |

> [!TIP]
> Eğer alaka düzeyi puanı (relevance score) gerekmiyorsa (örneğin `status: "ACTIVE"`, `price > 100`, `category: "Electronics"` gibi kesin filtrelerde) her zaman **Filter Context** tercih edilmelidir.
