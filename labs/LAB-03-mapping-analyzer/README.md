# LAB-03 — Mapping ve Analyzer: Field Tipleri ve Türkçe Metin

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Kibana Dev Tools, curl | 9200 (Elasticsearch), 5601 (Kibana) — LAB-01 ana cluster'ı |

---

## Bu lab ne öğretiyor?

- Elasticsearch field tipini nasıl seçer (dynamic mapping)
- `text` ile `keyword` farkı; `term` ile `match` farkı
- Kendi mapping'inizi yazmak, yanlış veriyi reddetmek
- Analyzer: Türkçe küçük harf ve kök bulma
- Mapping neden değişmez; yeni index ve `_reindex`

---

## Ön Koşullar

- LAB-01 ana cluster'ı çalışıyor.

```bash
cd ~/elastic/labs/LAB-03-mapping-analyzer
```

---

## Kavramlar

- **mapping:** index'in şeması; her field'ın tipi (`text`, `keyword`, `date`, `float`...)
- **`text`:** analyzer'dan geçer, kelimelere (**token**) bölünür; kelime kelime aranır
- **`keyword`:** bölünmez, olduğu gibi saklanır; tam eşleşme, sıralama, gruplama için
- **analyzer:** metni token'lara çeviren zincir: tokenizer (böler) → filtreler (küçük harf, kök)
- **`match`** aranan metni de analyzer'dan geçirir; **`term`** geçirmez, olduğu gibi arar

---

## Adım Adım Uygulama Rehberi

Bu labda `http` bloklarını Kibana › Dev Tools'a, `bash` bloklarını terminale yapıştırın.

### 1. Tipi Elasticsearch seçerse: `text` ve `keyword`

**Soru: Mapping vermezsek Elasticsearch metni nasıl saklar, nasıl buluruz?**

**Index'i açın.** Mapping vermiyoruz; yalnız replica 0 (tek node'da sağlık yeşil kalsın):

```http
PUT /mapping-dinamik
{ "settings": { "number_of_replicas": 0 } }
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-dinamik"}
```

**Üç ürün yükleyin.** `_bulk` ile tek istekte; her ürün iki satırdır: eylem satırı (`{"index":{}}`, `_id`'yi
Elasticsearch üretir) ve ürünün kendisi:

```http
POST /mapping-dinamik/_bulk?refresh=true&filter_path=errors
{"index":{}}
{"ad":"Kablosuz Kulaklık","kategori":"Elektronik","fiyat":1149.5}
{"index":{}}
{"ad":"Kablolu Kulaklık","kategori":"Elektronik","fiyat":399.9}
{"index":{}}
{"ad":"Termos 750 ml","kategori":"Mutfak","fiyat":349.0}
```

```json
{"errors": false}
```

**Elasticsearch'ün seçtiği tiplere bakın** (`_mapping` index'in şemasını döndürür):

```http
GET /mapping-dinamik/_mapping?filter_path=*.mappings.properties
```

```json
{"mapping-dinamik":{"mappings":{"properties":{"ad":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"fiyat":{"type":"float"},"kategori":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}}}}
```

Her metin field'ı `text`, altında da `keyword` tipinde bir alt field (`kategori.keyword`) var: aynı değer
iki biçimde saklanıyor.

**`text` field'ına ne yazıldı?** `_analyze` metni o field'ın analyzer'ından geçirip çıkan token'ları listeler:

```http
POST /mapping-dinamik/_analyze?filter_path=tokens.token
{ "field": "ad", "text": "Kablosuz Kulaklık" }
```

```json
{"tokens":[{"token":"kablosuz"},{"token":"kulaklık"}]}
```

**Aynı değeri üç yolla arayın.** Yanıtta kaç document bulunduğu (`total`) ve ürünler görünür.

- **`term`:** değeri olduğu gibi, hiç değiştirmeden arar.
- **`match`:** metni önce field'ın analyzer'ından geçirir (küçük harf, kelimelere bölme), sonra arar.

**1) `text` field'ında `term`:**

```http
GET /mapping-dinamik/_search?filter_path=hits.total.value,hits.hits._source
{
  "_source": ["ad", "kategori"],
  "query": { "term": { "kategori": "Elektronik" } }
}
```

