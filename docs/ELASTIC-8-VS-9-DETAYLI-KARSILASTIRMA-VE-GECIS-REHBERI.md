# Elasticsearch 8.x ile 9.x Kapsamlı Karşılaştırma, Mimari Farklar ve Geçiş (Migration) Rehberi

Bu doküman, kurumsal üretim ortamlarında yaygın olarak kullanılan **Elasticsearch 8.x (özellikle 8.16 / 8.17 LTS)** ile yeni nesil **Elasticsearch 9.x (9.5.5)** arasındaki mimari farkları, kırıcı değişiklikleri (breaking changes), performans kazanımlarını ve sürüm yükseltme (upgrade/migration) stratejilerini ayrıntılı olarak ele alır.

---

## 📌 Yönetici Özeti (Executive Summary)

Elasticsearch 8.x sürümü, X-Pack güvenliğinin varsayılan olarak açılması, vektör arama (k-NN) temelleri ve ES|QL'in önizleme olarak gelmesiyle bir dönüm noktası olmuştu. 

**Elasticsearch 9.x** ise arama motoru çekirdeğinde **Apache Lucene 10** mimarisine geçmiş, **SIMD (Single Instruction Multiple Data)** donanım tabanlı vektör hızlandırmalarını devreye almış, **ES|QL**'i Kibana ve arama motorunun kalbine yerleştirmiş ve geçmişten kalan tüm eski görselleştirme ve şablon teknolojilerini (Canvas, TSVB, Timelion, eski `_template` API'si) tamamen temizleyerek saf, yüksek performanslı ve güvenli bir platform sunmuştur.

---

## 📊 Kapsamlı Özellik ve Değişiklik Karşılaştırma Matrisi

| Kategori / Bileşen | Elasticsearch & Kibana 8.x (8.17) | Elasticsearch & Kibana 9.x (9.5.5) | Kırıcı Değişiklik / Etki Derecesi | Geçiş ve Uyum (Migration) Aksiyonu |
|---|---|---|:---:|---|
| **Arama Motoru Çekirdeği** | Apache Lucene 9.x, Java 17/21 | **Apache Lucene 10.x**, Java 23/24 (SIMD desteği) | 🟢 Performans Artışı | İkili dosya uyumluluğu şeffaftır; ek konfigürasyon gerektirmez. |
| **Kibana Canvas** | ✅ **Mevcut.** İnfografik ve afiş tarzı serbest çizim panoları (`canvas-workpad`) desteklenir. | ⚠️ **Legacy.** Mevcut workpad'ler açılır, yeni workpad yok. | 🟡 **Önemli Değişiklik** | Mevcut panolar korunabilir; yeni görselleştirmeler doğrudan **Kibana Dashboard** ve modern **Kibana Lens** bileşenlerine aktarılmalıdır. |
| **Sorgu Dili (ES\|QL)** | Preview/Opsiyonel (8.11+). Discover'da ayrı bir deneme sekmesidir. | 🌟 **Birinci Sınıf Çekirdek Motor.** Discover, Lens ve Alerting'in merkezindedir. | 🟡 Önerilen Dönüşüm | Karmaşık Query DSL ve SQL sorguları boru hattı mimarisine (`\|`) taşınmalıdır. |
| **Index Şablonları** | Eski şablon API'si (`PUT /_template/<ad>`) standart olarak çalışır. | ⚠️ **Deprecated.** Composable template'e geçin. | 🟡 **Deprecation** | Eski `_template` HTTP 299 deprecation uyarısı üretir; tanımlar `_index_template` ve `_component_template` yapısına dönüştürülmelidir. |
| **Sistem Index'leri Koruması** | Sistem index'lerine (`.kibana*`, `.security*`) doğrudan REST erişimi kısmen kısıtlıdır. | 🔒 **Tam Kilitli (Strict Lockdown).** Doğrudan belge yazma, güncelleme veya silme tamamen yasaktır. | 🔴 **Kırıcı Değişiklik** | Script'lerde sistem index'lerine doğrudan `PUT/POST` atan yapılar kaldırılmalı, resmi Public API'ler kullanılmalıdır. |
| **Vektör Arama & k-NN** | HNSW algoritması, float32 veya int8 scalar quantization. | **HNSW + SIMD Vectorization (Lucene 10)**, 4-bit/8-bit dinamik kuantizasyon. | 🟢 Performans Artışı | Vektör aramalarında sorgu gecikmesi (p95 latency) 2-4 kat azalır, bellek ayak izi düşer. |
| **Hibrit Arama (RRF)** | Reciprocal Rank Fusion deneysel/erken aşamadadır. | **Tam Yerel RRF Desteği.** BM25 (text) ve k-NN (dense_vector) puanlarını matematiksel olarak dengeler. | 🟢 Yeni Yetenek | Arama servislerinde `retriever.rrf` yapısı doğrudan kullanılmalıdır. |
| **Tarihli Index Desteği** | 7.x sürümünde oluşturulmuş eski segmentler salt-okunur açılabilir. | ❌ **7.x Index'leri Açılamaz.** Yalnızca 8.x ve 9.x'te oluşturulmuş index'ler okunabilir (Node açılışı durdurulur). | 🔴 **Kırıcı Değişiklik** | 7.x döneminden kalan arşiv index'ler Elasticsearch 8.x üzerindeyken mutlaka `_reindex` edilmelidir. |
| **Translog Dayanıklılığı** | Varsayılan `request` flush (her yazmada diske `fsync`). | Optimize `async` arabellek ve otomatik checkpoint mekanizmaları. | 🟢 Performans Artışı | Yüksek hacimli log akışlarında disk I/O yükü minimize edilir. |

