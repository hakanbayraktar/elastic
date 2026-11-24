# LAB-07 — Aggregation ve Lens Panosu: Veriden Rapor Çıkarmak

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Kibana Dev Tools, Lens, Dashboard | 9200 (Elasticsearch), 5601 (Kibana) — LAB-01 ana cluster'ı |

---

## Bu lab ne öğretiyor?

- Tek sayılar: ciro, ortalama sepet, farklı müşteri (metric aggregation)
- Gruplamak: kategori ve gün bazında (bucket ve iç içe aggregation)
- E-ticaret filtre paneli: `post_filter`
- Lens ile grafik ve pano
- Gerçek zamanlı izleme; pano için veri hazırlama (runtime field)

---

## Ön Koşullar

- LAB-01 ana cluster'ı çalışıyor.
- LAB-04'teki örnek e-ticaret verisi yüklü (`kibana_sample_data_ecommerce`, 4675 sipariş).
  LAB-04'ü atladıysanız onun Adım 1'ini yapın.

```bash
cd ~/elastic/labs/LAB-07-aggregation-lens
```

---

## Kavramlar

- **aggregation:** document'leri tek tek döndürmeden hesap yapar: kaç tane, toplam, hangi grupta
- **metric:** bir sayı hesaplar: `sum` (toplam), `avg` (ortalama), `cardinality` (farklı değer sayısı)
- **bucket:** document'leri gruplara ayırır: `terms` (değere göre), `date_histogram` (zamana göre)
- **iç içe:** bucket'ın içine metric konur: "her kategori için ortalama sepet"
- **hangi field?** `keyword`, sayı, tarih; `text` field'da çalışmaz (metin token'lara bölünmüştür)

---

## Adım Adım Uygulama Rehberi

Bu labda `http` bloklarını Kibana › Dev Tools'a, `bash` bloklarını terminale yapıştırın.

### 1. Tek sayılar: metric aggregation

**Soru: Toplam ciro, ortalama sepet ve kaç farklı müşteri var?** `size: 0` document listesini döndürmez; yalnız hesap
sonucu gelir:

```http
GET /kibana_sample_data_ecommerce/_search?filter_path=aggregations
{
  "size": 0,
  "aggs": {
    "ciro":      { "sum":         { "field": "taxful_total_price" } },
    "ort_sepet": { "avg":         { "field": "taxful_total_price" } },
    "musteri":   { "cardinality": { "field": "customer_id" } }
  }
}
```

```json
{
  "aggregations": {
    "ciro": {
      "value": 350884.12890625
    },
    "ort_sepet": {
      "value": 75.05542864304813
    },
    "musteri": {
      "value": 46
    }
  }
}
```

- **Ad:** her aggregation'a bir ad verilir (`ciro`, `ort_sepet`, `musteri`); yanıt aynı adlarla gelir.
- **`cardinality`:** yaklaşık sayar; milyonlarca değerde bellek harcamamak için az hata payı kabul eder, küçük veride kesindir.

### 2. Gruplamak: bucket ve iç içe aggregation

**Soru: Hangi kategori en çok sipariş alıyor, sepetleri ne kadar?** En çok sipariş alan üç kategori ve ortalama sepetleri:

```http
GET /kibana_sample_data_ecommerce/_search?filter_path=aggregations
{
  "size": 0,
  "aggs": {
    "kategori": {
      "terms": { "field": "category.keyword", "size": 3 },
      "aggs": {
        "ort_sepet": { "avg": { "field": "taxful_total_price" } }
      }
    }
  }
}
```

```json
{
  "aggregations": {
    "kategori": {
      "doc_count_error_upper_bound": 0,
      "sum_other_doc_count": 2346,
      "buckets": [
        {
          "key": "Men's Clothing",
          "doc_count": 2024,
          "ort_sepet": {
            "value": 73.81122043292984
          }
        },
        {
          "key": "Women's Clothing",
          "doc_count": 1903,
          "ort_sepet": {
            "value": 70.99312352207042
          }
        },
        {
          "key": "Women's Shoes",
          "doc_count": 1136,
          "ort_sepet": {
            "value": 92.8513836927817
          }
        }
      ]
    }
  }
}
```