```json
{"hits":{"total":{"value":0}}}
```

"Elektronik" `text` field'ında küçük harfle `elektronik` token'ı olarak saklandı. `term` sorguyu olduğu gibi,
büyük E ile arar; böyle bir token yok, sonuç boş.

**2) Aynı field'da `match`:**

```http
GET /mapping-dinamik/_search?filter_path=hits.total.value,hits.hits._source
{
  "_source": ["ad", "kategori"],
  "query": { "match": { "kategori": "Elektronik" } }
}
```

```json
{"hits":{"total":{"value":2},"hits":[{"_source":{"ad":"Kablosuz Kulaklık","kategori":"Elektronik"}},{"_source":{"ad":"Kablolu Kulaklık","kategori":"Elektronik"}}]}}
```

`match` aranan metni de aynı analyzer'dan geçirir (`elektronik`) ve iki kulaklığı bulur.

**3) `keyword` alt field'ında `term`:**

```http
GET /mapping-dinamik/_search?filter_path=hits.total.value,hits.hits._source
{
  "_source": ["ad", "kategori"],
  "query": { "term": { "kategori.keyword": "Elektronik" } }
}
```

```json
{"hits":{"total":{"value":2},"hits":[{"_source":{"ad":"Kablosuz Kulaklık","kategori":"Elektronik"}},{"_source":{"ad":"Kablolu Kulaklık","kategori":"Elektronik"}}]}}
```

`.keyword` değeri tek parça ve harfi harfine saklar; birebir yazılmış "Elektronik" eşleşir.

**Kural:** metinde kelime aramak için `text` + `match`; tam değer, filtre, gruplama ve sıralama için `keyword` +
`term`. Discover'daki KQL ve Query DSL sorguları da bu ayrımla çalışır.

<details>
<summary><strong>Büyük/küçük harf farkını <code>keyword</code>'de gidermek: normalizer</strong></summary>

`keyword` değeri harfi harfine saklar. Kullanıcı kategoriyi küçük harfle yazarsa `term` bulamaz:

```http
GET /mapping-dinamik/_search?filter_path=hits.total.value,hits.hits._source
{
  "_source": ["ad", "kategori"],
  "query": { "term": { "kategori.keyword": "elektronik" } }
}
```

```json
{"hits":{"total":{"value":0}}}
```

Normalizer, `keyword` için tek parçalık bir analyzer gibidir: değeri bölmez, yalnız dönüştürür. `lowercase`
filtresiyle hem yazılan değer hem `term` sorgusundaki değer küçük harfe çevrilir:

```http
PUT /mapping-normalizer
{
  "settings": {
    "number_of_replicas": 0,
    "analysis": { "normalizer": { "kucuk_harf": { "type": "custom", "filter": ["lowercase"] } } }
  },
  "mappings": {
    "properties": {
      "ad":       { "type": "text" },
      "kategori": { "type": "keyword", "normalizer": "kucuk_harf" }
    }
  }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-normalizer"}
```

Kategorisi farklı harflerle yazılmış üç ürün yükleyin:

```http
POST /mapping-normalizer/_bulk?refresh=true&filter_path=errors
{"index":{}}
{"ad":"Kablosuz Kulaklık","kategori":"Elektronik"}
{"index":{}}
{"ad":"Akıllı Saat","kategori":"ELEKTRONIK"}
{"index":{}}
{"ad":"Termos 750 ml","kategori":"Mutfak"}
```

```json
{"errors": false}
```

Aynı küçük harfli `term` bu kez iki ürünü bulur:

```http
GET /mapping-normalizer/_search?filter_path=hits.total.value,hits.hits._source
{
  "_source": ["ad", "kategori"],
  "query": { "term": { "kategori": "elektronik" } }
}
```

```json
{"hits":{"total":{"value":2},"hits":[{"_source":{"ad":"Kablosuz Kulaklık","kategori":"Elektronik"}},{"_source":{"ad":"Akıllı Saat","kategori":"ELEKTRONIK"}}]}}
```

Dönen document'lerde değerler yazıldığı gibi durur; normalizer yalnız aramada kullanılan değeri değiştirir.
Deneme index'ini silin:

```http
DELETE /mapping-normalizer
```

