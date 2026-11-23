# 📖 Elastic Stack 9.x Eğitim ve Dokümantasyon Merkezi

Bu klasör, **Elastic Stack 9.x ile Merkezi Loglama, Arama, Analiz ve Elasticsearch Operasyonları** eğitiminin özet rehberlerini ve pekiştirme kaynaklarını tek bir çatı altında sunar.

---

## 🧭 Bu Kaynakları Nasıl Kullanmalısınız

Ana öğrenme akışı `labs/` altındaki lablar sırasıyla uygulanarak ilerler. Bu klasördeki özet rehberler lab içinde ihtiyaç duyduğunuz an başvurulacak referans el kitaplarıdır (komut listesi, karşılaştırma tablosu, kurulum notu); teorik ders anlatımının yerini tutmaz. Flashcards ise lablarda gördüğünüz kavramları eğitim sonrası tekrar etmek ve teknik mülakatlara hazırlanmak için hızlı pekiştirme kartlarıdır.

---

## 📖 Temel Terimler Sözlüğü

Elastic Stack'e özgü terimler bu eğitimde kasıtlı olarak İngilizce bırakılır (cluster, index, shard gibi); Türkçe çeviri yerine orijinal terime aşina olmanız beklenir. Hızlı başvuru için:

| Terim | Anlamı |
|---|---|
| **Cluster** | Birlikte çalışan bir veya daha fazla node'dan oluşan bütün; tek bir mantıksal Elasticsearch sistemi. |
| **Node** | Cluster'a katılan tek bir Elasticsearch süreci/sunucusu (master, data, ingest gibi rolleri olabilir). |
| **Index** | Birbirine benzer dokümanların saklandığı mantıksal veri koleksiyonu (ilişkisel veritabanındaki tabloya benzer). |
| **Shard** | Bir index'in yatay olarak bölündüğü, bağımsız bir Lucene index'i olan parça; ölçeklenebilirliği sağlar. |
| **Replica** | Bir shard'ın (primary) yedek kopyası; veri kaybını önler ve arama yükünü dağıtır. |
| **Mapping** | Bir index'teki alanların veri tiplerini ve nasıl indexleneceğini tanımlayan şema. |
| **Segment** | Bir shard içindeki değişmez (immutable) Lucene dosya birimi; refresh sırasında oluşur, merge ile birleştirilir. |
| **Snapshot** | Bir veya daha fazla index'in belirli bir andaki tutarlı yedeği. |
| **Repository** | Snapshot'ların saklandığı depolama hedefi (S3, MinIO, paylaşımlı dosya sistemi vb.). |
| **ILM** | Index Lifecycle Management — index'lerin hot/warm/cold/delete aşamaları arasında otomatik yönetimi. |

---

## 📚 Özet Rehberler

* **[Elasticsearch Yönetici & Sorun Giderme Rehberi (40 Temel Komut)](ELASTICSEARCH_TROUBLESHOOTING_GUIDE.md):** Cluster sağlığı, node kaynakları, unassigned shard teşhisi, slow logs, görev iptali ve `_cat` komutları referans el kitabı.
* **[Elasticsearch 8.x vs 9.x Kapsamlı Karşılaştırma ve Geçiş Rehberi](ELASTIC-8-VS-9-DETAYLI-KARSILASTIRMA-VE-GECIS-REHBERI.md):** Lucene 9 vs 10, SIMD donanım hızlandırma, Canvas emekliliği, Composable Templates ve sürüm yükseltme matrisi.
* **[Ubuntu Native Linux Kurulum Rehberi](UBUNTU_NATIVE_LINUX_KURULUM_REHBERI.md):** Container kullanmadan bare-metal/VM üzerinde Elasticsearch ve Kibana kurulumu.

---

## 🗂️ Mülakat ve Hızlı Tekrar Kartları (`docs/flashcards/`)

Öğrenilen bilgileri pekiştirmek ve teknik mülakatlara hazırlanmak için hazırlanmış 13 kategoride 100'den fazla soru-cevap kartı:

* [01 - Genel Kavramlar ve Mimari](flashcards/01-genel-kavramlar.md)
* [02 - Temel Terminoloji](flashcards/02-temel-terminoloji.md)
* [03 - REST API ve İstekler](flashcards/03-api-ve-istekler.md)
* [04 - Index Yönetimi ve Shard Mimarisi](flashcards/04-index-yonetimi.md)
* [05 - Veri Modelleme ve İlişkiler (Nested/Join)](flashcards/05-veri-modelleme-ve-iliskiler.md)
* [06 - Metin Analizi ve Analyzer'lar](flashcards/06-metin-analizi-ve-analyzerlar.md)
* [07 - Arama Sorguları ve Query DSL](flashcards/07-arama-sorgulari-query-dsl.md)
* [08 - Aggregations ve Analitik](flashcards/08-aggregations-analitik.md)
* [09 - Veri Toplama ve Ingestion (Beats/Logstash)](flashcards/09-veri-toplama-ingestion.md)
* [10 - Cluster Yönetimi, Yüksek Erişilebilirlik ve ILM](flashcards/10-cluster-yonetimi-ve-mimari.md)
* [11 - Güvenlik ve Erişim Kontrolü (RBAC)](flashcards/11-guvenlik-ve-erisim-kontrolu.md)
* [12 - Performans Optimizasyonu ve Kapasite](flashcards/12-performans-optimizasyonu.md)
* [13 - Kibana, ES\|QL ve SQL Entegrasyonu](flashcards/13-kibana-ve-sql.md)

---

## 📊 Kibana Görselleştirme Rehberi

* **[Kibana Uygulama Rehberi](https://gitlab.com/devops-monitoring/elastic/-/blob/eski-lab/labs/LAB-03-text-analysis-ve-arama/KIBANA_UYGULAMA_REHBERI.md):** Data View oluşturma, Discover arayüzünde KQL sorgulama, Lens ile KPI/Bar/Pie/Line panoları tasarlama ve Dashboard adımları (LAB-02 altında sunulmaktadır).
