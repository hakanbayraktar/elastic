# LAB-06 — Arama Deneyimi: Otomatik Tamamlama, Yazım Hatası, Eş Anlamlılar

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Kibana Dev Tools, curl, Synonyms API | 9200 (Elasticsearch), 5601 (Kibana) — LAB-01 ana cluster'ı |

---

## Bu lab ne öğretiyor?

Bir uygulamanın arama kutusundan beklenenler: yazarken öneri gelsin, "klavey" yazan da klavyeyi
bulsun, "headset" arayan kulaklığı görsün, ürün adındaki eşleşme açıklamadakinden önde olsun ve
eşleşen kelime vurgulansın. Bu labda bunları küçük bir ürün kataloğunda kuruyoruz. Son adımda
joker karakterli aramanın neden beklenmedik sonuç verdiğini görüyoruz.

---

## Ön Koşullar

- LAB-01 ana cluster'ı çalışıyor.
- Önceki labları atladıysanız da lab çalışır: index, analyzer'lar ve veri bu labda kurulur. Analyzer, metni
  aranabilir token'lara çeviren zincirdir (kelimelere bölme, küçük harf, kök bulma).

```bash
cd ~/elastic/labs/LAB-06-arama-deneyimi
```

---

## Kavramlar: yazarken ve ararken farklı analyzer

Bir field'ın iki analyzer'ı olabilir: `analyzer` document yazılırken, `search_analyzer` sorgu
çalışırken kullanılır. Eş anlamlıları yalnız arama tarafında genişletmek iki şey kazandırır:
index küçük kalır ve eş anlamlı listesi değişince document'leri yeniden yazmak gerekmez.

---

## Adım Adım Uygulama Rehberi

Bu labda `http` bloklarını Kibana › Dev Tools'a, `bash` bloklarını terminale yapıştırın.

### 1. Eş anlamlı seti, index ve veri

Eş anlamlıları index'ten ayrı, adı olan bir sette tutuyoruz (Synonyms API):

```http
PUT /_synonyms/deneyim-esanlam?filter_path=result
{
  "synonyms_set": [
    { "id": "kulaklik", "synonyms": "kulaklık, kulaklik, headset" },
    { "id": "telefon",  "synonyms": "cep telefonu, akıllı telefon, telefon" }
  ]
}
```

```json
{"result": "created"}
```

Her kural bir `id` (kuralın adı, sonra tek tek güncellemek için) ve virgülle ayrılmış, birbirinin yerine geçen
kelimelerden oluşur. "cep telefonu" gibi iki kelimelik ifadeler de bir kelimeyle eşleşebilir.

Index iki analyzer ve bir öneri field'ıyla açılır. Analyzer, `standard` tokenizer metni kelimelere böldükten sonra
filtreleri sırayla uygular:

- `apostrophe`: kesme işaretinden sonrasını atar ("Kulaklık'ı" → "Kulaklık").
- `tr_kucuk`: Türkçe kurallarla küçük harf (I → ı, İ → i).
- `tr_kok`: kelimeyi köküne indirir ("kulaklıklar" → "kulaklık").
- `tr_esanlam`: setteki eş anlamlıları ekler; `synonym_graph` çok kelimeli ifadeleri doğru eşler.

```http
PUT /deneyim-urunler
{
  "settings": {
    "number_of_replicas": 0,
    "analysis": {
      "filter": {
        "tr_kucuk":   { "type": "lowercase", "language": "turkish" },
        "tr_kok":     { "type": "stemmer", "language": "turkish" },
        "tr_esanlam": { "type": "synonym_graph", "synonyms_set": "deneyim-esanlam", "updateable": true }
      },
      "analyzer": {
        "tr_index": { "tokenizer": "standard", "filter": ["apostrophe", "tr_kucuk", "tr_kok"] },
        "tr_arama": { "tokenizer": "standard", "filter": ["apostrophe", "tr_kucuk", "tr_esanlam", "tr_kok"] },
        "tr_oneri": { "tokenizer": "standard", "filter": ["apostrophe", "tr_kucuk"] }
      }
    }
  },
  "mappings": {
    "properties": {
      "ad": {
        "type": "text", "analyzer": "tr_index", "search_analyzer": "tr_arama",
        "fields": { "oneri": { "type": "search_as_you_type", "analyzer": "tr_oneri" } }
      },
      "aciklama": { "type": "text", "analyzer": "tr_index", "search_analyzer": "tr_arama" },
      "kategori": { "type": "keyword" }
    }
  }
}
```

```json
{"acknowledged": true, "shards_acknowledged": true, "index": "deneyim-urunler"}
```

