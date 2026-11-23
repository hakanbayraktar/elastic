# Docker Compose ile 3-Node Rol Tabanlı Cluster vs Tek Node Kurulum Karşılaştırması

Bu doküman, Docker Compose ortamında **3 node'lu rol tabanlı (Dedicated Master, Hot Data, Ingest) Elasticsearch cluster** mimarisini, **tek node'lu (Single-Node) all-in-one** kurulum ile derinlemesine karşılaştırır. İki mimari arasındaki replica yerleşimi, quorum, split-brain koruması, kaynak izolasyonu ve hata toleransı (fault tolerance) farklarını ele alır.

---

## 1. Mimari Karşılaştırma Matrisi

| Kriter | Tek Node Docker Compose (LAB-01) | 3-Node Rol Tabanlı Docker Compose (LAB-19) |
|---|---|---|
| **Kullanım Amacı** | Geliştirme (Local Dev), test ortamı, düşük RAM kaynaklı hostlar. | Staging / Pre-prod, felaket senaryoları, quorum, failover ve HA eğitimleri. |
| **Discovery Yapılandırması** | `discovery.type: single-node` (Bootstrap ve master seçimi atlanır). | `discovery.seed_hosts` ve `cluster.initial_master_nodes` ile dinamik seçim. |
| **Node Rolleri Dağılımı** | Tek node tüm rolleri üstlenir (`master`, `data`, `ingest`, `ml`, vb.). | **Ayrıştırılmış Roller:**<br>- `es-master`: `[ master ]`<br>- `es-data`: `[ master, data_content, data_hot ]`<br>- `es-ingest`: `[ master, ingest, data_content, data_hot ]` |
| **Replica ve Cluster Health** | `number_of_replicas >= 1` olan indexler kalıcı olarak **`YELLOW`** kalır. | Replica'lar 2. data node'a dağıtılarak cluster durumu **`GREEN`** olur. |
| **Quorum ve Split-Brain Koruması** | Quorum yoktur. Node durursa tüm sistem çöker. | Raft tabanlı oy çoğunluğu ($Q = \lfloor 3/2 \rfloor + 1 = 2$). 1 node kaybında sistem kesintisiz sürer. |
| **Kaynak ve I/O İzolasyonu** | Ingest CPU yükü, Data NVMe I/O ve JVM Garbage Collection tek süreçte çakışır. | Ağır Ingest pipeline'ları Data node diskini ve Master cluster state'ini kilitlemez. |
| **Shared Snapshot Desteği** | Yerel tek dizin yeterlidir. | Tüm container'ların aynı shared Docker volume'a (`snapshots`) mount olması şarttır. |

---

## 2. Neden Tek Node'da Replica `YELLOW` Kalır?

Elasticsearch'ün en temel yüksek erişilebilirlik kuralı şudur:

> **"Bir primary shard ile onun replica kopyası asla aynı fiziksel node üzerinde bulunamaz."**

- **Tek Node Ortamında:**
  - Bir index açtığınızda varsayılan olarak `number_of_shards: 1`, `number_of_replicas: 1` gelir.
  - Primary shard (`p0`) tek node'a atanır.
  - Replica shard (`r0`) için cluster'da **ikinci bir data node** aranır. İkinci bir data node bulunamadığı için `r0` durumu `UNASSIGNED` olarak kalır.
  - Sonuç: `GET _cluster/health` çıktısı **`yellow`** görünür. Veri kaybı yoktur ancak node durursa veri okunamaz.

- **3 Node Rol Tabanlı Ortamda:**
  - Cluster'da 2 adet `data` rolüne sahip node bulunur (`es-data` ve `es-ingest`).
  - Primary shard `es-data` üzerine yazılırken, replica'sı `es-ingest` üzerine otomatik kopyalanır.
  - Sonuç: Bütün replica'lar atanmıştır ve `_cluster/health` **`green`** olur.

---

## 3. Rol Dağılımının Teknik Nedenleri ve Quorum Dayanıklılığı

