# Project: NovaShop E-Commerce Search Service & Relevance

Bu labda, NovaShop e-ticaret platformunun ürün kataloğunu Elasticsearch ile indexleyecek; tam metin arama (full-text search), alakadarlık (relevance ranking), yazım hatası toleransı (fuzziness), otomatik tamamlama (autocomplete) ve çok boyutlu filtreleme (aggregations) mantığını uygulayacaksınız. 

Son adımda ise port **8080** üzerinde çalışan canlı Spring Boot Arama Servisini ayağa kaldırarak gerçek arama API'sini sunucunun IP'si ve alan adıyla (adresler Adım 5'te) test edeceksiniz.
Bu proje arama labları (LAB-03…06) bittikten sonra önerilir.

---

## Amaç

1. **E-Ticaret Veri Modeli:** `ecommerce-products-v1`, `ecommerce-customers-v1` ve `ecommerce-orders-v1` şemalarını oluşturmak.
2. **Relevance Mühendisliği:** Multi-match, field boosting (`name^2`), slop proximity (`match_phrase`), fuzziness ve bool query kombinasyonlarını deneyimlemek.
3. **Analitik ve Faceted Search:** Fiyat dilimleri, kategori dağılımı ve aylık ciro aggregasyonlarını çalıştırmak.
4. **İleri İlişkisel Modelleme:** Ürün-Yorum arasında Parent-Child (`join` type) ilişkisi kurmak, shard routing zorunluluğunu ve `has_child`/`has_parent` sorgularını deneyimlemek.
5. **Canlı NovaShop Entegrasyonu:** Spring Boot REST arama servisini port `8080`'de çalıştırıp canlı API testini yapmak.
6. **İş Zekası (BI) ve Satış Dashboard'u:** Toplam ciro, sipariş hacmi, kategori dağılımı (Pie) ve en çok satan ürünleri Kibana panosunda görselleştirmek.
7. **Yönetim PDF Raporlama & Zamanlanmış Dağıtım:** E-ticaret satış panosunun headless PDF çıktısını almak ve haftalık otomatik e-posta gönderimini yapılandırmak.

---

## Dosyalar

```text
ecommerce-spring-search/
├── adapter/                        # Spring Boot 3 & Java 21 REST arama servisi
│   ├── pom.xml
│   └── target/product-search-adapter-1.0.0-SNAPSHOT.jar
├── dev-tools/                      # Kibana Dev Tools Console sorguları
│   ├── 01-create-ecommerce-schema.http
│   ├── 02-bulk-ecommerce-data.http
│   ├── 03-ecommerce-search-and-filtering.http
│   ├── 04-ecommerce-aggregations-and-analytics.http
│   └── 05-relational-join-parent-child.http
├── docker-compose.novashop.yml     # Konteynerize çalıştırma profili
├── run-novashop.sh                 # Tek komutla yükleme, başlatma ve test scripti
├── sample-data/                    # Ürün, müşteri ve sipariş NDJSON veri setleri
└── scripts/load_ecommerce_data.py  # Python toplu veri yükleyici
```

---

## Uygulama Adımları

### 0. Elasticsearch ve Kibana'nın Hazır Olduğunu Doğrulayın

Bu proje LAB-01 ana cluster'ını kullanır. Proje bu sunucuda daha önce kurulduysa önce **Temizlik** bölümündeki komutu çalıştırın:

```bash
curl -s -u elastic:DevOps2026! http://localhost:9200/_cluster/health?pretty
```

*(Eğer cluster çalışmıyorsa: `docker start elasticsearch-lab00 kibana-lab00` komutunu çalıştırın).*

### 1. Şema (Mapping) ve Toplu Veri Yükleme

Şemayı ([`dev-tools/01-create-ecommerce-schema.http`](dev-tools/01-create-ecommerce-schema.http): üç index, alias'lar,
tek node için replica 0) kurun, sonra veriyi yükleyin. Aynı dosyayı Kibana › Dev Tools'a yapıştırarak da çalıştırabilirsiniz:

```bash
cd ~/elastic/projects/ecommerce-spring-search
python3 scripts/apply_http.py dev-tools/01-create-ecommerce-schema.http
python3 scripts/load_ecommerce_data.py
```
   *`_count` çağrısında 20 ürün, 20 müşteri ve 20 siparişin başarıyla eklendiğini doğrulayın.*

---

### 2. Alakadarlık (Relevance) ve Arama Sorguları

[`dev-tools/03-ecommerce-search-and-filtering.http`](dev-tools/03-ecommerce-search-and-filtering.http) dosyasındaki sorguları Dev Tools'ta sırayla deneyin:

* **Field Boosting (`name^2`):**
  Arama terimi hem başlıkta hem açıklamada geçtiğinde, ürün adında geçen eşleşmenin 2 kat daha yüksek skor (`_score`) almasını sağlayın.
* **Fuzzy Search (`fuzziness: "AUTO"`):**
  Kullanıcı arama kutusuna `"wirless"` yazdığında bile `"Wireless"` kulaklık ürününün bulunabilmesini test edin.
* **Phrase Slop (`slop: 2`):**
  Kelimeler arasında başka sözcükler olsa dahi (`match_phrase`) yakınlık toleransıyla sonuç getirin.
* **Bool Filtreleme:**
  Kategori `Electronics` olan ve stokta bulunan (`in_stock: true`) ürünleri puan hesaplamadan (`filter context`) anında listeleyin.

---

### 3. Faceted Search ve Metrik Analitiği (Aggregations)

[`dev-tools/04-ecommerce-aggregations-and-analytics.http`](dev-tools/04-ecommerce-aggregations-and-analytics.http) dosyasını Console'da çalıştırın:
* **Fiyat Aralıkları (Ranges):** Ürünleri bütçe dilimlerine (<50, 50-200, >=200) göre gruplayın.
* **Kategori Bazında Ortalama Fiyat:** `terms` kategorileri altında `avg` alt-aggregasyonu ile her kategorinin ortalama sepet fiyatını çıkarın.
* **Aylık Ciro:** Siparişler üzerinde `date_histogram` ile aylık satış trendini hesaplayın.

---

### 4. Canlı NovaShop Arama Servisini Başlatın (Port 8080)

Host sunucunuzda NovaShop arama servisini ayağa kaldırmak için iki pratik yöntem sunulmuştur:

#### Yöntem A: Otomatik Başlatıcı Script (Önerilen)
```bash
cd ~/elastic/projects/ecommerce-spring-search
./run-novashop.sh
```
Bu script şemayı kontrol eder, eksik veriyi yükler, Spring Boot servisini başlatır ve canlı arama testini gerçekleştirir.

#### Yöntem B: Manuel Docker Compose ile Çalıştırma
İmaj, `Dockerfile` içindeki çok aşamalı derlemeyle (Maven + JDK 21 → JRE 21) üretilir; host'ta
Java veya Maven gerekmez:

Servis Elasticsearch'e parola yerine **API key** ile bağlanır. Key yalnızca ürün index'ini
okuyabilir (en az yetki); `ELASTICSEARCH_API_KEY` boş kalırsa konteyner kimliksiz istek atar ve
her arama `503 search_unavailable` döner:

```bash
cd ~/elastic/projects/ecommerce-spring-search
export ELASTICSEARCH_API_KEY=$(curl -s -u elastic:'DevOps2026!' -X POST "http://localhost:9200/_security/api_key" \
  -H 'Content-Type: application/json' \
  -d '{"name":"novashop-adapter","role_descriptors":{"novashop_search":{"indices":[{"names":["ecommerce-products-v1"],"privileges":["read","view_index_metadata"]}]}}}' \
  | jq -r .encoded)
docker compose -f docker-compose.novashop.yml up -d --build
for i in $(seq 1 40); do curl -sf "http://127.0.0.1:8080/api/products/search?q=wireless" >/dev/null && break; sleep 3; done
curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:8080/api/products/search?q=wireless"
```

Host'ta JDK 21 ve Maven kuruluysa JAR'ı önce derleyip doğrudan da çalıştırabilirsiniz
(`adapter/target/` derlemeden önce boştur):

<!-- runner:skip -->
```bash
mvn -q -f adapter/pom.xml package -DskipTests
nohup java -jar adapter/target/product-search-adapter-1.0.0-SNAPSHOT.jar > /tmp/search-service.log 2>&1 &
echo $! > /tmp/search-service.pid
```

---

### 5. Canlı Arama API'sini Doğrulayın

Servis ayağa kalktıktan sonra hem yerel porttan hem de dış HTTPS alan adınızdan sorgulayın:

```bash
# 1. Ürün Arama API'si
curl -s "http://127.0.0.1:8080/api/products/search?q=wireless&category=Electronics" | jq .

# 2. Otomatik Tamamlama (Autocomplete / Suggest) API'si
curl -s "http://127.0.0.1:8080/api/products/suggest?q=Smart" | jq .
```

Dışarıdan erişim adresleri sunucudan hesaplanır; alan adı üzerinden aynı arama:

```bash
IP=$(curl -s https://api.ipify.org); H=$(hostname -s)
echo "NovaShop API: http://$IP:8080/api/products/search?q=wireless   https://$H-novashop.devopsatolyesi.com/api/products/search?q=wireless"
curl -s "https://$H-novashop.devopsatolyesi.com/api/products/search?q=wireless" | jq -c '{total: (.total // .totalHits // null)}'
```

Beklenen çıktı:

```text
NovaShop API: http://<IP>:8080/api/products/search?q=wireless   https://<host>-novashop.devopsatolyesi.com/api/products/search?q=wireless
{"total":2}
```

---

### 6. İleri İlişkisel Modelleme: Parent-Child (`join`) ve Shard Routing

E-ticaret platformlarında bir ürünün binlerce müşteri yorumu ve puanı olabilir. Eğer bu yorumları ürün dokümanı içinde `nested` nesne olarak tutarsanız, **her yeni yorum geldiğinde tüm ürün dokümanı baştan indexlenir (reindex)**.

Bu problemi çözmek için Elasticsearch **Parent-Child (`join`)** veri tipini sunar. Ürün ve yorumlar **tamamen bağımsız dokümanlar** olarak saklanır. Ancak Lucene'in ilişkisel sorgu yapabilmesi için bir parent ve onun tüm child'larının **aynı fiziksel shard'da** yaşaması şarttır. Bu yüzden child doküman eklenirken `?routing=<parent_id>` zorunludur!

Kibana Dev Tools'ta [`dev-tools/05-relational-join-parent-child.http`](dev-tools/05-relational-join-parent-child.http) dosyasını açıp sırayla uygulayın:

1. **index'i Tanımlama:** `catalog_relation: { "type": "join", "relations": { "product": "review" } }` haritasını oluşturun.
2. **Parent (Ürün) ve Child (Yorum) Ekleme:** Yorumları eklerken `?routing=prod-101` parametresini verin.
3. **`has_child` ile Ürün Bulma:** *"En az 5 yıldızlı yorumu olan ürünleri listele ve inner_hits ile o 5 yıldızlı yorumu da ürünün altına iliştir!"*
4. **`has_parent` ile Yorum Bulma:** *"Fiyatı 2.000 TL üzeri olan elektronik ürünlere yapılmış yorumları getir!"*
5. **`parent_id` Sorgusu:** Belirli bir ürünün tüm yorumlarını hızlıca filtreleyin.

---

### 7. NovaShop E-Commerce Satış & Ciro Analitiği Dashboard'u

NovaShop e-ticaret verilerinden (ciro, sipariş adedi, kategori payları, çok satanlar ve coğrafi satışlar) yönetim düzeyinde bir analitik panosu oluşturabilirsiniz.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  Kibana ➔ Analytics ➔ Dashboard ➔ [ NovaShop E-Commerce Sales & Analytics ]           │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│  [ Panel 1: Toplam Satış Cirosu ($) ]    │  [ Panel 2: Toplam Sipariş Sayısı ]         │
│  Metric KPI: sum(taxful_total_price)     │  Metric KPI: count()                        │
├──────────────────────────────────────────┴─────────────────────────────────────────────┤
│  [ Panel 3: Kategori Bazında Satış Payı ]                                              │
│  Pie Chart: Terms(category.keyword), Metric: sum(taxful_total_price)                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  [ Panel 4: Günlük Satış ve Ciro Zaman Trendi ]                                        │
│  Area Chart: Date Histogram(order_date), Metric: sum(taxful_total_price)               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  [ Panel 5: En Çok Ciro Getiren 10 Ürün ]                                              │
│  Horizontal Bar: Terms(products.product_name.keyword), Metric: sum(taxful_total_price) │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  [ Panel 6: Şehir ve Ülke Bazında Sipariş / Gelir Tablosu ]                             │
│  Data Table: geoip.country_iso_code, geoip.city_name, Count, Sum(Revenue)              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Otomatik Kurulum:
Panoyu tek komutla Kibana üzerinde oluşturmak için:
```bash
cd ~/elastic/projects/ecommerce-spring-search
python3 scripts/provision_dashboard.py
```
*Bu script Data View (`novashop-orders`), 6 adet zengin Lens görselleştirmesini ve `novashop-ecommerce-analytics` panosunu otomatik olarak Kibana'ya kaydeder.*

---

### 8. Yönetim PDF Satış Raporu Çıkarma ve Zamanlanmış Dağıtım

Yönetim kuruluna veya e-ticaret operasyon ekibine haftalık/aylık satış raporlarını sunmak için Kibana Reporting motorunu kullanabilirsiniz.

#### Yöntem 1: Kibana UI ile Anlık PDF İndirme
1. Kibana'da **Analytics ➔ Dashboard** yolundan `NovaShop E-Commerce Sales & Analytics` panosunu açın.
2. Sağ üstteki **Export ➔ PDF reports** seçeneğine tıklayın (**Share** yalnız bağlantı içindir).
3. **Export PDF** butonuna basın. Headless Chromium motoru panoyu vektörel PDF olarak derler.
4. **Stack Management ➔ Reporting** listesinde raporun durumu `Done` olunca **Download report** diyerek PDF'i
   bilgisayarınıza indirin.

> [!IMPORTANT]
> **Lisans ön koşulu.** PDF ve PNG reporting **Basic** lisansta kullanılamaz;
> `standard` ve üstü (veya trial) gerekir. Yöntem 3'teki otomatik e-posta
> gönderimi ayrıca bir e-posta connector'ı istediği için `gold` ve üstü ister.
> Lisansınızı kontrol edin:
>
> ```bash
> curl -s -u "elastic:DevOps2026!" "http://127.0.0.1:9200/_license?pretty"
> ```
>
> `"type": "basic"` görüyorsanız LAB-01'deki trial adımını uygulayın:
> `POST _license/start_trial?acknowledge=true`. Basic lisansta kalmak
> isterseniz bu bölüm yerine Discover üzerinden **CSV export** kullanabilirsiniz;
> CSV reporting Basic lisansta çalışır.

#### Yöntem 2: Kibana REST API ile PDF Raporu Oluşturma
Terminalden veya CI/CD scriptinden doğrudan PDF oluşturup çekebilirsiniz:

```bash
# 1. Rapor işini başlatın
JOB_DATA=$(curl -s -u elastic:DevOps2026! -H "kbn-xsrf: true" -H "Content-Type: application/json" \
  -X POST 'http://localhost:5601/api/reporting/generate/printablePdf?jobParams=(browserTimezone:Europe%2FIstanbul,layout:(dimensions:(height:1200,width:1800),id:preserve_layout),objectType:dashboard,relativeUrls:!(%27/app/dashboards%23/view/novashop-ecommerce-analytics%27),title:%27NovaShop_Sales_Analytics_Report%27)')

JOB_ID=$(echo "$JOB_DATA" | jq -r '.job.id')
echo "Rapor işi kuyruğa alındı: $JOB_ID"

# 2. PDF derlenene kadar bekleyin (Chromium ile render ~20-60 sn sürer).
#    İş bitmeden indirme uç noktası PDF yerine "processing" metni döner.
for i in $(seq 1 30); do
  CODE=$(curl -s -u elastic:DevOps2026! -H "kbn-xsrf: true" -o novashop-yonetim-satisi.pdf -w "%{http_code}" \
    "http://localhost:5601/api/reporting/jobs/download/${JOB_ID}")
  [ "$CODE" = "200" ] && break
  sleep 5
done

file novashop-yonetim-satisi.pdf
```

#### Yöntem 3: Zamanlanmış (Scheduled) Otomatik E-Posta Gönderimi
1. Panoyu açıp sağ üstten **Export ➔ Schedule export** deyin.
2. **Report name** ve **File type** (PDF) seçin; **Repeat** ile sıklığı verin: saatlik, günlük, haftalık, aylık ya da
   özel (örneğin her Pazartesi sabahı).
3. E-posta ile göndermek için **Send by email** bölümünde bir e-posta connector'ı gerekir. LAB-27'de (Apache uçtan
   uca) tanımlanan **`apache-eposta`** connector'ı bunun için kullanılabilir; connector yoksa pencere
   `Email connector hasn't been created yet` der.
4. Zamanlanan raporlar çalışınca **Stack Management ➔ Reporting** listesine düşer.

*Böylece her hafta satış ve ciro raporu yönetimin e-posta kutusuna otomatik PDF olarak teslim edilir.*

---

### 9. Opsiyonel Adım: Dashboard Annotation Groups ile Canlı Olay İşaretçileri (Deployments & Campaigns)

Zaman serisi grafiklerinde (örneğin günlük satış trendi, CPU veya hata oranı) yaşanan ani artış ve düşüşlerin arkasındaki kök nedeni (RCA) tek bakışta görebilmek için **Annotation Groups** kullanılır.

#### Adım 1: Örnek Olay Verisini ve Data View'ı Yükleyin
Deploy, kampanya ve kesinti olaylarını içeren `novashop-events` indexini ve Kibana Data View'ını tek komutla oluşturun:

```bash
python3 scripts/seed_annotation_events.py
```

#### Adım 2: Panoya Annotation Group Ekleyin (Kibana UI)
1. Kibana'da **Analytics ➔ Dashboard** yolundan `NovaShop E-Commerce Sales & Analytics` panosunu açın.
2. Sağ üstten **Edit** moduna geçin.
3. Panel 4'teki (**"Günlük Satış ve Ciro Zaman Trendi"**) Lens grafiğinin sağ üstündeki kalem ikonuna (**Edit visualization**) tıklayın.
4. Sağ panelde **Layers & Annotations** sekmesine gelin veya alt kısımdaki **Annotations** başlığından **Add annotation** seçin:
   * **Data View:** `NovaShop Event Annotations (Deployments & Campaigns)` (`novashop-events*`)
   * **Time field:** `@timestamp`
   * **Tooltip field:** `event.action`
   * **Badge / Color:** Sarı veya Mavi
5. **Save and return** diyerek panoya dönün.

```text
Satış Cirosu ($)
    ▲                       🚩 Flash Sale Başladı
    │                        │
    │           🚩 v2.4.0    │       /\
    │           Deploy       │      /  \
    │             │          │     /    \      🚩 Black Friday
    │            / \        / \   /      \           │
    │           /   \______/   \_/        \_________/ \
    └───────────┴────────────┴───────────────────────┴──────► Zaman
```

*Artık satış grafiği üzerinde gezinirken, cironun tam olarak hangi deploy veya hangi kampanya anında fırladığını dikey bayrak işaretçileriyle anında görebilirsiniz!*

---

## Doğrulama

<details>
<summary><strong>Toplu kontrol betiği</strong></summary>

```bash
cd ~/elastic/projects/ecommerce-spring-search
./verify.sh
```

</details>

---

## Temizlik

```bash
cd ~/elastic/projects/ecommerce-spring-search
./teardown.sh
```

Silinenler: `ecommerce-search-service` compose projesi ve imajı (Java ile başlattıysanız
`/tmp/search-service.pid`'deki süreç), `ecommerce-products-v1`, `ecommerce-customers-v1`,
`ecommerce-orders-v1`, `novashop-events` index'leri, `novashop-*` Kibana nesneleri (data view,
6 Lens paneli, pano) ve `novashop-adapter` API key'i. Ana cluster ve `kibana_sample_data_ecommerce`
silinmez.
