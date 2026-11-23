# LAB-06 — Arama Deneyimi: Otomatik Tamamlama, Yazım Hatası, Eş Anlamlılar

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Kibana Dev Tools, curl, Synonyms API | 9200 (Elasticsearch), 5601 (Kibana) — LAB-01 ana cluster'ı |

---

## Bu lab ne öğretiyor?

- Yazarken öneri: otomatik tamamlama
- Yazım hatası toleransı: "klavey" yazan da klavyeyi bulsun
- Eş anlamlılar: "headset" arayan kulaklığı görsün
- Ad eşleşmesini öne çıkarmak, eşleşen kelimeyi vurgulamak
- Joker karakterli aramanın tuzağı

---

## Ön Koşullar

- LAB-01 ana cluster'ı çalışıyor.
- Önceki labları atladıysanız da lab çalışır: index, analyzer'lar ve veri bu labda kurulur.

```bash
cd ~/elastic/labs/LAB-06-arama-deneyimi
```

---

## Kavramlar

- **analyzer:** metni aranabilir token'lara çeviren zincir (kelimelere bölme, küçük harf, kök bulma)
- **`analyzer` / `search_analyzer`:** biri document yazılırken, öteki sorgu çalışırken kullanılır
- **eş anlamlılar arama tarafında:** index küçük kalır; liste değişince document'leri yeniden yazmak gerekmez
- **`search_as_you_type`:** otomatik tamamlama için kelime başlarını hazır tutan field tipi
- **`fuzziness`:** yazım hatasına kelime uzunluğuna göre izin verir

---

## Adım Adım Uygulama Rehberi

Bu labda `http` bloklarını Kibana › Dev Tools'a, `bash` bloklarını terminale yapıştırın.

### 1. Eş anlamlı seti, index ve veri

**Soru: Arama kutusunun beklentilerini karşılayacak index nasıl kurulur?** Önce eş anlamlı seti, sonra index, sonra veri.

**Eş anlamlı setini açın.** Eş anlamlılar index'ten ayrı, adı olan bir sette durur (Synonyms API):

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

- **`id`:** kuralın adı; sonra tek tek güncellemek için
- **kural:** virgülle ayrılmış, birbirinin yerine geçen kelimeler; "cep telefonu" gibi iki kelimelik ifade de olur

**Index'i açın.** İki analyzer ve bir öneri field'ı var; `standard` tokenizer metni böler, filtreler sırayla uygulanır:

- **`apostrophe`:** kesme işaretinden sonrasını atar ("Kulaklık'ı" → "Kulaklık").
- **`tr_kucuk`:** Türkçe kurallarla küçük harf (I → ı, İ → i).
- **`tr_kok`:** kelimeyi köküne indirir ("kulaklıklar" → "kulaklık").
- **`tr_esanlam`:** setteki eş anlamlıları ekler; `synonym_graph` çok kelimeli ifadeleri doğru eşler.

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

- **`tr_index`:** yazarken Türkçe küçük harf ve kök.
- **`tr_arama`:** ararken aynısı, artı eş anlamlılar. `updateable: true` setin güncellenince yeniden
  yüklenmesini sağlar; yalnız arama analyzer'ında kullanılabilir.
- **`tr_oneri`:** yalnız küçük harf; kök bulmaz, çünkü öneride kullanıcının yazdığı harflerle eşleşmek gerekir.
- **`ad.oneri`:** `search_as_you_type` field'ı, otomatik tamamlama için kelime başlarını hazır tutar.

**Örnek veriyi oluşturun:** yedi ürün, her biri eylem satırı + document satırı (`sample-data/urunler.ndjson`):

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

**Dosyayı `_bulk` ile yükleyin:**

```bash
curl -s -u elastic:'DevOps2026!' -X POST 'http://127.0.0.1:9200/_bulk?refresh=true&filter_path=errors' \
  -H 'Content-Type: application/x-ndjson' --data-binary @sample-data/urunler.ndjson; echo
```

Beklenen çıktı:

```text
{"errors":false}
```

### 2. Otomatik tamamlama

**Soru: Kullanıcı yazarken öneriyi nasıl veririz?**

- **`multi_match`:** aynı metni birden çok field'da arar (`ad.oneri` ve iki alt field'ı)
- **`type: bool_prefix`:** son kelimeyi yarım yazılmış sayar

**Kullanıcı "kab" yazdı:**

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