- `tr_index`: yazarken Türkçe küçük harf ve kök.
- `tr_arama`: ararken aynısı, artı eş anlamlılar. `updateable: true` setin güncellenince yeniden
  yüklenmesini sağlar; yalnız arama analyzer'ında kullanılabilir.
- `tr_oneri`: yalnız küçük harf; kök bulmaz, çünkü öneride kullanıcının yazdığı harflerle eşleşmek gerekir.
- `ad.oneri`: `search_as_you_type` field'ı, otomatik tamamlama için kelime başlarını hazır tutar.

Yedi ürünü `_bulk` ile yükleyin (her ürün iki satır: eylem satırı ve ürünün kendisi):

Önce örnek veri dosyasını oluşturun: `sample-data/urunler.ndjson`

```bash
mkdir -p sample-data
cat > sample-data/urunler.ndjson << 'EOF'
{ "index": { "_index": "deneyim-urunler", "_id": "1" } }
{ "ad": "Kablosuz Kulaklık", "aciklama": "Gürültü engelleme, 30 saat pil", "kategori": "Elektronik" }
{ "index": { "_index": "deneyim-urunler", "_id": "2" } }
{ "ad": "Kablolu Kulaklık", "aciklama": "3.5 mm jak, mikrofonlu", "kategori": "Elektronik" }
{ "index": { "_index": "deneyim-urunler", "_id": "3" } }
{ "ad": "Kablosuz Klavye", "aciklama": "Bluetooth, Türkçe Q klavye", "kategori": "Elektronik" }
{ "index": { "_index": "deneyim-urunler", "_id": "4" } }
{ "ad": "Akıllı Telefon", "aciklama": "128 GB, çift SIM", "kategori": "Elektronik" }
{ "index": { "_index": "deneyim-urunler", "_id": "5" } }
{ "ad": "Telefon Kılıfı", "aciklama": "Silikon, şeffaf", "kategori": "Aksesuar" }
{ "index": { "_index": "deneyim-urunler", "_id": "6" } }
{ "ad": "Oyuncu Kulaklığı", "aciklama": "7.1 surround, RGB ışık", "kategori": "Elektronik" }
{ "index": { "_index": "deneyim-urunler", "_id": "7" } }
{ "ad": "Şarj Kablosu", "aciklama": "USB-C, 1 metre, kulaklık ve telefon için", "kategori": "Aksesuar" }
EOF
```

Dosyayı `_bulk` ile yükleyin:

```bash
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/_bulk?refresh=true&filter_path=errors' \
  -H 'Content-Type: application/x-ndjson' --data-binary @sample-data/urunler.ndjson; echo
```

Beklenen çıktı:

```text
{"errors":false}
```

### 2. Otomatik tamamlama

Kullanıcı "kab" yazdı. `multi_match` aynı metni birden çok field'da arar. Burada `ad.oneri` ve onun ürettiği iki
alt field'da arıyoruz; `type: bool_prefix` son kelimeyi yarım yazılmış sayar:

```http
GET /deneyim-urunler/_search?filter_path=hits.hits._source.ad
{
  "query": {
    "multi_match": {
      "query": "kab",
      "type": "bool_prefix",
      "fields": ["ad.oneri", "ad.oneri._2gram", "ad.oneri._3gram"]
    }
  }
}
```

Yazmaya devam etti: "kablosuz ku".

```http
GET /deneyim-urunler/_search?filter_path=hits.hits._source.ad
{
  "query": {
    "multi_match": {
      "query": "kablosuz ku",
      "type": "bool_prefix",
      "fields": ["ad.oneri", "ad.oneri._2gram", "ad.oneri._3gram"]
    }
  }
}
```

| Yazılan | Öneriler (sırayla) |
|---|---|
| `kab` | Kablosuz Kulaklık · Kablolu Kulaklık · Kablosuz Klavye · Şarj Kablosu |
| `kablosuz ku` | Kablosuz Kulaklık · Kablosuz Klavye · Kablolu Kulaklık · Oyuncu Kulaklığı |

`bool_prefix` son kelimeyi ön ek ("ku…"), öncekileri tam kelime sayar. İki kelimesi de tutan
"Kablosuz Kulaklık" en üstte gelir; `_2gram` ve `_3gram` alt field'ları kelime çiftlerini tuttuğu
için yan yana geçen kelimeler daha yüksek skor alır.

<details><summary><strong>Arka planda: search_as_you_type'ın edge n-gram'ları</strong></summary>

`ad.oneri` field'ı yazılırken üç alt field üretir. `_analyze` her birinin token'larını gösterir:

```bash
for f in ad.oneri ad.oneri._2gram ad.oneri._index_prefix; do
  echo "$f: $(curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/deneyim-urunler/_analyze' -H 'Content-Type: application/json' \
    -d '{"field": "'$f'", "text": "Kablosuz Kulaklık"}' | jq -c '[.tokens[].token][0:8]')"
done
```

Beklenen çıktı:

```text
ad.oneri: ["kablosuz","kulaklık"]
ad.oneri._2gram: ["kablosuz kulaklık"]
ad.oneri._index_prefix: ["k","ka","kab","kabl","kablo","kablos","kablosu","kablosuz"]
```

`_index_prefix` her kelimenin baştan kesilmiş hâllerini (edge n-gram) index'e yazar: "kab" yazıldığında
eşleşecek token zaten hazırdır, sorgu anında ön ek araması yapılmaz. Bedeli daha büyük index'tir.

</details>

### 3. Yazım hatası toleransı

"klavey" yazıldı:

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": "klavey" } } }
```

Aynı arama, yazım hatasına izin vererek (`fuzziness`):

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": { "query": "klavey", "fuzziness": "AUTO" } } } }
```

| Sorgu | Sonuç |
|---|---|
| `match` "klavey" | 0 |
| `match` "klavey", `fuzziness: AUTO` | 1: Kablosuz Klavye |

`fuzziness: AUTO` harf farkına (silme, ekleme, değiştirme, yer değiştirme) kelimenin uzunluğuna
göre izin verir: 1-2 harflik kelimede hiç, 3-5 harfte bir, daha uzun kelimede iki fark. Kısa
kelimede kapalı olması, iki harflik bir aramanın yüzlerce kelimeyle eşleşmesini önler.

### 4. Eş anlamlılar

Ürün adlarında geçmeyen "headset" kelimesini arayın:

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": "headset" } } }
```

Sonuç 3: Kablosuz Kulaklık, Kablolu Kulaklık, Oyuncu Kulaklığı. Ürün adlarında "headset" geçmiyor;
arama analyzer'ı onu "kulaklık"a genişletti. "kulaklik" (ı'sız) da aynı kuralla bulunur. Şimdi
listede olmayan bir kelime (sonuç 0):

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value
{ "query": { "match": { "ad": "headphone" } } }
```

Kuralı güncelleyin. Index kapatılmaz, document'ler yeniden yazılmaz:

```http
PUT /_synonyms/deneyim-esanlam/kulaklik?filter_path=result,reload_analyzers_details.reload_details.reloaded_analyzers
{ "synonyms": "kulaklık, kulaklik, headset, headphone" }
```

```json
{"result": "updated", "reload_analyzers_details": {"reload_details": [{"reloaded_analyzers": ["tr_arama"]}]}}
```

