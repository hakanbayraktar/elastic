# Project: Telecom Operations Insight Platform (Capstone)

Bu bitirme labı, önceki lablarda ayrı ayrı kanıtlanan parçaları tek operasyon senaryosunda birleştirir. Amaç bir dashboard resmi üretmek değil, bir incident'in kaynaktan restore kanıtına kadar araştırılabildiği çalışan bir sistem göstermektir.

## Senaryo

NovaShop checkout trafiğinde beş dakikalık 5xx oranı artar. Aynı zaman aralığında p95 gecikme yükselir, edge proxy farklı IP'lerden olağandışı denemeler görür ve bir data node'un disk kullanımı watermark eşiğine yaklaşır. Kaynaklar Linux, Docker, Kind, proxy/API ve uygulama loglarıdır. Gerçek müşteri veya güvenlik verisi kullanılmaz.

## Hedef mimari

```text
Linux ─┐
Docker ─┼─> Filebeat / Elastic Agent ─> Logstash ─> ingest pipeline
Kind ──┤                                              │
NovaShop┘                                             v
                               logs-telecom.capstone-prod data stream ─> ILM
                                         │                     │
                                         v                     v
                             Kibana: Discover / Lens / Rule   Snapshot
```

Nginx bu mimarinin önünde erişim katmanıdır: DNS adı ve IP:port isteklerini TLS + kimlik doğrulamasıyla Kibana/Elasticsearch'e iletir. Elasticsearch ve Kibana backend portları doğrudan yayımlanmaz.

## Çalışma klasörü

```bash
cd ~/elastic/projects/telecom-operations-insight-platform
```

## Uygulama sırası

### 1. Platform kanıtını tekrar alın

- LAB-01: DNS ve IP:9200 üzerinden `/_cluster/health`.
- LAB-01: Kind node'ları `Ready`.
- Önceki lab verisi gerekmez; aşağıdaki generator kendi fixture'ını üretir.
- Capstone: kendi pipeline/template/ILM varlıkları ve `logs-telecom.capstone-prod` data stream'i.
- LAB-09B: snapshot repository erişimi ve read-only test kimliği.

Eksik basamağı sonraki adıma geçmeden tamamlayın. Bitirme labı, eksik bir altyapıyı gizlemek için kullanılmaz.

### 2. Beş kaynaktan veri üretin ve sayın

Kaynak başına en az bir olay gerekir: Linux, Docker, Kind, Nginx/proxy ve NovaShop. Bu olaylar 4. adımdaki generator ile üretilir; dağılımı veri yüklendikten sonra 4. adımın sonundaki sorguyla doğrularsınız.

Her kaynak için aynı minimum bağlamı koruyun: `@timestamp`, `service.name`, `event.dataset`, `message` ve uygun olduğunda `trace.id`.

### 3. ECS sözleşmesini yazın

`starter/ecs-contract.md` şablonunu kopyalayıp doldurun. En az şu eşlemeleri yazın:

| Kaynak değeri | ECS alanı | Tip | Neden |
|---|---|---|---|
| Proxy status | `http.response.status_code` | `short` | range, hata oranı |
| Uygulama süre ms | `event.duration` | `long` (ns) | p95 |
| İstek kimliği | `trace.id` | `keyword` | korelasyon |
| Kaynak IP | `client.ip` | `ip` | filtre/GeoIP |
| Pod adı | `kubernetes.pod.name` | `keyword` | Kubernetes bağlamı |

Bu sözleşme pipeline, mapping ve dashboard'un ortak dilidir. Aynı kavramı iki farklı özel alana yazmayın.

### 4. Incident verisini oluşturun

Capstone generator'ı her istek için proxy, API, NovaShop, subscriber DB simülasyonu ve 5G core olaylarını aynı trace ile üretir. Linux, Docker, Kind ve Nginx kaynakları her on istekte bir eklenir. Ayrı bulk dosyası, ECS/PII pipeline, component/index template, data stream ve ILM policy Capstone'a aittir; `load_capstone.py` kurulum varlıklarını kendi içinde uygular. Altı senaryo:

```bash
cd ~/elastic/projects/telecom-operations-insight-platform
python3 scripts/setup_capstone.py
python3 generator/generate_capstone.py --scenario normal --requests 100 --output /tmp/capstone.ndjson
python3 scripts/load_capstone.py --scenario normal --requests 100
python3 scripts/load_capstone.py --scenario surge --requests 100
python3 scripts/load_capstone.py --scenario high-5xx --requests 100
python3 scripts/load_capstone.py --scenario high-latency --requests 100
python3 scripts/load_capstone.py --scenario bad-auth --requests 100
python3 scripts/load_capstone.py --scenario suspicious-ip --requests 100
```