```json
{"hits":{"hits":[{"_source":{"ad":"Kablosuz Kulaklık"}},{"_source":{"ad":"Kablolu Kulaklık"}},{"_source":{"ad":"Kablosuz Klavye"}},{"_source":{"ad":"Şarj Kablosu"}}]}}
```

**Yazmaya devam etti: "kablosuz ku":**

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

```json
{"hits":{"hits":[{"_source":{"ad":"Kablosuz Kulaklık"}},{"_source":{"ad":"Kablosuz Klavye"}},{"_source":{"ad":"Kablolu Kulaklık"}},{"_source":{"ad":"Oyuncu Kulaklığı"}}]}}
```

| Yazılan | Öneriler (sırayla) |
|---|---|
| `kab` | Kablosuz Kulaklık · Kablolu Kulaklık · Kablosuz Klavye · Şarj Kablosu |
| `kablosuz ku` | Kablosuz Kulaklık · Kablosuz Klavye · Kablolu Kulaklık · Oyuncu Kulaklığı |

**Neden "Kablolu Kulaklık" da geldi?** `bool_prefix` "kablosuz ku" metnini koşullara böler ve **biri tutsa yeter** (OR):

- **"kablosuz":** tam kelime olarak aranır
- **"ku…":** son kelime yarım yazılmış sayılır; "ku" ile başlayan her kelime tutar (kulaklık, kulaklığı)
- **yan yana:** `_2gram` alt field'ı yan yana iki kelimeyi tek parça saklar ("kablosuz kulaklık"); "kablosuz ku" bu çiftle de
  eşleşir. `_3gram` aynısını üç kelime için yapar.

| Sıra · ürün | "kablosuz" | "ku…" | yan yana | Tutan |
|---|---|---|---|---|
| 1 · Kablosuz Kulaklık | var | var | var | 3 |
| 2 · Kablosuz Klavye | var | – | – | 1 |
| 3 · Kablolu Kulaklık | – | var | – | 1 |
| 4 · Oyuncu Kulaklığı | – | var | – | 1 |

Kablolu Kulaklık'ta "kablosuz" yok ama "kulaklık" "ku" ile başlıyor; listeye bu yüzden girer. Çok parçası tutan ürün üste çıkar.

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

**Soru: Yazım hatası yapan kullanıcı ürünü bulabilir mi?** "klavey" yazıldı:

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": "klavey" } } }
```

```json
{"hits":{"total":{"value":0}}}
```

**Aynı arama, yazım hatasına izin vererek (`fuzziness`):**

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": { "query": "klavey", "fuzziness": "AUTO" } } } }
```

```json
{"hits":{"total":{"value":1},"hits":[{"_source":{"ad":"Kablosuz Klavye"}}]}}
```

| Sorgu | Sonuç |
|---|---|
| `match` "klavey" | 0 |
| `match` "klavey", `fuzziness: AUTO` | 1: Kablosuz Klavye |

- **`fuzziness: AUTO`:** harf farkına (silme, ekleme, değiştirme, yer değiştirme) kelime uzunluğuna göre izin verir.
- **Ne kadar?** 1-2 harfte hiç, 3-5 harfte bir, daha uzun kelimede iki fark.
- **Neden kısa kelimede kapalı?** İki harflik bir arama yüzlerce kelimeyle eşleşirdi.

### 4. Eş anlamlılar

**Soru: Kullanıcı ürün adında geçmeyen bir kelime yazarsa?** Ürün adlarında geçmeyen "headset" kelimesini arayın:

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": "headset" } } }
```

```json
{"hits":{"total":{"value":3},"hits":[{"_source":{"ad":"Kablosuz Kulaklık"}},{"_source":{"ad":"Kablolu Kulaklık"}},{"_source":{"ad":"Oyuncu Kulaklığı"}}]}}
```

- **Sonuç 3:** Kablosuz Kulaklık, Kablolu Kulaklık, Oyuncu Kulaklığı. Arama analyzer'ı "headset"i "kulaklık"a genişletti.
- **"kulaklik"** (ı'sız) da aynı kuralla bulunur.

**Listede olmayan bir kelime** (sonuç 0):

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value
{ "query": { "match": { "ad": "headphone" } } }
```

```json
{"hits":{"total":{"value":0}}}
```

**Kuralı güncelleyin.** Index kapatılmaz, document'ler yeniden yazılmaz:

```http
PUT /_synonyms/deneyim-esanlam/kulaklik?filter_path=result,reload_analyzers_details.reload_details.reloaded_analyzers
{ "synonyms": "kulaklık, kulaklik, headset, headphone" }
```

```json
{"result": "updated", "reload_analyzers_details": {"reload_details": [{"reloaded_analyzers": ["tr_arama"]}]}}
```

**`reloaded_analyzers`:** setin değişmesiyle yeniden yüklenen analyzer'lar; yalnız arama analyzer'ı `tr_arama`.

```http
GET /deneyim-urunler/_search?filter_path=hits.total.value,hits.hits._source.ad
{ "query": { "match": { "ad": "headphone" } } }
```

```json
{"hits":{"total":{"value":3},"hits":[{"_source":{"ad":"Kablosuz Kulaklık"}},{"_source":{"ad":"Kablolu Kulaklık"}},{"_source":{"ad":"Oyuncu Kulaklığı"}}]}}
```

- **Sonuç artık 3 kulaklık:** set güncellenince onu kullanan arama analyzer'ları yeniden yüklenir.
- **Neden arama tarafında?** Yazma tarafında olsaydı eski token'lar kalır, yeni kural için `_reindex` gerekirdi.
- **Arayüzden:** kural listesi Kibana'da **Elasticsearch › Synonyms** sayfasından da yönetilir.

### 5. Önemli field'ı öne çıkarmak ve vurgulamak

**Soru: Ürün adındaki eşleşme açıklamadakinden önde olsun, kelime de vurgulansın: nasıl?** Ad ve açıklamada
birlikte arayın; addaki eşleşme üç kat değerli, eşleşen kelime işaretli:

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

- **`ad^3`:** ad field'ının skoru 3 ile çarpılır; "Şarj Kablosu"nun yalnız açıklamasında "kulaklık" geçer, en altta kalır
  ama listeden düşmez.
- **`highlight`:** eşleşen kelimeyi `<em>` ile sarar; "Kulaklığı" da işaretlenir (kök bulma sayesinde aynı terim).

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

**Soru: Yıldızlı arama neden bazen hiçbir şey bulmaz?** Kullanıcı "kulaklıklar" yazdı, bir de sonuna yıldız koydu.

**`match`:**

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "match": { "ad": "kulaklıklar" } } }
```

```json
{"count":3}
```

**Aynı kelime, sonuna yıldız koyarak (`wildcard`):**

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "wildcard": { "ad": { "value": "kulaklıklar*" } } } }
```

```json
{"count":0}
```

**Daha kısa bir başlangıçla (`kulak*`):**

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "wildcard": { "ad": { "value": "kulak*" } } } }
```

```json
{"count":3}
```

| Sorgu | Sayı |
|---|---|
| `match` "kulaklıklar" | 3 |
| `wildcard` "kulaklıklar*" | 0 |
| `wildcard` "kulak*" | 3 |

- **`match`:** analyzer'dan geçirir: "kulaklıklar" → `kulaklık`, index'teki terimle aynı: 3.
- **`wildcard`:** analyzer'dan **geçmez**; index'te "kulaklıklar" ile başlayan terim yok: 0.
- **`kulak*`:** `kulaklık` terimini yakalar: 3.

**Çözüm: `query_string` + `analyze_wildcard`.** `query_string` sorguyu tek metin olarak alır, `AND`, `OR`, `*` işaretlerini
kendisi çözer (Kibana'da Lucene sözdizimi). `analyze_wildcard: true` yıldızlı kelimeyi de analyzer'dan geçirir (sonuç 3):

```http
GET /deneyim-urunler/_count?filter_path=count
{ "query": { "query_string": { "query": "kulaklıklar*", "fields": ["ad"], "analyze_wildcard": true } } }
```

```json
{"count":3}
```

- **Yıldızın yeri:** `kulak*` (sonda) hızlıdır; `*lak` (başta) bütün terimleri tarar, büyük index'te yavaştır.
- **Yazarken arama için** wildcard yerine Adım 2'deki `search_as_you_type`.
- **Pahalı sorguları kapatmak:** cluster ayarı `search.allow_expensive_queries: false`.
- **Kullanıcı girdisi için `simple_query_string`:** `query_string` hatalı sözdiziminde (kapanmayan tırnak, tek `(`) hata
  verir ve baştaki jokere izin verir; `simple_query_string` hatalı kısmı yok sayar, arama kutusu için daha güvenlidir.

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
