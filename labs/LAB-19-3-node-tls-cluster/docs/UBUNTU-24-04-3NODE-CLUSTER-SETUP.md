# Ubuntu 24.04 LTS Üzerinde 3-Node Rol Tabanlı Elasticsearch 9.5.5 Cluster Kurulum Kılavuzu

Bu kılavuz, **Ubuntu 24.04 LTS (Noble Numbat)** üzerinde bare-metal veya sanal sunucularda (VM), üretim seviyesinde (production-grade), rollerin ayrıştırıldığı **3 node'lu yüksek erişilebilir (HA) Elasticsearch 9.5.5 cluster** kurulumunu, işletim sistemi optimizasyonlarını, dahili TLS altyapısını, NFS shared snapshot deposunu ve operasyonel yönetim adımlarını eksiksiz olarak anlatır.

---

## 1. Mimarî Tasarım ve Node Rolleri

Elasticsearch'te node rolleri, her sunucunun kaynaklarını (CPU, RAM, Disk I/O) en verimli şekilde kullanmasını sağlar ve arıza anında cluster'ın bölünmesini (split-brain) önler.

### 1.1. Sunucu Dağılım Tablosu

| Sunucu Adı | IP Adresi | Atanan Node Rolleri | Rol Amacı | Minimum Donanım |
|---|---|---|---|---|
| **es-node-01** | `192.168.10.11` | `[ master ]` | **Dedicated Master:** Yalnızca cluster state, shard routing, index oluşturma/silme ve metadata yönetir. Veri saklamaz, ingest yapmaz. Disk I/O baskısı yaşamaz. | 2 vCPU, 4 GB RAM, 50 GB SSD |
| **es-node-02** | `192.168.10.12` | `[ data_content, data_hot ]` | **Dedicated Hot Data Node:** CRUD, arama, filtreleme, aggregation ve indexleme yükünü üstlenir. Yüksek NVMe disk ve RAM gerektirir. | 4 vCPU, 8–16 GB RAM, 200 GB NVMe |
| **es-node-03** | `192.168.10.13` | `[ master, ingest, data_content, data_hot ]` | **Hybrid Node (Master-eligible + Ingest + Hot Data):** Ingest pipeline'ları (Grok, GeoIP, Date parse) çalıştırır, 2. data node olarak replica'ları barındırır ve quorum için 2. master oyunu sağlar. | 4 vCPU, 8–16 GB RAM, 200 GB NVMe |

> [!IMPORTANT]
> **3 Node'lu Ortamlarda Quorum ve Split-Brain Formülü:**
> Elasticsearch, Raft-benzeri dağıtık konsensüs algoritması kullanır. Yeni bir master seçimi veya cluster state mutasyonu için gereken oy çoğunluğu:
> $$\text{Quorum} = \lfloor \frac{N_{\text{master-eligible}}}{2} \rfloor + 1$$
> - Eğer cluster'da yalnızca **1** adet master-eligible node olursa, o node durduğunda cluster felç olur.
> - Bu nedenle 3 node'lu bütçe dostu üretim mimarisinde:
>   - **es-node-01** dedicated master (`master`)
>   - **es-node-02** master-eligible data (`master, data_content, data_hot`)
>   - **es-node-03** master-eligible ingest/data (`master, ingest, data_content, data_hot`)
>   olarak yapılandırılır. Böylece $N=3$ olur, $\text{Quorum} = 2$'dir. Herhangi bir sunucu kapansa dahi cluster kesintisiz çalışır!

---

## 2. İşletim Sistemi ve Çekirdek Hazırlıkları (Tüm Node'larda)

Aşağıdaki adımları her üç Ubuntu 24.04 sunucusunda da sırasıyla uygulayın.

### 2.1. Hostname ve Ağ Eşlemeleri (`/etc/hosts`)

Her sunucuda `/etc/hosts` dosyasına diğer node'ların IP ve adlarını yazın:

```bash
sudo tee -a /etc/hosts > /dev/null << 'EOF'
192.168.10.11 es-node-01
192.168.10.12 es-node-02
192.168.10.13 es-node-03
EOF
```

Her sunucunun kendi hostname'ini ayarlayın:
- `es-node-01` üzerinde: `sudo hostnamectl set-hostname es-node-01`
- `es-node-02` üzerinde: `sudo hostnamectl set-hostname es-node-02`
- `es-node-03` üzerinde: `sudo hostnamectl set-hostname es-node-03`

