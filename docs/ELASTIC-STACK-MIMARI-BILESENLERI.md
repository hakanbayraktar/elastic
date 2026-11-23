# 🏛️ Elastic Stack Temel Mimari Bileşenleri

Elastic Stack (ELK), dağıtık arama, büyük veri analitiği, log yönetimi ve tam gözlemlenebilirlik (observability) sağlayan entegre bir platformdur:

```mermaid
flowchart TD
    subgraph DataSources["Veri Kaynakları & İstemciler"]
        A1["Sunucu Logları & Metrikleri"]
        A2["Mikroservisler & API'lar (OTel)"]
        A3["Veritabanları (PostgreSQL CDC)"]
    end

    subgraph Ingestion["Veri Toplama & İşleme (Ingestion)"]
        B1["Beats (Filebeat / Metricbeat)"]
        B2["Elastic Agent & Fleet Server"]
        B3["Logstash (ETL Pipeline: Input-Filter-Output)"]
        B4["OpenTelemetry (EDOT Collector)"]
    end

    subgraph Storage["Depolama & Sorgu Motoru"]
        C1["Elasticsearch Core Engine<br/>- Ingest Pipelines & Enrich<br/>- Distributed Shards & Replicas<br/>- ES|QL & Query DSL<br/>- HNSW Dense Vectors (AI/k-NN)"]
    end

    subgraph Visualization["Görselleştirme & Yönetim"]
        D1["Kibana UI<br/>- Discover & Dev Tools<br/>- Lens Dashboards<br/>- Alerting & Detection Rules<br/>- Fleet & Stack Management"]
    end

    DataSources --> Ingestion
    Ingestion --> Storage
    Storage --> Visualization
```

### Temel Bileşenlerin Rolleri:

1. **Elasticsearch:**
   * Apache Lucene tabanlı, dağıtık, RESTful JSON arama ve analitik motorudur.
   * Verileri **Index** yapılarında saklar; index'leri paralel işleme için **Shard** (birincil) ve **Replica** (yedek) parçalarına böler.
   * Veri girişinde **Ingest Node / Ingest Pipelines** ile dokümanları dönüştürür, PII maskelemesi yapar ve coğrafi IP (GeoIP) ekler.
2. **Kibana:**
   * Elasticsearch üzerindeki verileri keşfetmek (Discover), görsel panolar hazırlamak (Lens Dashboards), SQL/PPL/ES|QL sorguları çalıştırmak ve güvenlik/yaşam döngüsü (ILM/SLM) yönetmek için web arayüzüdür.
3. **Logstash:**
   * Ağır veri dönüştürme (ETL) boru hattıdır. `Input ➔ Filter (Grok, Dissect, Mutate) ➔ Output` mimarisiyle çalışır.
4. **Beats & Elastic Agent:**
   * **Beats:** Filebeat (log), Metricbeat (sistem metrikleri), Packetbeat (ağ) gibi tek amaçlı hafif Go ajanlarıdır.
   * **Elastic Agent & Fleet:** Tüm veri toplama araçlarını tek bir ajan altında toplayan ve Kibana üzerinden merkezi olarak yapılandırılan yeni nesil yönetim standardıdır.