Yükleyici `logs-telecom.capstone-prod` data stream'ine ve `lab04-telecom-capstone-v1` pipeline'ına yazar; `labels.training_profile=capstone` ve `labels.run_id` senaryo sorgusu için tutulur. Her yüklemede bulk hatası, beklenen doküman sayısı, 5 servisli trace, ECS dönüşümü, PII temizliği, p95, normal hata eşiği, 401 ve şüpheli IP ölçümleri doğrulanır. Her senaryonun raporu `reports/capstone-<scenario>-runtime-report.json` olarak yazılır. Bu lab LAB-02 verisine bağlı değildir ve kendi index varlıklarını üretir.

Beş kaynağın ve servislerin data stream'deki dağılımını doğrulayın (Kibana Dev Tools):

```http
GET logs-telecom.capstone-prod/_search
{
  "size": 0,
  "aggs": {
    "by_dataset": {"terms": {"field": "event.dataset", "size": 20}},
    "by_service": {"terms": {"field": "service.name", "size": 20}}
  }
}
```

### 5. Operasyon dashboard'unu oluşturun

Tek dashboard'a şu panelleri ekleyin:

1. İstek sayısı (zaman serisi).
2. 5xx oranı (beş dakikalık oran).
3. p95 response time.
4. En sorunlu 10 endpoint.
5. Kaynak IP veya GeoIP dağılımı.
6. Host disk/CPU ve uptime sonucu.
7. `trace.id` drilldown bağlantısı veya Discover saved search.

Her panelde environment/dataset/zaman filtresini görünür yapın. Metrik birimi açık olmalıdır: `event.duration` nanosaniye ise Lens'te ms/sn dönüşümünü doğru yapın.

### 6. Incident araştırması ve isteğe bağlı alert

Temel akışta dashboard ve Dev Tools ile 5xx/p95 araştırmasını tamamlayın. Scheduled rule için security/API key ve kalıcı Kibana encryption key önkoşulu vardır; lisanslı ML/SLO bölümü en son birlikte etkinleştirilir. Bu önkoşullar hazır değilse `--dashboard-only` kullanın ve rule kabulünü ertelendi olarak raporlayın.

> [!NOTE]
> **Lisans:** Bu capstone'un uyarı kuralı `.server-log` connector'ını kullanır
> ve bu connector `basic` lisansla çalışır; alert bölümü için trial gerekmez,
> uyarı Kibana sunucu log'una yazılır. Buna karşılık LAB-07'deki Slack ve
> e-posta connector'ları `gold` ve üstü ister (Basic lisansta
> `enabled_in_license: false` dönerler). Yani bu capstone'u Basic lisansta
> uçtan uca tamamlayabilirsiniz.


Beş dakika içinde 5xx oranı %5 üstüne çıktığında çalışan bir kural oluşturun. Alert geldikten sonra aşağıdaki sırayla araştırın:

1. Zaman aralığını kilitleyin; request count ve 5xx oranını doğrulayın.
2. En sorunlu endpoint, `service.name` ve `trace.id` ile olayları daraltın.
3. Aynı aralıkta p95, uptime, host CPU/disk ve container/pod olaylarını karşılaştırın.
4. Disk veya allocation belirtisi varsa LAB-09B operasyon karar sırasını kullanın.
5. Kanıta dayalı kısa incident runbook'u yazın.

### 7. Retention ve kurtarma kanıtını tamamlayın

```http
GET logs-telecom.capstone-prod/_ilm/explain
GET _data_stream/logs-telecom.capstone-prod
```

Snapshot alın; test indexini farklı isimle restore edin. Restore edilen veride aynı trace'i arayın. Böylece yalnız snapshot `SUCCESS` değil, geri gelen verinin kullanılabilir olduğu da kanıtlanır.

## Teslim paketi

- Veri akış mimarisi diyagramı.
- Tamamlanmış ECS sözleşmesi.
- Collector/Logstash/ingest/template/ILM yapılandırmaları.
- Dashboard export veya ekran kanıtı ve alert kuralı.
- Snapshot/restore API sonucu ve count/trace doğrulaması.
- `high-5xx-latency-disk-pressure` incident runbook'u.

