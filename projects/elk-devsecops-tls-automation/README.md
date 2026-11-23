# Project: ELK Stack 9.x DevSecOps Full TLS/SSL & 5x Beats Otomasyonu

Bu proje; kurumsal **DevSecOps** standartlarına uygun olarak tüm Elastic Stack 9.x ekosistemini (Elasticsearch, Logstash, Kibana ve **5 Beats: Filebeat, Metricbeat, Heartbeat, Packetbeat, Auditbeat**) uçtan uca **mTLS (Mutual TLS)** ve **Dahili Sertifika Otoritesi (CA)** ile koruma altına alan, adım adım eğitici bir uygulama platformudur.

---

> [!IMPORTANT]
> **Ayrı bir sunucu gerekir.** Bu proje kendi Elasticsearch/Kibana/Logstash/Nginx yığınını
> host'un `80`, `443`, `9200`, `5601`, `5044` portlarında açar; Packetbeat host ağını, Auditbeat
> host'un `/etc` ve `/usr/bin` dizinlerini izler. LAB-01 omurgasının ve host Nginx'inin çalıştığı
> eğitim sunucusunda **çalıştırmayın** (port çakışması). En az 6 GB boş RAM önerilir.

## Sunucu hazırlığı (boş Ubuntu 24.04)

Boş bir sunucuda önce paketleri güncelleyin, Docker'ı kurun ve repoyu indirin. Ayrıca
Elasticsearch'in istediği `vm.max_map_count` değerini kalıcı yapın; düşük kalırsa Elasticsearch
container'ı açılırken kapanır.

```bash
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io docker-compose-v2 git curl jq openssl
sudo usermod -aG docker "$USER"
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee /etc/sysctl.d/99-elasticsearch.conf
git clone https://github.com/hakanbayraktar/elastic.git ~/elastic
```

`usermod` grubu bir sonraki oturumda geçerli olur: bağlantıyı kapatıp yeniden bağlanın, sonra
`docker ps` komutunun `sudo` olmadan çalıştığını görün.

---

## 🚀 Çalışma Klasörüne Geçiş

Herhangi bir klasördeyken doğrudan bu projeye geçmek için:

```bash
cd ~/elastic/projects/elk-devsecops-tls-automation
```

---

## 💡 Temel Zihinsel Model: Neden ve Nasıl Güvenlik?

Geleneksel geliştirme ortamlarında güvenlik genellikle kapatılır (`xpack.security.enabled: false`) veya sadece tarayıcı ile Kibana arasına bir reverse proxy konularak iç trafik korunmasız bırakılır. Ancak **Zero-Trust (Sıfır Güven)** prensibine göre:

1. **İç Ağ Güvenli Değildir:** Node'lar arası veri kopyalama (Replication / Port 9300) trafiği ağ dinleyicilerine (packet sniffer) karşı mutlaka şifrelenmelidir (**Transport TLS**).
2. **REST API Koruması:** Elasticsearch'e atılan her sorgu ve indexleme isteği HTTPS üzerinden şifrelenmeli ve doğrulanmalıdır (**HTTP TLS / Port 9200**).
3. **İstemci Kimlik Doğrulaması (mTLS):** Logstash'e log basan Filebeat, sunucunun sertifikasını doğrulamakla kalmamalı; sunucu da Filebeat'in güvenilir bir ajan olduğunu teyit etmelidir (**Mutual TLS / Port 5044**).
4. **Dış Giriş Noktası (Ingress Gateway):** Dış dünyadan (tarayıcılardan) gelen trafik için ise **Let's Encrypt** veya kurumsal bir CA imzalı sertifika sunulmalıdır.