```json
{"acknowledged": true}
```

</details>

### 2. Kendi mapping'inizi tanımlayın

**Soru: Tipleri Elasticsearch'e bırakmak yerine biz verirsek ne kazanırız?** Yanlış veri reddedilir, Türkçe
tarih ("21.11.2026 14:30") gerçek tarih olarak saklanır, metin doğru analyzer'dan geçer.

**Mapping'i yazın:**

```http
PUT /mapping-urunler
{
  "settings": { "number_of_replicas": 0 },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "ad": {
        "type": "text",
        "analyzer": "turkish",
        "fields": {
          "keyword": { "type": "keyword" },
          "std":     { "type": "text", "analyzer": "standard" }
        }
      },
      "kategori": { "type": "keyword" },
      "fiyat":    { "type": "float" },
      "stok":     { "type": "integer" },
      "eklendi":  { "type": "date", "format": "dd.MM.yyyy HH:mm||strict_date_optional_time" }
    }
  }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-urunler"}
```

- **`dynamic: strict`:** mapping'de olmayan bir field gelirse document reddedilir (Adım 3).
- **`ad`:** Türkçe analyzer'lı `text`; `ad.keyword` tam değer için, `ad.std` karşılaştırma için
  standart analyzer'lı (Adım 4).
- **`kategori`:** `keyword`; kategori aranmaz, tam değerle süzülür ve gruplanır.
- **`eklendi`:** `format` iki biçimi kabul eder: `21.11.2026 14:30` ve ISO 8601. Türkçe tarih artık
  gerçek tarih olarak saklanır.

**Yalnız birkaç field'a bakmak:** büyük bir mapping'in içinden `_mapping/field` ile:

```http
GET /mapping-urunler/_mapping/field/kategori,eklendi?filter_path=*.mappings.*.mapping
```

```json
{"mapping-urunler":{"mappings":{"eklendi":{"mapping":{"eklendi":{"type":"date","format":"dd.MM.yyyy HH:mm||strict_date_optional_time"}}},"kategori":{"mapping":{"kategori":{"type":"keyword"}}}}}}
```

**Örnek veriyi oluşturun:** dört ürün, biri ISO, üçü Türkçe tarihli (`sample-data/urunler.ndjson`):

```bash
mkdir -p sample-data
cat > sample-data/urunler.ndjson << 'EOF'
{ "index": { "_index": "mapping-urunler", "_id": "1" } }
{ "ad": "Kablosuz Kulaklıklar", "kategori": "Elektronik", "fiyat": 1299.5, "stok": 42, "eklendi": "18.11.2026 10:30" }
{ "index": { "_index": "mapping-urunler", "_id": "2" } }
{ "ad": "Yazlık Elbiseler", "kategori": "Giyim", "fiyat": 899.9, "stok": 15, "eklendi": "19.11.2026 14:00" }
{ "index": { "_index": "mapping-urunler", "_id": "3" } }
{ "ad": "Deri Ceketler", "kategori": "Giyim", "fiyat": 2499, "stok": 8, "eklendi": "2026-11-20T09:15:00Z" }
{ "index": { "_index": "mapping-urunler", "_id": "4" } }
{ "ad": "Işıklı Klavye", "kategori": "Elektronik", "fiyat": 749, "stok": 30, "eklendi": "21.11.2026 08:45" }
EOF
```

**Dosyayı `_bulk` ile yükleyin:**

```bash
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/_bulk?refresh=true&filter_path=errors' \
  -H 'Content-Type: application/x-ndjson' --data-binary @sample-data/urunler.ndjson; echo
```

Beklenen çıktı:

```text
{"errors":false}
```

**Tarih aralığıyla sayın:** 19 Kasım ve sonrasında eklenen ürünler:

```http
GET /mapping-urunler/_count?filter_path=count
{ "query": { "range": { "eklendi": { "gte": "19.11.2026 00:00" } } } }
```

```json
{"count": 3}
```

`range` bir değer aralığı arar: `gte` büyük veya eşit (diğerleri `gt`, `lt`, `lte`). Sorgudaki tarih de aynı
`format` ile okunur: 19 Kasım ve sonrası eklenen üç ürün.