### 2.2. Swap Alanının Devre Dışı Bırakılması

Elasticsearch bellek swap'lemeye başladığında GC duraklamaları dakikalar sürebilir ve node cluster'dan düşebilir.

```bash
# Geçici olarak swap'ı kapatın
sudo swapoff -a

# Kalıcı olması için /etc/fstab içindeki swap satırını yorum satırına alın
sudo sed -i '/swap/s/^\(.*\)$/#\1/g' /etc/fstab

# Doğrulayın (Swap satırı 0B olmalıdır)
free -h
```

### 2.3. Kernel Parametreleri (`vm.max_map_count` ve Dosya Tanımlayıcıları)

Elasticsearch mmap ve dosya sisteminde yüksek performans için `vm.max_map_count` değerinin en az `262144` olmasını zorunlu kılar.

```bash
sudo tee /etc/sysctl.d/99-elasticsearch.conf > /dev/null << 'EOF'
# Elasticsearch mmap sınırları
vm.max_map_count=262144

# Ağ soket kuyrukları ve bağlantı optimizasyonu
net.core.somaxconn=65535
fs.file-max=2097152
EOF

# Ayarları hemen uygulayın
sudo sysctl --system
sudo sysctl vm.max_map_count
```

### 2.4. Sistem Kaynak Limitleri (`limits.conf`)

`nofile` (open file descriptors) ve `memlock` (JVM bellek kilitleme) limitlerini tanımlayın:

```bash
sudo tee /etc/security/limits.d/99-elasticsearch.conf > /dev/null << 'EOF'
elasticsearch soft nofile 65535
elasticsearch hard nofile 65535
elasticsearch soft memlock unlimited
elasticsearch hard memlock unlimited
elasticsearch soft nproc 4096
elasticsearch hard nproc 4096
EOF
```

Systemd servislerinin bu limitleri miras alması için `/etc/systemd/system.conf` dosyasını düzenleyin:

```bash
sudo sed -i 's/#DefaultLimitNOFILE=/DefaultLimitNOFILE=65535/' /etc/systemd/system.conf
sudo sed -i 's/#DefaultLimitMEMLOCK=/DefaultLimitMEMLOCK=infinity/' /etc/systemd/system.conf
sudo systemctl daemon-reexec
```

### 2.5. Güvenlik Duvarı (UFW) Yapılandırması

Elasticsearch iki ağ portu kullanır:
- **Port 9200 (HTTP REST API):** Kibana, Logstash, Beats, Curl ve dış istemciler içindir.
- **Port 9300 (Transport TCP):** Node'lar arasındaki cluster içi iletişim, state senkronizasyonu ve shard replication'ı içindir. Dış dünyaya kesinlikle kapatılmalıdır!

```bash
sudo ufw allow 22/tcp comment 'SSH erisimi'

# Yalnızca internal subnet'ten 9300 Transport erişimine izin verin
sudo ufw allow from 192.168.10.0/24 to any port 9300 proto tcp comment 'ES Transport Inter-node'

# 9200 HTTP API erişimine (Kibana sunucusu veya yönetim subnet'i için) izin verin
sudo ufw allow from 192.168.10.0/24 to any port 9200 proto tcp comment 'ES HTTP REST API'
sudo ufw allow from 192.168.10.0/24 to any port 2049 proto tcp comment 'NFSv4 snapshot repository'

sudo ufw enable
sudo ufw status verbose
```

---

## 3. Elasticsearch 9.5.5 Kurulumu (Tüm Node'larda)

### 3.1. Elastic APT Repository ve GPG Key

```bash
# Gerekli araçları yükleyin
sudo apt-get update
sudo apt-get install -y wget curl gnupg apt-transport-https ca-certificates

# Elastic GPG anahtarını ekleyin
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /etc/apt/keyrings/elasticsearch-keyring.gpg
sudo chmod a+r /etc/apt/keyrings/elasticsearch-keyring.gpg

# APT source listesini oluşturun (9.x serisi)
echo "deb [signed-by=/etc/apt/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/9.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-9.x.list

# Paketi yükleyin
sudo apt-get update
sudo apt-get install -y elasticsearch=9.5.5
```

> [!WARNING]
> Servisi henüz başlatmayın! Önce TLS sertifikalarını ve `elasticsearch.yml` dosyasını yapılandıracağız.

