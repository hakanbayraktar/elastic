# 🏢 Seçenek B: 3 Bağımsız Linux Sunucusunda (Bare-Metal / VM) DevSecOps TLS Kurulumu

Bu kılavuz, AWS veya herhangi bir bulut sağlayıcısına bağımlı olmadan, **3 adet Ubuntu 22.04 / 24.04 Linux sanal makinesi (VirtualBox, Proxmox, VMware, Vagrant veya yerel sunucular)** üzerinde uçtan uca TLS/SSL ile güvenli Elastic Stack 9.x kurulumunu adım adım açıklar.

---

## 🏛️ Topoloji ve Sunucu Rol Dağılımı

| Sunucu / Node | IP Örneği | Görev ve Servisler | Açık Portlar |
|---|---|---|---|
| **Sunucu 1 (Node 1)** | `192.168.1.10` | **Elasticsearch 9.x Master/Data Node** + Root CA Yetkilisi | `9200` (HTTPS), `9300` (TLS Transport) |
| **Sunucu 2 (Node 2)** | `192.168.1.11` | **Logstash 9.x** (Beats SSL) + **Kibana 9.x** (HTTPS) + **Nginx Gateway** | `5601` (Kibana), `5044` (Beats SSL), `80/443` (Nginx) |
| **Sunucu 3 (Node 3)** | `192.168.1.12` | **5x Beats İstemcisi:** Filebeat, Metricbeat, Heartbeat, Packetbeat, Auditbeat | Dışarıdan port açmaz; giden TLS trafiği üretir |

---

## 🚀 Adım Adım Kurulum

### Adım 1: Sunucu 1 (Elasticsearch ve Root CA Kurulumu)
1. Sunucu 1'e SSH ile bağlanın:
   ```bash
   ssh user@192.168.1.10
   ```
2. Kurulum betiğini çalıştırın:
   ```bash
   cd node1-elasticsearch
   sudo bash setup-node1.sh 192.168.1.11 192.168.1.12   # Node 2 ve Node 3 IP'leri
   ```
3. Betik:
   * Elastic 9.x APT deposunu ekler ve Elasticsearch paketini kurar.
   * `elasticsearch-certutil ca` ile kurumsal Root CA (`ca.crt`, `ca.key`) üretir.
   * `instances.yml` dosyasını okuyarak Node 1, Node 2 ve Node 3 için sertifikaları üretir.
   * `elasticsearch.yml` dosyasında TLS HTTP (9200) ve TLS Transport (9300) ayarlarını kilitler.
   * Sertifikaları diğer sunuculara dağıtmak üzere `/tmp/elk-certs-bundle/` dizininde hazırlar.

---

### Adım 2: Sunucu 2 (Logstash, Kibana ve Nginx Kurulumu)
1. Sunucu 1'de üretilen `kibana` ve `logstash` sertifikalarını Sunucu 2'ye kopyalayın. `user`,
   Sunucu 1'de `sudo bash setup-node1.sh` komutunu çalıştıran kullanıcıdır: paket düğüm özel
   anahtarlarını içerdiği için yalnızca o kullanıcı okuyabilir (`700`). Sunucu 2'den Sunucu 1'e bu
   kullanıcıyla SSH erişimi (parola veya anahtar) olmalıdır.
   ```bash
   scp -r user@192.168.1.10:/tmp/elk-certs-bundle /tmp/
   ```
2. Kurulum betiğini çalıştırın:
   ```bash
   cd node2-kibana-logstash
   sudo bash setup-node2.sh 192.168.1.10
   ```
3. Betik:
   * Kibana ve Logstash paketlerini kurar.
   * Kibana HTTPS (`server.ssl.enabled: true`) ve Logstash TLS Beats girişi (`5044`) yapılandırır.
   * Logstash'in beats girdisi için anahtarı PKCS#8 biçimine çevirir (`logstash.pk8`).
   * Nginx ve Certbot paketlerini kurar ama **yapılandırmaz**: Let's Encrypt sertifikası için
     sunucuyu gösteren bir DNS kaydı gerekir; bu adım betikte otomatik yapılmaz.
   * Kibana ve Logstash'in açılması 1-2 dakika sürer (JVM / Node.js açılışı).

---

### Adım 3: Sunucu 3 (5x Beats Kurulumu ve İstemci mTLS Doğrulaması)
1. Sunucu 1'deki `ca.crt` ve `beats` sertifikalarını Sunucu 3'e aktarın (aynı SSH koşulu):
   ```bash
   scp -r user@192.168.1.10:/tmp/elk-certs-bundle /tmp/
   ```
2. Kurulum betiğini çalıştırın:
   ```bash
   cd node3-beats
   sudo bash setup-node3.sh 192.168.1.10 192.168.1.11
   ```
