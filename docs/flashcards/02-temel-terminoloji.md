# Flashcard 02: Temel Terminoloji ve Veri Yapıları

---

### Soru 1: Cluster, Node, Index, Document ve Shard nedir?
**Cevap:**
* **Cluster:** Birlikte çalışan, aynı cluster adını (`cluster.name`) paylaşan bir veya daha fazla Elasticsearch node'unün (node) oluşturduğu yapıdır.
* **Node:** Cluster'a ait çalışan tek bir Elasticsearch işlemidir (process / container).
* **Index (Index):** Benzer özelliklere sahip JSON belgelerinin mantıksal koleksiyonudur (İlişkisel veritabanlarındaki "Tablo" kavramına benzer).
* **Document (Belge):** İndekslenebilen temel veri birimidir. JSON formatındadır ve benzersiz bir `_id` değerine sahiptir.
* **Shard (Bölüm):** Bir index'in yatayda bölündüğü fiziksel Lucene örnekleridir. Bir index birden çok shard'a bölünerek farklı node'lara dağıtılabilir.

---

### Soru 2: Primary Shard ile Replica Shard farkı nedir?
**Cevap:**
* **Primary Shard:** Bir belgenin ilk yazıldığı asıl fiziksel shard'dır. Index oluşturulurken belirlenir (Elasticsearch varsayılanı: 1).
* **Replica Shard:** Primary shard'ın birebir yedeğidir. Hiçbir zaman kendi primary shard'ı ile aynı fiziksel node'da bulunmaz. Sayısı index çalışırken dinamik olarak değiştirilebilir (`number_of_replicas`).

---

### Soru 3: Inverted Index (Inverted Index) nedir ve nasıl çalışır?
**Cevap:**
* **Tanım:** Elasticsearch'ün tam metin (full-text) aramayı milisaniyeler içinde yapmasını sağlayan temel veri yapısıdır.
* **Mantık:** Belgelerin hangi kelimeleri içerdiğini tutmak yerine; **her benzersiz kelimenin hangi belgelerde, kaç kez ve hangi konumlarda geçtiğini** listeler (Kitapların arkasındaki "Fihrist / Index" gibidir).
* **Örnek:**
  * Doküman 1: "Elasticsearch çok hızlı"
  * Doküman 2: "Elasticsearch ve Kibana"
  * *Inverted Index Tablosu:*
    * `elasticsearch` ➔ [Doc 1, Doc 2]
    * `çok` ➔ [Doc 1]
    * `hızlı` ➔ [Doc 1]
    * `kibana` ➔ [Doc 2]
  Bir kullanıcı "hızlı" aradığında doğrudan Doc 1 getirilir, tüm metin taranmaz.

---

### Soru 4: Node Rolleri (Node Roles) nelerdir?
**Cevap:**
Elasticsearch 8 ve 9'da node'lara özel roller verilebilir:
1. **`master`:** Cluster durumunu (cluster state), index şablonlarını, shard yerleşimlerini yönetir.
2. **`data`:** Shard'ları barındırır, CRUD, arama ve aggregation işlemlerini fiilen yürütür (`data_content`, `data_hot`, `data_warm`, `data_cold`).
3. **`ingest`:** Belgeler indexlenmeden önce Ingest Pipeline işlemcilerinden (Grok, GeoIP, Date vb.) geçirir.
4. **`coordinating` (Role gerekmez):** İstekleri istemciden karşılar, ilgili data node'larıne dağıtır ve gelen sonuçları birleştirip istemciye döner.

---

### Soru 5: `_source` alanı nedir ve ne işe yarar?
**Cevap:**
* indexlenen orijinal JSON belgesinin değiştirilmemiş ham halini saklayan meta alandır.
* **Kullanım:** Arama sonuçlarında belgenin içeriğini geri dönebilmek (`GET /index/_doc/1`), reindex yapabilmek ve `_update` operasyonlarında mevcudu okuyup birleştirebilmek için gereklidir.
* **Dikkat:** `_source` devre dışı bırakılırsa arama yapılabilir (çünkü Inverted Index vardır) fakat arama sonucunda orijinal JSON geri dönmez ve reindex yapılamaz.