<details>
<summary><strong>İki field'ı tek field'da aramak: <code>copy_to</code></strong></summary>

Kişi kayıtlarında ad ve soyad ayrı field'dır. Arama kutusuna "Ahmet Yılmaz" yazan kullanıcıyı düşünün: "Ahmet"
`ad`'da, "Yılmaz" `soyad`'dadır; iki kelimenin birlikte geçtiği tek bir field yoktur. `copy_to` bunun için
vardır: Elasticsearch `ad` ve `soyad` değerlerini index'lerken üçüncü bir field'a (`tam_ad`) da koyar.

Index'i açın. `tam_ad`'ı biz doldurmayacağız; `copy_to` dolduracak:

```http
PUT /mapping-kopya
{
  "settings": { "number_of_replicas": 0 },
  "mappings": {
    "properties": {
      "ad":     { "type": "text", "copy_to": "tam_ad" },
      "soyad":  { "type": "text", "copy_to": "tam_ad" },
      "tam_ad": { "type": "text" }
    }
  }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-kopya"}
```

Bir kişi ekleyin; yalnız `ad` ve `soyad` gönderiyoruz:

```http
POST /mapping-kopya/_doc?refresh=true&filter_path=result
{ "ad": "Ahmet", "soyad": "Yılmaz" }
```

```json
{"result": "created"}
```

Önce sorunu görün: "ahmet yılmaz"ı `ad` field'ında arayın. `operator: and` yazılan iki kelimenin de aynı field'da
geçmesini ister (yazmasaydık "ahmet" tek başına yeterdi):

```http
GET /mapping-kopya/_search?filter_path=hits.total.value
{ "query": { "match": { "ad": { "query": "ahmet yılmaz", "operator": "and" } } } }
```

```json
{"hits": {"total": {"value": 0}}}
```

Sonuç 0: `ad`'da "yılmaz" yok. Şimdi aynı aramayı `tam_ad`'da yapın:

```http
GET /mapping-kopya/_search?filter_path=hits.total.value,hits.hits._source
{ "query": { "match": { "tam_ad": { "query": "ahmet yılmaz", "operator": "and" } } } }
```

```json
{"hits": {"total": {"value": 1}, "hits": [{"_source": {"ad": "Ahmet", "soyad": "Yılmaz"}}]}}
```

Kişi bulundu: `tam_ad`'da iki kelime de var. Dönen document'te `tam_ad` yok; `copy_to` gönderdiğiniz document'i
değiştirmez, kopyayı yalnız aramada kullanılmak üzere tutar.

Deneme index'ini silin:

```http
DELETE /mapping-kopya
```

```json
{"acknowledged": true}
```

</details>

### 3. Yanlış veri reddedilir

**Soru: Mapping'e uymayan bir document gelirse ne olur?** İki hatalı document gönderin; yanıtta şunlara bakın:

- **`type`:** hatanın türü
- **`reason`:** nedeni; baştaki `[1:61]` hatanın gövdedeki satır ve sütunudur (boşluklar değişirse sayı değişir)

**Sayı field'ına metin:**

<!-- runner:expect-fail -->
```http
PUT /mapping-urunler/_doc/5
{ "ad": "Akıllı Saat", "kategori": "Elektronik", "fiyat": "ücretsiz" }
```

```json
{
  "error": {
    "root_cause": [
      {
        "type": "document_parsing_exception",
        "reason": "[1:61] failed to parse field [fiyat] of type [float] in document with id '5'. Preview of field's value: 'ücretsiz'"
      }
    ],
    "type": "document_parsing_exception",
    "reason": "[1:61] failed to parse field [fiyat] of type [float] in document with id '5'. Preview of field's value: 'ücretsiz'",
    "caused_by": {
      "type": "number_format_exception",
      "reason": "For input string: \"ücretsiz\""
    }
  },
  "status": 400
}
```

**Mapping'de olmayan bir field:**

<!-- runner:expect-fail -->
```http
PUT /mapping-urunler/_doc/5
{ "ad": "Akıllı Saat", "kategori": "Elektronik", "renk": "siyah" }
```