3. Betik:
   * Filebeat, Metricbeat, Heartbeat, Packetbeat ve Auditbeat servislerini kurar.
   * CA doğrulamalı SSL parametrelerini uygular.
   * Tüm servisleri `systemctl enable --now` ile başlatır ve 15 saniye sonra beşinin de çalıştığını
     kontrol eder; çalışmayan varsa adını yazıp hata koduyla çıkar.

---

## 🔍 Doğrulama

Komutları **Sunucu 3**'te çalıştırın; CA sertifikası orada `/etc/beats/certs/ca/ca.crt` yolundadır.
`-k` kullanılmaz: amaç sertifikanın dahili CA ile doğrulandığını görmektir.

```bash
# 1. Elasticsearch HTTPS (sertifika Sunucu 1'in IP'si için SAN içerir)
curl -s --cacert /etc/beats/certs/ca/ca.crt -u elastic:'DevOps2026!' \
  "https://192.168.1.10:9200/_cluster/health?filter_path=cluster_name,status,number_of_nodes"
```
*Beklenen Çıktı:*
```text
{"cluster_name":"devsecops-cluster","status":"yellow","number_of_nodes":1}
```
Tek düğümde replica shard'ları atanamadığı için `yellow` normaldir.

```bash
# 2. Logstash 5044 TLS el sıkışması
openssl s_client -connect 192.168.1.11:5044 -CAfile /etc/beats/certs/ca/ca.crt </dev/null 2>/dev/null \
  | grep -E "^New,|Verify return code"
```
*Beklenen Çıktı:*
```text
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Verify return code: 0 (ok)
```

```bash
# 3. Beş Beat'in verisi (sayılar zamanla artar)
curl -s --cacert /etc/beats/certs/ca/ca.crt -u elastic:'DevOps2026!' \
  "https://192.168.1.10:9200/_cat/indices/devsecops-*,*beat-*?v&s=index&h=index,docs.count"
```
*Beklenen Çıktı:*
```text
index                                  docs.count
.ds-auditbeat-9.5.5-2026.11.22-000001         990
.ds-heartbeat-9.5.5-2026.11.22-000001           2
.ds-metricbeat-9.5.5-2026.11.22-000001          6
.ds-packetbeat-9.5.5-2026.11.22-000001          5
devsecops-baremetal-2026.11.22               4302
```
* `devsecops-baremetal-*`: Filebeat'in `/var/log/syslog` ve `/var/log/auth.log` satırları,
  Sunucu 2'deki Logstash üzerinden (Beat istemci sertifikasıyla TLS) gelir.
  Sunucu 2 betiği bittikten sonra Logstash'in 5044'ü açması 1-2 dakika sürer. Sunucu 3 bu sürede
  kurulduysa Filebeat önce `connection refused` alır, kendiliğinden yeniden dener ve bu index en
  geç bir dakika sonra belirir: `sudo journalctl -u filebeat | grep -o 'Connection to [^"]*established'`.
* `.ds-*beat-*`: diğer dört Beat'in doğrudan Elasticsearch'e HTTPS ile yazdığı data stream'ler.
  Betikler paketleri `9.5.5` sürümüne sabitler ve `apt-mark hold` ile tutar; Docker kurulumundaki sürümle aynıdır.

---

## Temizlik

Her sunucuda yalnız o sunucuya kurulanları kaldırın. Paketler purge edilir; veri, sertifika ve ayar
klasörleri silinir. Elastic APT deposu kaydı ve anahtarı sunucuda kalır.

Sunucu 1:

```bash
sudo systemctl stop elasticsearch
sudo apt-mark unhold elasticsearch
sudo apt-get purge -y -qq elasticsearch
sudo rm -rf /var/lib/elasticsearch /etc/elasticsearch /var/log/elasticsearch /tmp/elk-certs-bundle /tmp/instances.yml
```

Sunucu 2:

```bash
sudo systemctl stop kibana logstash nginx
sudo apt-mark unhold kibana logstash
sudo apt-get purge -y -qq kibana logstash nginx nginx-common certbot python3-certbot python3-certbot-nginx
sudo rm -rf /var/lib/kibana /etc/kibana /var/log/kibana /var/lib/logstash /etc/logstash /var/log/logstash /tmp/elk-certs-bundle
```

Sunucu 3:

```bash
sudo systemctl stop filebeat metricbeat heartbeat-elastic packetbeat auditbeat
sudo apt-mark unhold filebeat metricbeat heartbeat-elastic packetbeat auditbeat
sudo apt-get purge -y -qq filebeat metricbeat heartbeat-elastic packetbeat auditbeat
sudo rm -rf /etc/beats /var/lib/filebeat /var/lib/metricbeat /var/lib/heartbeat /var/lib/packetbeat /var/lib/auditbeat /tmp/elk-certs-bundle
```
