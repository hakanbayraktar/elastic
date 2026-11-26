# Elastic Stack 9.x Eğitimi

Bu depo, **Elastic Stack 9.x ile Merkezi Loglama, Arama, Analiz ve Elasticsearch Operasyonları** eğitiminin lab ve dokümantasyon kaynağıdır.

---

## Lab ve Proje Mimarisi

Lablar sırayla ilerler; çoğu tek başına da yapılabilir. Önceki bir labın verisine ya da cluster'ına ihtiyaç duyanlar:
LAB-05, LAB-07, LAB-08 ve LAB-21 LAB-04'ün örnek e-ticaret verisini, LAB-23 LAB-19'un 3-node cluster'ını kullanır. Her labın
Ön Koşullar bölümü, önceki labı atladıysanız ne yapacağınızı söyler. Temizlik yalnız labın kendi kaynaklarını siler.

### Çekirdek Lablar (LAB-01 … LAB-27)

Eğitim 27 çekirdek labdan oluşur ve sırayla ilerler. `*` işaretli lablar mutlaka yapılır,
işaretsizler vakit olursa. Önceki lab yapısı `eski-lab` dalındadır.

| Lab | Öncelik | Başlık | Durum |
|---|:---:|---|---|
| **[LAB-01](labs/LAB-01-kurulum-kontrol/README.md)** | * | Kurulum ve erişim | Hazır, test edildi |
| **[LAB-02](labs/LAB-02-ilk-belgeler/README.md)** | * | İlk document'ler: curl, Dev Tools ve Discover | Hazır, test edildi |
| **[LAB-03](labs/LAB-03-mapping-analyzer/README.md)** | * | Mapping ve analyzer | Hazır, test edildi |
| **[LAB-04](labs/LAB-04-discover-kql/README.md)** | * | Discover ve KQL | Hazır, test edildi |
| **[LAB-05](labs/LAB-05-query-dsl/README.md)** | * | Query DSL | Hazır, test edildi |
| **[LAB-06](labs/LAB-06-arama-deneyimi/README.md)** | * | Arama deneyimi: otomatik tamamlama, fuzzy, eş anlamlı, vurgulama | Hazır, test edildi |
| **[LAB-07](labs/LAB-07-aggregation-lens/README.md)** | * | Aggregation ve Lens panosu | Hazır, test edildi |
| **[LAB-08](labs/LAB-08-esql-sql/README.md)** | * | ES\|QL ve SQL | Hazır, test edildi |
| **[LAB-09](labs/LAB-09-iliskisel-veri-modelleme/README.md)** |  | İlişkisel veriyi modelleme | Hazır, test edildi |
| **[LAB-10](labs/LAB-10-filebeat-metricbeat/README.md)** | * | Filebeat: host ve Docker logları (+Metricbeat) | Hazır, test edildi |
| **[LAB-11](labs/LAB-11-fleet-elastic-agent/README.md)** |  | Fleet ve Elastic Agent | Hazır, test edildi |
| **[LAB-12](labs/LAB-12-logstash-excel/README.md)** | * | Excel verisini Logstash ile aktarma | Hazır, test edildi |
| **[LAB-13](labs/LAB-13-logstash-mysql-jdbc/README.md)** |  | MySQL verisini Logstash JDBC ile aktarma | Hazır, test edildi |
| **[LAB-14](labs/LAB-14-logstash-grok-dissect/README.md)** | * | Logstash ile log ayrıştırma: grok ve dissect | Hazır, test edildi |
| **[LAB-15](labs/LAB-15-logstash-operasyonu/README.md)** |  | Logstash operasyonu: çoklu pipeline, persistent queue, DLQ | Hazır, test edildi |
| **[LAB-16](labs/LAB-16-kibana-pano-atolyesi/README.md)** | * | Kibana pano atölyesi | Hazır, test edildi |
| **[LAB-17](labs/LAB-17-kibana-spaces-saved-objects/README.md)** | * | Kibana Spaces ve saved objects | Hazır, test edildi |
| **[LAB-18](labs/LAB-18-alerting-raporlama/README.md)** | * | Harita, alerting ve raporlama | Hazır, test edildi |
| **[LAB-19](labs/LAB-19-3-node-tls-cluster/README.md)** | * | 3-node TLS cluster | Hazır, test edildi |
| **[LAB-20](labs/LAB-20-guvenlik-cok-ekipli-kibana/README.md)** | * | Güvenlik ve çok ekipli Kibana | Hazır, test edildi |
| **[LAB-21](labs/LAB-21-cluster-sagligi-api/README.md)** | * | Cluster sağlığı ve API'ler | Hazır, test edildi |
| **[LAB-22](labs/LAB-22-index-yasam-dongusu-ilm/README.md)** | * | Index yaşam döngüsü (ILM) | Hazır, test edildi |
| **[LAB-23](labs/LAB-23-cluster-operasyonu-snapshot/README.md)** | * | Cluster operasyonu ve snapshot | Hazır, test edildi |
| **[LAB-24](labs/LAB-24-performans-teshisi/README.md)** |  | Performans teşhisi | Hazır, test edildi |
| **[LAB-25](labs/LAB-25-uygulamadan-elasticsearch/README.md)** |  | Uygulamadan Elasticsearch | Hazır, test edildi |
| **[LAB-26](labs/LAB-26-siem/README.md)** |  | SIEM: tespit ve alarm | Hazır, test edildi |
| **[LAB-27](labs/LAB-27-apache-uctan-uca/README.md)** |  | Apache uçtan uca proje: Logstash, harita, alarm, PDF rapor | Hazır, test edildi |