```json
{
  "error": {
    "root_cause": [
      {
        "type": "strict_dynamic_mapping_exception",
        "reason": "[1:60] mapping set to strict, dynamic introduction of [renk] within [_doc] is not allowed"
      }
    ],
    "type": "strict_dynamic_mapping_exception",
    "reason": "[1:60] mapping set to strict, dynamic introduction of [renk] within [_doc] is not allowed"
  },
  "status": 400
}
```

- **`fiyat`:** `float` olduğu için "ücretsiz" sayıya çevrilemez, document yazılmaz.
- **`renk`:** mapping'de yok; `dynamic: strict` olmasaydı Elasticsearch field'ı sessizce `text` olarak eklerdi.
  Beklenmeyen field'ı reddetmek veri kalitesini korur.

<details>
<summary><strong>Reddetmek yerine kabul edip yok saymak: <code>ignore_malformed</code> ve <code>dynamic: false</code></strong></summary>

Log toplarken tek bir bozuk değer yüzünden bütün kaydı kaybetmek istemeyebilirsiniz. İki ayar document'i kabul
eder ama sorunlu kısmı index'lemez:

- `ignore_malformed: true`: field'a uymayan değer (sayı field'ına "ücretsiz") index'lenmez, document yine yazılır.
- `dynamic: false`: mapping'de olmayan field (`renk`) `_source`'ta saklanır ama index'lenmez, aranamaz.

```http
PUT /mapping-tolerans
{
  "settings": { "number_of_replicas": 0 },
  "mappings": {
    "dynamic": false,
    "properties": {
      "ad":    { "type": "text" },
      "fiyat": { "type": "float", "ignore_malformed": true }
    }
  }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-tolerans"}
```

Adım 3'te reddedilen iki hatayı tek document'te gönderin:

```http
POST /mapping-tolerans/_doc?refresh=true&filter_path=result
{ "ad": "Akıllı Saat", "fiyat": "ücretsiz", "renk": "siyah" }
```

```json
{"result": "created"}
```

Document yazıldı. Hangi field'ın atlandığı `_ignored` meta field'ında durur:

```http
GET /mapping-tolerans/_search?filter_path=hits.hits._ignored,hits.hits._source
{ "query": { "exists": { "field": "_ignored" } } }
```

```json
{"hits":{"hits":[{"_ignored":["fiyat"],"_source":{"ad":"Akıllı Saat","fiyat":"ücretsiz","renk":"siyah"}}]}}
```

`renk` `_source`'ta görünür ama index'lenmediği için aranamaz:

```http
GET /mapping-tolerans/_search?filter_path=hits.total.value
{ "query": { "match": { "renk": "siyah" } } }
```

```json
{"hits":{"total":{"value":0}}}
```

Hangisi ne zaman: veri kalitesi önemliyse `strict` (hata hemen görünür); kaynağı sizin kontrolünüzde olmayan log ve
olaylarda `ignore_malformed` ve `dynamic: false` (kayıt kaybolmaz, sorun `_ignored` ile bulunur). Deneme index'ini
silin:

```http
DELETE /mapping-tolerans
```

```json
{"acknowledged": true}
```

</details>

<details>
<summary><strong>Metin sayıya çevrilsin mi: <code>coerce</code>; boş değeri aramak: <code>null_value</code></strong></summary>

Excel'den gelen fiyat çoğu zaman `"349.90"` gibi tırnaklı metindir. Sayı field'ları varsayılan olarak bunu sayıya
çevirir (`coerce`); `coerce: false` çevirmeyi kapatır ve metni reddeder. `null` değer ise index'lenmez ve
aranamaz; `null_value` onun yerine aranabilir bir değer yazar:

```http
PUT /mapping-coerce
{
  "settings": { "number_of_replicas": 0 },
  "mappings": {
    "properties": {
      "ad":       { "type": "text" },
      "fiyat":    { "type": "float" },
      "stok":     { "type": "integer", "coerce": false },
      "kategori": { "type": "keyword", "null_value": "BILINMIYOR" }
    }
  }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-coerce"}
```

Fiyatı metin, kategorisi boş bir ürün gönderin:

```http
POST /mapping-coerce/_doc?refresh=true&filter_path=result
{ "ad": "Termos 750 ml", "fiyat": "349.90", "stok": 120, "kategori": null }
```

```json
{"result": "created"}
```

