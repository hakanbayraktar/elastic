# Elastic Eğitim Repo Sözleşmesi (devops-monitoring/elastic)

Bu dosya, `devops-monitoring/elastic` reposunda çalışan her ajan için **bağlayıcı**
kurallardır. Kök sözleşme (`~/devops-workspace/AGENTS.md`) geçerliliğini korur;
buradaki kurallar onu **daraltır**, gevşetmez. Paralel çalışma, sahiplik, faz
kapıları ve güvenlik için kök sözleşme esastır.

Dil: lab içeriği ve README'ler **Türkçe** yazılır; kod yorumları Türkçe, commit
mesajları İngilizce başlık + Türkçe/İngilizce gövde olabilir.

---

## 0. Pazarlıksız üç kural

1. **Test etmeden "tamam" denmez.** Bir lab ancak hedef sunucuda sıfırdan
   kurulup, README'deki her komut çalıştırılıp, `verify.sh` geçtikten sonra
   bitmiş sayılır. Sözdizimi/lint geçmesi bitti demek değildir.
2. **Uydurulmuş çıktı yasaktır.** README'deki her örnek çıktı, gerçekten
   çalıştırılmış bir komutun çıktısıdır. Hatırlanan, tahmin edilen veya
   "muhtemelen böyle olur" diye yazılan JSON/log satırı sözleşme ihlalidir.
3. **Yıkıcı komut yasaktır.** `docker system prune`, `docker rm -f $(docker ps -aq)`,
   `git clean -fd`, `git checkout -- .`, `git reset --hard`, joker karakterle
   index silme ve kullanıcının izlenmeyen/değiştirilmiş dosyalarını silen hiçbir
   komut çalıştırılmaz. Temizlik yalnızca labın **kendi** kaynaklarını hedefler.

---

## 1. Ortam gerçekleri