---

## 4. Ortak Snapshot Deposu (NFS Mount) Yapılandırması

Elasticsearch Snapshot API'sinin çalışabilmesi için **tüm node'ların aynı fiziksel dizine okuma ve yazma erişimi** olması şarttır.

### 4.1. NFS Server Kurulumu (Örn. `es-node-01` veya ayrı bir depolama sunucusu)

`es-node-01` üzerinde:
```bash
sudo apt-get install -y nfs-kernel-server
sudo mkdir -p /mnt/elasticsearch-snapshots
sudo chown -R elasticsearch:elasticsearch /mnt/elasticsearch-snapshots
sudo chmod 775 /mnt/elasticsearch-snapshots

# /etc/exports içine ekleyin
echo "/mnt/elasticsearch-snapshots 192.168.10.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports
sudo exportfs -ra
sudo systemctl enable --now nfs-kernel-server
```

### 4.2. NFS Client Yapılandırması (`es-node-02` ve `es-node-03`)

Diğer node'larda:
```bash
sudo apt-get install -y nfs-common
sudo mkdir -p /mnt/elasticsearch-snapshots
sudo mount -t nfs 192.168.10.11:/mnt/elasticsearch-snapshots /mnt/elasticsearch-snapshots

# Kalıcı mount için /etc/fstab dosyasına ekleyin
echo "192.168.10.11:/mnt/elasticsearch-snapshots /mnt/elasticsearch-snapshots nfs defaults 0 0" | sudo tee -a /etc/fstab
```

Her iki node'da yazma iznini test edin:
```bash
sudo -u elasticsearch touch /mnt/elasticsearch-snapshots/test-write && rm /mnt/elasticsearch-snapshots/test-write
```

---

## 5. TLS / SSL Sertifikalarının Üretimi ve Dağıtımı

Üretim seviyesinde Elasticsearch'te hem **Transport Layer** (node-node iletişimi) hem de **HTTP Layer** (REST API) TLS ile şifrelenmelidir.

Bu işlemi **yalnızca `es-node-01`** üzerinde yapıp sertifikaları diğer sunuculara `scp` ile kopyalayacağız.

### 5.1. Sertifika Yetkilisi (CA) Oluşturma (`es-node-01`)

```bash
cd /usr/share/elasticsearch
sudo bin/elasticsearch-certutil ca --silent --pem -out /tmp/elastic-ca.zip
sudo unzip -q /tmp/elastic-ca.zip -d /tmp/ca-extracted
```

### 5.2. `instances.yml` Dosyası Hazırlama (`es-node-01`)

Node'ların IP ve FQDN bilgilerini içeren dosya:

```yaml
# /tmp/instances.yml
instances:
  - name: "es-node-01"
    ip:
      - "192.168.10.11"
      - "127.0.0.1"
    dns:
      - "es-node-01"
      - "localhost"
  - name: "es-node-02"
    ip:
      - "192.168.10.12"
      - "127.0.0.1"
    dns:
      - "es-node-02"
      - "localhost"
  - name: "es-node-03"
    ip:
      - "192.168.10.13"
      - "127.0.0.1"
    dns:
      - "es-node-03"
      - "localhost"
```

### 5.3. Node Sertifikalarını İmzalatma (`es-node-01`)

```bash
sudo bin/elasticsearch-certutil cert --silent --pem \
  --in /tmp/instances.yml \
  --ca-cert /tmp/ca-extracted/ca/ca.crt \
  --ca-key /tmp/ca-extracted/ca/ca.key \
  --out /tmp/elastic-nodes.zip

sudo unzip -q /tmp/elastic-nodes.zip -d /tmp/nodes-extracted
```

### 5.4. Sertifikaları Dağıtma ve İzinleri Ayarlama

Her node'da `/etc/elasticsearch/certs` klasörü oluşturup ilgili sertifikayı yerleştirin:

