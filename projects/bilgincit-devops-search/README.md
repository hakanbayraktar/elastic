# BilgincIT DevOps & Cloud Search Engine (Elasticsearch Eğitim Portalı)

Bu proje; Elasticsearch'ün **Full-Text Arama**, **Fuzzy Arama**, **Nested Arama** ve **Türkçe Dil Analizcisi (Turkish Analyzer & Stemmer)** yeteneklerini canlı olarak deneyimlemek ve eğitimlerde kullanmak üzere geliştirilmiş interaktif bir bilgi bankası arama motorudur.

`docs/` klasörü altına konulan tüm teknik dokümanlar (Markdown, YAML, Bash, TXT vb.) otomatik olarak taranır, ayrıştırılır ve Elasticsearch'e index'lenir.

---

## Öne Çıkan Özellikler

1. **Beş arama metodu, her biri için gerçek Query DSL:**
   * **Multi-Match:** başlık (`title^4`), etiket, dosya adı ve içerikte birlikte arar; `operator: and`.
   * **Fuzzy:** `fuzziness: AUTO` ile yazım hatasını tolere eder (`kuberntes` → `kubernetes`).
   * **Match Phrase:** kelimelerin sıralı ve yan yana geçmesini ister (`slop: 1`).
   * **Nested:** kod blokları (`commands`) ve alt başlıklar (`sections`) nested field'lardır; eşleşen
     alt nesne `inner_hits` ile vurgulanarak döner.
   * **Match:** yalnız `content` field'ında, Türkçe analyzer'lı token'larla arar.
2. **Facet'ler:** soldaki kategori ve etiket sayıları aynı istekteki `terms` aggregation'larından
   gelir. Seçilen filtre `post_filter` ile uygulanır; her facet yalnız diğer facet'in seçimiyle
   süzüldüğü için seçim yapınca öteki sayılar kaybolmaz. Boş ifadeyle kategori seçmek `match_all`
   ile o kategorideki tüm dokümanları listeler.
3. **Sorgu laboratuvarı (sağ panel):** sorgu süresi, sonuç sayısı, en yüksek skor ve üç sekme:
   * **Query DSL:** Kibana Dev Tools'a doğrudan yapıştırılabilen `GET bilgincit_docs/_search` gövdesi.
   * **Analyzer:** aranan ifadenin `turkish_bilginc_analyzer` ve `standard` analyzer ile hangi
     token'lara dönüştüğü (`_analyze` API).
   * **curl:** aynı sorgunun terminal karşılığı (parola `ELASTIC_PASSWORD` değişkeninden).
4. **Arama deneyimi:** yazarken başlık önerileri (↑ ↓ Enter ile klavyeden seçim), `/` kısayolu,
   sonuçta skor çubuğu, 0 sonuçta tek tıkla Fuzzy'ye geçiş. Doküman sayfasında içindekiler, aranan
   kelimelerin vurgulanması ve ham metni kopyalama.
5. **Türkçe analyzer:** `apostrophe` → Türkçe `lowercase` → `stop` → `keyword_repeat` →
   Türkçe `stemmer` → `asciifolding` → `remove_duplicates`. Sıranın gerekçesi `indexer.py`
   içindeki yorumlardadır (stemmer, asciifolding'den önce çalışmalı).
6. **JSON uç noktaları:** `/api/search`, `/api/analyze`, `/api/suggest`, `/api/health`; arayüzde
   yapılan her şeyi terminalden de doğrulayabilirsiniz.

---

## Kurulum ve Çalıştırma

Ön koşul: LAB-01 ana cluster'ı (`elasticsearch-lab00`) çalışıyor olmalı. Durmuşsa
`docker start elasticsearch-lab00 kibana-lab00` ile başlatın. Proje bu sunucuda daha önce kurulduysa önce
**Temizlik** bölümündeki komutları çalıştırın. Bu proje arama labları (LAB-03…06) bittikten sonra önerilir.

### 1. Python Ortamını Kurun
Ubuntu 24.04'te sistem Python'una `pip install` yapılamaz (PEP 668,
`externally-managed-environment`). Paketler projeye ait `.venv` sanal ortamına kurulur:

```bash
cd ~/elastic/projects/bilgincit-devops-search
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
```

### 2. Elasticsearch Bağlantı Ayarları
Örnek ayar dosyasını kopyalayın:

```bash
cp .env.example .env
grep -v PASSWORD .env
```

```ini
ELASTICSEARCH_URL=http://127.0.0.1:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_INDEX=bilgincit_docs
ELASTICSEARCH_VERIFY_CERTS=false
FLASK_PORT=19003
FLASK_DEBUG=false
```

* `FLASK_PORT=19003`: servis sunucunun IP'si ve bu portla dışarıdan açılır (adres Adım 4'te). Alan adıyla
  erişim, panel profiline `app3` eklenince gelir.
* `FLASK_DEBUG=false` bilinçli bir seçimdir: Flask debug modunda Werkzeug'un etkileşimli
  hata ayıklayıcısı 0.0.0.0 üzerinden dışarıya açılır ve uzaktan kod çalıştırmaya izin verir.

### 3. Dokümanları İndeksleyin
`docs/` altındaki tüm dokümanları Elasticsearch'e aktarmak için indexer scriptini çalıştırın.
Script index'i her çalıştırmada Türkçe analyzer ve nested mapping ile **baştan** oluşturur
(var olanı korumak için `--no-recreate`):

