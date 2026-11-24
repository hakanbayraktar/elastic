# LAB-22 — Index Yaşam Döngüsü: Template, Data Stream ve ILM ile Veriyi Kendiliğinden Yönetmek

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Kibana Dev Tools, component ve index template, data stream, ILM, `_ilm/explain` | 9200 / 5601 — LAB-01 ana cluster'ı |

---

## Bu lab ne öğretiyor?

Log her gün büyür. Tek bir index'e yazılırsa shard'ı büyür, eski veri silinemez (document document silmek pahalıdır)
ve disk dolar. Çözüm, veriyi zamanla yeni index'lere bölmek ve eski index'i bütün olarak silmektir. Bu labda:

- Şablonlarla bir data stream kuracağız.
- ILM politikasıyla rollover, warm ve delete fazlarını dakikalar içinde tetikleyeceğiz.
- Eski verinin kendiliğinden silinişini son duruma kadar izleyeceğiz.
- Politikayı ve data stream'i Kibana arayüzünde de göreceğiz.

![Template, data stream ve ILM: hot, warm, delete](../../assets/infographics/31-ilm-yasam-dongusu.png)

---

## Ön Koşullar

- LAB-01 ana cluster'ı çalışıyor. LAB-01'i atladıysanız onun Adım 1-2'sini çalıştırın.
- Lab yaklaşık 5 dakika boyunca ILM'in kontrol aralığını 10 saniyeye indirir (Adım 2); temizlik varsayılana
  döndürür.

```bash
cd ~/elastic/labs/LAB-22-index-yasam-dongusu-ilm
```

Kibana adresini sunucuda hesaplayın:

```bash
IP=$(curl -s https://api.ipify.org); H=$(hostname -s)
echo "Kibana: http://$IP:5601   https://$H-kibana.devopsatolyesi.com"
```

Beklenen çıktı:

```text
Kibana: http://<IP>:5601   https://<host>-kibana.devopsatolyesi.com
```

---

## Kavramlar: dört parça

- **Component template:** tekrar kullanılan ayar ya da mapping parçası; burada `ilm-ayarlar` ve `ilm-mappings`.
- **Index template:** hangi ada hangi parçaların uygulanacağı ve data stream olup olmadığı; burada `ilm-uygulama*`.
- **Data stream:** tek bir yazma adı; arkasında zamanla çoğalan gizli index'ler (`.ds-…`) vardır; burada `ilm-uygulama`.
- **ILM politikası:** index'in yaşına ya da boyutuna göre ne yapılacağı; burada `ilm-politika`.

Data stream'e yalnız document eklenir (`create`). Yazma hep en yeni arka plan index'ine gider; eski index'ler
okunur ve sonunda silinir.

---

## Adım Adım Uygulama Rehberi

Bu labdaki `http` blokları **Kibana › Dev Tools**'a, `bash` blokları terminale yapıştırılır.

### 1. Şablonları kurun

**Soru: Yeni açılan her index'e aynı ayar nasıl verilir?**

Ayarlar ve mapping iki ayrı component template'tir; başka şablonlar da aynı parçaları kullanabilir:

```http
PUT /_component_template/ilm-ayarlar
{ "template": { "settings": { "number_of_shards": 1, "number_of_replicas": 0, "index.lifecycle.name": "ilm-politika" } } }
```

```http
PUT /_component_template/ilm-mappings
{
  "template": { "mappings": { "properties": {
    "@timestamp": { "type": "date" }, "servis": { "type": "keyword" }, "seviye": { "type": "keyword" },
    "sure_ms": { "type": "long" }, "mesaj": { "type": "text" } } } }
}
```

Index template bu iki parçayı birleştirir ve `data_stream` satırıyla bu adın bir data stream olacağını söyler:

```http
PUT /_index_template/ilm-uygulama
{ "index_patterns": ["ilm-uygulama*"], "data_stream": {}, "composed_of": ["ilm-ayarlar", "ilm-mappings"], "priority": 200 }
```

Index açmadan, bu ada hangi ayarların uygulanacağını görün:

```http
POST /_index_template/_simulate_index/ilm-uygulama?filter_path=template.settings.index.lifecycle,template.settings.index.number_of_replicas,template.mappings.properties.servis
```

```json
{"template":{"settings":{"index":{"lifecycle":{"name":"ilm-politika"},"number_of_replicas":"0"}},"mappings":{"properties":{"servis":{"type":"keyword"}}}}}
```

`priority: 200`, yerleşik `logs-*-*` gibi şablonlarla çakışmada bizimkinin seçilmesini sağlar.

### 2. ILM politikası

**Soru: Bir index ne zaman bölünsün, ne zaman silinsin?**

```http
PUT /_ilm/policy/ilm-politika
{
  "policy": { "phases": {
    "hot":    { "actions": { "rollover": { "max_docs": 100 } } },
    "warm":   { "min_age": "1m", "actions": { "readonly": {}, "set_priority": { "priority": 50 } } },
    "delete": { "min_age": "3m", "actions": { "delete": {} } }
  } }
}
```