---

## 🔍 Temel Mimari Farkların Derinlemesine Analizi

### 1. Lucene 9 vs Lucene 10: Çekirdek Motor ve Donanım Hızlandırması
* **SIMD Vektör Talimatları:** Lucene 10, modern CPU mimarilerinde (Intel AVX-512, ARM Neon) vektör benzerlik hesaplamalarını (Cosine, Dot Product, Euclidean) tek bir CPU saat çevriminde paralel olarak hesaplar. Bu, özellikle `dense_vector` alanları kullanan semantik arama motorlarında bellek bant genişliğini ve CPU tüketimini yarıya indirir.
* **Segment Sıkıştırma (Codec):** Lucene 10, inverted index posting listeleri ve doc values için daha agresif ve düşük CPU maliyetli sıkıştırma algoritmaları kullanır.

### 2. Kibana 9 ve Arayüz Devrimi: Canvas'ın Legacy Durumu
Elastic Stack 8.x'te sunulan Canvas modülü; afiş, broşür, TV ekranı panoları tasarlamak için özel bir syntax (`canvas-workpad`) kullanıyordu. Ancak Canvas:
* Kibana'nın geri kalanıyla (Data Views, Lens, Discover, Dashboard Controls) kod ve mimari paylaşmıyordu.
* ES|QL ve modern akış filtreleriyle tam uyumlu değildi.
* Yüksek bakım maliyeti yaratıyordu.

**Elasticsearch 9 ile birlikte:**
Canvas **legacy** durumuna getirilmiştir: Mevcut workpad'ler görüntülenip incelenebilir ancak **yeni Canvas workpad oluşturulamaz**. Yeni nesil tüm sunum ve görselleştirme ihtiyaçları doğrudan modern Kibana Dashboard bileşenlerine aktarılmalıdır.

### 3. Composable Index Templates vs Eski `_template` (Deprecated)
Elastic 8.x'te eski `_template` çağrıları standart olarak çalışıyordu:
```http
PUT /_template/legacy_template
{
  "index_patterns": ["legacy-*"],
  "settings": { "number_of_shards": 1 }
}
```

**Elastic 9 Davranışı:**
Elasticsearch 9'da bu API çalışmaya devam eder ancak HTTP 299 yanıt başlığında `! Legacy index templates are deprecated in favor of composable templates` uyarısı üretir. Hedeflenen modern mimari Composable Index Templates (`_index_template`) ve bileşen şablonlarıdır (`_component_template`):
```http
PUT /_index_template/modern_template
{
  "index_patterns": ["modern-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text" }
      }
    }
  },
  "priority": 200
}
```

### 4. ES|QL (Elasticsearch Query Language): Boru Hattı Mimarisi
Elastic 8.x'te veri analizi genellikle Query DSL JSON blokları veya sınırlı SQL API'si ile yapılıyordu. Elastic 9.x ile birlikte **ES|QL** ana standart haline gelmiştir:
* Linux shell boru hattı (`|`) mantığı ile sorgulama yapılır.
* Sorgu zamanında dinamik zenginleştirme (`| ENRICH`), tip dönüştürme (`TO_INTEGER`, `TO_STRING`), koşul blokları (`CASE(...)`) ve arama zamanı lookup birleştirmeleri (`index.mode: "lookup"`) doğrudan desteklenir.
* Arama motoru içinde C++ seviyesinde vektörize edilmiş sorgu yürütme motoru sayesinde geleneksel `terms` aggregations sorgularına göre çok daha hızlı çalışır.