### 3.1. Dedicated Master Node (`node.roles: [ master ]`)
- **Görevi:** Cluster State yönetimini yürütür (hangi shard nerede, mapping şemaları nedir, yeni index açıldı mı).
- **Neden Data Rolü Yok?** Ağır bir aggregation sorgusu veya yüksek disk I/O, JVM heap'ini şişirebilir ve Garbage Collection (GC) duraklamasına neden olabilir. Master node GC'ye girip ping'lere yanıt veremezse, diğer node'lar onu "öldü" sanıp gereksiz yere master seçimine gider (flapping). Master'ı veri saklamadan soyutlamak cluster kararlılığının omurgasıdır.

### 3.2. Hot Data Node (Master-Eligible) (`node.roles: [ master, data_content, data_hot ]`)
- **Görevi:** Indexing ve arama yükünü disk ve Lucene indexleri üzerinde yürütür.
- **Master Rolü Ekleme Nedeni:** 3 node'luk küçük bir cluster'da yalnız 2 master adayı bulunursa, bir node kaybedildiğinde kalan 1 oy çoğunluğu ($Q=2$) sağlayamaz ve cluster kilitlenir. Bu sebeple `es-data` node'una da `master` adayı rolü verilir. Normal operasyonda `es-master` liderdir; ancak node arızasında 3 adaydan 2'si ayakta kaldığı sürece cluster kesintisiz devam eder.

### 3.3. Hybrid Ingest + Data Node (Master-Eligible) (`node.roles: [ master, ingest, data_content, data_hot ]`)
- **Görevi:**
  1. Gelen ham logları `ingest pipeline` (Grok, GeoIP, Dissect, Painless script) ile işler.
  2. 2. data kopyasını saklayarak replica'nın yeşile dönmesini sağlar.
  3. Master-eligible rolü taşıyarak, 3 node'luk cluster'da Quorum ($Q=2$) çoğunluğunu garanti eder.

---

## 4. 3-Node Rol Tabanlı Docker Compose Dosyası (`docker-compose.roles.yml`)

Aşağıdaki compose dosyası, izole TLS sertifikaları, paylaşımlı snapshot volume'u ve açık node rolleri ile yapılandırılmıştır:

```yaml
name: elastic-cluster-roles

services:
  # -------------------------------------------------------------
  # 1. SETUP: CA ve TLS Sertifikalarını Hazırlar, İzinleri Düzenler
  # -------------------------------------------------------------
  setup:
    image: docker.elastic.co/elasticsearch/elasticsearch:9.5.5
    user: '0'
    volumes:
      - certs:/certs
      - snapshots:/mnt/elasticsearch-snapshots
      - ./instances.yml:/instances.yml:ro
    command:
      - bash
      - -ec
      - |
        if [ ! -f /certs/es-a/es-a.crt ]; then
          bin/elasticsearch-certutil ca --silent --pem -out /certs/ca.zip
          unzip -q /certs/ca.zip -d /certs
          bin/elasticsearch-certutil cert --silent --pem --in /instances.yml \
            --ca-cert /certs/ca/ca.crt --ca-key /certs/ca/ca.key -out /certs/nodes.zip
          unzip -q /certs/nodes.zip -d /certs
        fi
        chown -R 1000:0 /certs /mnt/elasticsearch-snapshots
        find /certs -type d -exec chmod 750 {} "+"
        find /certs -type f -exec chmod 640 {} "+"
    environment:
      ES_JAVA_OPTS: -Xms128m -Xmx256m
    mem_limit: 512m

  # -------------------------------------------------------------
  # 2. ES-MASTER: Dedicated Master Node (Veri ve Ingest Tutmaz)
  # -------------------------------------------------------------
  es-master:
    image: docker.elastic.co/elasticsearch/elasticsearch:9.5.5
    environment:
      cluster.name: elastic-roles-cluster
      node.name: es-master
      node.roles: master
      discovery.seed_hosts: es-master,es-data,es-ingest
      cluster.initial_master_nodes: es-master,es-data,es-ingest
      xpack.security.enabled: 'true'
      xpack.license.self_generated.type: basic
      ELASTIC_PASSWORD: ${CLUSTER_ELASTIC_PASSWORD:?export CLUSTER_ELASTIC_PASSWORD}
      ES_JAVA_OPTS: -Xms384m -Xmx384m
      path.repo: /mnt/elasticsearch-snapshots
      xpack.security.transport.ssl.enabled: 'true'
      xpack.security.transport.ssl.verification_mode: certificate
      xpack.security.transport.ssl.key: certs/es-a/es-a.key
      xpack.security.transport.ssl.certificate: certs/es-a/es-a.crt
      xpack.security.transport.ssl.certificate_authorities: certs/ca/ca.crt
      xpack.security.http.ssl.enabled: 'true'
      xpack.security.http.ssl.key: certs/es-a/es-a.key
      xpack.security.http.ssl.certificate: certs/es-a/es-a.crt
      xpack.security.http.ssl.certificate_authorities: certs/ca/ca.crt
      xpack.ml.enabled: 'false'
    volumes:
      - data-master:/usr/share/elasticsearch/data
      - certs:/usr/share/elasticsearch/config/certs:ro
      - snapshots:/mnt/elasticsearch-snapshots
    depends_on:
      setup:
        condition: service_completed_successfully
    mem_limit: 1g

  # -------------------------------------------------------------
  # 3. ES-DATA: Hot Data Node (Master-Eligible)
  # -------------------------------------------------------------
  es-data:
    image: docker.elastic.co/elasticsearch/elasticsearch:9.5.5
    environment:
      cluster.name: elastic-roles-cluster
      node.name: es-data
      node.roles: master,data_content,data_hot
      discovery.seed_hosts: es-master,es-data,es-ingest
      cluster.initial_master_nodes: es-master,es-data,es-ingest
      xpack.security.enabled: 'true'
      xpack.license.self_generated.type: basic
      ELASTIC_PASSWORD: ${CLUSTER_ELASTIC_PASSWORD:?export CLUSTER_ELASTIC_PASSWORD}
      ES_JAVA_OPTS: -Xms512m -Xmx512m
      path.repo: /mnt/elasticsearch-snapshots
      xpack.security.transport.ssl.enabled: 'true'
      xpack.security.transport.ssl.verification_mode: certificate
      xpack.security.transport.ssl.key: certs/es-b/es-b.key
      xpack.security.transport.ssl.certificate: certs/es-b/es-b.crt
      xpack.security.transport.ssl.certificate_authorities: certs/ca/ca.crt
      xpack.security.http.ssl.enabled: 'true'
      xpack.security.http.ssl.key: certs/es-b/es-b.key
      xpack.security.http.ssl.certificate: certs/es-b/es-b.crt
      xpack.security.http.ssl.certificate_authorities: certs/ca/ca.crt
      xpack.ml.enabled: 'false'
    volumes:
      - data-storage:/usr/share/elasticsearch/data
      - certs:/usr/share/elasticsearch/config/certs:ro
      - snapshots:/mnt/elasticsearch-snapshots
    depends_on:
      setup:
        condition: service_completed_successfully
    mem_limit: 1g

  # -------------------------------------------------------------
  # 4. ES-INGEST: Hybrid Node (Master + Ingest + Hot Data + REST Port)
  # -------------------------------------------------------------
  es-ingest:
    image: docker.elastic.co/elasticsearch/elasticsearch:9.5.5
    environment:
      cluster.name: elastic-roles-cluster
      node.name: es-ingest
      node.roles: master,ingest,data_content,data_hot
      discovery.seed_hosts: es-master,es-data,es-ingest
      cluster.initial_master_nodes: es-master,es-data,es-ingest
      xpack.security.enabled: 'true'
      xpack.license.self_generated.type: basic
      ELASTIC_PASSWORD: ${CLUSTER_ELASTIC_PASSWORD:?export CLUSTER_ELASTIC_PASSWORD}
      ES_JAVA_OPTS: -Xms512m -Xmx512m
      path.repo: /mnt/elasticsearch-snapshots
      xpack.security.transport.ssl.enabled: 'true'
      xpack.security.transport.ssl.verification_mode: certificate
      xpack.security.transport.ssl.key: certs/es-c/es-c.key
      xpack.security.transport.ssl.certificate: certs/es-c/es-c.crt
      xpack.security.transport.ssl.certificate_authorities: certs/ca/ca.crt
      xpack.security.http.ssl.enabled: 'true'
      xpack.security.http.ssl.key: certs/es-c/es-c.key
      xpack.security.http.ssl.certificate: certs/es-c/es-c.crt
      xpack.security.http.ssl.certificate_authorities: certs/ca/ca.crt
      xpack.ml.enabled: 'false'
    volumes:
      - data-ingest:/usr/share/elasticsearch/data
      - certs:/usr/share/elasticsearch/config/certs:ro
      - snapshots:/mnt/elasticsearch-snapshots
    depends_on:
      setup:
        condition: service_completed_successfully
    ports:
      - "127.0.0.1:${CLUSTER_PORT:-19208}:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl --silent --cacert config/certs/ca/ca.crt -o /dev/null -w '%{http_code}' https://localhost:9200 | grep -q 401"]
      interval: 5s
      timeout: 5s
      retries: 60
    mem_limit: 1g

  # -------------------------------------------------------------
  # 5. KIBANA: Yönetim ve Arayüz Servisi
  # -------------------------------------------------------------
  kibana:
    image: docker.elastic.co/kibana/kibana:9.5.5
    environment:
      SERVER_NAME: kibana-cluster
      ELASTICSEARCH_HOSTS: '["https://es-ingest:9200"]'
      ELASTICSEARCH_USERNAME: elastic
      ELASTICSEARCH_PASSWORD: ${CLUSTER_ELASTIC_PASSWORD}
      ELASTICSEARCH_SSL_CERTIFICATEAUTHORITIES: /usr/share/kibana/config/certs/ca/ca.crt
      XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    volumes:
      - certs:/usr/share/kibana/config/certs:ro
    ports:
      - "127.0.0.1:15608:5601"
    depends_on:
      es-ingest:
        condition: service_healthy
    mem_limit: 1g

volumes:
  certs: {}
  snapshots: {}
  data-master: {}
  data-storage: {}
  data-ingest: {}
```