| Konu | Değer |
|---|---|
| Eğitim sunucusu | Hazırlık: `student@35.189.94.73` (SSH anahtarıyla; sunucu kapalıysa kullanıcıdan açmasını isteyin). Eğitim günü ayrı, sıfırdan kurulan bir sunucu kullanılır. |
| Sunucudaki repo | `~/elastic` (bu reponun checkout'u) |
| Ana cluster | LAB-01 Docker single-node: `elasticsearch-lab00` + `kibana-lab00` |
| Docker ağı | `elastic-lab00_default` (lablar bu ağa **katılır**, yeni ağ kurmaz) |
| ES / Kibana sürümü | 9.5.5 (imaj etiketleri `docker.elastic.co/.../9.5.5`) |
| Kimlik bilgisi | `elastic` / `DevOps2026!` — kaynağı `labs/LAB-01-kurulum-kontrol/starter/.env` |
| ES erişimi (lab içinden) | `http://elasticsearch-lab00:9200` |
| ES/Kibana erişimi (hosttan) | `http://localhost:9200` / `http://localhost:5601` |
| Sunucuda hazır araçlar | `docker`, `docker compose`, `jq`, `python3`, `curl`, GNU `date` |
| RAM bütçesi | 16 GB; ana cluster ~2.5 GB. Yeni lab 1 GB üstü heap istiyorsa gerekçelendirin |
| Dokunulmaz host servisleri | Nginx (`80`/`443`), Cockpit (`9090`) |

Sunucuda dosya güncelleme: yerelde değiştir → `rsync -az` ile gönder → test et →
commit/push → sunucuda `git fetch` + `git merge --ff-only`. Sunucuda `git clean`
veya `checkout -- .` **kullanılmaz**; çakışma varsa `git stash push -u` ile
geri alınabilir şekilde kenara alınır.

---

## 2. Port kayıt defteri

Yeni bir port açmadan önce bu tabloya bakın; **çakışma en sık yapılan hatadır**
(bir lab bir dönem başka bir labın `5044` portunu istiyordu ve hiç ayağa kalkmıyordu).
Bu tablo portların **tek kaynağıdır**; yeni port eklediğinizde burayı ve ilgili
labın `Ön Koşullar` bölümünü güncelleyin.

| Port | Sahibi | Dış erişim |
|---|---|
| `80`, `443`, `9090` | Host Nginx / Cockpit — dokunulmaz | evet |
| `9200`, `5601` | Ana cluster (LAB-01) — paylaşılır | evet |
| `127.0.0.1:9603` | LAB-12 Excel Logstash API | hayır |
| `127.0.0.1:9604` | LAB-13 MySQL JDBC Logstash API (MySQL host'a açılmaz) | hayır |
| `127.0.0.1:5000`, `127.0.0.1:9600` | LAB-14 Logstash grok (TCP girdi / API) | hayır |
| `127.0.0.1:5001`, `127.0.0.1:9601` | LAB-15 Logstash operasyonu (TCP girdi / API) | hayır |
| `8081`, `3001` | LAB-10 demo Nginx / demo API | hayır |
| `8088`, `127.0.0.1:8025` | LAB-27 Apache / Mailpit arayüzü (SSH tüneli). Logstash Beats girdisi `5044` yalnız Docker ağında | `8088` evet |
| `127.0.0.1:8220` | LAB-11 Fleet Server | hayır |
| `19208` | LAB-19 bağımsız 3-node TLS cluster, HTTPS (LAB-23 aynı cluster'ı kullanır; node arası `9300` yalnız Docker ağında, host'a açılmaz) | hayır (SSH tüneli) |
| `15608` | LAB-19/23 3-node cluster'ın Kibana'sı (`kibana3` subdomain) | evet |
| `127.0.0.1:9602` | LAB-26 SIEM Logstash API (Beats girdisi yalnız Docker ağında) | hayır |
| `127.0.0.1:4317`, `127.0.0.1:4318` | ADV-02 OTLP gRPC / HTTP (yalnız loopback) | hayır |
| `127.0.0.1:9000`, `9191` | ADV-04 MinIO S3 API (yalnız loopback) / konsol | `9191` evet |
| `9208`, `5608` | ADV-08 bağımsız Elastic 8.19 | evet |
| `127.0.0.1:30086`, `127.0.0.1:30087` | ADV-09 ECK Kibana / Elasticsearch (kind `extraPortMappings`, yalnız loopback; Kibana'ya SSH tüneli) | hayır |
| `9200`, `9300` | ADV-10 — **yalnız ayrı üç VM'in iç ağında** (paketle kurulum; ana cluster ile çakışır) | hayır |
| `19001` | projects/ecommerce-fastapi-search (FastAPI, nginx app1) | evet |
| `19002` | projects/fastapi-elk-monitoring (FastAPI; doğrudan IP:port, alan adı yok) | evet |
| `19003` | projects/bilgincit-devops-search (Flask; doğrudan IP:port, alan adı yok) | evet |
| `127.0.0.1:5010` | projects/fastapi-elk-monitoring Logstash TCP (konteyner içi 5000) | hayır |
| `8080` | projects/ecommerce-spring-search (Spring Boot) | evet |
| `80`, `443`, `9200`, `5601`, `5044`, `127.0.0.1:9201` | projects/elk-devsecops-tls-automation — **yalnız ayrı sunucuda** (ana cluster ve host Nginx ile çakışır) | ayrı sunucu |

Sunucu firewall'u ve Nginx/Cloudflare subdomain listesi "Dış erişim = evet" satırlarından
üretilir (panel elastic profili: `cockpit`, `kibana`, `elastic`, `apache`, `kibana3`,
`minio`, `kibana8`, `elastic8`, `novashop`, `app1`).
---

## 3. Lab dizin yapısı ve isimlendirme

Müfredat iki kümeden oluşur ve bu ayrım bağlayıcıdır:

- **Çekirdek:** `labs/LAB-<NN>-<slug>` — eğitimin ("Elasticsearch with Logstash and
  Kibana") sırayla işlenen **27 labı** (kullanıcı kararı, 2026-11-22: pedagojik sıra; mapping aramadan önce,
  toplama (Beats, Fleet) işlemeden (Logstash) önce, yeni 17 Kibana Spaces ve saved objects, 4. gün cluster
  kurulumuyla açılır). `*` = mutlaka yapılır; işaretsizler vakit olursa. Gün dağılımı (onaylı; yetişmeyen lab
  sonraki güne sarkar ya da atlanır):
  - 1. gün: 01* kurulum, node ve cluster · 02* ilk document'ler · 03* mapping ve analyzer · 04* Discover ve KQL ·
    05* Query DSL
  - 2. gün: 06* arama deneyimi · 07* aggregation, Lens, gerçek zamanlı analiz · 08* ES|QL ve SQL ·
    09 ilişkisel veri modelleme · 10* Filebeat (+Metricbeat) · 11 Elastic Agent ve Fleet
  - 3. gün: 12* Logstash: Excel ve CSV · 13 Logstash JDBC (MySQL) · 14* grok, dissect, ingest pipeline ·
    15 Logstash operasyonu · 16* Kibana pano atölyesi · 17* Kibana Spaces ve saved objects ·
    18* harita, alerting, raporlama
  - 4. gün: 19* 3-node TLS cluster · 20* güvenlik · 21* cluster sağlığı ve yönetimi · 22* ILM ·
    23* snapshot ve cluster operasyonu · 24 performans teşhisi · 25 uygulamadan Elasticsearch · 26 SIEM ·
    27 Apache uçtan uca proje labı (Logstash GeoIP, pano, alarm: e-posta/Slack/Mailpit, PDF rapor)
  Gün bilgisi lab README'lerine yazılmaz (§5); `*` kök README tablosundaki "Öncelik"
  kolonunda ve sunumlarda aynı tutulur. Sayıyı değiştirmek kullanıcı kararıdır. Eski yapı `eski-lab` dalındadır.
- **İleri/seçmeli:** `labs/advanced/ADV-<NN>-<slug>` — kurs akışında zorunlu olmayan,
  profil bazlı seçilen lablar. `ADV` numaraları da **ardışıktır**, boşluk bırakılmaz (kullanıcı kararı,
  2026-11-22): bir lab silinir ya da eklenirse sonrakiler `git mv` ile kaydırılır ve bütün atıflar aynı
  commit'te güncellenir.

Lab kapsamı değişirse dizin adı da `git mv` ile değişir ve **tüm atıflar** güncellenir
(markdown linkleri, betik içi yollar, compose dosyaları, kök README, port defteri).
Yeniden numaralandırmadan sonra link doğrulaması zorunludur: her markdown linki
çözülmeli, hiçbiri kırık kalmamalıdır.

```text
labs/LAB-NN-<slug>/
├── README.md                  # zorunlu — iskelet icin bkz. bolum 4
├── docker-compose.yml         # konteyner gerekiyorsa
├── config/                    # servis ayar dosyalari
├── pipeline/ | manifests/ ... # labin dogasina gore
├── sample-data/               # sentetik ornek veri
├── scripts/
│   ├── common.sh              # ES_URL, KIBANA_URL, kimlik, port, es() yardimcisi
│   ├── setup-*.sh             # sablon/politika/on kosul kurulumu
│   ├── provision_kibana.py    # data view + pano (gerekiyorsa)
│   ├── lens_builder.py        # pano uretimi icin paylasilan modul (kopyalanir)
│   └── ...                    # labin kendi adim betikleri
├── verify.sh                  # istege bagli (bkz. §14); test kaniti README runner + commit govdesi
└── teardown.sh                # yalnizca bu labin kaynaklarini siler
```

İsimlendirme sözleşmesi — kaynak adları **lab numarasına değil konu koduna**
bağlanır. Sebep: müfredat değiştiğinde lab numarası değişir; numarayı index,
container ve pano adlarına gömmek her revizyonda test edilmiş labları kırar.
Numara yalnızca **dizin adında ve README başlığında** bulunur.

Konu kodu kısa, kalıcı ve konuyu anlatan bir sözcüktür: `grok`, `dlq`, `fleet`,
`beats`, `cluster`, `rca`, `ilm`, `enrich`, `apache`.

| Nesne | Kural | Örnek |
|---|---|
| Index / data stream | `<kod>-...` | `grok-error-2026.11.12`, `dlq-recovered-*` |
| Index şablonu | `<kod>-...` | `grok-logs`, `dlq-recovered` |
| Konteyner / compose projesi | `<servis>-<kod>-lab` | `logstash-grok-lab`, `logstash-dlq-lab` |
| Kibana data view id | `<kod>-logs` | `grok-logs`, `fleet-metrics` |
| Kibana pano id | `<kod>-<konu>` | `grok-logstash-overview`, `fleet-agent-observability` |
| Lens panel id | `<kod>-<panel>` | `grok-errors-by-service`, `dlq-error-types` |
| Kibana başlıkları | **Numara içermez** | "Logstash Grok Ayrıştırma ve Log Analizi" |
| Infografik | `assets/infographics/<sıra>-<konu-slug>.svg` | `07-logstash-grok-pipeline.svg` |

Teardown kapsamı bu önekle belirlenir (`<kod>-*`), bu yüzden önek labın
kendisine özgü olmalı ve başka bir labın önekiyle çakışmamalıdır.

**Yerleşik şablonlarla çakışmayın:** `logs-*-*` ve `metrics-*-*` desenleri
Elasticsearch 9'da **data stream** şablonlarıdır; bu adlarla klasik index
yaratmak `cannot create index ... template [logs] that creates data streams only`
hatasıyla reddedilir. Bu yüzden hedef adlar `lab<NN>-` ile başlar.

---

## 4. README zorunlu iskeleti

Sıra birebir şudur. Boş bölüm bırakmak yerine bölümü hiç koymayın.

1. `# LAB-<NN> — <Başlık>: <ne kazandırıyor>`
2. **Metadata tablosu:** yalnızca `Kullanılan Araçlar | Açık / Kullanılan Portlar`.
   **`Seviye` ve `Tahmini Süre` kolonu konmaz** (öğrenciler farklı hızda çalışır;
   eskimiş tahmin hiç olmamasından kötüdür).
3. **`## Bu lab ne öğretiyor?`** — 2-3 paragraf. Somut bir problemle açılır
   ("şu log satırı şu soruyu cevaplayamaz, çünkü..."), ardından labın o problemi
   nasıl çözdüğü. Kök sözleşmedeki "Amaç" madde listesinin yerini tutar; madde
   listesi yerine problem-çözüm anlatımı tercih edilir çünkü öğrenci neyi neden
   yaptığını ilk paragrafta anlamalı.
4. **Mimari görsel:** kaynağı SVG, README'de PNG kopyası gömülür (bkz. bölüm 6). Altına "görseli okuma sırası" gibi açıklama cümlesi yazılmaz.
5. **`## Ön Koşullar`** — ana cluster komutu, ağ/erişim notu, port notu, `cd` satırı.
6. **Kavram bölümü** — `## <X> nedir, neden var?` veya `## Kavramlar: ...`.
   Tablo veya kısa paragraflar. Ezber değil, karar kuralı verir.
7. **`## Config dosyaları: hangi satır ne işe yarıyor?`** — her dosyanın
   **kritik bloğu** alıntılanır (≤ 15 satır), altında madde madde "ne yapar /
   neden böyle". Tüm dosyayı yapıştırmak yasak.
8. **`## Adım Adım Uygulama Rehberi`** — numaralı adımlar. Her adım: ne
   yapılacak (1-3 cümle) → komut → **gerçek beklenen çıktı** → çıktının ne
   anlattığı.
9. **`## Doğrulama`** — yalnız adımların göstermediğini kontrol eder (birden çok
   parçanın son durumu, güvenlik/restore kanıtı); adım komutları tekrar edilmez.
   Her adım sonucunu zaten gösteriyorsa bölüm konmaz. `./verify.sh` bizim test
   aracımızdır; README'de en çok `<details>` içinde tek satır (bkz. §14).
10. **`## Temizlik`** — `./teardown.sh` ve neyin silindiği/silinmediği.
11. **Son satır:** `Sonraki lab: **[LAB-XX — ...](../LAB-XX-.../README.md)**`

---

## 5. İçerik yazım kuralları

- **Önce/sonra zorunludur.** Veriyi dönüştüren her lab (ayrıştırma, zenginleştirme,
  normalizasyon, kurtarma) ham girdiyi ve dönüşüm sonrası hâlini **yan yana**
  gösterir. Öğrenci "tam olarak ne değişti" sorusunu okuyarak cevaplayabilmeli.
- **Çıktılar gerçek ve kırpılmış.** Uzun document'i olduğu gibi yapıştırmak yerine
  komutu kısaltın: `filter_path=hits.hits._source` + `_source=alan1,alan2`.
  Böylece öğrencinin ekranı README'deki blokla **birebir** aynı olur.
- **Her açıklama bir soruya cevap verir:** "ne yapar" + "neden böyle" + (varsa)
  "yapmazsan ne olur". Bunlardan hiçbirini taşımayan cümle dolgudur, silinir.
- Yasaklı içerik: emoji içeren başlık/metadata/zorluk etiketi, gün bazlı
  gruplama ("3. Gün"), zorunlu quiz, çözüm açma kutusu, genel cheat-sheet,
  uzun troubleshooting bölümü, README sonuna harici blog/kaynak listesi,
  pazarlama cümlesi, sağlayıcı/fiyat/sertifika metni.
- Komutlar kopyala-yapıştır çalışır olmalı: mutlak/net yollar, tırnaklanmış
  parola (`-u elastic:'DevOps2026!'`), `sudo` yalnızca gerçekten gerekliyse.
- Terminoloji sabit: `Monitoring`, `IaC`, `data view`, `pipeline`, `index`,
  `pano`. Aynı şey için iki terim kullanılmaz.
- **İngilizce teknik terim Türkçeleştirilmez:** `cluster`, `shard`, `replica`, `node`,
  `container`, `image`, `volume`, `snapshot`, `document`, `field` olduğu gibi yazılır; `küme`, `parça`,
  `kopya`, `kapsayıcı`, `görüntü`, `belge`, `alan` yazılmaz. Türkçe ek kesme işaretiyle: `document'ler`,
  `document'in`, `document'te`.
- **Rol yok:** labda eğitmen ve öğrenci yoktur. "Eğitmen doğrulaması", "öğrenci",
  "katılımcı" yazılmaz; okura doğrudan "siz" diye seslenilir. Doğrulama başlığı `Doğrulama`
  ya da §4'teki kalıptır.
- **Kısa ve sade:** "Bu lab ne öğretiyor?" en çok iki kısa paragraf; amaç listesi varsa en
  çok 3-4 tek satırlık madde. İsteğe bağlı yollar, hızlı yol, klasör ağacı, başvuru tablosu
  ve uzun sorun giderme `<details>` içinde. Bilgi, ona ihtiyaç duyan adımdan önce verilmez.
- **Metin sadeleştirirken komutlar değişmez:** kod bloklarının içeriği ve sırası korunur;
  commit öncesi `python3 scripts/readme_komut_denetimi.py <README...>` çalıştırılır.

---

## 6. Diyagram kuralları

- Mevcut büyük ve okunaklı **Mermaid diyagramlarına dokunulmaz** (kullanıcı kararı,
  2026-11-12). Yeni diyagramlar aşağıdaki kurallarla SVG olarak eklenir; gerekirse PNG/JPEG
  ek görsel kullanılabilir.
- Diyagram `assets/infographics/` altına **elle yazılmış SVG** olarak eklenir;
  mevcut dosyalar referans stildir: `width="1600"`, `viewBox="0 0 1600 1000"`
  civarı, `<style>` içinde sınıflar, Elastic paleti (`#005571`, `#0b6e99`,
  `#f5a700`, `#6b5b95`, `#5aa454`, `#bd271e`, zemin `#f7fafc`), gövde yazısı
  ≥ 17px, başlık 40px.
- `<title>` ve `<desc>` zorunlu (erişilebilirlik ve arama).
- `&nbsp;` gibi XML'de tanımsız varlık **kullanılmaz** (SVG geçersiz olur);
  boşluk için `x` koordinatı kaydırılır.
- Eklemeden önce doğrula:
  `python3 -c "import xml.etree.ElementTree as ET; ET.parse('<dosya>.svg')"`
- GitLab SVG'yi tıklanınca indirir, büyütmez. Bu yüzden README'ye SVG'nin **PNG kopyası** gömülür:
  `![açıklama](../../assets/infographics/<dosya>.png)`. PNG, SVG'den `python3 scripts/svg_png.py`
  ile üretilir (Playwright + Chrome, 1,5x); SVG değişince PNG yeniden üretilip birlikte commit edilir.
- Görsele "lab doğrulama sorusu" kutusu konmaz; README'ye "görseli okuma sırası" cümlesi yazılmaz.

---

## 7. Kibana raporu kuralları

Veri üreten her lab, o verinin **bir soruya cevap verdiğini** göstermek zorundadır:

- `scripts/provision_kibana.py` data view + panoyu Saved Objects API ile kurar;
  pano/panel üretimi için `lens_builder.py` **yeniden kullanılır** (şeması çalışan
  Kibana 9.x nesnelerinden doğrulanmıştır, `validate()` ve `validate_dashboard()`
  çağrılmadan nesne gönderilmez).
- Panel başlıkları operasyonel soru cevaplar ("Servis bazında hata sayısı"),
  teknik alan adı değil.
- Her panoda en az bir **sağlık göstergesi** olmalı (ayrıştırılamayan olay,
  reddedilen document, hata oranı gibi).
- README hem script yolunu **hem de** aynı panelleri Lens arayüzünde elle kurma
  adımlarını verir — öğrenci sonucu görmekle kalmayıp nasıl yapıldığını öğrenir.
- `timeRestore: true` + `timeFrom` verilir, ki pano ilk açılışta boş görünmesin.
- Kibana arayüzünde elle yapılan adımlara **işaretli ekran görüntüsü** eklenir: tıklanacak yer
  kırmızı kutu + ok + README'deki adım numarasıyla gösterilir. Görüntüler
  `scripts/screenshots/kibana_shots.py` ile kendi lab ortamımızdan alınır (kutu, ögenin ölçülen
  konumuna çizilir), `assets/screenshots/<LAB-NN>/` altına 1600 px genişlikte yazılır. Komut
  çıktıları görüntü olarak verilmez; metin kalır. Sunum görüntüleri (`elastic-sunumlar/ekran/`)
  işaretsiz tutulur.
- Örnek veri üreten betikler zaman damgalarını **geçmişe yayar**; aksi halde
  zaman serisi panelleri tek sütun görünür.

---

## 8. Doğrulama (`verify.sh`) kuralları

- Tek komut, bölümlenmiş çıktı, satır başına `[OK]` / `[HATA]` / `[i]`, sonunda
  `[SONUC]` ve **anlamlı exit kodu** (`0` geçti).
- Gerçek runtime kanıtı kullanır: `curl` (ES/Kibana API), Logstash `:9600` API
  sayaçları, `docker logs`, `docker exec ls`, `kubectl get`. Yapay bir
  `validate.sh` mantığı kurulmaz.
- Kontroller yalnızca "index var mı" değil, **alan düzeyinde** doğrular
  (örn. `loglevel: error`, `payload.*` dolu mu, hata sayacı kaç).
- Kibana nesneleri de doğrulanır (data view + pano + panel sayısı).
- `jq` serbesttir (sunucuda kurulu). **Logstash API `filter_path` desteklemez**;
  alan seçimi `jq` ile yapılır (Elasticsearch `filter_path` destekler).

---

## 9. Temizlik (`teardown.sh`) kuralları

- Kapsam: yalnızca o labın compose projesi (`down -v`), kendi index'leri, kendi
  şablonları, kendi Kibana nesneleri. Ana cluster (ES/Kibana) ve diğer lablar
  **etkilenmez**; README bunu açıkça yazar.
- Elasticsearch varsayılan olarak joker karakterle silmeye izin vermez
  (`action.destructive_requires_name`). Doğru kalıp:
  ```bash
  INDICES=$(es "${ES_URL}/_cat/indices/lab13-*?h=index" | tr -d ' ' | paste -sd, -)
  [ -n "${INDICES}" ] && es -X DELETE "${ES_URL}/${INDICES}"
  ```
- Kibana nesneleri id ile tek tek silinir (pano, panel, data view).
- `docker system prune`, global `volume prune`, `docker rm -f $(docker ps -aq)`
  kesinlikle yasak.

---

## 10. Elastic 9.x tuzak listesi (lab yazmadan önce oku)

| Tuzak | Doğrusu |
|---|---|
| Logstash `http.host` / `http.port` | 9.x'te kaldırıldı → `api.http.host` / `api.http.port`. Yanlışsa servis `Setting "http.host" doesn't exist` ile hiç açılmaz. |
| `logs-*` / `metrics-*` index adı | Yerleşik data stream şablonlarına çarpar → `lab<NN>-*` kullan. |
| Joker karakterle index silme | `action.destructive_requires_name` engeller → adları çöz, sonra sil. |
| Logstash API'de `filter_path` | Desteklenmez → `jq`. |
| Aynı konteynerde ikinci Logstash | `path.data` kilidi çakışır → ayrı `path.data` ile ayrı (tek seferlik) servis. |
| DLQ okuma offset'i | `commit_offsets` tek başına yetmez; `--rm` konteynerde `sincedb_path` paylaşılan volume'de olmalı, yoksa mükerrer kurtarma olur. |
| DLQ segmenti | Aktif segment `dead_letter_queue.flush_interval` sonunda kapanır (varsayılan 5 dk); kurtarma kapanan segmenti okur. |
| Hangi hata DLQ'ya düşer | Yalnızca kalıcı red (400/404). 429/5xx yeniden denenir. |
| İç içe env varsayılanı | Logstash'te `${A:${B:x}}` çalışmaz; tek seviye `${A:x}` kullan ve değeri compose'tan geç. |
| Kibana Lens saved object | `embeddableConfig` ve `panelRefName` eksikse pano açılışta HTTP 500 verir → `lens_builder.dashboard_panel()` kullan. |
| Benchmark ölçümü | JVM açılışı (~35 sn) mutlak süreyi domine eder; referans geçişle **fark** ölçülür, gürültü eşiğinin altındaki sonuç "fark yok" diye yazılır. |

---

## 11. İş akışı ve bitmiş tanımı

Sıra: **teşhis → plan → uygula → sunucuda test → README'yi ölçümle hizala → commit → push → sunucuda pull.**

Bir lab ancak şu listenin tamamı sağlandığında bitmiştir:

- [ ] `docker compose up -d` sıfırdan başlıyor, log'da `FATAL`/`invalid setting` yok
- [ ] Lab verisi gerçekten Elasticsearch'e yazılıyor (sayı ile kanıtlı)
- [ ] README'deki **her** komut sunucuda çalıştırıldı; çıktılar README'deki bloklarla eşleşiyor
- [ ] Önce/sonra blokları gerçek çıktıyla duruyor
- [ ] Kibana panosu kuruluyor ve panellerin hepsi **veri gösteriyor** (agregasyonla doğrulandı)
- [ ] README runner 0 FAIL, çıktı karşılaştırması temiz, PASS/FAIL sayısı commit gövdesinde
  (`verify.sh` zorunlu değil; kullanıcı kararı 2026-11-21: gereksiz doğrulama yok)
- [ ] `./teardown.sh` yalnızca labın kaynaklarını sildi; ana cluster ayakta
- [ ] Teardown sonrası baştan kurulum tekrar çalışıyor (tekrarlanabilirlik)
- [ ] Port defteri (bu dosya), kök `README.md` ve komşu labların "sonraki lab"
      linkleri güncel
- [ ] SVG mimari var ve XML geçerli

Commit mesajı gövdesinde **bulunan gerçek hatalar** ve **doğrulama kanıtı**
(sayılarla) yer alır; "iyileştirmeler yapıldı" gibi içi boş gövde yazılmaz.
Kök sözleşmedeki attribution satırları korunur.

---

## 12. Model ve çaba seviyesi önerisi

| İş | Model | Seviye |
|---|---|
| "Neden çalışmıyor" teşhisi, yeni lab tasarımı, içerik kurgusu | Opus 5 | high |
| Onaylı planı uygulama, script/README yazımı, test koşuları | Sonnet 5.5 | medium |
| Toplu yeniden adlandırma, format, kolon silme | Haiku 5.5 | low |

Maliyetin asıl kaynağı model değil **bekleme döngüleridir** (JVM ~36 sn, compose
başlatma ~55 sn). Testleri arka plana alın, SSH komutlarını tek çağrıda demetleyin.

---

## 13. Lab durumu

Çekirdek lablar bu sözleşmeye göre yeniden yazıldı ve sunucuda README runner + Playwright ile temiz kurulumdan
test edildi (2026-11-21); Apache uçtan uca labı 2026-11-22'de eklendi. 2026-11-22'de 26, aynı gün pedagojik sırayla 27 laba yeniden numaralandı.
İleri lablar (`labs/advanced/`) bu tabloda yok; durumları
kendi README'lerinde.

| Lab | Durum |
|---|---|
| LAB-01 — Kurulum ve erişim | Hazır, test edildi |
| LAB-02 — İlk document'ler: curl, Dev Tools ve Discover | Hazır, test edildi |
| LAB-03 — Mapping ve analyzer | Hazır, test edildi |
| LAB-04 — Discover ve KQL | Hazır, test edildi |
| LAB-05 — Query DSL | Hazır, test edildi |
| LAB-06 — Arama deneyimi: otomatik tamamlama, fuzzy, eş anlamlı, vurgulama | Hazır, test edildi |
| LAB-07 — Aggregation ve Lens panosu | Hazır, test edildi |
| LAB-08 — ES\|QL ve SQL | Hazır, test edildi |
| LAB-09 — İlişkisel veriyi modelleme | Hazır, test edildi |
| LAB-10 — Filebeat: host ve Docker logları (+Metricbeat) | Hazır, test edildi |
| LAB-11 — Fleet ve Elastic Agent | Hazır, test edildi |
| LAB-12 — Excel verisini Logstash ile aktarma | Hazır, test edildi |
| LAB-13 — MySQL verisini Logstash JDBC ile aktarma | Hazır, test edildi |
| LAB-14 — Logstash ile log ayrıştırma: grok ve dissect | Hazır, test edildi |
| LAB-15 — Logstash operasyonu: çoklu pipeline, persistent queue, DLQ | Hazır, test edildi |
| LAB-16 — Kibana pano atölyesi | Hazır, test edildi |
| LAB-17 — Kibana Spaces ve saved objects | Hazır, test edildi |
| LAB-18 — Harita, alerting ve raporlama | Hazır, test edildi |
| LAB-19 — 3-node TLS cluster | Hazır, test edildi |
| LAB-20 — Güvenlik ve çok ekipli Kibana | Hazır, test edildi |
| LAB-21 — Cluster sağlığı ve API'ler | Hazır, test edildi |
| LAB-22 — Index yaşam döngüsü (ILM) | Hazır, test edildi |
| LAB-23 — Cluster operasyonu ve snapshot | Hazır, test edildi |
| LAB-24 — Performans teşhisi | Hazır, test edildi |
| LAB-25 — Uygulamadan Elasticsearch | Hazır, test edildi |
| LAB-26 — SIEM: tespit ve alarm | Hazır, test edildi |
| LAB-27 — Apache uçtan uca | Hazır, test edildi |

Bir labı yeniden yazarken: önce sunucuda **mevcut hâliyle** çalıştırıp gerçek hataları çıkarın, sonra bu
sözleşmenin iskeletine taşıyın. Tahminle yeniden yazmak yasaktır; labların çoğu "sözdizimi doğru ama
çalışmıyor" durumundan çıktı.

---

## 14. Test, erişim ve yazım ek kuralları (kullanıcı kararı, 2026-11-21)

### Bekleme ve doğrulama
- Sabit `sleep N` yazılmaz. Bekleme yalnız gerçekten asenkron yerde (JVM açılışı,
  Kibana `available`, ilk document'in index'e düşmesi, ajan enrollment) yapılır; koşula
  bağlı, zaman aşımlı ve ilerleme gösteren tek döngüdür. Önünde beklenen süre yazar:
  `timeout 180 bash -c 'until <koşul>; do printf .; sleep 3; done'; echo`
- Bir adımın çıktısı sonucu zaten gösteriyorsa arkasına ayrı doğrulama komutu konmaz.
- `verify.sh` canlı veriye bağlı sabit eşikle (oran, sayı) kırılmaz: ölçüm labın
  kendi ürettiği deterministik veriyle yapılır, canlı gürültü `[i]`/uyarı olarak gösterilir.

### Açıklama ve kod blokları
- Önemli noktada 1-3 cümle: ne yapar, neden gerekli, yapılmazsa ne olur. Önemli =
  yeni kavram, hata verebilecek ayar, güvenlik etkisi, veri kaybı riski. Dolgu cümle,
  tekrar, "ayrıntısı LAB-X'te" yok.
- Terminal komutu yalnız ` ```bash ` bloğunda olur. Dosya içeriği / config alıntısı
  dilinin etiketiyle (` ```yaml `, ` ```conf `, ` ```python `) ve üstünde dosya adıyla
  verilir; terminale yapıştırılacak gibi görünmez. Kibana Dev Tools isteği ` ```http `
  bloğunda, üstünde "Kibana › Dev Tools'a yapıştırın" satırıyla verilir.
- Komut kullanıcıdan girdi beklemez: `read -p` varsayılansız kullanılmaz, `ssh`
  betiklerde `-o BatchMode=yes` ile çalışır.
- Lab tek konu anlatır: en çok 6-7 adım, ~300 satır, her adım tek soruya cevap verir. Konu
  dışı adım asıl labına taşınır (konu silinmez), küçük ayrıntı aynı labda `<details>` içinde
  kalır. Küçük konular için lab bölünmez; bölme yalnız konu kendi başına 4-5 adım tutuyorsa.

### Erişim (her labda)
- Arayüzü olan her lab, adresleri sunucudan hesaplayıp **iki biçimde** yazdırır;
  `studentXX` gibi sabit ad yazılmaz:
  ```bash
  IP=$(curl -s https://api.ipify.org); H=$(hostname -s)
  echo "Kibana: http://$IP:5601   https://$H-kibana.devopsatolyesi.com"
  ```
- Dışarı açılmayan (loopback) servis için `ssh -f -N -L <port>:127.0.0.1:<port>
  <kullanıcı>@<IP>` tüneli ve kapatma komutu (`pkill -f "\-L <port>:127.0.0.1:<port>"`; `-L` ile başlayan desen 15601 gibi aynı rakamla biten başka tünelleri yakalamaz) verilir.
- Dışarıdan erişilen portlar §2 port defterinde "dış" olarak işaretlenir; sunucu
  firewall'u ve Nginx/Cloudflare subdomain listesi bu tablodan üretilir.

### Sürüm ve ekran görüntüsü
- Bütün lablar aynı sürümü kullanır: image'lar `9.5.5`, native paketler
  `=9.5.5` ile sabitlenir. Elastic 8 yalnız ADV-08'de (8 ve 9 farkı) bulunur.
- Kibana'da elle yapılan her adımın işaretli ekran görüntüsü vardır (§7). Klasörde
  alındığı Kibana sürümü yazar; sürüm değişince görüntüler yeniden alınır.

### Test
- Lab oluşturma, silme ve test bu sözleşmeye göre yapılır. Temiz sunucuda, README
  sırasıyla; yalnız üç kaynak: README komutları (birebir), README sırasıyla Playwright
  ile arayüz adımları, repodaki dosyalar. Elle/API ile düzeltme yok. Patlayan adım
  repoda düzeltilir, test temiz kurulumdan tekrarlanır.
- Ön kontrol: lab portları boş mu, başka stack açık mı, boş RAM yeterli mi. Geçmezse
  test başlamaz.
- Çıktı eşleşmesi: README'deki beklenen çıktıdan anahtar satırlar gerçek çıktıda
  aranır; eşleşmeyen satır README'de ya da kodda düzeltilir.
- Dış erişim: README'de verilen her URL (IP:port ve domain) sunucu dışından açılır.
- Zamana bağlı her iddia ("tetiklenir", "temizlenir") son duruma kadar izlenir;
  geçen süre README'ye yazılır.
- Kanıt: test commit'inin gövdesinde PASS/FAIL sayısı ve taban commit (IP ve parola yok). Ayrı test kaydı
  dosyası tutulmaz (kullanıcı kararı, 2026-11-22: `docs/test-logs` kaldırıldı). Kanıt yoksa lab bitmiş sayılmaz.
- Süreç durdurmadan önce `pgrep -af <tam desen>` ile eşleşen bakılır; geniş
  `pkill -f` kullanılmaz.
- Eğitim `main`'den verilir: bir lab `main`'den ancak yerine geçen yeni lab aynı commit'te geldiğinde
  kaldırılır. Kullanıcı tek bir klasörü kastettiyse yalnız onu kaldır; kapsamı genişletme.
- Sonraki bir labın kaynağı olan eski dosyalar (`*-kaynak/` klasörleri, "eski içerik" lablar)
  başlarındaki "Silmeyin" uyarısıyla durur; o lab yazılıp main'e alınmadan silinmez.
- Ön Koşullar'da iki satır: "önce kurulu olmalı" ve "önceki labı atladıysanız".
- Push'tan önce `python3 scripts/link_kontrol.py` çalışır ve `[SONUC] kirik link: 0` verir.
  "Sonraki lab" linki henüz yazılmamış bir labı gösteriyorsa o lab aynı push'ta gelir; kırık
  linkle push edilmez.