Fiyat sayıya çevrildiği için aralık sorgusu ürünü bulur; `_source`'ta değer gönderildiği gibi metin kalır:

```http
GET /mapping-coerce/_search?filter_path=hits.hits._source
{ "query": { "range": { "fiyat": { "gte": 300 } } } }
```

```json
{"hits":{"hits":[{"_source":{"ad":"Termos 750 ml","fiyat":"349.90","stok":120,"kategori":null}}]}}
```

Kategorisi boş ürünü `null_value` değeriyle arayın:

```http
GET /mapping-coerce/_search?filter_path=hits.hits._source.ad,hits.hits._source.kategori
{ "query": { "term": { "kategori": "BILINMIYOR" } } }
```

```json
{"hits":{"hits":[{"_source":{"ad":"Termos 750 ml","kategori":null}}]}}
```

`coerce: false` olan `stok`'a metin gönderin:

<!-- runner:expect-fail -->
```http
POST /mapping-coerce/_doc
{ "ad": "Çaydanlık", "fiyat": 499, "stok": "10" }
```

```json
{
  "error": {
    "root_cause": [
      {
        "type": "document_parsing_exception",
        "reason": "[1:46] failed to parse field [stok] of type [integer] in document with id 'f2CYBaIBCkKviuGl7PT2'. Preview of field's value: '10'"
      }
    ],
    "type": "document_parsing_exception",
    "reason": "[1:46] failed to parse field [stok] of type [integer] in document with id 'f2CYBaIBCkKviuGl7PT2'. Preview of field's value: '10'",
    "caused_by": {
      "type": "illegal_argument_exception",
      "reason": "Integer value passed as String"
    }
  },
  "status": 400
}
```

`Integer value passed as String`: `stok` metni sayıya çevirmedi, document reddedildi. Hatadaki document id
sizde farklıdır. Deneme index'ini silin:

```http
DELETE /mapping-coerce
```

```json
{"acknowledged": true}
```

</details>

### 4. Türkçe metin: küçük harf ve kök

**Soru: Kullanıcı "kulaklık" yazınca "Kulaklıklar" bulunur mu?** Analyzer'a bağlıdır. Aynı metni iki analyzer'la
görün: `ad` (Türkçe) ve `ad.std` (standart):

```http
POST /mapping-urunler/_analyze?filter_path=tokens.token
{ "field": "ad", "text": "IŞIKLI Kulaklıklar" }
```

```json
{"tokens": [{"token": "ışıklı"}, {"token": "kulaklık"}]}
```

**Aynı metin standart analyzer'la (`ad.std`):**

```http
POST /mapping-urunler/_analyze?filter_path=tokens.token
{ "field": "ad.std", "text": "IŞIKLI Kulaklıklar" }
```

```json
{"tokens": [{"token": "işikli"}, {"token": "kulaklıklar"}]}
```

- Türkçe analyzer `I`'yı `ı`'ya çevirir; standart analyzer `i`'ye çevirir ("işikli"). Türkçede
  `I/ı` ve `İ/i` ayrı harflerdir.
- Türkçe analyzer kelimeyi köküne indirir: "Kulaklıklar" → "kulaklık". Kullanıcı tekil arasa da
  çoğul ürün bulunur.

**Arama sonucu da değişir.** Aynı kelimeyi önce Türkçe analyzer'lı `ad`'da, sonra standart analyzer'lı
`ad.std`'de arayın:

```http
GET /mapping-urunler/_count?filter_path=count
{ "query": { "match": { "ad": "kulaklık" } } }
```

```json
{"count": 1}
```

**Aynı kelime standart analyzer'lı `ad.std`'de:**

```http
GET /mapping-urunler/_count?filter_path=count
{ "query": { "match": { "ad.std": "kulaklık" } } }
```

```json
{"count": 0}
```

Standart analyzer kök bulmaz: "Kulaklıklar" `kulaklıklar` olarak saklandı, "kulaklık" araması eşleşmedi.

<details>
<summary><strong>Türkçe karakter yazmadan aramak: <code>asciifolding</code>; kelimeye bölme: <code>whitespace</code></strong></summary>

