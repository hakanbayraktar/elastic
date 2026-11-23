# ADV-04 — S3 / MinIO ile Snapshot, Restore ve Searchable Snapshot: Cluster Dışına Yedek

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| MinIO (S3 uyumlu), `mc`, Elasticsearch keystore, snapshot/restore, searchable snapshot, `curl`, `jq` | 9200 / 5601 (ana cluster), `127.0.0.1:9000` (MinIO S3 API), `9191` (MinIO konsolu, `minio` alt alan adı) |

---

## Bu lab ne öğretiyor?

Bir index yanlışlıkla silindiğinde replica işe yaramaz: silme replica'ya da uygulanır. Cluster'ın kendi diskindeki
bir kopya da yetmez; disk ya da sunucu gidince o kopya da gider. Geri dönülebilecek yer **cluster'ın dışındaki**
bir depodur.

Bu labda S3 uyumlu bir nesne deposunu (MinIO) snapshot repository olarak bağlayacak, 1000 bankacılık işleminin
snapshot'ını alacak, index'i kasten silip geri yükleyecek ve aynı snapshot'ı geri yüklemeden doğrudan index olarak
bağlayacağız (**searchable snapshot**).

```mermaid
flowchart LR
    A["Elasticsearch Node<br/>(banking-transactions)"] -->|"1. Snapshot PUT"| B["Snapshot Repository<br/>(type: s3)"]
    B -->|"2. Chunked Segments"| C["MinIO Object Storage<br/>(Bucket: elastic-backups)"]
    D["Kaza / Ransomware<br/>(DELETE Index)"] -.->|"3. Veri Kaybı"| A
    C -->|"4. In-Place Restore"| A
    C -->|"5. Forensic Restore<br/>(rename_pattern)"| E["Restored Index<br/>(restored_banking-transactions)"]
```

Diyagramdaki adlar eski sürümden kalmadır; bu labda index `s3-islemler`, repository `s3-yedek`'tir.

---

## Ön Koşullar

- LAB-01 ana cluster'ı çalışıyor ve trial lisans açık (searchable snapshot ücretli özelliktir). Önceki labları
  atladıysanız da lab çalışır; veri bu labın kendi dosyasından gelir.
- `127.0.0.1:9000` ve `9191` boş olmalı.

```bash
cd ~/elastic/labs/advanced/ADV-04-snapshot-restore-minio-s3
```


---

## Kavramlar: hangi kopya neye karşı korur?