- `hot` / `rollover`: yazılan index 100 document'e ulaşınca yeni bir arka plan index'i açılır. Üretimde
  `max_age: 1d` ya da `max_primary_shard_size: 50gb` gibi değerler kullanılır.
- `warm`, `min_age: 1m`: rollover'dan 1 dakika sonra index salt okunur olur, önceliği düşer. Üretimde 7 gün gibi.
- `delete`, `min_age: 3m`: rollover'dan 3 dakika sonra index bütün olarak silinir. Üretimde saklama süresi
  (30, 90 gün).

ILM index'leri varsayılan olarak 10 dakikada bir kontrol eder. Fazları dakikalar içinde görmek için bu aralığı
10 saniyeye indiriyoruz; bu ayar cluster genelindedir ve bütün politikaları etkiler, temizlik geri alır:

```http
PUT /_cluster/settings
{ "persistent": { "indices.lifecycle.poll_interval": "10s" } }
```

### 3. Data stream'e yazın

**Soru: Uygulama hangi ada yazar, veri nereye gider?**

150 olay gönderiyoruz. Data stream ilk document'le kendiliğinden açılır; işlem türü `create`'tir:

```bash
head -2 sample-data/olaylar-1.ndjson
curl -s -u elastic:'DevOps2026!' -H 'Content-Type: application/x-ndjson' -X POST \
  'http://127.0.0.1:9200/ilm-uygulama/_bulk?refresh=true&filter_path=errors' --data-binary @sample-data/olaylar-1.ndjson; echo
```

Beklenen çıktı:

```text
{"create": {}}
{"@timestamp": "2026-11-21T08:00:00Z", "servis": "odeme", "seviye": "info", "sure_ms": 20, "mesaj": "istek 1 tamamlandi"}
{"errors":false}
```

```http
GET /_data_stream/ilm-uygulama?filter_path=data_streams.name,data_streams.generation,data_streams.indices.index_name,data_streams.ilm_policy
```

```json
{"data_streams":[{"name":"ilm-uygulama","indices":[{"index_name":".ds-ilm-uygulama-2026.11.21-000001"}],"generation":1,"ilm_policy":"ilm-politika"}]}
```

Document'ler `ilm-uygulama` adına yazıldı ama gerçekte `.ds-ilm-uygulama-<tarih>-000001` index'inde duruyor. Addaki
tarih index'in açıldığı gündür; sizde labı yaptığınız gün görünür.

### 4. Rollover: yeni arka plan index'i

**Soru: Index dolunca yazma nereye geçer?**

İlk index'te 150 document var, eşik 100. ILM bir sonraki kontrolde (en çok birkaç kez 10 saniye) rollover yapar:

```bash
timeout 300 bash -c 'until [ "$(curl -s -u elastic:"DevOps2026!" http://127.0.0.1:9200/_data_stream/ilm-uygulama | jq .data_streams[0].generation)" = 2 ]; do printf .; sleep 5; done'; echo
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/_cat/indices/.ds-ilm-uygulama-*?h=index,docs.count&s=index'
```

Beklenen çıktı:

```text
..
.ds-ilm-uygulama-2026.11.21-000001 150
.ds-ilm-uygulama-2026.11.21-000002   0
```

Yeni gelen document'ler artık `000002`'ye yazılır; `000001` kapandı. Rollover'dan sonra index'in yaşı sayılmaya
başlar, warm ve delete fazlarının `min_age`'i bu andan itibaren işler.

<details>
<summary><strong>Politika ve data stream Kibana'da nerede?</strong></summary>

Politikayı Dev Tools'la kurduk; Kibana'da aynı politika ve data stream şöyle görünür (değiştirmeden bakın):

1. Menü, **Stack Management**, soldaki listede **Data** altında **Index Lifecycle Policies** (1):

![Stack Management: 1 Index Lifecycle Policies](../../assets/screenshots/LAB-22/04a-ilm-menu.png)

2. Tablonun arama kutusuna (1) `ilm-politika` yazın, politikanın adına (2) tıklayın:

![ILM listesi: 1 arama, 2 ilm-politika](../../assets/screenshots/LAB-22/04b-ilm-listesi.png)

3. Sağdaki panelde fazlar soldan sağa sıralıdır: **Hot phase** (1) rollover'ı (Maximum documents 100), **Warm phase**
   (2) `1m` sonra salt okunur ve öncelik 50'yi, çöp kutusu simgesi (3) **Delete phase**'i gösterir. **Close** ile kapatın:

![ILM fazları: 1 hot, 2 warm, 3 delete](../../assets/screenshots/LAB-22/04c-ilm-fazlar.png)

4. Soldaki listede **Index Management** (1):

![Stack Management: 1 Index Management](../../assets/screenshots/LAB-22/04e-index-management.png)