- **`terms`:** değere göre gruplar, en kalabalık `size` grubu döndürür; tam değer için `category.keyword`.
- **`doc_count`:** gruptaki sipariş sayısı; içteki `ort_sepet` yalnız o grubun document'leriyle hesaplanır.
- **`sum_other_doc_count`:** listeye girmeyen gruplardaki document sayısı.
- **`doc_count_error_upper_bound`:** çok shard'da sayımın en fazla ne kadar eksik olabileceği; tek shard'da 0.

**Zamana göre: `date_histogram`.** Son yedi günün günlük sipariş sayısı ve cirosu:

```http
GET /kibana_sample_data_ecommerce/_search?filter_path=aggregations.gun.buckets.key_as_string,aggregations.gun.buckets.doc_count
{
  "size": 0,
  "query": { "range": { "order_date": { "gte": "now-7d/d", "lt": "now/d" } } },
  "aggs": {
    "gun": {
      "date_histogram": { "field": "order_date", "calendar_interval": "day", "format": "yyyy-MM-dd" }
    }
  }
}
```

```json
{
  "aggregations": {
    "gun": {
      "buckets": [
        {
          "key_as_string": "2026-11-14",
          "doc_count": 141
        },
        {
          "key_as_string": "2026-11-15",
          "doc_count": 151
        },
        {
          "key_as_string": "2026-11-16",
          "doc_count": 143
        },
        {
          "key_as_string": "2026-11-17",
          "doc_count": 143
        },
        {
          "key_as_string": "2026-11-18",
          "doc_count": 142
        },
        {
          "key_as_string": "2026-11-19",
          "doc_count": 161
        },
        {
          "key_as_string": "2026-11-20",
          "doc_count": 144
        }
      ]
    }
  }
}
```

- **Sayılar sizde farklı:** örnek verinin tarihleri yükleme gününe göre kayar; gün başına 140-160 sipariş görürsünüz.
- **`now-7d/d`:** "yedi gün önce, günün başına yuvarlanmış".

### 3. Filtre paneli: seçilen marka listeyi daraltmasın

**Soru: Kullanıcı bir marka seçince marka listesi neden daralmamalı?** "shirt" arayan kullanıcı soldan bir marka
seçer: sonuçlar daralmalı, ama marka listesi bütün markaları göstermeye devam etmeli; yoksa başka markayı seçemez.

**`post_filter`:** aggregation hesaplandıktan **sonra** yalnız sonuç listesine uygulanır:

```http
GET /kibana_sample_data_ecommerce/_search?filter_path=hits.total.value,aggregations.marka.buckets
{
  "size": 0,
  "query":       { "match": { "products.product_name": "shirt" } },
  "post_filter": { "term":  { "manufacturer.keyword": "Elitelligence" } },
  "aggs": {
    "marka": { "terms": { "field": "manufacturer.keyword", "size": 4 } }
  }
}
```

```json
{
  "hits": {
    "total": {
      "value": 503
    }
  },
  "aggregations": {
    "marka": {
      "buckets": [
        {
          "key": "Elitelligence",
          "doc_count": 503
        },
        {
          "key": "Low Tide Media",
          "doc_count": 500
        },
        {
          "key": "Oceanavigations",
          "doc_count": 330
        },
        {
          "key": "Pyramidustries",
          "doc_count": 161
        }
      ]
    }
  }
}
```

- **`hits.total.value` (503):** yalnız seçilen markanın shirt siparişleri; sonuç listesi daraldı.
- **`marka`:** "shirt" arayan bütün siparişlerde markalar; seçim listeyi daraltmadı. Uygulama bu
  sayıları filtre panelinde, sonuçları ortada gösterir.
- **`query` içinde olsaydı:** marka listesinde yalnız Elitelligence kalırdı.

### 4. Lens ile pano

**Soru: Aynı soruyu kod yazmadan grafiğe ve panoya nasıl çeviririz?** Lens ile, tıklayarak.

1. Discover'da `Kibana Sample Data eCommerce` data view'ını ve **Last 7 days** zaman aralığını seçin.
   Varsayılan **Last 15 minutes** aralığında grafik boş kalır.