### İleri / Seçmeli Lablar (`labs/advanced/`)

Kurs akışında zorunlu değildir; ihtiyaca göre seçilir.

| Lab | Başlık | Konu özeti |
|---|---|---|
| **[ADV-01](labs/advanced/ADV-01-data-stream-kurallari-dsl/README.md)** | **Data Stream Kuralları ve Data Stream Lifecycle** | Yalnız ekleme kuralı, `_update_by_query`/`_delete_by_query` ile KVKK silmesi, DSL retention, ILM'den DSL'e geçiş |
| **[ADV-02](labs/advanced/ADV-02-opentelemetry-edot/README.md)** | **OpenTelemetry ve EDOT Collector** | OTLP gRPC/HTTP ile trace, metrik ve log toplama |
| **[ADV-03](labs/advanced/ADV-03-kubernetes-pod-loglari/README.md)** | **Kubernetes'te Pod Logları** | kind, Filebeat DaemonSet, `add_kubernetes_metadata`, multiline ile tek document'te stacktrace |
| **[ADV-04](labs/advanced/ADV-04-snapshot-restore-minio-s3/README.md)** | **S3/MinIO Snapshot, Restore ve DR** | S3 repository, SLM, felaket kurtarma tatbikatı |
| **[ADV-05](labs/advanced/ADV-05-semantic-search-knn-rrf/README.md)** | **Semantik Arama: Embedding Modeli, k-NN ve RRF** | `.multilingual-e5-small` modeli, `semantic_text`, Türkçe sorgu / İngilizce document, BM25 vs semantik, RRF |
| **[ADV-06](labs/advanced/ADV-06-zero-downtime-reindex/README.md)** | **Sıfır Kesintili Reindex** | `_reindex` + atomik alias geçişi ve geri alma |
| **[ADV-07](labs/advanced/ADV-07-esql-causal-rca/README.md)** | **ES\|QL ile Kök Neden Analizi** | Zincirleme arızada ilk kırılan servisi bulma, olay raporu |
| **[ADV-08](labs/advanced/ADV-08-elastic-8-vs-9/README.md)** | **Elastic 8 ve 9: Yükseltme Kapısı** | 8.19 ile 9.5.5 yan yana; uyumluluk sürümleri, eski API uyarıları, deprecation API ve logu, Upgrade Assistant |
| **[ADV-09](labs/advanced/ADV-09-eck-operator/README.md)** | **ECK: Kubernetes Operatörüyle Elasticsearch** | ECK 3.5.0, istenen durum ve üretilen nesneler, doğrulanmış TLS, PVC ile pod kaybında veri, Kibana'ya SSH tüneli |
| **[ADV-10](labs/advanced/ADV-10-paketle-3-node-cluster/README.md)** | **Paketle 3-Node Cluster** | Üç Ubuntu sunucusunda APT paketi, otomatik güvenlik ve TLS, enrollment token ile node ekleme, üç master adayı ve quorum, node kaybı |

### Projeler (Projects)