```bash
# es-node-01 için:
sudo mkdir -p /etc/elasticsearch/certs/ca
sudo cp /tmp/ca-extracted/ca/ca.crt /etc/elasticsearch/certs/ca/
sudo cp -r /tmp/nodes-extracted/es-node-01 /etc/elasticsearch/certs/
sudo chown -R root:elasticsearch /etc/elasticsearch/certs
sudo chmod 750 /etc/elasticsearch/certs
sudo chmod 640 /etc/elasticsearch/certs/ca/ca.crt /etc/elasticsearch/certs/es-node-01/*

# es-node-02'ye kopyalama:
ssh es-node-02 "sudo mkdir -p /etc/elasticsearch/certs/ca"
scp /tmp/ca-extracted/ca/ca.crt es-node-02:/tmp/ca.crt
ssh es-node-02 "sudo mv /tmp/ca.crt /etc/elasticsearch/certs/ca/ca.crt"
scp -r /tmp/nodes-extracted/es-node-02 es-node-02:/tmp/
ssh es-node-02 "sudo mv /tmp/es-node-02 /etc/elasticsearch/certs/ && sudo chown -R root:elasticsearch /etc/elasticsearch/certs && sudo chmod 750 /etc/elasticsearch/certs && sudo chmod 640 /etc/elasticsearch/certs/ca/ca.crt /etc/elasticsearch/certs/es-node-02/*"

# es-node-03'e kopyalama:
ssh es-node-03 "sudo mkdir -p /etc/elasticsearch/certs/ca"
scp /tmp/ca-extracted/ca/ca.crt es-node-03:/tmp/ca.crt
ssh es-node-03 "sudo mv /tmp/ca.crt /etc/elasticsearch/certs/ca/ca.crt"
scp -r /tmp/nodes-extracted/es-node-03 es-node-03:/tmp/
ssh es-node-03 "sudo mv /tmp/es-node-03 /etc/elasticsearch/certs/ && sudo chown -R root:elasticsearch /etc/elasticsearch/certs && sudo chmod 750 /etc/elasticsearch/certs && sudo chmod 640 /etc/elasticsearch/certs/ca/ca.crt /etc/elasticsearch/certs/es-node-03/*"
```

---

## 6. Node Rollerine Özel Konfigürasyon Dosyaları

Her sunucunun `/etc/elasticsearch/elasticsearch.yml` dosyasını kendi rolüne göre yapılandırın.

### 6.1. Node 1 (`es-node-01`): Dedicated Master Node

```yaml
# ======================== Elasticsearch Configuration =========================
cluster.name: elastic-prod-cluster
node.name: es-node-01

# --- ROL TANIMI ---
# Yalnızca Master rolü atanmıştır; veri saklamaz ve ingest yapmaz.
node.roles: [ master ]

# --- VERİ VE LOG YOLLARI ---
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
path.repo: [ "/mnt/elasticsearch-snapshots" ]

# --- JVM BELLEK KİLİTLEME ---
bootstrap.memory_lock: true

# --- AĞ BAĞLANTILARI ---
network.host: 192.168.10.11
http.port: 9200
transport.port: 9300

# --- CLUSTER DISCOVERY & QUORUM ---
discovery.seed_hosts: ["192.168.10.11:9300", "192.168.10.12:9300", "192.168.10.13:9300"]
# İlk açılışta master seçimi için 3 node aday gösterilir:
cluster.initial_master_nodes: ["es-node-01", "es-node-02", "es-node-03"]

# --- GÜVENLİK (X-PACK SECURITY & TLS) ---
xpack.security.enabled: true
xpack.security.enrollment.enabled: true

# Transport TLS (Node-to-Node)
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.key: certs/es-node-01/es-node-01.key
xpack.security.transport.ssl.certificate: certs/es-node-01/es-node-01.crt
xpack.security.transport.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]

# HTTP TLS (REST API)
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.key: certs/es-node-01/es-node-01.key
xpack.security.http.ssl.certificate: certs/es-node-01/es-node-01.crt
xpack.security.http.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]
```

### 6.2. Node 2 (`es-node-02`): Dedicated Hot Data Node (Master-Eligible)