5. **Data Streams** sekmesi (1), arama kutusuna (2) `ilm-uygulama`. Satırda (3) data stream'in sağlığı, arka plan index
   sayısı (**Indices**) ve bağlı politika `ilm-politika` görünür; sayı ILM'in o anki adımına göre 1 ya da 2'dir:

![Data Streams: 1 sekme, 2 arama, 3 ilm-uygulama satırı](../../assets/screenshots/LAB-22/04f-data-stream.png)

</details>

### 5. warm: eski index salt okunur olur

**Soru: Eski index'e hâlâ yazılabilir mi?**

Eski index'in warm fazını bitirmesini bekleyin (rollover'dan yaklaşık 1–2 dakika sonra) ve ayarlarına bakın:

```bash
timeout 400 bash -c 'until curl -s -u elastic:"DevOps2026!" http://127.0.0.1:9200/ilm-uygulama/_ilm/explain | jq -e "[.indices[] | select(.phase==\"warm\" and .step==\"complete\")] | length == 1" >/dev/null; do printf .; sleep 5; done'; echo
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/ilm-uygulama/_ilm/explain?filter_path=indices.*.phase,indices.*.step' | jq -c '.indices | to_entries | map({index: .key[-6:], phase: .value.phase, step: .value.step})'
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/.ds-ilm-uygulama-*-000001/_settings?filter_path=*.settings.index.blocks.write,*.settings.index.priority' | jq -c '.[].settings.index'
```

Beklenen çıktı:

```text
..............
[{"index":"000001","phase":"warm","step":"complete"},{"index":"000002","phase":"hot","step":"check-rollover-ready"}]
{"blocks":{"write":"true"},"priority":"50"}
```

`blocks.write: true`: eski index artık yazmaya kapalı, okumaya açık. `priority: 50`: node yeniden başladığında
önce yüksek öncelikli (hot) index'ler kurtarılır.

### 6. delete: eski veri kendiliğinden silinir

**Soru: Saklama süresi dolan veri nasıl gider?**

Rollover'dan yaklaşık 3–4 dakika sonra eski index silinir. Data stream'de tek index kalana kadar bekleyin:

```bash
timeout 600 bash -c 'until [ "$(curl -s -u elastic:"DevOps2026!" http://127.0.0.1:9200/_data_stream/ilm-uygulama | jq ".data_streams[0].indices | length")" = 1 ]; do printf .; sleep 5; done'; echo
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/_data_stream/ilm-uygulama?filter_path=data_streams.indices.index_name' | jq -c .
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/ilm-uygulama/_count?filter_path=count'; echo
```

Beklenen çıktı:

```text
............................
{"data_streams":[{"indices":[{"index_name":".ds-ilm-uygulama-2026.11.21-000002"}]}]}
{"count":0}
```

Bu koşuda rollover ilk kontrolde (10 sn), warm yaklaşık 70 sn, silme yaklaşık 3,5 dk sonra gerçekleşti;
labın tamamı 4 dakikadan kısa sürdü.

150 olay `000001` ile birlikte silindi; tek tek document silinmedi, index bütün olarak gitti. Bu, büyük veride
`_delete_by_query`'den çok daha ucuzdur.

Saklama süresi diski doğrudan belirler: **günlük veri × saklama günü × (1 + replica sayısı)**. Günde 20 GB
log, 30 gün saklama ve 1 replica yaklaşık 20 × 30 × 2 = 1,2 TB eder; saklamayı 7 güne indirmek bunu 280 GB'a
düşürür. Saklama süresini iş ihtiyacı belirler, ILM'in `delete` fazı uygular.

<details>
<summary><strong>Silmeden önce snapshot beklemek: <code>wait_for_snapshot</code></strong></summary>

Silinecek verinin bir yedeği olması gerekiyorsa `delete` fazının başına `wait_for_snapshot` eklenir. ILM,
belirtilen SLM politikası index'in snapshot'ını alana kadar silmeyi bekler. SLM politikası ve snapshot deposu
önceden var olmalıdır:

```json
"delete": {
  "min_age": "30d",
  "actions": {
    "wait_for_snapshot": { "policy": "gunluk-snapshot" },
    "delete": {}
  }
}
```

</details>

---

## Temizlik

Yalnız bu labın data stream'ini (arka plan index'leriyle), şablonlarını ve politikasını siler; ILM kontrol
aralığını varsayılana (10 dakika) döndürür. Ana cluster'daki diğer verilere dokunmaz:

```bash
./teardown.sh
```

Beklenen çıktı:

```text
data stream ilm-uygulama -> 200
index template ilm-uygulama -> 200
component template ilm-ayarlar -> 200
component template ilm-mappings -> 200
ILM politikasi ilm-politika -> 200
poll_interval varsayilan -> true
```

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

---

Sonraki lab: **[LAB-23 — Cluster Operasyonu: Snapshot, SLM, Geri Yükleme ve Node Boşaltma](../LAB-23-cluster-operasyonu-snapshot/README.md)**