```text
               İSTEMCİLER & TARAYICILAR
                          │
                          ▼ (HTTPS / 443, 9200, 5601) [Let's Encrypt / Public SSL]
             ┌─────────────────────────┐
             │   Nginx Reverse Proxy   │
             └────────────┬────────────┘
                          │ (Dahili CA ile mTLS)
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
 ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
 │ Elasticsearch│◄─┤    Kibana    │  │   Logstash   │
 │   9.x TLS    │  │  9.x HTTPS   │  │ 5044 TLS In  │
 └──────▲───────┘  └──────────────┘  └──────▲───────┘
        │                                   │ (mTLS)
        │ (Direct HTTPS TLS)                │
 ┌──────┴───────────────────────────────────┴───────┐
 │                   5x BEATS                       │
 │  Filebeat  Metricbeat  Heartbeat  Packetbeat  Auditbeat │
 └──────────────────────────────────────────────────┘
```

---

## 🌐 Alan Adı ve Port Mimarisi

Lab ortamına tam uyum sağlamak üzere `.env` dosyasında `STUDENT_ID` parametresi tanımlanmıştır:

| Bileşen | FQDN Örneği | Dinlenen Port | Protokol ve Güvenlik |
|---|---|---|---|
| **Elasticsearch** | `student101-elastic.devopsatolyesi.com` | `9200` & `443` | HTTPS (Nginx Let's Encrypt / Dahili CA) |
| **Kibana** | `student101-kibana.devopsatolyesi.com` | `5601` & `443` | HTTPS Web Arayüzü |
| **Logstash Beats** | `student101-logstash.devopsatolyesi.com`| `5044` | TCP mTLS (İstemci Sertifika Doğrulamalı) |
| **Transport Ağı** | `elasticsearch:9300` | `9300` | Node-to-Node TLS Şifreleme |

---

## 📚 BÖLÜM 1: Adım Adım Eğitici Docker Kurulumu

Her şeyi arka planda sihirli tek bir script ile yapmak yerine, bu adımları sırayla inceleyerek ve komutları anlayarak çalıştırın:

### Adım 1.1: Ortam Değişkenlerini İnceleyin
```bash
cp .env.example .env
sed -i "s/student101/$(hostname -s | tr -d '-')/g" .env   # önek sunucunun adından gelir (student-1 -> student1)
cat .env
```
* `STUDENT_ID`: Kendi kullanıcı numaranızı veya sunucu ön ekinizi girin (Örn: `student101`).
* `DOMAIN_BASE`: Kurumsal alan adı (`devopsatolyesi.com`).
* `ELASTIC_PASSWORD`: Cluster genelinde geçerli süper kullanıcı parolası (`DevOps2026!`).

---

### Adım 1.2: Sertifika Konfigürasyonunu (`instances.yml`) İnceleyin
Elastic Stack'te `elasticsearch-certutil` aracının hangi servisler için hangi IP ve DNS alternatif adlarını (SAN - Subject Alternative Names) içereceğini bir YAML dosyası ile belirtiriz.

`instances.yml` dosyasının kritik rolü:
Eğer bir istemci `https://student101-elastic.devopsatolyesi.com:9200` adresine istek attığında sertifikada o DNS adı yazmıyorsa **`Hostname mismatch`** hatası alır!

```yaml
instances:
  - name: elasticsearch
    dns:
      - elasticsearch
      - student101-elastic.devopsatolyesi.com
      - localhost
    ip:
      - 127.0.0.1
  - name: kibana
    dns:
      - kibana
      - student101-kibana.devopsatolyesi.com
      - localhost
    ip:
      - 127.0.0.1
  - name: logstash
    dns:
      - logstash
      - student101-logstash.devopsatolyesi.com
      - localhost
    ip:
      - 127.0.0.1
  - name: beats
    dns:
      - beats
      - localhost
    ip:
      - 127.0.0.1
```

---

### Adım 1.3: Sertifikaları Adım Adım Üretin
Sertifika üretim mantığını elle çalıştırmak için:

```bash
# 1. Sertifika klasörlerini hazırlayın:
mkdir -p certs/ca certs/elasticsearch certs/kibana certs/logstash certs/beats nginx/certs

# 2. Hazırlanan adımlı scripti çalıştırarak sertifika otoritesini (Root CA) ve servis sertifikalarını üretin:
bash scripts/generate-internal-certs.sh
```

**Bu betik arka planda ne yapar?**
1. `elasticsearch-certutil ca --silent --pem -out /certs/ca.zip`: Kendi kendine imzalı kurumsal bir Root CA (`ca.crt` ve `ca.key`) üretir. Yollar mutlaktır: certutil göreli yolları kendi kurulum dizinine göre çözer.
2. `elasticsearch-certutil cert --in /certs/instances.yml --ca-cert ... --ca-key ...`: Belirlenen DNS ve IP alternatif adlarıyla her bileşene özel sertifika ve özel anahtar (`.crt` ve `.key`) basar.
3. `openssl pkcs8 -in logstash.key -topk8 -nocrypt -out logstash.pk8`: Logstash'in beats girdisi anahtarı PKCS#8 biçiminde ister; certutil ise PKCS#1 (`BEGIN RSA PRIVATE KEY`) üretir. Elasticsearch 9.x imajında `openssl` bulunmadığı için bu adım Logstash imajında çalıştırılır.

`docker compose up` sırasında `setup` ve `setup-convert` servisleri aynı adımları uygular; `certs/`
dizininde sertifikalar zaten varsa yeniden üretmez. Bu yüzden aşağıdaki doğrulamalarda kullanılan
`certs/ca/ca.crt`, konteynerlerin güvendiği CA ile aynı dosyadır.

---

### Adım 1.4: Nginx için SSL Sertifikasını Hazırlayın

Nginx ön tarafta gelen HTTPS isteklerini karşılayacaktır. İki seçeneğiniz vardır:

* **Yerel / Offline Test İçin (Self-Signed Wildcard):**
  ```bash
  bash scripts/generate-selfsigned-nginx.sh
  ```
  Bu komut `nginx/certs/fullchain.pem` ve `nginx/certs/privkey.pem` dosyalarını üretir.

* **Canlı / İnternete Açık Sunucu İçin (Let's Encrypt Certbot):** Önce self-signed sertifikayla
  yığını başlatın (Adım 1.5). ACME HTTP doğrulaması Nginx'in 80 portundan yapıldığı için Nginx
  çalışırken alınır; ayrıntı Adım 1.7'dedir.

---

### Adım 1.5: Docker Compose ile Servisleri Ayağa Kaldırın

Sertifikalar hazırlandıktan sonra Docker yığınını başlatın:

```bash
docker compose up -d
```

Çalışan servisleri kontrol edin:
```bash
docker compose ps
```

---

### Adım 1.6: Adım Adım Güvenlik Doğrulamaları

Her servisin güvenliğinin çalıştığını adım adım terminalden teyit edin:

#### 1. Elasticsearch HTTPS Kontrolü
İki farklı sertifika zinciri vardır: Elasticsearch'in kendisi dahili CA ile imzalı sertifika sunar
(yalnız `127.0.0.1:9201`), dış giriş noktası Nginx ise kendi sertifikasını (self-signed veya
Let's Encrypt) sunar (`9200`).

```bash
# Dahili CA ile doğrudan Elasticsearch:
curl -s --cacert certs/ca/ca.crt -u elastic:'DevOps2026!' "https://localhost:9201/_cluster/health?pretty"

# Nginx gateway üzerinden (self-signed sertifikanın kendisine güvenerek):
curl -s --cacert nginx/certs/fullchain.pem -u elastic:'DevOps2026!' "https://localhost:9200/_cluster/health?pretty"
```
*Beklenen Çıktı:* `"status": "green"` veya `"yellow"`. Dahili CA ile 9200'e gitmeyi denerseniz
doğrulama hatası alırsınız; çünkü 9200'de Nginx'in sertifikası sunulur.

#### 2. Logstash SSL Portu El Sıkışma Testi
```bash
openssl s_client -connect localhost:5044 -CAfile certs/ca/ca.crt </dev/null 2>/dev/null | grep -E "^New,|Verify return code"
```
*Beklenen Çıktı:*
```text
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Verify return code: 0 (ok)
```
`0 (ok)`, Logstash'in sunduğu sertifikanın dahili CA (`certs/ca/ca.crt`) tarafından imzalandığını
ve `localhost` adının SAN listesinde olduğunu gösterir. `</dev/null` olmadan `s_client` bağlantıyı
açık tutup klavyeden girdi bekler.

#### 3. Beats Loglarının Akışı
Filebeat, Nginx'in JSON erişim logunu (`nginx_logs` volume'u) okur ve Logstash'e bağlantıyı ilk
olay oluştuğunda açar; yukarıdaki gateway `curl` isteği bu olayı üretmiş olmalıdır.

Filebeat bağlantıyı ilk olayla açar; satır görünene kadar (en çok 2 dakika) bekleyin:

```bash
timeout 120 bash -c 'until docker compose logs --no-log-prefix filebeat | grep -q "tcp://logstash:5044)) established"; do printf .; sleep 3; done'; echo
docker compose logs --no-log-prefix filebeat | grep -o 'Connection to [^"]*established'
docker compose logs --no-log-prefix metricbeat | grep -o 'Connection to [^"]*established'
```
*Beklenen Çıktı:*
```text
Connection to backoff(async(tcp://logstash:5044)) established
Connection to backoff(elasticsearch(https://elasticsearch:9200)) established
```
İlk satır Filebeat → Logstash mTLS kanalının, ikincisi Metricbeat → Elasticsearch HTTPS kanalının
kurulduğunu gösterir. Satır yoksa Beat sertifikayı reddetmiş olabilir:
`docker compose logs filebeat | grep -i x509`.

#### 4. Elasticsearch'e Gelen Verileri Kontrol Edin
```bash
curl -s --cacert nginx/certs/fullchain.pem -u elastic:'DevOps2026!' \
  "https://localhost:9200/_cat/indices/devsecops-*,*beat-*?v&s=index&h=index,docs.count"
```
*Beklenen Çıktı (sayılar zamanla artar):*
```text
index                                  docs.count
.ds-auditbeat-9.5.5-2026.11.13-000001        1766
.ds-heartbeat-9.5.5-2026.11.13-000001          77
.ds-metricbeat-9.5.5-2026.11.13-000001        405
.ds-packetbeat-9.5.5-2026.11.13-000001        223
devsecops-2026.11.13                            2
```
* `devsecops-*` klasik bir index'tir: Filebeat → Logstash (mTLS) → Elasticsearch hattından gelir;
  her gateway isteği bir belgedir.
* Diğer dördü Beat'lerin doğrudan Elasticsearch'e HTTPS ile yazdığı **data stream**'lerdir;
  `.ds-...` adları data stream'in arka plandaki index'leridir.
* Cluster `yellow` görünür: tek düğümde replica shard'ı atanacak ikinci düğüm yoktur.

---

### Adım 1.7 (Opsiyonel): Let's Encrypt Sertifikası

Bu adım yalnızca dış giriş noktasının (Nginx) sertifikasını değiştirir; bileşenler arası TLS
(dahili CA) aynen kalır. Üç ön koşul vardır:

* `.env`'deki `ELASTIC_FQDN` ve `KIBANA_FQDN` için sunucunun açık IP'sini gösteren **A kaydı**.
  Logstash adı bu sertifikaya yazılmaz: 5044 Nginx'ten geçmez ve Beats, Logstash'in dahili CA
  sertifikasını doğrular. (Dışarıdaki Beat'ler Logstash'e adla bağlanacaksa `LOGSTASH_FQDN` için
  de A kaydı açılır; o ad dahili sertifikanın SAN listesinde zaten vardır.) Cloudflare kullanılıyorsa kayıt **DNS only** olmalıdır; proxy açıksa
  doğrulama isteği sunucuya değil Cloudflare'e gider.
* Sunucunun **80 portu internete açık** olmalı. Let's Encrypt doğrulamayı önceden bilinmeyen
  adreslerden yapar; bulut firewall'unda kaynak `0.0.0.0/0` gerekir. Kapalıysa hata
  `Timeout during connect (likely firewall problem)` olur.
* Yığın çalışıyor olmalı (Adım 1.5): Nginx `/.well-known/acme-challenge/` isteğini karşılar.

```bash
bash scripts/init-letsencrypt.sh
docker compose exec nginx nginx -s reload
```

Betik sertifikayı alır ve Nginx'in okuduğu `nginx/certs/fullchain.pem` / `privkey.pem`
dosyalarının yerine kopyalar; `reload` ile Nginx yeni sertifikayı yükler. `.env`'deki
`LETSENCRYPT_STAGING=0` gerçek sertifika ister; aynı adlar için haftada 5 sertifika sınırı vardır.
Denemeler için `1` yapın (staging sertifikasına tarayıcı güvenmez).

Sertifikayı inceleyin:

```bash
openssl x509 -in nginx/certs/fullchain.pem -noout -subject -issuer -enddate
```
*Beklenen Çıktı (tarihler farklı olur):*
```text
subject=CN = student1-elastic.devopsatolyesi.com
issuer=C = US, O = Let's Encrypt, CN = YE1
notAfter=Feb 11 19:11:17 2027 GMT
```

Artık `--cacert` ve `-k` olmadan, işletim sisteminin güvendiği kök sertifikalarla bağlanılır.
Adres **alan adıdır**: Let's Encrypt sertifikasında `localhost` yoktur, bu yüzden Adım 1.6'daki
`--cacert nginx/certs/fullchain.pem ... https://localhost:9200` komutu bu adımdan sonra
`no alternative certificate subject name matches target host name 'localhost'` hatası verir.

```bash
source .env
curl -s -u elastic:'DevOps2026!' \
  "https://${ELASTIC_FQDN}:9200/?filter_path=cluster_name" -w " verify=%{ssl_verify_result}\n"
```
*Beklenen Çıktı:*
```text
{
  "cluster_name" : "devsecops-cluster"
}
 verify=0
```
`verify=0` sertifika zincirinin (sunucu → Let's Encrypt YE1 → ISRG kökü) doğrulandığını
gösterir. Dahili CA ile doğrudan Elasticsearch erişimi (`https://localhost:9201`) etkilenmez.

---

## 🏢 BÖLÜM 2: Adım Adım 3 Sunuculu Kurulum (Bare-Metal / VM)

AWS zorunluluğu olmadan; VirtualBox, VMware, Proxmox veya yerel ağdaki 3 adet Ubuntu 22.04 / 24.04 sunucusu üzerinde sırayla kurulum:

### 1. Sunucu Dağılımı
* **Node 1 (`192.168.1.10`):** Elasticsearch 9.x + Root CA Otoritesi
* **Node 2 (`192.168.1.11`):** Logstash 9.x + Kibana 9.x (Nginx ve Certbot paketleri kurulur, yapılandırılmaz)
* **Node 3 (`192.168.1.12`):** 5x Beats (Filebeat, Metricbeat, Heartbeat, Packetbeat, Auditbeat)

Üç sunucuda da repo `~/elastic` altında bulunmalı ve her sunucu en az 8 GB RAM'e sahip olmalıdır.
Komutlar proje dizininden (`cd ~/elastic/projects/elk-devsecops-tls-automation`) çalıştırılır.

### 2. Node 1 Adımları (Elasticsearch)
Sunucu 1'de terminali açın:
```bash
cd bare-metal-3-nodes/node1-elasticsearch
sudo bash setup-node1.sh 192.168.1.11 192.168.1.12   # Node 2 ve Node 3 IP'leri (sertifika SAN'ı)
```
* Elastic APT deposu eklenir ve Elasticsearch kurulur.
* Root CA ve sertifikalar `/etc/elasticsearch/certs/` altında oluşturulur.
* `elasticsearch.yml` dosyasına TLS transport ve HTTP SSL yapılandırması işlenir.
* `elastic` parolası `DevOps2026!`, `kibana_system` parolası `DevOps2026!` olarak atanır.
* Diğer sunuculara dağıtılacak sertifikalar (`ca.crt` ve düğüm sertifikaları; CA özel anahtarı hariç) `/tmp/elk-certs-bundle/` dizininde toplanır. Paket düğüm özel anahtarlarını içerdiği için yalnızca betiği `sudo` ile çalıştıran kullanıcı okuyabilir.

### 3. Node 2 Adımları (Logstash & Kibana)
Sunucu 1'den sertifikaları Sunucu 2'ye aktarın (`user`: Sunucu 1'de betiği çalıştıran kullanıcı;
Sunucu 2'den Sunucu 1'e bu kullanıcıyla SSH erişimi olmalı):
```bash
scp -r user@192.168.1.10:/tmp/elk-certs-bundle /tmp/
```
Sunucu 2 kurulum betiğini Node 1 IP'sini vererek çalıştırın:
```bash
cd bare-metal-3-nodes/node2-kibana-logstash
sudo bash setup-node2.sh 192.168.1.10
```

### 4. Node 3 Adımları (5 Beats)
Sunucu 1'den Beat sertifikalarını Sunucu 3'e aktarın:
```bash
scp -r user@192.168.1.10:/tmp/elk-certs-bundle /tmp/
```
Sunucu 3 kurulum betiğini Node 1 (ES) ve Node 2 (Logstash) IP'lerini vererek çalıştırın:
```bash
cd bare-metal-3-nodes/node3-beats
sudo bash setup-node3.sh 192.168.1.10 192.168.1.11
```

### 5. Doğrulama
Sunucu 3'te Elasticsearch HTTPS, Logstash TLS el sıkışması ve beş Beat'in index'leri için
komutlar ve beklenen çıktılar [bare-metal-3-nodes/README.md](bare-metal-3-nodes/README.md)
dosyasındadır.

---

## 🛠️ BÖLÜM 3: SSL/TLS Sorun Giderme (Troubleshooting) Kılavuzu

Kurumsal ortamlarda karşılaşılan en yaygın SSL hataları ve çözümleri:

### 1. `PKIX path building failed: SunCertPathBuilderException: unable to find valid certification path to requested target`
* **Neden:** İstemci (Kibana, Logstash veya Beats), bağlandığı Elasticsearch sunucusunun sunduğu sertifikayı imzalayan Root CA'yı tanımıyor.
* **Çözüm:** İstemcinin konfigürasyonuna `certificate_authorities: ["/yol/ca.crt"]` parametresi eklenmeli ve Root CA dosyası gösterilmelidir.

### 2. `SSLHandshakeException: Received fatal alert: certificate_unknown`
* **Neden:** Sunucu, istemcinin sunduğu mTLS sertifikasını tanımadı veya sertifika süresi dolmuş.
* **Çözüm:** `openssl x509 -in client.crt -text -noout` ile sertifikanın `Issuer` (veren) bilgisini kontrol edin. Root CA ile eşleştiğinden emin olun.

### 3. `Hostname mismatch: certificate is valid for elasticsearch, not for student101-elastic.devopsatolyesi.com`
* **Neden:** Sunucuya bağlandığınız alan adı (Domain), sertifikanın `Subject Alternative Name (SAN)` listesinde yer almıyor.
* **Çözüm:** `instances.yml` dosyasına bağlanılan FQDN adını ekleyin ve sertifikayı `elasticsearch-certutil cert` ile yeniden üretin.

---

## 🧪 Bütünleşik Test Betiği

Docker kurulumunu (Bölüm 1) tek komutla denetlemek için:

```bash
./verify.sh
```

Betik sertifikaları, gateway ve dahili CA ile Elasticsearch erişimini, Kibana'yı, Logstash TLS el
sıkışmasını, her Beat index'inin ve `devsecops-*` index'inin belge sayısını ve Heartbeat'in ES,
Kibana ve Logstash TLS uçlarını son 2 dakikada `up` görüp görmediğini kontrol eder. Beklenen son:

```text
  Başarılı : 14
  Uyarı    : 0
  Hata     : 0
```

## Temizlik

```bash
./teardown.sh
```

Yalnızca bu projenin konteynerlerini, `es_data` / `nginx_logs` volume'larını ve üretilen
sertifikaları (`certs/`, `nginx/certs/*.pem`) siler. `.env` dosyanız ve indirilen Docker imajları
korunur; başka compose projelerine ve host servislerine dokunulmaz. Ardından Bölüm 1 baştan
tekrar uygulanabilir.