| Kopya | Neye karşı korur | Neye karşı korumaz |
|---|---|---|
| Replica shard | Node kaybı | Silme, yanlış güncelleme (replica'ya da uygulanır) |
| `fs` snapshot repository | Silme | Diskin ya da paylaşımlı dosya sisteminin kaybı |
| `s3` snapshot repository | Silme, cluster ve disk kaybı | Bucket'ın kendisinin silinmesi (sürümleme ve kilit ayrı konu) |

**Searchable snapshot**, snapshot'ı geri yüklemeden index olarak bağlar (`_mount`). `full_copy` modunda veri yerel
diske kopyalanır ama replica gerekmez: shard kaybolursa snapshot'tan yeniden kurulur. `shared_cache` modunda veri
diske kopyalanmaz, arama sırasında S3'ten okunur; ayrılmış bir frozen node ister, tek node'lu ana cluster'da
denenmez.

---

## Config dosyaları: hangi satır ne işe yarıyor?

`../../LAB-01-kurulum-kontrol/starter/docker-compose.yml` (ana cluster):

```yaml
      - s3.client.default.endpoint=elastic-minio:9000
      - s3.client.default.protocol=http
      - s3.client.default.path_style_access=true
```

- Bunlar **statik** node ayarlarıdır, yalnız node başlarken okunur. Ana cluster bunlarla kurulduğu için bu lab
  node'u yeniden başlatmaz.
- `endpoint`: `elastic-minio`, MinIO container'ının Docker ağındaki adıdır.
- `path_style_access=true`: istek `http://elastic-minio:9000/elastic-backups/...` biçiminde gider. Kapalı olursa
  istemci `elastic-backups.elastic-minio` adını çözmeye çalışır ve `UnknownHostException` alır.

`docker-compose.minio.yml`: MinIO ana cluster'ın Docker ağına (`elastic-lab00_default`) katılır. S3 API
(`9000`) yalnız sunucuya açılır; konsol (`9191`) dışarıdan erişilir. Image digest ile sabitlenmiştir.

---

## Adım Adım Uygulama Rehberi

### 1. MinIO ve bucket

MinIO'yu başlatın, hazır olmasını bekleyin (birkaç saniye) ve snapshot'ların yazılacağı bucket'ı `mc` ile açın:

```bash
docker compose -f docker-compose.minio.yml up -d 2>&1 | grep -E "Started|Running"
timeout 60 bash -c 'until [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9000/minio/health/live)" = 200 ]; do printf .; sleep 2; done'; echo
docker run --rm --net elastic-lab00_default -e MC_HOST_minio=http://minioadmin:miniopassword2026@elastic-minio:9000 \
  cgr.dev/chainguard/minio-client@sha256:94433f625c8057d18c69675dbaa33da6e4864f084f9c44faf30d3eb8e3754e0b mb --ignore-existing minio/elastic-backups
```

Beklenen çıktı:

```text
 Container elastic-minio Started
.
Bucket created successfully `minio/elastic-backups`.
```

`MC_HOST_minio` değişkeni `mc`'ye adresi ve anahtarları tek satırda verir; ayrı bir yapılandırma dosyası gerekmez.
Konsol adresi (kullanıcı `minioadmin`, parola `miniopassword2026`):

```bash
IP=$(curl -s https://api.ipify.org); H=$(hostname -s)
echo "MinIO konsolu: http://$IP:9191   https://$H-minio.devopsatolyesi.com"
```

Beklenen çıktı:

```text
MinIO konsolu: http://<IP>:9191   https://<host>-minio.devopsatolyesi.com
```

### 2. Anahtarlar keystore'a, repository Elasticsearch'e

S3 anahtarları `elasticsearch.yml`'ye değil **keystore**'a yazılır. Bu anahtarlar yeniden yüklenebilir türdendir;
node'u yeniden başlatmak gerekmez:

```bash
echo minioadmin | docker exec -i elasticsearch-lab00 ./bin/elasticsearch-keystore add -f --stdin s3.client.default.access_key
echo miniopassword2026 | docker exec -i elasticsearch-lab00 ./bin/elasticsearch-keystore add -f --stdin s3.client.default.secret_key
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/_nodes/reload_secure_settings?filter_path=_nodes'; echo
```

```json
{"_nodes":{"total":1,"successful":1,"failed":0}}
```

Repository'yi kaydedin ve doğrulayın. Kibana › Dev Tools'a yapıştırın:

```http
PUT _snapshot/s3-yedek
{ "type": "s3", "settings": { "bucket": "elastic-backups", "client": "default", "compress": true } }
POST _snapshot/s3-yedek/_verify?filter_path=nodes.*.name
```

```json
{"acknowledged":true}
{"nodes":{"aht6XyPEQQ6ns3mBHH_ALA":{"name":"4f9d920003f7"}}}
```

`"client": "default"` repository'yi `s3.client.default.*` ayarlarına bağlar. Node kimliği ve adı sizde farklıdır. `_verify` node'un bucket'a yazıp
okuyabildiğini sınar; node listesi gelmiyorsa snapshot o node'un shard'larını yedekleyemez.

### 3. Veri ve snapshot

1000 işlemi yükleyin ve sayıyı ile toplam tutarı not edin; geri yüklemeden sonra aynı değerler aranacak:

```http
PUT s3-islemler
{ "settings": { "number_of_shards": 1, "number_of_replicas": 0 },
  "mappings": { "properties": { "transaction_id": { "type": "keyword" }, "account_id": { "type": "keyword" },
    "recipient_account": { "type": "keyword" }, "amount": { "type": "double" }, "currency": { "type": "keyword" },
    "channel": { "type": "keyword" }, "transaction_type": { "type": "keyword" }, "timestamp": { "type": "date" } } } }
```

```json
{"acknowledged":true,"shards_acknowledged":true,"index":"s3-islemler"}
```

```bash
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/s3-islemler/_bulk?refresh=true' \
  -H 'Content-Type: application/x-ndjson' --data-binary @sample-data/islemler.ndjson | jq -c '{errors, yazilan: (.items | length)}'
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/s3-islemler/_search?size=0&filter_path=hits.total.value,aggregations.toplam.value' \
  -H 'Content-Type: application/json' -d '{"track_total_hits": true, "aggs": {"toplam": {"sum": {"field": "amount"}}}}'; echo
```

```json
{"errors":false,"yazilan":1000}
{"hits":{"total":{"value":1000}},"aggregations":{"toplam":{"value":2.478873997E7}}}
```

Snapshot'ı alın ve bucket'a gerçekten nesne yazıldığını `mc` ile görün:

```bash
curl -s -u elastic:'DevOps2026!' -X PUT 'http://127.0.0.1:9200/_snapshot/s3-yedek/s3-snap-1?wait_for_completion=true' \
  -H 'Content-Type: application/json' -d '{"indices": "s3-islemler", "include_global_state": false}' | jq -c '.snapshot | {snapshot, state, shards}'
docker run --rm --net elastic-lab00_default -e MC_HOST_minio=http://minioadmin:miniopassword2026@elastic-minio:9000 \
  cgr.dev/chainguard/minio-client@sha256:94433f625c8057d18c69675dbaa33da6e4864f084f9c44faf30d3eb8e3754e0b ls --recursive minio/elastic-backups | wc -l
```

Beklenen çıktı:

```text
{"snapshot":"s3-snap-1","state":"SUCCESS","shards":{"total":1,"failed":0,"successful":1}}
9
```

Snapshot index'in segment dosyalarını ve meta verisini nesne olarak bucket'a yazdı. Aynı nesneleri konsolda
**Object Browser › elastic-backups** altında görebilirsiniz.

### 4. Felaket ve geri yükleme

Index'i silin, gittiğini görün, snapshot'tan aynı adla geri yükleyin ve sayıyla toplamı karşılaştırın:

```bash
curl -s -u elastic:'DevOps2026!' -X DELETE 'http://127.0.0.1:9200/s3-islemler'; echo
curl -s -o /dev/null -w 'silindikten sonra: %{http_code}\n' -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/s3-islemler/_count'
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/_snapshot/s3-yedek/s3-snap-1/_restore?wait_for_completion=true&filter_path=snapshot.indices,snapshot.shards' \
  -H 'Content-Type: application/json' -d '{"indices": "s3-islemler"}'; echo
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/s3-islemler/_search?size=0&filter_path=hits.total.value,aggregations.toplam.value' \
  -H 'Content-Type: application/json' -d '{"track_total_hits": true, "aggs": {"toplam": {"sum": {"field": "amount"}}}}'; echo
```

Beklenen çıktı:

```text
{"acknowledged":true}
silindikten sonra: 404
{"snapshot":{"indices":["s3-islemler"],"shards":{"total":1,"failed":0,"successful":1}}}
{"hits":{"total":{"value":1000}},"aggregations":{"toplam":{"value":2.478873997E7}}}
```

Önce ve sonra (`2.478873997E7` = 24.788.739,97): silmeden önce 1000 document ve aynı toplam, silindikten sonra `404`, geri yüklemeden sonra yine 1000
document ve aynı toplam. Snapshot'ı farklı adla açıp canlı index'e dokunmadan karşılaştırmak için restore isteğine
`rename_pattern` ve `rename_replacement` eklenir. Zamanlanmış snapshot için SLM politikasında `repository` olarak
`s3-yedek` verilir; politika yapısı `fs` repository ile aynıdır.

### 5. Searchable snapshot: geri yüklemeden index olarak bağlamak

Aynı snapshot'ı farklı adla bağlayın ve arayın:

```http
POST _snapshot/s3-yedek/s3-snap-1/_mount?wait_for_completion=true&filter_path=snapshot.indices,snapshot.shards
{ "index": "s3-islemler", "renamed_index": "s3-islemler-aranabilir", "index_settings": { "index.number_of_replicas": 0 } }
GET s3-islemler-aranabilir/_count?filter_path=count
GET s3-islemler-aranabilir/_settings?filter_path=*.settings.index.store.type,*.settings.index.store.snapshot.repository_name,*.settings.index.store.snapshot.snapshot_name
GET _cat/indices/s3-islemler*?v&h=index,docs.count,rep&s=index
```

Beklenen çıktı:

```text
{"snapshot":{"indices":["s3-islemler-aranabilir"],"shards":{"total":1,"failed":0,"successful":1}}}
{"count":1000}
{"s3-islemler-aranabilir":{"settings":{"index":{"store":{"type":"snapshot","snapshot":{"snapshot_name":"s3-snap-1","repository_name":"s3-yedek"}}}}}}
index                  docs.count rep
s3-islemler                  1000   0
s3-islemler-aranabilir       1000   0
```

Bağlanan index'in deposu `snapshot` türündedir ve hangi repository ile snapshot'tan geldiğini bilir. Replica'sı yoktur
ve gerekmez: kaybolursa S3'teki snapshot'tan yeniden kurulur. Bu modda (`full_copy`) veri yine yerel diske
kopyalanır; asıl disk tasarrufu `shared_cache` (frozen) modundadır.

---

## Temizlik

Yalnız bu labın iki index'ini, `s3-yedek` repository kaydını, ana cluster keystore'undaki `s3.client.default.*`
anahtarlarını ve MinIO'yu (container ve volume, bucket içeriğiyle) siler. Ana cluster'ın kendisine ve diğer labların
kaynaklarına dokunmaz:

```bash
./teardown.sh
```

Beklenen çıktı:

```text
index s3-islemler-aranabilir -> 200
index s3-islemler -> 200
repository s3-yedek -> 200
keystore s3.client.default.access_key -> silindi
keystore s3.client.default.secret_key -> silindi
reload_secure_settings -> 200
Container elastic-minio Removed
Volume minio-s3-lab_minio_data Removed
Network minio-s3-lab_default Removed
```

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

---

Sonraki lab: **[ADV-05 — Dense Vector, k-NN ve Hybrid Search (RRF): Kelime Uyuşmazlığına Karşı Vektör](../ADV-05-semantic-search-knn-rrf/README.md)**