---

## 5. Başlatma ve Çalıştırma Komutları

```bash
cd ~/elastic/labs/LAB-19-3-node-tls-cluster

# 1. Parolayı tanımlayın (varsa starter/.env dosyasından okur)
export CLUSTER_ELASTIC_PASSWORD="DevopsLab2026!SecurePassword"
export CLUSTER_PORT=19208

# 2. Cluster'ı başlatın
docker compose --env-file starter/.env -f starter/docker-compose.roles.yml up -d --wait

# 3. Servis durumunu kontrol edin
docker compose --env-file starter/.env -f starter/docker-compose.roles.yml ps

# 4. Node rollerini REST API üzerinden doğrulayın
curl --cacert <(docker compose --env-file starter/.env -f starter/docker-compose.roles.yml cp es-ingest:/usr/share/elasticsearch/config/certs/ca/ca.crt -) \
     -u "elastic:$CLUSTER_ELASTIC_PASSWORD" \
     "https://127.0.0.1:19208/_cat/nodes?v&h=name,roles,master,heap.percent,cpu"
```

Beklenen çıktı:
```text
name        roles           master heap.percent cpu
es-master m               *                15   2
es-data   m,d,h           -                20   3
es-ingest m,d,h,i         -                22   4
```

Bu yapı ile:
- `es-master` varsayılan elected master olarak cluster state'ini yönetir.
- `es-data` ve `es-ingest` data node olarak shard'ları paylaşır (biri primary, diğeri replica).
- `es-data` ve `es-ingest` aynı zamanda master adayı olduğu için tek bir node kapandığında quorum ($2/3$) korunur.
- `es-ingest` ingest pipeline işleme merkezi ve dışarıya açılan port kapısıdır.
- Replica'lar ikinci data node'a atanabildiği için cluster sağlığı kalıcı olarak **`GREEN`** olur.