2. Soldaki field listesinde `category` field'ına (1) tıklayın, açılan pencerede **Visualize** (2):

![Discover field penceresi: 1 category field'ı, 2 Visualize](../../assets/screenshots/LAB-07/02-field-visualize.png)

3. Lens, kategori başına sipariş sayısını bar grafiği olarak açar (3). Yatay eksen kategoriler
   (`Top values of category.keyword`), dikey eksen kayıt sayısıdır. Sağ üstten **Save** (4):

![Lens: 3 kategori bazında bar grafiği, 4 Save](../../assets/screenshots/LAB-07/03-lens-bar.png)

   Sağ paneldeki **Breakdown** (a) kutusuna tıklayıp `customer_gender` seçin: her çubuk cinsiyete
   göre iki renge bölünür (b). Breakdown, grafiğe ikinci bir gruplama ekler:

![Lens breakdown: a Breakdown kutusu, b cinsiyete bölünmüş çubuklar](../../assets/screenshots/LAB-07/03b-lens-breakdown.png)

4. Title alanına `Kategori bazında sipariş` (5) yazın, **Add to dashboard** altında **New** (6)
   seçin, **Save and go to dashboard** (7):

![Lens kaydetme: 5 başlık, 6 New dashboard, 7 Save and go to dashboard](../../assets/screenshots/LAB-07/04-lens-save.png)

5. Pano açılır ve grafik ilk panel olarak eklenir. Sağ üstteki **Save** (8) ile panoya
   `Satış özeti` adını verip kaydedin:

![Pano: 8 Save, 9 eklenen panel](../../assets/screenshots/LAB-07/05-dashboard.png)

- **Pano:** **Dashboards** listesinden açılır; zaman aralığı değişince bütün paneller birlikte güncellenir.
- **Başka panel:** dikey eksene `taxful_total_price` sürükleyip **Sum** seçmek "kategori bazında ciro" grafiğini verir.

<details>
<summary><strong>Panoya üç panel daha: günlük ciro, ortalama sepet, cinsiyete göre sipariş</strong></summary>

Tek grafik tek soruya cevap verir; panonun değeri birkaç soruyu yan yana görmektir. "Satış özeti" panosuna üç panel
ekleyin. Her panel için:

1. **Dashboards › Satış özeti**'ni açın; zaman aralığı **Last 7 days**
2. **Edit**, sonra **Add › Visualization**: Lens, örnek verinin data view'ıyla açılır

**a) Günlük ciro: çizgi grafik** (soru: ciro zamanla nasıl değişiyor?)

1. Grafik türü (1): **Line**
2. **Horizontal axis** (2): **Date histogram**, field `order_date`
3. **Vertical axis** (3): **Sum**, field `taxful_total_price`
4. **Save to library** (4): başlık `Günlük ciro`, **Save**; panoya dönülür

![Lens çizgi grafik: 1 grafik türü, 2 yatay eksen, 3 dikey eksen, 4 Save to library](../../assets/screenshots/LAB-07/08-lens-gunluk-ciro.png)

**b) Ortalama sepet: tek sayı** (soru: bir sipariş ortalama ne kadar?)

1. Grafik türü (1): **Metric**
2. **Primary metric** (2): **Average**, field `taxful_total_price`
3. **Save to library** (3): başlık `Ortalama sepet`, **Save**

![Lens metric: 1 grafik türü, 2 primary metric, 3 Save to library](../../assets/screenshots/LAB-07/09-lens-ortalama-sepet.png)

**c) Cinsiyete göre sipariş: pasta** (soru: siparişlerin yüzde kaçı kimden?)

1. Grafik türü (1): **Pie**
2. **Slice by** (2): **Top values**, field `customer_gender`
3. **Metric** (3): **Count**
4. **Save to library** (4): başlık `Cinsiyete göre sipariş`, **Save**

![Lens pasta: 1 grafik türü, 2 slice by, 3 metric, 4 Save to library](../../assets/screenshots/LAB-07/10-lens-cinsiyet-pasta.png)

