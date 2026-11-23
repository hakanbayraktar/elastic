# Project: NovaCommerce E-Commerce Search FastAPI & Autocomplete

| Profil / Araçlar | Açık Portlar / Slot | Dış Erişim |
|---|---|---|
| Elasticsearch 9.5.5, Kibana, Python 3.12, FastAPI, Dev Tools | **19001** (App1), 9200, 5601 | `http://<IP>:19001`, `https://<host>-app1.devopsatolyesi.com` (Adım 7'de hesaplanır) |

---

## Amaç ve Teorik Çerçeve

Bu labda, büyük ölçekli modern e-ticaret platformlarının arama mimarisini temel alarak; **Search Bar (Arama Çubuğu)**, **Autocomplete (Otomatik Tamamlama)**, **Relevance Boosting (Alaka Düzeyi Mühendisliği)**, **Filtreler/Facets (Aggregations)** ve **ES|QL Analitiği** bileşenlerini uçtan uca inşa edeceksiniz.

Tüm arama altyapısı, LAB-01'de kurulan ana cluster (**Elasticsearch 9.5.5**) ve LAB-04'te eklenen **`kibana_sample_data_ecommerce`** örnek verisiyle beslenir. Bu proje arama labları (LAB-03…06) bittikten sonra önerilir. Uygulama katmanında ise Python 3.12 ve **FastAPI** ile geliştirilmiş, çift erişim modelli (Cloudflare DNS + Doğrudan IP) mikroservis çalıştırılır.

```text
Tarayıcı / İstemci (DNS: <host>-app1.devopsatolyesi.com:443  /  IP: http://<IP>:19001)
                                      │
                                      ▼
                        [Host Nginx Reverse Proxy / Port 19001]
                                      │
                                      ▼
              [FastAPI Arama Mikroservisi (Python 3.12 / Port 19001)]
              ├── GET /api/v1/search/autocomplete?q=...  (4-Clause Should Query + Set Dedup)
              ├── GET /api/v1/search?q=...&category=...  (Full-text + Boosting + Facets)
              └── GET /api/v1/analytics/top-categories   (ES|QL Piped Query)
                                      │
                                      ▼ (Resmi elasticsearch Python SDK)
                   [Elasticsearch 9.5.5 Cluster / Port 9200]
                   ├── kibana_sample_data_ecommerce (Ham Siparişler)
                   └── ecommerce_search_products (Edge N-Gram Özel Arama Kataloğu)
```

---

## Makaledeki Temel Bileşenler ve Mimari Prensipler

### 1. E-Ticaret Aramasının 7 Temel Bileşeni
Bir e-ticaret arama motoru yalnızca "bir arama kutusu" değildir; birbirine bağlı 7 kritik parçadan oluşur:
1. **Search Bar (Arama Çubuğu):** Kullanıcının siteye geldiğinde ilk yöneldiği yer; yazım hatası toleransı, eşanlamlılar ve anlık tamamlama.
2. **Autocomplete (Otomatik Tamamlama):** Kullanıcı kelimeyi tamamlamadan önce en olası eşleşmeleri fırlatan tahmin motoru.
3. **Product Listing (Ürün Listeleme):** Arama sonuçlarının grid veya liste halinde gösterilmesi.
4. **Filters / Facets (Dinamik Filtreleme):** Kategori, marka, fiyat aralığı gibi kriterlerin Bucket Aggregations (`terms`, `range`) ile dinamik hesaplanması.
5. **Sorting (Sıralama):** Fiyata göre (artan/azalan), en çok satanlara (`units_sold`) veya alakaya (`_score`) göre sıralama.
6. **Pagination (Sayfalama):** Sayfa geçişleri (`from`/`size` veya derin sayfalama `search_after`).
7. **Ranking & Scoring (Skorlama):** BM25 formülüne ek olarak alan ağırlıklandırma (Field Boosting) ile en doğru ürünü ilk sıraya taşıma.

---

### 2. Edge N-Gram ve Analyzer Stratejisi
* **Tokenizer (`edge_ngram`):** Kelimenin başından başlayarak 2 ila 20 karakterlik ön ek parçaları üretir.
  * Örnek: `"iphone"` ➔ `["ip", "iph", "ipho", "iphon", "iphone"]`
* **Indexleme Analyzer'ı (`autocomplete_index`):** Doküman yazılırken edge n-gram tokenizer ve `lowercase` filtresini uygular.
* **Arama Analyzer'ı (`autocomplete_search`):** Arama yaparken **standard tokenizer** ve `lowercase` kullanılır.
  > [!IMPORTANT]
  > **Neden Arama Sırasında Edge N-Gram Kullanılmaz?**  
  > Kullanıcı arama çubuğuna `"iph"` yazdığında, bu ifadenin arama anında tekrar n-gram'e bölünmesini istemeyiz. `"iph"` tam olarak bir token olarak kalmalı ve indexlenmiş `["ip", "iph", "ipho", ...]` parçaları arasındaki `"iph"` ile doğrudan birebir eşleşmelidir.

---

### 3. Makaledeki 4-Clause `bool.should` Arama Çubuğu Mimarisi

Kullanıcı davranışları çeşitlidir ("dres" yazıp bekleyen de vardır, "Casual Summer Dress" tam adını yazan da vardır). Tek bir sorgu tipi tüm durumları karşılayamaz:

```json
{
  "bool": {
    "should": [
      {
        "match": {
          "search_autocomplete.autocomplete": {
            "query": "cas",
            "operator": "and",
            "boost": 5
          }
        }
      },
      {
        "term": {
          "search_autocomplete.keyword": {
            "value": "cas",
            "boost": 100
          }
        }
      },
      {
        "multi_match": {
          "query": "cas",
          "fields": ["product_name", "brand"],
          "type": "phrase",
          "slop": 5,
          "boost": 5
        }
      },
      {
        "match_phrase": {
          "search_autocomplete": "cas"
        }
      }
    ]
  }
}
```

* **Clause 1 — Match (Edge N-Gram, `boost: 5`):** Kullanıcı henüz kelimeyi bitirmemişken prefix parçalarını yakalar. `operator: and` ile kullanıcının yazdığı tüm kelimelerin dokümanda bulunması garanti edilir.
* **Clause 2 — Term (Exact Match, `boost: 100`):** Kullanıcı ürünün adını eksiksiz yazdıysa, `keyword` alanındaki birebir eşleşme sonucu listenin en tepesine fırlatır.
* **Clause 3 — Multi-Match Phrase (`slop: 5`, `boost: 5`):** Marka ve ürün adı sıralı aranır. `slop: 5` esnekliği sayesinde marka ile ürün arasına başka kelimeler girse bile (örn: "Oceanavigations *Summer* Dress") sonuç kaçırılmaz.
* **Clause 4 — Match Phrase (`boost: 1`):** Cümledeki kelimelerin katı olarak yan yana ve aynı sırada geçmesini denetler.

---

### 4. Backend Post-Processing ve Tekilleştirme (Deduplication)
Elasticsearch'ten gelen 30 sonuç arasında aynı model adı farklı varyasyonlarla onlarca kez geçebilir. Python katmanında:
1. Sonuçların `search_autocomplete` alanları okunur.
2. Python `set()` veri yapısı ile küçük harf duyarlı tekilleştirme yapılır.
3. Skor sıralaması korunarak kullanıcıya ilk 10 temiz öneri iletilir.

---

## Python ile Elasticsearch 9.x Bağlantı Rehberi

Python uygulamasından Elasticsearch'e bağlanmak için resmi `elasticsearch` kütüphanesi kullanılır:

### 1. Kütüphanenin Yüklenmesi
Ubuntu 24.04'te sistem Python'u PEP 668 ile korunur; `pip install` doğrudan çalıştırılırsa
`externally-managed-environment` hatası verir. Paketler bu yüzden projeye ait bir sanal ortama
(`.venv`) kurulur. Kurulum komutu Adım 2'dedir:

```text
python3 -m venv .venv && source .venv/bin/activate && pip install -r app/requirements.txt
```

### 2. Güvenli ve Dayanıklı Bağlantı Kodu
```python
import os
import urllib3
from elasticsearch import Elasticsearch

# Lab ortamındaki self-signed TLS sertifika uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = Elasticsearch(
    hosts=[os.getenv("ELASTIC_URL", "http://localhost:9200")],
    basic_auth=(
        os.getenv("ELASTIC_USER", "elastic"),
        os.getenv("ELASTIC_PASSWORD", "DevOps2026!")
    ),
    verify_certs=False,        # Prodüksiyonda ca_certs="/path/to/ca.crt" kullanılmalıdır
    ssl_show_warn=False,
    request_timeout=30,        # Zaman aşımı (sn)
    max_retries=3,             # Başarısız isteklerde 3 kez tekrar dene
    retry_on_status=(502, 503, 504) # Gateway hatalarında otomatik yeniden dene
)

# Bağlantı ve Sağlık Testi
if client.ping():
    info = client.info()
    print(f"✅ Bağlantı Başarılı: Cluster={info['cluster_name']}, Sürüm={info['version']['number']}")
```

---

## Çift Erişim Modeli ve Port Eşleşmesi (App1 / Port 19001)

Eğitim altyapımızdaki `elastic.sh` şablonu ve DNS otomasyonu (`dnsupdate`) ile %100 uyumluluk için uygulamamız **Port 19001 (App1 Slotu)** üzerinde çalışır:

| Erişim Kanalı | URL Formatı | İletim Mekanizması |
|---|---|---|
| **1. Cloudflare DNS (HTTPS)** | `https://<host>-app1.devopsatolyesi.com` | Cloudflare Edge (443) ➔ Host Nginx (Regex `app1`) ➔ `127.0.0.1:19001` |
| **2. Doğrudan IP (Port Erişimi)** | `http://<IP>:19001` | Linux Host (`0.0.0.0:19001`) ➔ FastAPI Servisi |
| **3. Yerel Erişim (Localhost)** | `http://localhost:19001` | Doğrudan Loopback |

> [!NOTE]
> Uygulamamız `HOST="0.0.0.0"` üzerinde dinlediği için hem yerel Nginx ters proxy'si hem de dış dünyadan doğrudan Public IP üzerinden gelen çağrılar eksiksiz yanıtlanır.

---

## Dosya ve Dizin Yapısı

```text
projects/ecommerce-fastapi-search/
├── README.md                                  # Kapsamlı teorik ve pratik lab rehberi
├── run-search-api.sh                          # Servisi ve veri ETL'ini tek komutla başlatan script
├── verify.sh                                  # Cluster, index, mapping ve servis doğrulayıcı
├── docker-compose.app1.yml                    # Konteynerize App1 çalıştırma profili
├── Dockerfile                                 # Python 3.12-slim tabanlı imaj tarifi
├── dev-tools/                                 # Kibana Dev Tools Console sorguları
│   ├── 01-create-autocomplete-schema.http     # Custom edge_ngram tokenizer ve explicit mapping
│   ├── 02-search-bar-4clause-queries.http     # Makaledeki 4 clause'lu should sorgusu denemeleri
│   ├── 03-catalog-fullsearch-facets.http      # Katalog arama, boosting, facets ve sayfalama
│   └── 04-kql-and-esql-comparisons.http       # KQL ve modern ES|QL analitik karşılaştırmaları
├── app/                                       # FastAPI Arama Mikroservisi
│   ├── main.py                                # FastAPI uygulaması, CORS ve HTML karşılama
│   ├── config.py                              # Port 19001 ve ES ortam değişkenleri
│   ├── es_client.py                           # Elasticsearch bağlantı yöneticisi
│   ├── routers/
│   │   ├── autocomplete.py                    # 4-Clause autocomplete ve set deduplication endpoint'i
│   │   ├── search.py                          # Full-text, boosting, facets ve filtreleme
│   │   └── analytics.py                       # ES|QL analitik endpoint'i
│   ├── schemas/
│   │   └── search_models.py                   # Pydantic v2 veri modelleri
│   └── requirements.txt                       # Python paket bağımlılıkları
└── scripts/
    ├── ingest_from_kibana_sample.py           # kibana_sample_data_ecommerce ETL scripti
    └── test_search_api.py                     # Uç noktaları test eden otomatik senaryo scripti
```

---

## Adım Adım Uygulama Rehberi

### Adım 1: Elasticsearch ve Kibana'nın Hazır Olduğunu Doğrulayın
LAB-01 ana cluster'ı çalışır durumda olmalıdır (LAB-04'ün örnek verisi de yüklü olmalı). Proje bu sunucuda daha önce kurulduysa önce **Temizlik** bölümündeki komutu çalıştırın:

```bash
curl -s -u elastic:DevOps2026! http://localhost:9200/_cluster/health?pretty
```

*(Eğer cluster çalışmıyorsa: `docker start elasticsearch-lab00 kibana-lab00` komutunu çalıştırın).*

---

### Adım 2: Python Ortamını Kurun ve Arama Kataloğunu Üretin (ETL)
Projeye ait sanal ortamı kurun; ETL scripti `kibana_sample_data_ecommerce` index'indeki
siparişlerden tekil ürünleri çıkarır ve `ecommerce_search_products` index'ini **edge n-gram
analyzer'lı mapping ile** baştan oluşturur:

```bash
cd ~/elastic/projects/ecommerce-fastapi-search
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r app/requirements.txt
python3 scripts/ingest_from_kibana_sample.py
```

*Çıktıda tekil ürünlerin tespit edildiğini ve başarıyla indexlendiğini doğrulayın.*
Index'in mapping'i [`dev-tools/01-create-autocomplete-schema.http`](dev-tools/01-create-autocomplete-schema.http)
dosyasındaki şemayla aynıdır; Dev Tools'ta o dosyayı çalıştırırsanız index'i silip boş
oluşturur, bu durumda ETL'i tekrar çalıştırın.

---

### Adım 3: Edge N-Gram Parçalamasını Dev Tools'ta Görün
Kibana arayüzünden **Management ➔ Dev Tools ➔ Console** ekranını açın ve `"Casual Dress"`
ifadesinin indexleme sırasında nasıl ön eklere ayrıldığını görün:

```http
POST ecommerce_search_products/_analyze
{
  "analyzer": "autocomplete_index",
  "text": "Casual Dress"
}
```

---

### Adım 4: Dev Tools Üzerinde 4-Clause Arama Çubuğu Sorgularını Test Edin
[`dev-tools/02-search-bar-4clause-queries.http`](dev-tools/02-search-bar-4clause-queries.http) dosyasındaki sorguları Dev Tools'ta sırayla deneyin:
* **"cas"** yazıldığında Edge N-Gram'in anlık eşleşmesini gözlemleyin.
* **"Casual Dress"** tam adı yazıldığında `term` clause'unun `boost: 100` etkisiyle ilgili ürünü en tepeye fırlatışını izleyin.
* **"Elitelligence Shoes"** yazıldığında `slop: 5` toleransıyla marka ve ürün adının sıralı yakalanışını test edin.

[`dev-tools/04-kql-and-esql-comparisons.http`](dev-tools/04-kql-and-esql-comparisons.http) dosyasından da KQL ve ES|QL analitik sorgularını çalıştırın.

---

### Adım 5: FastAPI Arama Servisini Başlatın
Arama mikroservisi konteyner olarak Port **19001** üzerinde başlar ve ana cluster'ın Docker ağına
(`elastic-lab00_default`) katılarak Elasticsearch'e `elasticsearch-lab00:9200` adıyla erişir:

```bash
cd ~/elastic/projects/ecommerce-fastapi-search
docker compose -f docker-compose.app1.yml up -d --build 2>&1 | tail -1
timeout 120 bash -c 'until curl -sf http://localhost:19001/api/v1/health >/dev/null; do printf .; sleep 2; done'; echo
curl -s http://localhost:19001/api/v1/health | jq .
```

Geliştirme modunda (kod değişikliğini konteyner yeniden kurmadan denemek için) aynı servisi
ön planda da çalıştırabilirsiniz; terminal servis kapatılana kadar meşgul kalır, testler için
ikinci bir terminal açın. Konteyner çalışıyorsa önce onu durdurun (aynı port):

<!-- runner:skip -->
```bash
docker compose -f docker-compose.app1.yml down
./run-search-api.sh
```

---

### Adım 6: API Uç Noktalarını Test Edin

Sağlanan otomatik test scriptini çalıştırın:

```bash
cd ~/elastic/projects/ecommerce-fastapi-search
python3 scripts/test_search_api.py
```

Dilerseniz `curl` ile elle de test edebilirsiniz:

```bash
# 1. Autocomplete Testi:
curl -s "http://localhost:19001/api/v1/search/autocomplete?q=cas&limit=5" | jq .

# 2. Katalog Arama ve Dinamik Filtreler Testi:
curl -s "http://localhost:19001/api/v1/search?q=dress&category=Women's%20Clothing" | jq .

# 3. ES|QL Analitik Testi:
curl -s "http://localhost:19001/api/v1/analytics/top-categories" | jq .
```

---

### Adım 7: İnteraktif Swagger Dokümantasyonunu Açın
Adresleri sunucuda hesaplayın ve tarayıcıda açıp parametreleri görsel olarak deneyin:

```bash
IP=$(curl -s https://api.ipify.org); H=$(hostname -s)
echo "Swagger: http://$IP:19001/docs   https://$H-app1.devopsatolyesi.com/docs"
```

Beklenen çıktı:

```text
Swagger: http://<IP>:19001/docs   https://<host>-app1.devopsatolyesi.com/docs
```

---

## Doğrulama (Verify)

<details>
<summary><strong>Toplu kontrol betiği</strong></summary>

```bash
./verify.sh
```

</details>

---

## Temizlik

```bash
cd ~/elastic/projects/ecommerce-fastapi-search
./teardown.sh
```

Silinenler: `ecommerce-search-fastapi` compose projesi (konteyner ve imaj) ve
`ecommerce_search_products` index'i. Ana cluster (`elasticsearch-lab00`, `kibana-lab00`) ve
`kibana_sample_data_ecommerce` örnek verisi **silinmez**; proje tekrar kurulabilir.