`reloaded_analyzers` setin değişmesiyle yeniden yüklenen analyzer'ları listeler: yalnız arama analyzer'ı
`tr_arama`.

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": "headphone" } } }
```

Sonuç artık 3 kulaklık. Set güncellenince Elasticsearch onu kullanan arama analyzer'larını yeniden
yükler. Bu, eş anlamlıların yalnız arama tarafında olmasının kazancıdır: yazma tarafında olsaydı
document'ler index'lenirken üretilmiş eski token'larla kalır ve yeni kuralın geçmesi için `_reindex` gerekirdi. Kural listesini Kibana'da **Elasticsearch ›
Synonyms** sayfasından da yönetebilirsiniz.

### 5. Önemli field'ı öne çıkarmak ve vurgulamak

Ad ve açıklamada birlikte arayın; addaki eşleşme üç kat değerli olsun, eşleşen kelime işaretlensin:

```http
GET /deneyim-urunler/_search?filter_path=hits.hits._score,hits.hits._source.ad,hits.hits.highlight
{
  "query": { "multi_match": { "query": "kulaklık", "fields": ["ad^3", "aciklama"] } },
  "highlight": { "fields": { "ad": {}, "aciklama": {} } }
}
```

```json
{
  "hits": {
    "hits": [
      {
        "_score": 2.4800358,
        "_source": {
          "ad": "Kablosuz Kulaklık"
        },
        "highlight": {
          "ad": [
            "Kablosuz <em>Kulaklık</em>"
          ]
        }
      },
      {
        "_score": 2.4800358,
        "_source": {
          "ad": "Kablolu Kulaklık"
        },
        "highlight": {
          "ad": [
            "Kablolu <em>Kulaklık</em>"
          ]
        }
      },
      {
        "_score": 2.4800358,
        "_source": {
          "ad": "Oyuncu Kulaklığı"
        },
        "highlight": {
          "ad": [
            "Oyuncu <em>Kulaklığı</em>"
          ]
        }
      },
      {
        "_score": 1.2587123,
        "_source": {
          "ad": "Şarj Kablosu"
        },
        "highlight": {
          "aciklama": [
            "USB-C, 1 metre, <em>kulaklık</em> ve telefon için"
          ]
        }
      }
    ]
  }
}
```

- `ad^3`: ad field'ının skoru 3 ile çarpılır. "Şarj Kablosu"nun yalnız açıklamasında "kulaklık"
  geçtiği için en altta kalır, ama listeden düşmez.
- `highlight`: eşleşen kelimeyi `<em>` ile sarar; uygulama bunu kalın gösterir. "Kulaklığı" da
  işaretlenir, çünkü kök bulma sayesinde aynı terimdir.

<details>
<summary><strong>Bir sonucu silmeden geri plana itmek: <code>boosting</code></strong></summary>

"Kulaklık" aramasında kablolu modeller listede kalsın ama sona insin. `boosting` sorgusu `positive`
kısmına uyan document'leri bulur; `negative` kısmına da uyanların skorunu `negative_boost` ile çarpar:

```http
GET /deneyim-urunler/_search?filter_path=hits.hits._score,hits.hits._source.ad
{
  "query": { "boosting": {
    "positive": { "match": { "ad": "kulaklık" } },
    "negative": { "match": { "ad": "kablolu" } },
    "negative_boost": 0.2 } }
}
```

```json
{"hits":{"hits":[{"_score":0.8266786,"_source":{"ad":"Kablosuz Kulaklık"}},{"_score":0.8266786,"_source":{"ad":"Oyuncu Kulaklığı"}},{"_score":0.16533571,"_source":{"ad":"Kablolu Kulaklık"}}]}}
```

"Kablolu Kulaklık"ın skoru öbürleriyle aynıyken (0,83) 0,2 ile çarpılıp 0,17'ye indi ve sona düştü.

`must_not` "Kablolu Kulaklık"ı listeden çıkarırdı; `boosting` onu yalnız aşağı iter. Kampanyalı ya da
stokta olmayan ürünü gizlemeden geri plana almak için kullanılır.

</details>

### 6. Joker karakter tuzağı

Kullanıcı "kulaklıklar" yazdı, bir de sonuna yıldız koydu:

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "match": { "ad": "kulaklıklar" } } }
```

Aynı kelime, sonuna yıldız koyarak (`wildcard`):

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "wildcard": { "ad": { "value": "kulaklıklar*" } } } }
```

Daha kısa bir başlangıçla (`kulak*`):

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "wildcard": { "ad": { "value": "kulak*" } } } }
```

| Sorgu | Sayı |
|---|---|
| `match` "kulaklıklar" | 3 |
| `wildcard` "kulaklıklar*" | 0 |
| `wildcard` "kulak*" | 3 |

- `match` aramayı analyzer'dan geçirir: "kulaklıklar" → `kulaklık`, index'teki terimle aynı: 3.
- `wildcard` analyzer'dan **geçmez**; deseni index'teki terimlerle karşılaştırır. Index'te
  `kulaklık` var, "kulaklıklar" ile başlayan terim yok: 0.
- `kulak*`, `kulaklık` terimini yakalar: 3.

Analyzer doğru terimi üretse bile sorgu türü o terime ulaşamayabilir. `query_string` sorguyu tek bir metin olarak
alır ve `AND`, `OR`, `*` gibi işaretleri kendisi çözer (Kibana'da sorgu dili KQL yerine Lucene seçildiğinde kullanılan sözdizimi).
`analyze_wildcard: true` sondaki yıldızlı kelimeyi de analyzer'dan geçirir (sonuç 3):

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "query_string": { "query": "kulaklıklar*", "fields": ["ad"], "analyze_wildcard": true } } }
```

Yıldızın yeri maliyeti belirler: `kulak*` (sonda) terimlerin başından arar, hızlıdır; `*lak`
(başta) bütün terimleri tarar, büyük index'te yavaştır. Yazarken arama için wildcard yerine
Adım 2'deki `search_as_you_type` kullanılır. Pahalı sorguları cluster genelinde kapatmak için
`search.allow_expensive_queries: false` ayarı vardır.

---

## Temizlik

Yalnız bu labın index'ini ve eş anlamlı setini siler; ana cluster'a dokunmaz:

```bash
./teardown.sh
```

Beklenen çıktı:

```text
index deneyim-urunler -> 200
synonyms deneyim-esanlam -> 200
```

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

---

Sonraki lab: **[LAB-07 — Aggregation ve Lens Panosu: Veriden Rapor Çıkarmak](../LAB-07-aggregation-lens/README.md)**