Çalışan sentetik veriyi Kibana varlıkları ile yüklemek için:

```bash
cd ~/elastic/projects/telecom-operations-insight-platform
python3 scripts/provision_capstone.py --dashboard-only
```

Komut ayrı Data View, beş Lens paneli ve dashboard oluşturur/günceller. Bu labın ECS sözleşmesinde `labels` flattened olduğu için Kibana Data View alt alanları göstermiyor; dashboard, indexlenmiş ECS `trace.id` alanında `capstone-trace-*` prefix filtresiyle capstone proxy olaylarını ayırır. `labels.training_profile=capstone` de ham Elasticsearch Query DSL'de filtrelenebilir. `KIBANA_URL`, `ELASTIC_URL`, `*_USER`, `*_PASSWORD` (varsayılan `elastic` / `DevOps2026!`) ve gerekiyorsa `*_CA_FILE` ortam değişkenleri desteklenir.

Generator'ın birim testlerini çalıştırın (Elasticsearch gerektirmez):

```bash
python3 -m unittest discover -s tests -v
```

Uyarı kuralını da kurmak için `--dashboard-only` olmadan çalıştırın: `.server-log` connector'ı ve
5 dakikalık >%5 5xx ES|QL kuralı eklenir. `verify_alert.py` yeni incident verisi yükler ve
scheduler'ın aktif alert ürettiğini doğrular (kuralın çalışmasını beklediği için birkaç dakika sürer):

```bash
python3 scripts/provision_capstone.py
python3 tests/verify_alert.py
```

Tarayıcı testi Node.js 20+ ve Chrome ister; eğitim sunucusunda kurulu değildir. Kendi
makinenizde proje dizininden çalıştırırsanız ekran görüntüsünü ve Lens sorgu metriklerini
`reports/ui/` içine kaydeder:

<!-- runner:skip -->
```bash
UI_EVIDENCE_DIR=reports/ui node ../../labs/LAB-02-indexleme-mapping-crud/tests/kibana-ui.mjs --capstone-only
```

## Doğrulama

```bash
./verify.sh
```

Pipeline, data stream ve doküman sayısı, dashboard ve Kibana erişimi denetlenir; eksikse
`exit 1`. Uyarı kuralı opsiyonel olduğu için kural yoksa yalnız uyarı verir.

## Kabul kontrolü

| Kontrol | Başarılı kanıt |
|---|---|
| Merkezi loglama | Beş kaynak tek data stream'de filtrelenebilir |
| Arama | Bir `trace.id` ile en az iki servis olayı sıralanır |
| Analiz | Dashboard'da 5xx, p95, endpoint ve kaynak dağılımı vardır |
| Observability | Log, metric ve uptime aynı zaman aralığında karşılaştırılır |
| Yaşam döngüsü | `_ilm/explain` ve backing index görünür |
| Operasyon | Snapshot sonrası farklı isimli restore doğrulanır |

## Manuel incident dashboard ve drilldown

[Manuel Kibana rehberi](https://gitlab.com/devops-monitoring/elastic/-/blob/eski-lab/labs/LAB-03-text-analysis-ve-arama/KIBANA_UYGULAMA_REHBERI.md) §1–5 ile `logs-telecom.capstone-prod` üzerinde “Telecom Olay Araştırması” dashboard'unu oluşturun. Incident aralığını mutlak zamana sabitleyin; request panellerinde yalnız proxy kayıtlarını kullanın. CPU/disk/uptime panelleri ancak ilgili metric/uptime stream'lerinde veri varsa eklenir; yoksa varmış gibi çizilmez. §4'teki panel adımlarından sonra gerçek metric alanını Lens'e sürükleyip Average veya Last value seçin; trace için §5'teki Discover geçişini uygulayın.

## Temizlik

```bash
cd ~/elastic/projects/telecom-operations-insight-platform
./teardown.sh
```

Silinenler: `logs-telecom.capstone-prod` data stream'i, `lab04-telecom-capstone-*` şablon,
component template, ILM policy ve ingest pipeline'ı, `telecom-capstone-view` data view'ı, beş
`capstone-*` Lens paneli, `telecom-operations-capstone` panosu, `telecom-capstone-error-rate`
kuralı ve `telecom-capstone-log` connector'ı, yerel `reports/` dizini. Omurga ve diğer labların
kaynakları etkilenmez.