```bash
python3 indexer.py
```

### 4. Web Arayüzünü Başlatın
Servisi arka planda başlatın; çıktısı `app.log` dosyasına, süreç kimliği `app.pid`
dosyasına yazılır:

```bash
nohup .venv/bin/python app.py > app.log 2>&1 &
echo $! > app.pid
until curl -sf http://localhost:19003/api/health >/dev/null; do sleep 1; done
curl -s http://localhost:19003/api/health | jq .
```

Arama servisinin Türkçe kök bulma ile sonuç döndürdüğünü terminalden de görün:

```bash
curl -s "http://localhost:19003/api/suggest?q=kubernetes" | jq '.[0:3]'
```

Tarayıcıda açılacak iki adresi sunucuda hesaplayın:

```bash
IP=$(curl -s https://api.ipify.org)
echo "Arama arayüzü: http://$IP:19003"
```

Beklenen çıktı:

```text
Arama arayüzü: http://<IP>:19003
```

---

## Hazır Test Senaryoları

Arayüzdeki **Hızlı testler** çiplerinin her biri bir metodu gösterir. Aynı aramaları JSON uç
noktasından terminalde çalıştırın:

```bash
for t in "fuzzy kuberntes" "nested docker%20run" "match_phrase control%20plane" "match k%C3%BCmeler" "multi_match vm.max_map_count"; do
  set -- $t
  curl -s "http://localhost:19003/api/search?type=$1&q=$2" | jq -c "{type, total, ilk: .hits[0].title}"
done
```

Beklenen çıktı:

```text
{"type":"fuzzy","total":4,"ilk":"Kubernetes Ingress ve Service Mimarisi"}
{"type":"nested","total":4,"ilk":"Docker Network ve Volume Yönetimi"}
{"type":"match_phrase","total":1,"ilk":"Kubernetes Mimarisi ve Pod Troubleshooting Rehberi"}
{"type":"match","total":4,"ilk":"Elasticsearch Cluster Mimarisi ve Sharding Rehberi"}
{"type":"multi_match","total":1,"ilk":"Linux Sunucu Performansı ve Kernel Ayarları Rehberi"}
```

| Senaryo | Metot | İfade | Ne gösterir |
| :--- | :--- | :--- | :--- |
| Yazım hatası | `fuzzy` | `kuberntes` | Bir harf eksik olsa da Kubernetes dokümanları bulunur. |
| Kod bloğunda komut | `nested` | `docker run` | Eşleşen kod bloğu ve bölüm `inner_hits` ile kartın içinde vurgulanır. |
| Sıralı kalıp | `match_phrase` | `control plane` | İki kelimenin yan yana geçtiği tek doküman gelir. |
| Türkçe kök | `match` | `kümeler` | Çoğul eki atılır (`küme`); "kümesinde", "küme" geçen dokümanlar bulunur. |
| Noktalı terim | `multi_match` | `vm.max_map_count` | Standard tokenizer noktalı terimi bölmez; Linux dokümanı gelir. |

Analyzer'ın kelimeleri nasıl parçaladığını görün:

```bash
curl -s "http://localhost:19003/api/analyze?text=K%C3%BCmeler%20ILM" | jq -c "{turkish, standard}"
```

Beklenen çıktı:

```text
{"turkish":["kumeler","kümeler","kume","küme","ilm","ılm"],"standard":["kümeler","ilm"]}
```

* `küme` / `kume`: stemmer çoğul ekini attı; `asciifolding` ü → u biçimini de ekledi, bu yüzden
  kullanıcı `kume` yazsa da aynı dokümanlar bulunur.
* `ılm`: Türkçe küçük harf kuralı `I` → `ı` yapar. İngilizce teknik terimlerde bu yanlış bir biçim
  üretir; `asciifolding` orijinal `ilm` biçimini de koruduğu için `ILM` araması yine çalışır.
* Snowball Türkçe stemmer her türevi aynı köke indirmez (`kümelenme` olduğu gibi kalır, `podları`
  → `podu`). `keyword_repeat` orijinal kelimeyi de indexlediği için tam kelime araması kaybolmaz.

---

## Dizin Yapısı
```text
bilgincit-devops-search/
├── docs/                   # Aranacak tüm dokümanlar (Markdown, YAML, Bash vb.)
│   ├── elasticsearch/      # Cluster, Shard, ILM, Query DSL
│   └── devops/             # Docker, Kubernetes, Linux, Monitoring
├── templates/
│   ├── index.html          # Arama sayfası: metotlar, facet'ler, sorgu laboratuvarı
│   └── document.html       # Doküman okuyucu: içindekiler, vurgulama, kod renklendirme
├── static/css/app.css      # Ortak stil (açık/koyu tema)
├── app.py                  # Flask Web Servisi & Elasticsearch Entegrasyonu
├── indexer.py              # Türkçe Analyzer & Nested Mapping destekli indeksleyici
├── requirements.txt        # Python kütüphaneleri
└── .env.example            # Bağlantı ayarları şablonu (cp .env.example .env)
```

---

## Temizlik

```bash
cd ~/elastic/projects/bilgincit-devops-search
[ -f app.pid ] && kill "$(cat app.pid)"; rm -f app.pid
curl -s -u elastic:'DevOps2026!' -X DELETE "http://localhost:9200/bilgincit_docs"
```

Yalnızca bu projenin Flask süreci ve `bilgincit_docs` index'i silinir; ana cluster etkilenmez.
