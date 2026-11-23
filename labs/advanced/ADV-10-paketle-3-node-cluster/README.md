# ADV-10 — Paketle 3-Node Cluster: APT Kurulumu, Enrollment Token ve Quorum

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Ubuntu 24.04, Elasticsearch 9.5.5 APT paketi, systemd, `elasticsearch-create-enrollment-token`, `elasticsearch-reconfigure-node`, `curl`, `jq` | `9200` (HTTPS) ve `9300` (node'lar arası TLS), yalnız üç VM'in iç ağında |

---

## Bu lab ne öğretiyor?

LAB-19'da üç node'u Docker'da, sertifikaları elle üreterek kurduk. Şirket sunucularında Elasticsearch çoğu zaman
paketle (APT) ve systemd servisi olarak çalışır. Paket kurulumu güvenliği kendisi açar: kendi CA'sını, TLS
sertifikalarını ve `elastic` parolasını üretir. Yeni bir node'u cluster'a eklemek de sertifika taşımak yerine tek
kullanımlık bir **enrollment token** ile olur.

Bu labda üç ayrı sunucuya paketi kuracak, ilk node'u başlatıp cluster'ı oluşturacak, diğer iki node'u token ile
ekleyecek, üçünün de master adayı olduğunu ve oylamaya katıldığını görecek ve bir node'u durdurup cluster'ın
çalışmaya devam ettiğini kanıtlayacağız.

---

## Ön Koşullar

- **Üç ayrı Ubuntu 24.04 sunucusu**, her biri en az 2 vCPU ve 8 GB RAM, aynı ağda. Bu lab eğitim sunucusunda
  yapılmaz: Docker ana cluster'ı da `9200` portunu kullanır.
- Sunucular birbirine `9200` ve `9300` portlarından ulaşabilmeli. GCP'de aynı VPC'deki VM'ler arası trafik varsayılan
  `default-allow-internal` kuralıyla açıktır; dışarıya port açmak gerekmez.
- Komutların hepsi **node-1'de** çalışır; node-1 diğer ikisine SSH ile komut gönderir. Önceki labları
  atladıysanız da bu lab çalışır.

Sunucular boş geliyorsa önce **node-1'de** paket listesini güncelleyin, `git`'i kurun ve repoyu indirin (diğer iki
node'a repo gerekmez; onlara komutlar node-1'den gider):

```bash
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
sudo -E apt-get update -qq && sudo -E apt-get install -y -qq git jq >/dev/null
[ -d ~/elastic ] || git clone -q https://gitlab.com/devops-monitoring/elastic.git ~/elastic
git -C ~/elastic log --oneline -1
```

```text
<kısa-hash> <son commit başlığı>
```

`NEEDRESTART_MODE=a` Ubuntu'nun "hangi servisler yeniden başlatılsın?" sorusunu otomatik cevaplar; yoksa komut
yarıda bekler. Her node'daki tam güncelleme (`apt-get upgrade`) Adım 1'deki betiğin içinde.

Node-1'de bir SSH anahtarı oluşturun ve açık anahtarı ekrana yazdırın:

```bash
[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -q -t ed25519 -N '' -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... student@student-1
```

Bu açık anahtarı node-2 ve node-3'e ekleyin. Kendi bilgisayarınızdan, her biri için bir kez (yer tutucuları kendi
değerlerinizle değiştirin):

```bash
ssh <KULLANICI>@<NODE2_DIS_IP> "echo '<NODE1_ACIK_ANAHTAR>' >> ~/.ssh/authorized_keys"
ssh <KULLANICI>@<NODE3_DIS_IP> "echo '<NODE1_ACIK_ANAHTAR>' >> ~/.ssh/authorized_keys"
```