```yaml
# ======================== Elasticsearch Configuration =========================
cluster.name: elastic-prod-cluster
node.name: es-node-02

# --- ROL TANIMI ---
# Master adayıdır (quorum desteği için) ve Hot/Content verileri saklar.
node.roles: [ master, data_content, data_hot ]

# --- VERİ VE LOG YOLLARI ---
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
path.repo: [ "/mnt/elasticsearch-snapshots" ]

# --- JVM BELLEK KİLİTLEME ---
bootstrap.memory_lock: true

# --- AĞ BAĞLANTILARI ---
network.host: 192.168.10.12
http.port: 9200
transport.port: 9300

# --- CLUSTER DISCOVERY & QUORUM ---
discovery.seed_hosts: ["192.168.10.11:9300", "192.168.10.12:9300", "192.168.10.13:9300"]
cluster.initial_master_nodes: ["es-node-01", "es-node-02", "es-node-03"]

# --- GÜVENLİK (X-PACK SECURITY & TLS) ---
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.key: certs/es-node-02/es-node-02.key
xpack.security.transport.ssl.certificate: certs/es-node-02/es-node-02.crt
xpack.security.transport.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]

xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.key: certs/es-node-02/es-node-02.key
xpack.security.http.ssl.certificate: certs/es-node-02/es-node-02.crt
xpack.security.http.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]
```

### 6.3. Node 3 (`es-node-03`): Hybrid Ingest + Hot Data Node (Master-Eligible)

```yaml
# ======================== Elasticsearch Configuration =========================
cluster.name: elastic-prod-cluster
node.name: es-node-03

# --- ROL TANIMI ---
# Ingest pipeline'ları çalıştırır, 2. kopya veriyi saklar ve master quorum'unu tamamlar.
node.roles: [ master, ingest, data_content, data_hot ]

# --- VERİ VE LOG YOLLARI ---
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
path.repo: [ "/mnt/elasticsearch-snapshots" ]

# --- JVM BELLEK KİLİTLEME ---
bootstrap.memory_lock: true

# --- AĞ BAĞLANTILARI ---
network.host: 192.168.10.13
http.port: 9200
transport.port: 9300

# --- CLUSTER DISCOVERY & QUORUM ---
discovery.seed_hosts: ["192.168.10.11:9300", "192.168.10.12:9300", "192.168.10.13:9300"]
cluster.initial_master_nodes: ["es-node-01", "es-node-02", "es-node-03"]

# --- GÜVENLİK (X-PACK SECURITY & TLS) ---
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.key: certs/es-node-03/es-node-03.key
xpack.security.transport.ssl.certificate: certs/es-node-03/es-node-03.crt
xpack.security.transport.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]

xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.key: certs/es-node-03/es-node-03.key
xpack.security.http.ssl.certificate: certs/es-node-03/es-node-03.crt
xpack.security.http.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]
```

### 6.4. JVM Heap Boyutlandırması (`jvm.options.d/heap.options`)

Elasticsearch için altın kural:
1. Heap boyutu fiziksel RAM'in en fazla **%50'si** olmalıdır. Kalan %50 OS sayfa önbelleğine (Lucence Page Cache) ayrılmalıdır.
2. Compressed OOPs avantajını kaybetmemek için Heap boyutu kesinlikle **30.5 GB**'ı geçmemelidir.
3. Minimum ve maksimum heap değerleri eşit (`-Xms` = `-Xmx`) olmalıdır.

Sunucuların RAM miktarına göre `/etc/elasticsearch/jvm.options.d/heap.options` dosyasını oluşturun:

```bash
# Örnek: 8 GB RAM olan bir sunucu için 4 GB Heap ayarı
sudo tee /etc/elasticsearch/jvm.options.d/heap.options > /dev/null << 'EOF'
-Xms4g
-Xmx4g
EOF
```

---

## 7. Servislerin Başlatılması ve Parola Yönetimi

### 7.1. Servisleri Başlatma Sırası

Önce `es-node-01` (Master), ardından `es-node-02` ve `es-node-03` servislerini başlatın:

```bash
# Her node üzerinde:
sudo systemctl daemon-reload
sudo systemctl enable --now elasticsearch

# Başlama durumunu ve logları kontrol edin:
sudo systemctl status elasticsearch
sudo journalctl -u elasticsearch -f
```

### 7.2. Yönetici Parolasının (`elastic` kullanıcısı) Belirlenmesi

Node'lar ayağa kalktıktan sonra `es-node-01` üzerinde built-in `elastic` kullanıcısının parolasını belirleyin:

```bash
sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic -i
# Konsoldan güçlü bir parola girin (örn: DevopsLab2026!Secure)
```

### 7.3. Cluster Sağlığının Terminalden Doğrulanması

```bash
curl --cacert /etc/elasticsearch/certs/ca/ca.crt \
     -u elastic:DevopsLab2026!Secure \
     "https://192.168.10.11:9200/_cat/nodes?v&h=name,roles,master,heap.percent,ram.percent,cpu"
```