Türkçe klavyesi olmayan kullanıcı "Çağrı" yerine "cagri" yazar. `asciifolding` filtresi harflerin
işaretlerini kaldırır (ç → c, ğ → g, ı → i); yazılan ve aranan aynı token'a iner. `_analyze` index olmadan da
çalışır; zinciri istekte verin:

```http
POST /_analyze?filter_path=tokens.token
{ "tokenizer": "standard", "filter": [ { "type": "lowercase", "language": "turkish" }, "asciifolding" ], "text": "Çağrı Merkezi" }
```

```json
{"tokens":[{"token":"cagri"},{"token":"merkezi"}]}
```

```http
POST /_analyze?filter_path=tokens.token
{ "tokenizer": "standard", "filter": [ { "type": "lowercase", "language": "turkish" }, "asciifolding" ], "text": "cagri merkezi" }
```

```json
{"tokens":[{"token":"cagri"},{"token":"merkezi"}]}
```

Zincirin ilk halkası tokenizer'dır ve metni nereden böleceğine o karar verir. `whitespace` yalnız boşluktan böler,
`standard` noktalama işaretlerinden de:

```http
POST /_analyze?filter_path=tokens.token
{ "tokenizer": "whitespace", "text": "USB-C, 1 metre" }
```

```json
{"tokens":[{"token":"USB-C,"},{"token":"1"},{"token":"metre"}]}
```

```http
POST /_analyze?filter_path=tokens.token
{ "tokenizer": "standard", "text": "USB-C, 1 metre" }
```

```json
{"tokens":[{"token":"USB"},{"token":"C"},{"token":"1"},{"token":"metre"}]}
```

`whitespace` virgülü kelimeye yapıştırdı ("USB-C,"); "usb-c" araması bu token'ı bulamaz. `standard` "USB" ve "C"
diye böldü. Şimdi `asciifolding`'li bir analyzer'ı bir field'a verin:

```http
PUT /mapping-ascii
{
  "settings": {
    "number_of_replicas": 0,
    "analysis": {
      "filter":   { "tr_kucuk": { "type": "lowercase", "language": "turkish" } },
      "analyzer": { "tr_ascii": { "tokenizer": "standard", "filter": ["tr_kucuk", "asciifolding"] } }
    }
  },
  "mappings": { "properties": { "ad": { "type": "text", "analyzer": "tr_ascii" } } }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-ascii"}
```

```http
POST /mapping-ascii/_doc?refresh=true&filter_path=result
{ "ad": "Çağrı Merkezi Kulaklığı" }
```

```json
{"result": "created"}
```

Türkçe karakter kullanmadan arayın:

```http
GET /mapping-ascii/_search?filter_path=hits.total.value,hits.hits._source
{ "query": { "match": { "ad": "cagri" } } }
```

```json
{"hits":{"total":{"value":1},"hits":[{"_source":{"ad":"Çağrı Merkezi Kulaklığı"}}]}}
```

Deneme index'ini silin:

```http
DELETE /mapping-ascii
```

```json
{"acknowledged": true}
```

</details>

### 5. Kök bulma yanılırsa: kurallı düzeltme ve yeni index

**Soru: Kök bulma yanlış kök üretirse ne yaparız?** Kök bulma bir algoritmadır, her kelimede doğru çalışmaz:

```http
GET /mapping-urunler/_count?filter_path=count
{ "query": { "match": { "ad": "elbise" } } }
```

```json
{"count": 0}
```

**Hangi köke iniyor?**

```http
POST /mapping-urunler/_analyze?filter_path=tokens.token
{ "field": "ad", "text": "elbise Elbiseler ceket Ceketler" }
```

```json
{"tokens": [{"token": "elbis"}, {"token": "elbise"}, {"token": "ceket"}, {"token": "ceket"}]}
```

"Ceketler" ve "ceket" aynı köke iner, ama "elbise" → `elbis`, "Elbiseler" → `elbise` olur; tekil
arama çoğul ürünü bulamaz. Çözüm, analyzer zincirine kendi kuralımızı eklemek: `stemmer_override`
sözlükteki kelimeyi verilen köke çevirir, kök bulucu o kelimeye dokunmaz.

**Mevcut index'te düzeltebilir miyiz?** Bir field'ın tipini değiştirmeyi deneyin:

<!-- runner:expect-fail -->
```http
PUT /mapping-urunler/_mapping
{ "properties": { "kategori": { "type": "text" } } }
```

```json
{
  "error": {
    "root_cause": [
      {
        "type": "illegal_argument_exception",
        "reason": "mapper [kategori] cannot be changed from type [keyword] to [text]"
      }
    ],
    "type": "illegal_argument_exception",
    "reason": "mapper [kategori] cannot be changed from type [keyword] to [text]"
  },
  "status": 400
}
```

**Neden reddedildi?** Var olan field'ın tipi ve analyzer'ı değiştirilemez: token'lar eski kurala göre yazıldı,
değiştirmek bütün document'leri yeniden işlemek demektir. Yeni field eklemek serbesttir. Düzeltme yeni bir
index'te yapılır, veri `_reindex` ile taşınır:

```http
PUT /mapping-urunler-v2
{
  "settings": {
    "number_of_replicas": 0,
    "analysis": {
      "filter": {
        "tr_kucuk": { "type": "lowercase", "language": "turkish" },
        "tr_kural": { "type": "stemmer_override", "rules": ["elbiseler, elbise => elbise"] },
        "tr_kok":   { "type": "stemmer", "language": "turkish" }
      },
      "analyzer": {
        "tr_urun": {
          "tokenizer": "standard",
          "filter": ["apostrophe", "tr_kucuk", "tr_kural", "tr_kok"]
        }
      }
    }
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "ad":       { "type": "text", "analyzer": "tr_urun", "fields": { "keyword": { "type": "keyword" } } },
      "kategori": { "type": "keyword" },
      "fiyat":    { "type": "float" },
      "stok":     { "type": "integer" },
      "eklendi":  { "type": "date", "format": "dd.MM.yyyy HH:mm||strict_date_optional_time" }
    }
  }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "mapping-urunler-v2"}
```

- **`apostrophe`:** kesme işaretinden sonrasını atar ("İstanbul'daki" → "İstanbul").
- **`tr_kucuk`:** Türkçe küçük harf (`I` → `ı`); hazır `lowercase` filtresine `language: turkish` verilerek
  tanımlanır.
- **`tr_kural`:** kuraldaki kelimeler `elbise` olur ve kök bulucu onlara dokunmaz. Kural sırası
  önemlidir: kök bulucudan önce gelmelidir.
- **`tr_kok`:** diğer kelimeler için Türkçe kök bulma.

**Veriyi yeni index'e taşıyın** (`source` okunan, `dest` yazılan index):

```http
POST /_reindex?refresh=true&filter_path=total,created
{
  "source": { "index": "mapping-urunler" },
  "dest":   { "index": "mapping-urunler-v2" }
}
```

```json
{"total": 4, "created": 4}
```

**Yeni index'te kontrol:** kural uygulanıyor mu, tekil arama çoğul ürünü buluyor mu?

```http
POST /mapping-urunler-v2/_analyze?filter_path=tokens.token
{ "field": "ad", "text": "elbise Elbiseler ceket Ceketler" }
```

```json
{"tokens": [{"token": "elbise"}, {"token": "elbise"}, {"token": "ceket"}, {"token": "ceket"}]}
```

**Tekil "elbise" aramasını sayın:**

```http
GET /mapping-urunler-v2/_count?filter_path=count
{ "query": { "match": { "ad": "elbise" } } }
```

```json
{"count": 1}
```

- **`_reindex`:** document'leri `_source`'tan okuyup yeni index'in mapping'iyle yeniden yazar.
- **Kural yine değişirse:** aynı işlem tekrarlanır; eski document'ler eski token'larla durur.
- **alias:** uygulama index adı yerine alias'a yazar ve okur; alias tek istekte yeni index'e çevrilir.

---

## Temizlik

Yalnız bu labın `mapping-*` index'lerini siler; ana cluster'a dokunmaz:

```bash
./teardown.sh
```

Beklenen çıktı:

```text
index mapping-dinamik -> 200
index mapping-urunler -> 200
index mapping-urunler-v2 -> 200
```

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

---

Sonraki lab: **[LAB-04 — Discover ve KQL: Veriye Soru Sorarak Bakmak](../LAB-04-discover-kql/README.md)**