Node-1'de üç node'un **iç** IP adresini bir dosyaya yazın (`hostname -I` her sunucunun iç IP'sini verir):

```bash
cat > ~/adv10.env << 'EOF'
NODE1=<NODE1_IC_IP>
NODE2=<NODE2_IC_IP>
NODE3=<NODE3_IC_IP>
EOF
```

Lab klasörüne geçin ve node-1'in diğer ikisine şifresiz bağlanabildiğini doğrulayın:

```bash
cd ~/elastic/labs/advanced/ADV-10-paketle-3-node-cluster
. scripts/ortam.sh
n2 hostname; n3 hostname
```

```text
student-2.europe-west2-c.c.<proje>.internal
student-3.europe-west2-c.c.<proje>.internal
```


---

## Kavramlar: paket kurulumu ve node ekleme

| Kavram | Ne yapar | Neden önemli |
|---|---|---|
| Otomatik güvenlik yapılandırması | Paket kurulurken CA, HTTP ve transport sertifikalarını üretir, `elasticsearch.yml`'e TLS satırlarını yazar | TLS'siz bir cluster hiç açılmaz; sertifika elle üretilmez |
| `cluster.initial_master_nodes` | Cluster **ilk kez** kurulurken kimlerin oy vereceğini söyler | Yalnız ilk açılışta gerekir; cluster kurulduktan sonra kaldırılır, kalırsa ileride ikinci, ayrı bir cluster doğabilir |
| Enrollment token | Yeni node'a CA'yı, transport sertifikasını ve mevcut node'un adresini taşıyan, 30 dakika geçerli anahtar | Sertifika dosyalarını sunucular arasında kopyalamak gerekmez |
| `elasticsearch-reconfigure-node` | Kurulmuş ama hiç başlatılmamış node'un kendi ürettiği güvenlik ayarını token'daki cluster'a göre yeniden yazar | Node yanlışlıkla bir kez başlatılırsa kendi cluster'ını kurar; o zaman veri klasörü silinip baştan yapılır |
| Voting configuration | Master seçiminde oyu sayılan node'lar | Üç master adayıyla bir node kaybı çoğunluğu (2/3) bozmaz |

<details>
<summary><strong>Config dosyaları: paketin yazdığı satırlar</strong></summary>

Paket kurulumundan sonra `/etc/elasticsearch/elasticsearch.yml`'in sonunda otomatik bir güvenlik bloğu bulunur:

```yaml
xpack.security.enabled: true
xpack.security.enrollment.enabled: true
xpack.security.http.ssl:
  enabled: true
  keystore.path: certs/http.p12
xpack.security.transport.ssl:
  enabled: true
  verification_mode: certificate
  keystore.path: certs/transport.p12
  truststore.path: certs/transport.p12
cluster.initial_master_nodes: ["<hostname>"]
http.host: 0.0.0.0
#transport.host: 0.0.0.0
```

- `http.p12`, `transport.p12`: sertifikalar ve anahtarlar; parolaları `elasticsearch.keystore` içinde.
- `certs/http_ca.crt`: istemcilerin HTTPS bağlantısını doğrulayacağı CA.
- `transport.host` yorumlu gelir: node yalnız kendi üzerinde (localhost) dinler, başka node bağlanamaz. Adım 2'de
  açıyoruz.

</details>

---

## Adım Adım Uygulama Rehberi

### 1. Paketi üç node'a kurmak

`scripts/hazirla.sh` her node'da aynı işi yapar: `apt-get update` ve `upgrade`, `vm.max_map_count`, Elastic'in imzalı APT deposu, `elasticsearch=9.5.5`
paketi ve 2 GB heap. Paketi kurar ama **servisi başlatmaz**; node-2 ve node-3 hiç başlatılmadan token ile
yapılandırılmalıdır.

```bash
. scripts/ortam.sh
n1 "bash scripts/hazirla.sh"
n2 'bash -s' < scripts/hazirla.sh
n3 'bash -s' < scripts/hazirla.sh
```

```text
student-1: elasticsearch 9.5.5, servis: inactive
student-2: elasticsearch 9.5.5, servis: inactive
student-3: elasticsearch 9.5.5, servis: inactive
```

Paket kurulurken her node kendi CA'sını ve rastgele bir `elastic` parolası üretti. Node-1'inkiler kullanılacak;
node-2 ve node-3'ünkiler Adım 3'te token ile değiştirilecek.

### 2. İlk node: cluster'ı oluşturmak

`transport.host`'u açın ki diğer node'lar node-1'e bağlanabilsin, servisi başlatın:

```bash
sudo sed -i 's/^#transport.host: 0.0.0.0/transport.host: 0.0.0.0/' /etc/elasticsearch/elasticsearch.yml
sudo grep -E '^(cluster.initial_master_nodes|http.host|transport.host)' /etc/elasticsearch/elasticsearch.yml
sudo systemctl start elasticsearch
systemctl is-active elasticsearch
```

```text
cluster.initial_master_nodes: ["student-1.europe-west2-c.c.<proje>.internal"]
http.host: 0.0.0.0
transport.host: 0.0.0.0
active
```

`systemctl start` servis istek almaya hazır olunca döner. `enable` bilerek kullanılmıyor: bu VM'ler yalnız lab için.

HTTP artık TLS'li. İstemci için CA'yı ev klasörüne kopyalayın, `elastic` parolasını önce rastgele bir değere sıfırlayıp
(`-a` otomatik, `-b` onay sorma, `-s` yalnız parolayı yaz) o parolayla eğitim parolasına çevirin:

```bash
sudo cp /etc/elasticsearch/certs/http_ca.crt ~/ && sudo chown "$USER" ~/http_ca.crt
TMP_PW=$(sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic -a -b -s)
curl -s --cacert ~/http_ca.crt -u "elastic:$TMP_PW" -X POST 'https://127.0.0.1:9200/_security/user/elastic/_password' \
  -H 'Content-Type: application/json' -d '{"password": "DevOps2026!"}'; echo
. scripts/ortam.sh
es 'https://127.0.0.1:9200/_cluster/health?filter_path=cluster_name,status,number_of_nodes'; echo
```

```text
{}
{"cluster_name":"elasticsearch","status":"green","number_of_nodes":1}
```

`--cacert` sunucunun sertifikasını paketin ürettiği CA ile doğrular. `-k` ile doğrulamayı kapatmak lab'da çalışır
ama bağlantının kime yapıldığını kanıtlamaz.

### 3. Enrollment token ile node-2 ve node-3'ü eklemek

Node-1'de **node** türünde bir token üretin ve her yeni node'da `elasticsearch-reconfigure-node`'a verin.
Komut onay sorar; `echo y` onu cevaplar. Token 30 dakika geçerlidir; süre geçerse yenisini üretin:

```bash
. scripts/ortam.sh
for N in n2 n3; do
  T=$(sudo /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s node)
  $N "echo y | sudo /usr/share/elasticsearch/bin/elasticsearch-reconfigure-node --enrollment-token $T | tail -3; sudo systemctl start elasticsearch; systemctl is-active elasticsearch"
done
```

```text
  - Security auto configuration will be removed from elasticsearch.yml
  - The [certs] config directory will be removed
  - Security auto configuration related secure settings will be removed from the elasticsearch.keystore
active
  - Security auto configuration will be removed from elasticsearch.yml
  - The [certs] config directory will be removed
  - Security auto configuration related secure settings will be removed from the elasticsearch.keystore
active
Do you want to continue with the reconfiguration process [y/N]Do you want to continue with the reconfiguration process [y/N]
```

Üç node'un cluster'a katılmasını bekleyin:

```bash
. scripts/ortam.sh
es 'https://127.0.0.1:9200/_cluster/health?wait_for_nodes=3&timeout=120s&filter_path=status,number_of_nodes'; echo
es 'https://127.0.0.1:9200/_cat/nodes?v&h=name,ip,node.role,master'
```

```text
{"status":"green","number_of_nodes":3}
name                                               ip         node.role   master
student-2.europe-west2-c.c.<proje>.internal 10.154.0.5 cdfhilmrstw -
student-3.europe-west2-c.c.<proje>.internal 10.154.0.6 cdfhilmrstw -
student-1.europe-west2-c.c.<proje>.internal 10.154.0.4 cdfhilmrstw *
```

`node.role` sütunundaki `m` harfi node'un master adayı olduğunu gösterir; rol vermediğimiz için üçü de varsayılan
olarak her rolü taşır. `master` sütunundaki `*` o anki master'dır.

<details>
<summary><strong>Token neden her node için ayrı üretiliyor?</strong></summary>

Bir token birden çok node'a verilebilir, ama komut satırında açıkça göründüğü ve 30 dakika boyunca cluster'a node
eklemeye yettiği için kısa ömürlü ve tek iş için kullanmak daha güvenlidir. Kibana için `-s kibana` türünde ayrı bir
token üretilir.

</details>

### 4. Quorum: üç oy ve `cluster.initial_master_nodes`

Oylamaya katılan node'lar cluster durumunda tutulur:

```bash
. scripts/ortam.sh
es 'https://127.0.0.1:9200/_cluster/state?filter_path=metadata.cluster_coordination.last_committed_config' | jq -c '.metadata.cluster_coordination.last_committed_config | length'
```

```text
3
```

Üç oy var: bir node kaybolursa kalan iki node çoğunluğu (2/3) sağlar ve master seçebilir. İki master adayı olsaydı
biri düştüğünde 1/2 çoğunluk olmazdı.

`cluster.initial_master_nodes` yalnız ilk kurulum içindi. Cluster kurulduğu için node-1'de kaldırın; satır
kalırsa node ileride verisi silinmiş halde yeniden başlatıldığında tek başına yeni bir cluster kurabilir:

```bash
sudo sed -i 's/^cluster.initial_master_nodes/#cluster.initial_master_nodes/' /etc/elasticsearch/elasticsearch.yml
sudo grep -n 'initial_master_nodes' /etc/elasticsearch/elasticsearch.yml
```

```text
74:#cluster.initial_master_nodes: ["node-1", "node-2"]
109:#cluster.initial_master_nodes: ["student-1.europe-west2-c.c.<proje>.internal"]
```

Ayar yalnız açılışta okunur; değişiklik için servisi yeniden başlatmak gerekmez.

### 5. Bir node'u durdurmak: cluster çalışmaya devam eder mi?

Üç primary ve birer replica'lı bir index açın, document yazın ve shard'ların node'lara dağılımına bakın:

```bash
. scripts/ortam.sh
es -X PUT 'https://127.0.0.1:9200/paket-urunler' -H 'Content-Type: application/json' \
  -d '{"settings": {"number_of_shards": 3, "number_of_replicas": 1}}'; echo
for i in 1 2 3 4 5 6; do es -X POST "https://127.0.0.1:9200/paket-urunler/_doc/$i" -H 'Content-Type: application/json' -d "{\"ad\": \"urun-$i\"}" -o /dev/null; done
es 'https://127.0.0.1:9200/paket-urunler/_refresh' -o /dev/null
es 'https://127.0.0.1:9200/_cluster/health/paket-urunler?wait_for_status=green&timeout=60s&filter_path=status'; echo
es 'https://127.0.0.1:9200/_cat/shards/paket-urunler?v&h=shard,prirep,state,node&s=shard,prirep'
```

```text
{"acknowledged":true,"shards_acknowledged":true,"index":"paket-urunler"}
{"status":"green"}
shard prirep state   node
0     p      STARTED student-3.europe-west2-c.c.<proje>.internal
0     r      STARTED student-2.europe-west2-c.c.<proje>.internal
1     p      STARTED student-1.europe-west2-c.c.<proje>.internal
1     r      STARTED student-3.europe-west2-c.c.<proje>.internal
2     p      STARTED student-2.europe-west2-c.c.<proje>.internal
2     r      STARTED student-1.europe-west2-c.c.<proje>.internal
```

Node-3'ün servisini durdurun. Veri hâlâ okunur, cluster replica eksikliği yüzünden yellow olur:

```bash
. scripts/ortam.sh
n3 'sudo systemctl stop elasticsearch; systemctl is-active elasticsearch'
es 'https://127.0.0.1:9200/_cluster/health?wait_for_nodes=2&timeout=60s&filter_path=status,number_of_nodes'; echo
es 'https://127.0.0.1:9200/paket-urunler/_count?filter_path=count'; echo
es 'https://127.0.0.1:9200/_cat/nodes?h=name,master'
```

```text
inactive
{"status":"yellow","number_of_nodes":2}
{"count":6}
student-2.europe-west2-c.c.<proje>.internal -
student-1.europe-west2-c.c.<proje>.internal *
```

Node-3 master ise kalan iki node yeni bir master seçer; seçim saniyeler sürer. Node-3'ü geri başlatın ve green'e
dönüşü bekleyin:

```bash
. scripts/ortam.sh
n3 'sudo systemctl start elasticsearch; systemctl is-active elasticsearch'
es 'https://127.0.0.1:9200/_cluster/health?wait_for_status=green&wait_for_nodes=3&timeout=120s&filter_path=status,number_of_nodes'; echo
```

```text
active
{"status":"green","number_of_nodes":3}
```

---

## Doğrulama

Cluster'ın son durumu: üç node, green, üç oy ve TLS'li transport. Node'lar arası bağlantının TLS olduğu
sertifika üzerinden görülür:

```bash
. scripts/ortam.sh
es 'https://127.0.0.1:9200/_cluster/health?filter_path=status,number_of_nodes'; echo
echo | openssl s_client -connect "$NODE2:9300" 2>/dev/null | grep -E '^(subject|issuer)='
```

```text
{"status":"green","number_of_nodes":3}
subject=CN = student-1.europe-west2-c.c.<proje>.internal
issuer=CN = Elasticsearch security auto-configuration transport CA
```

`subject` node-1'in adıdır: paketin ürettiği transport sertifikası token ile node-2 ve node-3'e kopyalanır, üç node aynı sertifikayı sunar. `verification_mode: certificate` yalnız zincire bakar, ada bakmaz; `issuer` paketin ürettiği transport CA'dır.

<details>
<summary><strong>Servis açılmazsa nereye bakılır?</strong></summary>

<!-- runner:skip -->
```bash
sudo systemctl status elasticsearch --no-pager
sudo journalctl -u elasticsearch -n 50 --no-pager
sudo tail -n 60 /var/log/elasticsearch/elasticsearch.log
sudo ss -tlnp | grep -E '9200|9300'
```

Sık nedenler: node-2/3 token'dan önce bir kez başlatıldı (kendi cluster'ını kurdu: `teardown.sh` ve baştan), node-1'de
`transport.host` açılmadı (token komutu bağlanamaz), sunucular arası 9300 kapalı, token süresi geçti.

</details>

---

## Temizlik

Üç node'da Elasticsearch paketini, verisini (`/var/lib/elasticsearch`), ayarlarını ve sertifikalarını siler.
`~/adv10.env`, SSH anahtarı ve indirilen depo tanımı kalır. Yalnız bu lab için açılmış VM'lerde çalıştırın:

```bash
./teardown.sh
```

```text
student-1: paket yok
student-2: paket yok
student-3: paket yok
```

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

---

İleri labların sonuncusu. Ana sayfa: **[Elasticsearch, Logstash ve Kibana lab listesi](../../../README.md)**