Beklenen çıktı örneği:
```text
name       roles                     master heap.percent ram.percent cpu
es-node-01 m                         *                18          45   2
es-node-02 m,d,h                     -                22          52   3
es-node-03 m,d,h,i                   -                24          55   4
```
- `m`: master
- `d`: data
- `h`: hot data
- `i`: ingest
- `*`: Aktif seçilmiş master node (`es-node-01`)

Cluster sağlık durumunu kontrol edin:
```bash
curl --cacert /etc/elasticsearch/certs/ca/ca.crt \
     -u elastic:DevopsLab2026!Secure \
     "https://192.168.10.11:9200/_cluster/health?pretty"
```
```json
{
  "cluster_name" : "elastic-prod-cluster",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 3,
  "number_of_data_nodes" : 2,
  "active_primary_shards" : 0,
  "active_shards" : 0,
  "unassigned_shards" : 0
}
```
> [!NOTE]
> `number_of_nodes: 3`, ancak `number_of_data_nodes: 2` görünmektedir. Çünkü `es-node-01` dedicated master olarak ayarlanmıştır ve data rolü taşımamaktadır!

---

## 8. Kibana Kurulumu ve Entegrasyonu

Kibana genellikle ayrı bir yönetim sunucusuna kurulur veya `es-node-01` üzerine konuşlandırılabilir.

```bash
# Kibana kurulumu
sudo apt-get install -y kibana=9.5.5

# Kibana için CA sertifikasını kopyalayın
sudo mkdir -p /etc/kibana/certs/ca
sudo cp /etc/elasticsearch/certs/ca/ca.crt /etc/kibana/certs/ca/
sudo chown -R root:kibana /etc/kibana/certs

# Elasticsearch üzerinde kibana_system parolasını belirleyin (es-node-01 üzerinde çalıştırılır):
sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u kibana_system -i
```

`/etc/kibana/kibana.yml` dosyasını düzenleyin:

```yaml
server.port: 5601
server.host: "0.0.0.0"
server.name: "kibana-prod"

elasticsearch.hosts: ["https://192.168.10.11:9200", "https://192.168.10.12:9200", "https://192.168.10.13:9200"]
elasticsearch.username: "kibana_system"
elasticsearch.password: "KibanaSystem2026!Pass"
elasticsearch.ssl.certificateAuthorities: [ "/etc/kibana/certs/ca/ca.crt" ]

# Saved Objects şifreleme anahtarları (en az 32 karakter):
xpack.encryptedSavedObjects.encryptionKey: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
xpack.reporting.encryptionKey: "b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q7"
xpack.security.encryptionKey: "c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5r8"
```

Kibana servisini başlatın:
```bash
sudo systemctl enable --now kibana
sudo systemctl status kibana
```

Artık `http://192.168.10.11:5601` üzerinden Kibana'ya erişebilir, `elastic` kullanıcısı ile oturum açabilirsiniz.

---

## 9. Log Dosyaları ve Troubleshooting Haritası

Bir sorun çıktığında ilk bakılması gereken dosya yolları şunlardır:

| Log Dosyası | Konum | İnceleme Amacı |
|---|---|---|
| **Ana Sunucu Logu** | `/var/log/elasticsearch/elastic-prod-cluster.log` | Node başlangıcı, exception'lar, bağlantı hataları ve cluster state güncellemeleri. |
| **Yapılandırılmış JSON Logu** | `/var/log/elasticsearch/elastic-prod-cluster_server.json` | Logstash veya Filebeat ile parse edilip merkezi izlemeye alınacak format. |
| **Deprecation Logu** | `/var/log/elasticsearch/elastic-prod-cluster_deprecation.log` | 9.x sürümünde kaldırılacak veya eskiyen API çağrıları. |
| **JVM Garbage Collection (GC) Logu** | `/var/log/elasticsearch/gc.log` | Bellek baskısı, uzun GC duraklamaları (Stop-The-World) ve OOM (Out Of Memory) analizleri. |
| **Systemd Servis Logu** | `journalctl -u elasticsearch -e -f` | Servis crash'leri, Linux kernel OOM-killer müdahaleleri. |

Tebrikler! Ubuntu 24.04 üzerinde 3 node rol tabanlı cluster mimarisini başarıyla tamamladınız. Şimdi bu cluster üzerinde test ve operasyon senaryolarına geçebilirsiniz.