Sağ üstten **Save** ile panoyu kaydedin. Pano dört panelle açılır; zaman aralığını değiştirince hepsi birlikte güncellenir:

![Satış özeti panosu: dört panel](../../assets/screenshots/LAB-07/11-pano-dort-panel.png)

</details>

### 5. Gerçek zamanlı: canlı sipariş akışı

**Soru: "Gerçek zamanlı" ne kadar gerçek zamanlı?** Yazılan document ancak **refresh** ile (varsayılan saniyede bir)
aramaya girer. Canlı veri için bir index açıp bunu görün:

```bash
curl -s -u elastic:'DevOps2026!' -X PUT 'http://127.0.0.1:9200/analiz-canli' -H 'Content-Type: application/json' -d '{
  "settings": { "number_of_shards": 1, "number_of_replicas": 0, "refresh_interval": "1s" },
  "mappings": { "properties": { "@timestamp": { "type": "date" }, "kategori": { "type": "keyword" }, "tutar": { "type": "float" } } } }' -o /dev/null
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/analiz-canli/_doc' -H 'Content-Type: application/json' \
  -d '{"@timestamp": "'"$(date -u +%FT%TZ)"'", "kategori": "Giyim", "tutar": 50}' -o /dev/null
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/analiz-canli/_count?filter_path=count'; echo
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/analiz-canli/_doc?refresh=wait_for&filter_path=result' -H 'Content-Type: application/json' \
  -d '{"@timestamp": "'"$(date -u +%FT%TZ)"'", "kategori": "Giyim", "tutar": 75}'; echo
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/analiz-canli/_count?filter_path=count'; echo
```

Beklenen çıktı:

```text
{"count":0}
{"result":"created"}
{"count":2}
```

- **`_count` 0:** ilk document yazıldı ama refresh henüz olmadı.
- **`refresh=wait_for`:** document aramaya girene kadar bekler; ardından iki document de görünür.
- **Sonuç:** "gerçek zamanlı" yaklaşık 1 saniye içinde demektir.

**Canlı akışı başlatın:** son 15 dakika saniyede bir siparişle dolar, 10 dakika sürecek akış arka planda başlar:

```bash
python3 scripts/canli_siparis.py gecmis
nohup python3 scripts/canli_siparis.py canli 600 > /dev/null 2>&1 &
```

Beklenen çıktı:

```text
gecmis 15 dakika: 900 siparis, hata: False
```

**Son 15 dakikada dakika başına kaç sipariş geldi?**

```bash
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/analiz-canli/_search?size=0' -H 'Content-Type: application/json' -d '{
  "query": { "range": { "@timestamp": { "gte": "now-15m" } } },
  "aggs": { "dakika": { "date_histogram": { "field": "@timestamp", "fixed_interval": "1m" } } } }' | jq -c '[.aggregations.dakika.buckets[].doc_count]'
```

Beklenen çıktı:

```text
[23,60,60,60,60,60,60,60,60,60,60,60,60,60,60,37]
```

- **Her dakika 60:** ilk ve son bucket yarımdır; 15 dakikalık pencere dakika sınırına denk gelmez.
- **Tekrar çalıştırın:** canlı akış son bucket'ı büyütür (sayılar sizde farklıdır).

**Kibana'da izlemek için data view açın:**

```http
POST kbn:/api/data_views/data_view
{ "data_view": { "id": "analiz-canli", "title": "analiz-canli", "name": "Canlı siparişler", "timeFieldName": "@timestamp" } }
```

1. Discover'da `Canlı siparişler` data view'ı, zaman aralığı **Last 15 minutes** (1)
2. Zaman kutusunu yeniden açın, menünün altındaki dişli simgesine tıklayın (**Settings**, 2). Düğmenin yazısı yoktur:

![Zaman menüsü: 2 Settings (dişli simgesi)](../../assets/screenshots/LAB-07/06a0-canli-settings.png)

3. **Refresh every** anahtarını açın (3), değer `10 seconds`:

![Otomatik yenileme: 3 Refresh every anahtarı](../../assets/screenshots/LAB-07/06a-canli-ayar.png)

4. Histogram (4) her 10 saniyede yenilenir, sağ uçtaki çubuk büyür:

![Canlı izleme: 1 Last 15 minutes, 4 dakikalık histogram](../../assets/screenshots/LAB-07/06-canli-discover.png)


### 6. Pano için veri hazırlama: doğru tip ve runtime field

**Soru: Grafik neden bazı field'larla çizilmez?** Grafikler aggregation'dan beslenir, aggregation `text` field'da çalışmaz.
`category` hem `text` hem `category.keyword` olarak index'lenmiş; ikisiyle de gruplamayı deneyin:

```bash
for f in category category.keyword; do
  curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/kibana_sample_data_ecommerce/_search?size=0' -H 'Content-Type: application/json' \
    -d '{"aggs": {"k": {"terms": {"field": "'$f'", "size": 1}}}}' | jq -c --arg f "$f" '{field: $f, status, ilk: .aggregations.k.buckets[0].key, hata: .error.root_cause[0].reason[0:60]}'
done
```

Beklenen çıktı:

```text
{"field":"category","status":400,"ilk":null,"hata":"Fielddata is disabled on [category] in [kibana_sample_data_e"}
{"field":"category.keyword","status":null,"ilk":"Men's Clothing","hata":null}
```

- **Lens** bu yüzden `category` yerine `Top values of category.keyword` kullanır.

**Veride olmayan değer: runtime field.** Örneğin siparişin saati; veri yeniden yazılmaz, değer sorgu anında script ile hesaplanır:

```http
GET kibana_sample_data_ecommerce/_search?size=0&filter_path=aggregations
{
  "runtime_mappings": { "siparis_saati": { "type": "long", "script": "emit(doc['order_date'].value.getHour())" } },
  "aggs": { "saat": { "terms": { "field": "siparis_saati", "size": 3 } } }
}
```

```json
{"aggregations":{"saat":{"doc_count_error_upper_bound":0,"sum_other_doc_count":4048,"buckets":[{"key":16,"doc_count":211},{"key":3,"doc_count":210},{"key":1,"doc_count":206}]}}}
```

**Data view'a ekleyin** (saat UTC): Discover ve Lens onu sıradan bir field gibi görür:

```http
POST kbn:/api/data_views/data_view/ff959d40-b880-11e8-a6d9-e546fe2bba5f/runtime_field
{ "name": "siparis_saati", "runtimeField": { "type": "long", "script": { "source": "emit(doc['order_date'].value.getHour())" } } }
```

Discover'da `Kibana Sample Data eCommerce` data view'ında `siparis_saati` (1) görünür; tıklayınca en sık saatler (2):

![Runtime field: 1 siparis_saati field'ı, 2 en sık saatler](../../assets/screenshots/LAB-07/07-runtime-field.png)

- **Bedeli:** runtime field her sorguda yeniden hesaplanır; sık kullanılan değer büyük veride yavaşlatır.
- **O zaman:** field mapping'e eklenir, veri ingest pipeline ile yazılırken doldurulur.

---

## Temizlik

Örnek veri sonraki lablarda kullanılır, silinmez. Bu labın oluşturduğu panoyu, canlı akışı, `analiz-canli`
index'ini ve data view'ını, örnek data view'a eklenen `siparis_saati` field'ını siler. İlk Lens grafiği panonun
içinde kaydedildiği için onunla birlikte gider; kutudaki üç panel kütüphaneye kaydedildiği için ayrıca silinir:

```bash
./teardown.sh
```

Beklenen çıktı:

```text
dashboard 'Satış özeti' -> 200
lens 'Günlük ciro' -> 200
lens 'Ortalama sepet' -> 200
lens 'Cinsiyete göre sipariş' -> 200
canli siparis akisi -> durduruldu
runtime field siparis_saati -> 200
data view analiz-canli -> 200
index analiz-canli -> 200
```

`lens` satırları yalnız kutudaki paneller eklendiyse, `canli siparis akisi` satırı yalnız akış hâlâ çalışıyorsa görünür.

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

---

Sonraki lab: **[LAB-08 — ES|QL ve SQL: Pipeline ile Sorgu ve SQL Köprüsü](../LAB-08-esql-sql/README.md)**