---

## 🛠️ Elastic 8'den Elastic 9'a Adım Adım Geçiş (Upgrade) Rehberi

Üretim ortamındaki bir Elasticsearch 8.x cluster'ını 9.x sürümüne yükseltirken aşağıdaki kontrol listesi uygulanmalıdır:

> [!IMPORTANT]
> **Yükseltme Yolu Önkoşulu:** Elasticsearch 9.x'e doğrudan yükseltme (rolling upgrade) yalnızca **Elasticsearch 8.19.x (son 8.x kararlı sürümü)** üzerinden desteklenir. Daha eski 8.x sürümlerindeki (örn. 8.16, 8.17) cluster'lar önce 8.19.x'e yükseltilmeli, ardından 9.x'e geçilmelidir.

### Adım 1: Migration Deprecations API ve Upgrade Assistant'ı Çalıştırın
Cluster'ın 9.x'e hazır olup olmadığını hem REST API hem de Kibana arayüzünden denetleyin:
```http
# 1. API ile deprecation uyarılarını sorgulayın:
GET /_migration/deprecations
```
Ardından Kibana 8.19 arayüzünde:
`Management > Stack Management > Upgrade Assistant` yolunu izleyin.
Bu araç cluster'daki tüm index'leri, şablonları ve ayarları tarayarak 9.x uyumsuzluklarını kırmızı ve sarı uyarılarla listeler.

### Adım 2: 7.x Sürümünde Oluşturulmuş Index'leri Reindex Edin (Zorunlu)
> [!CAUTION]
> **Node Başlatma Engeli:** Elasticsearch 9.x, Elasticsearch 7.x döneminde oluşturulmuş Lucene segmentlerini okuyamaz. Eğer cluster'da 7.x'te oluşturulmuş tek bir index dahi bulunursa, **Elasticsearch 9 node'ları başlatılamaz (fatal startup failure)**!

```http
# 7.x index kontrolü:
GET /_cat/indices?v&h=index,version.created

# 7.x'te oluşturulmuş index'leri 8.x üzerindeyken reindex edin:
POST /_reindex
{
  "source": { "index": "es7-archive-data" },
  "dest": { "index": "es8-migrated-data" }
}
```

### Adım 3: Eski Şablonları Modern Şablonlara Dönüştürün
Mevcut eski şablonları listeleyin ve kaldırıp composable şablon olarak yeniden oluşturun:
```http
GET /_template
DELETE /_template/old_template_name
```

### Adım 4: Tam Snapshot Alın
SLM veya doğrudan Snapshot API ile tüm cluster'ın yedeğini S3 veya MinIO deposuna yazın:
```http
PUT /_snapshot/backup_repo/pre_upgrade_snapshot?wait_for_completion=true
{
  "indices": "*",
  "ignore_unavailable": true,
  "include_global_state": true
}
```

### Adım 5: Sırayla Yükseltme (Rolling Upgrade) Sırası
3 veya daha fazla node içeren HA cluster'larda kesintisiz yükseltme sırası:
1. Shard tahsisini geçici olarak kapatın:
   ```http
   PUT /_cluster/settings
   {
     "persistent": { "cluster.routing.allocation.enable": "primaries" }
   }
   ```
2. Sırayla önce Master-eligible olmayan Data node'ları yükseltin (Paket veya Container imajını 9.5.5 yapın).
3. Node başladığında ve cluster'a katıldığında shard tahsisini açın:
   ```http
   PUT /_cluster/settings
   {
     "persistent": { "cluster.routing.allocation.enable": "all" }
   }
   ```
4. Cluster yeşile dönünce sonraki node'a geçin.
5. Tüm Data node'lar bittikten sonra Master node'ları yükseltin.
6. En son Kibana servisini 9.x imajına çekin.

---

## 🧪 Pratik Lab Eşleştirmesi

Bu farklılıkları bizzat ellerinizle deneyimlemek ve yan yana test etmek için hazırlanan lablar:
* **[ADV-08: Elastic 8 vs 9 Karşılaştırması ve Geçiş](../labs/advanced/ADV-08-elastic-8-vs-9/README.md):** Port `9208` üzerinde çalışan Elastic 8.17 (Canvas aktif) ile Port `9200` üzerindeki Elastic 9.x'i yan yana çalıştırıp farkları canlı API'lerle inceleyin.