| Proje Adı | Teknoloji & Mimari | Dizin |
|---|---|---|
| **ecommerce-spring-search** | Spring Boot REST Arama Servisi (Port 8080), Relevance boosting, Autocomplete, Parent-Child (`join`) | [projects/ecommerce-spring-search](projects/ecommerce-spring-search/README.md) |
| **ecommerce-fastapi-search** | Python FastAPI, Edge N-Gram Autocomplete, 4-Clause Bool Should, Facets, ES\|QL | [projects/ecommerce-fastapi-search](projects/ecommerce-fastapi-search/README.md) |
| **fastapi-elk-monitoring** | Python FastAPI ECS JSON Formatter, Logstash TCP Socket, HTTP 500 Stack Trace ve ES\|QL RCA | [projects/fastapi-elk-monitoring](projects/fastapi-elk-monitoring/README.md) |
| **telecom-operations-insight-platform** | Çok kaynaklı sentetik capstone telemetrisi, pipeline'lar, incident evidence ve alert yönetimi | [projects/telecom-operations-insight-platform](projects/telecom-operations-insight-platform/README.md) |
| **elk-devsecops-tls-automation** | Full TLS/SSL, mTLS Root CA, 5x Beats ve Let's Encrypt Nginx Gateway | [projects/elk-devsecops-tls-automation](projects/elk-devsecops-tls-automation/README.md) |
| **bilgincit-devops-search** | BilgincIT DevOps & Cloud Arama Portalı; Türkçe Stemmer, Match, Fuzzy, Nested ve Phrase Query DSL eğitim laboratuvarı | [projects/bilgincit-devops-search](projects/bilgincit-devops-search/README.md) |

---

## Dokümantasyon ve Yardımcı Kaynaklar

* **[Dokümantasyon Merkezi (`docs/README.md`)](docs/README.md):** Özet rehberler ve mimari kılavuzlar.
* **[Mülakat & Tekrar Kartları (Flashcards)](docs/flashcards/README.md):** Mimariden performansa, güvenlikten sorgulama dillerine kadar 13 kategoride soru-cevap kartları.
* **[Python İstemcisi ve Otomasyon](scripts/python-automation/README.md):** Elasticsearch 9.x Python SDK ile CRUD, query DSL, aggregations, SQL ve Matplotlib offline görsel analitik raporlama scriptleri.

---

## Sürüm Standardı

Tüm lablarda tutarlı **Elastic Stack 9.5.5** sürümü kullanılmaktadır (Elasticsearch, Kibana ve Logstash aynı patch sürümünde çalışır). Tek istisna, 8.x ile karşılaştırma yapan ADV-08'dir.

### Hangi lab hangi Elasticsearch'te çalışır?

Eğitim boyunca **üç ayrı Elasticsearch** bulunur ve bunlar aynı anda çalışabilir.
Bir labın komutlarını yanlış cluster'da çalıştırmamak için önce bu tabloya bakın:

| Cluster | Elasticsearch | Kibana | Sürüm | Nasıl başlatılır | Kullanan lablar |
|---|---|---|---|---|---|
| **Ana cluster** (tek node) | `9200` | `5601` | 9.5.5 | LAB-01 `starter/docker-compose.yml` | LAB-02 … LAB-18, LAB-20 … LAB-22, LAB-24 … LAB-27 ve ADV-01 … ADV-07 |
| **3-node TLS cluster** | `19208` (HTTPS) | `15608` | 9.5.5 | LAB-19 Adım 1 (`starter/docker-compose.yml`) | Yalnızca **LAB-19 / LAB-21 / LAB-23**, LAB-24 Adım 7 (izleme) |
| **Eski sürüm profili** | `9208` | `5608` | 8.19 | ADV-08 profili | Yalnızca **ADV-08** |
| **ECK cluster'ı** (kind içinde) | `127.0.0.1:30087` (HTTPS) | `127.0.0.1:30086` | 9.5.5 | ADV-09 Adım 1-3 | Yalnızca **ADV-09** |

> [!IMPORTANT]
> LAB-19/23, ADV-08 ve ADV-09 kendi izole cluster'larını kullanır; ana cluster'ı (9200) etkilemezler.
> Kibana Dev Tools Console **bağlı olduğu** Kibana'nın cluster'ına istek gönderir:
> `5601` üzerindeki Console ana cluster'a, `15608` üzerindeki Console 3-node
> cluster'a yazar. LAB-19/23 komutlarını `5601`'deki Console'a yapıştırırsanız
> yanlış cluster'ı değiştirirsiniz.
>
> Çoğu labın README'si başındaki **Açık / Kullanılan Portlar** sütununda aynı
> bilgiyi tekrar eder; bu sütunu bulamadığınız lablarda hedef cluster giriş
> metninde yazılıdır. Tereddüt ederseniz yukarıdaki tablo bağlayıcıdır.
