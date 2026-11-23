# LAB-27 — Apache Uçtan Uca: Logstash, Harita, Alarm (E-posta ve Slack) ve PDF Rapor

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Apache, Filebeat, Logstash (grok, GeoIP), Metricbeat, Kibana (pano, Maps, Alerting, Reporting), Mailpit, Resend, Slack | `8088` (Apache, dışarıdan), `127.0.0.1:8025` (Mailpit arayüzü), 9200 / 5601 (ana cluster) |

---

## Bu lab ne öğretiyor?

Önceki lablarda her parçayı ayrı ayrı kurduk. Gerçek bir web sitesinde ise hepsi birbirine bağlıdır:
Apache bir istek alır, Filebeat log satırını Logstash'e taşır, Logstash satırı field'lara ayırıp IP'den
ülkeyi bulur, Kibana panoda ve haritada gösterir. Hata oranı artınca da kimse panoya bakmadan e-posta
ve Slack mesajı gelir; yönetime giden rapor PDF olarak hazırlanır.

Bu labda bu zincirin tamamını tek seferde kuracak, bir arızayı kendimiz üretip alarmın Mailpit'e,
gerçek e-posta kutusuna ve Slack kanalına geldiğini görecek, sonunda panoyu PDF rapor olarak alacağız.

![Apache uçtan uca: Apache, Filebeat, Logstash, Elasticsearch, Kibana, alarm ve rapor](../../assets/infographics/21-apache-uctan-uca.png)

---

## Ön Koşullar

- Önce kurulu olmalı: LAB-01 ana cluster'ı ve trial lisans. E-posta/Slack connector'ları ve PDF rapor ücretli
  özelliklerdir.
- Önceki labları atladıysanız da bu lab çalışır; LAB-01 dışında hiçbir labın verisini kullanmaz.
- `8088` ve `127.0.0.1:8025` boş olmalı. Yedi container birlikte yaklaşık 2 GB RAM kullanır.

```bash
cd ~/elastic/labs/LAB-27-apache-uctan-uca
```


---

## Kavramlar: bir istek nereden geçer?

| Parça | Görevi | Bu labda |
|---|---|---|
| Apache | İsteği karşılar, her isteği `access_log`'a bir satır yazar | `apache-web-observability-apache-1`, port 8088 |
| Trafik üreteci | Siteye sürekli istek atar; boş pano olmasın | Saniyede bir istek, farklı ülkelerden IP'lerle |
| Filebeat | Log dosyasını okuyup Logstash'e gönderir | `access_log`, `error_log` |
| Logstash | grok ile field'lara ayırır, GeoIP ile IP'den konum bulur | `logstash/pipeline/apache.conf` |
| Metricbeat | Apache'nin anlık durumunu (`server-status`) ve container metriklerini ölçer | 10 saniyede bir |
| Kibana | Pano, harita, alarm kuralı, PDF rapor | |
| Mailpit | Gerçek e-posta göndermeden alarm e-postalarını yakalayan yerel posta sunucusu | `127.0.0.1:8025` |

---

## Config dosyaları: hangi satır ne işe yarıyor?

`logstash/pipeline/apache.conf` (kritik satırlar):

```conf
grok { match => { "message" => '^%{IP:[apache][remote_ip]} %{NOTSPACE:[apache][xff_ip]} ... %{INT:[http][response][status_code]} ...' } }
if [apache][xff_ip] != "-" { mutate { rename => { "[apache][xff_ip]" => "[source][ip]" } } }
geoip { source => "[source][ip]" target => "[source]" }
elasticsearch { index => "apache-web-%{+yyyy.MM.dd}" }
```

- Apache'nin log biçimi (`apache/conf`) istemci IP'sinin yanına `X-Forwarded-For` başlığını da yazar.
  Site bir yük dengeleyicinin arkasındaysa gerçek ziyaretçi IP'si bu başlıktadır; Logstash varsa onu
  `source.ip` yapar.
- `geoip`: IP'den `source.geo.country_name`, `city_name` ve haritada kullanılan `source.geo.location`
  (`geo_point`) üretir. Özel ağ IP'lerinin (10.x, 172.x, 192.168.x) konumu yoktur.
- `apache-web-*` index'leri `elastic/apache-index-template.json` şablonuyla tek shard ve 0 replica açılır.

---

## Adım Adım Uygulama Rehberi

### 1. Yığını başlatın

```bash
docker compose up --build -d
timeout 240 bash -c 'until [ "$(curl -s -u elastic:"DevOps2026!" "http://127.0.0.1:9200/apache-web-*/_count" 2>/dev/null | jq .count 2>/dev/null)" -gt 20 ] 2>/dev/null; do printf .; sleep 5; done'; echo " veri akiyor"
docker compose ps --format '{{.Name}}\t{{.Status}}'
```

<details>
<summary><strong>Çıktının tamamı (7 satır)</strong></summary>

```text
........... veri akiyor
apache-web-observability-apache-1	Up About a minute
apache-web-observability-filebeat-1	Up About a minute
apache-web-observability-logstash-1	Up About a minute
apache-web-observability-metricbeat-1	Up 56 seconds
apache-web-observability-traffic-generator-1	Up About a minute
mailpit-apache-lab	Up About a minute (healthy)
```

</details>

Apache'yi tarayıcıda açmak için adresleri sunucuda hesaplayın:

```bash
IP=$(curl -s https://api.ipify.org); H=$(hostname -s)
echo "Apache: http://$IP:8088   https://$H-apache.devopsatolyesi.com"
echo "Kibana: http://$IP:5601   https://$H-kibana.devopsatolyesi.com"
```

Beklenen çıktı:

```text
Apache: http://<IP>:8088   https://<host>-apache.devopsatolyesi.com
Kibana: http://<IP>:5601   https://<host>-kibana.devopsatolyesi.com
```

### 2. Bir isteğin yolculuğu: ham satır ve document

Siteye Almanya'daki bir IP'den geliyormuş gibi tek bir istek atın; `X-Request-ID` onu sonra bulmamızı sağlar:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H 'X-Forwarded-For: 5.9.0.1' -H 'X-Request-ID: apache-yolculuk' http://127.0.0.1:8088/products/sku-100
docker compose exec -T apache grep apache-yolculuk /usr/local/apache2/logs/access_log
```

Beklenen çıktı:

```text
404
172.23.0.1 5.9.0.1 apache-yolculuk - - [22/Nov/2026:02:35:25 +0000] "GET /products/sku-100 HTTP/1.1" 404 236 231 "-" "curl/8.5.0"
```

Aynı istek birkaç saniye sonra Elasticsearch'te:

```bash
timeout 60 bash -c 'until [ "$(curl -s -u elastic:"DevOps2026!" "http://127.0.0.1:9200/apache-web-*/_count?q=http.request.id:apache-yolculuk" | jq .count)" -ge 1 ]; do printf .; sleep 3; done'; echo
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/apache-web-*/_search?q=http.request.id:apache-yolculuk' \
  | jq -c '.hits.hits[0]._source | {"source.ip": .source.ip, ulke: .source.geo.country_name, sehir: .source.geo.city_name, konum: .source.geo.location, method: .http.request.method, "url.path": .url.path, durum: .http.response.status_code}'
```

Beklenen çıktı:

```text
..
{"source.ip":"5.9.0.1","ulke":"Germany","sehir":"Falkenstein","konum":{"lon":12.3649,"lat":50.4777},"method":"GET","url.path":"/products/sku-100","durum":404}
```

Ham satırdaki Docker ağ adresi (`172.23.0.1`) ve tarih sizde farklıdır.

| Ham satırda | Document'te | Nasıl |
|---|---|---|
| `172.x... 5.9.0.1 apache-yolculuk` | `source.ip: 5.9.0.1` (Docker ağının IP'si değil) | grok + `X-Forwarded-For` kuralı |
| (yok) | `ulke`, `sehir`, `konum` | `geoip` |
| `"GET /products/sku-100 HTTP/1.1" 404` | `method`, `url.path`, `durum` (sayı) | grok + `convert` |

### 3. Pano ve harita

Betik iki data view ve Lens panellerinden oluşan bir pano kurar:

```bash
python3 scripts/provision_kibana.py
```

<details>
<summary><strong>Çıktının tamamı (8 satır)</strong></summary>

```text
PASS Data View: Apache Web İstek ve Hata Logları (apache-web-*)
PASS Data View: Apache ve Docker Metrikleri (metricbeat-*)
PASS Lens: apache-web-requests
PASS Lens: apache-web-error-count
PASS Lens: apache-web-endpoints
PASS Lens: apache-web-latency
PASS Lens: apache-web-geo
PASS Dashboard: apache-web-operations (5 Lens panels)
```

</details>

Kibana'da **Analytics › Dashboards › Apache Web Trafiği ve GeoIP**:

![Apache panosu: 1 dakikalık istek sayısı; yanında 5xx sayısı, altta en sorunlu endpoint'ler ve p95 yanıt süresi](../../assets/screenshots/LAB-27/01-pano.png)

Ziyaretçilerin nereden geldiğini haritada görmek için **Analytics › Maps › Create map**, **Add layer ›
Clusters**, data view **Apache Web İstek ve Hata Logları**, **Add and close**. Haritayı `Apache ziyaretçileri`
adıyla kaydedin; panoya **Add › From library** ile eklenebilir:

![Harita: 1 Clusters katmanı; daireler ülkelere göre istek sayısını gösterir](../../assets/screenshots/LAB-27/02-harita.png)

### 4. Alarm: 5xx artınca e-posta (Mailpit)

Önce gerçek bir hesap gerektirmeyen Mailpit'le kuralı kuralım. Kibana'nın e-postayı gönderebileceği bir
connector (Kibana › Dev Tools):

```http
POST kbn:/api/actions/connector/apache-mailpit
{ "name": "apache-mailpit", "connector_type_id": ".email",
  "config": { "service": "other", "host": "mailpit-apache-lab", "port": 1025, "secure": false, "from": "alarm@lab.local", "hasAuth": false },
  "secrets": {} }
```

<details>
<summary><strong>Çıktının tamamı (7 satır)</strong></summary>

```json
{
  "id": "apache-mailpit",
  "name": "apache-mailpit",
  "config": { "service": "other", "host": "mailpit-apache-lab", "port": 1025, "secure": false, "from": "alarm@lab.local", ... },
  "connector_type_id": ".email",
  ...
}
```

</details>

Her dakika çalışan ve son 2 dakikada 40'tan fazla 5xx görünce alarm açan kural. Yalnız Apache'nin kendi
kayıtları (`event.dataset: apache.access`) sayılır; trafik üretecinin kendi kayıtları (`apache.traffic`) aynı
isteği ikinci kez yazdığı için dışarıda kalır. Trafik üreteci kendi başına dakikada 2-7 hata üretir (testte 2 dakikada en çok 10); eşik
bunun belirgin biçimde üstünde olduğu için alarm yalnız gerçek bir artışta açılır, 60 istekli arıza ise eşiği
her zaman aşar. Pencere 2 dakikadır, çünkü loglar Elasticsearch'e birkaç saniye geç ulaşır;
1 dakikalık pencerede iki çalışmanın arasına düşen hatalar hiç sayılmaz.
`notify_when: onActionGroupChange` alarm açıldığında bir kez mesaj gönderir, alarm sürdükçe tekrarlamaz:

```http
POST kbn:/api/alerting/rule/apache-5xx
{
  "name": "Apache 5xx artışı", "rule_type_id": ".es-query", "consumer": "stackAlerts", "schedule": { "interval": "1m" },
  "params": { "searchType": "esQuery", "index": ["apache-web-*"], "timeField": "@timestamp",
    "esQuery": "{\"query\":{\"bool\":{\"filter\":[{\"term\":{\"event.dataset\":\"apache.access\"}},{\"range\":{\"http.response.status_code\":{\"gte\":500}}}]}}}",
    "threshold": [40], "thresholdComparator": ">", "timeWindowSize": 2, "timeWindowUnit": "m",
    "size": 0, "aggType": "count", "groupBy": "all", "excludeHitsFromPreviousRun": false },
  "actions": [ { "id": "apache-mailpit", "group": "query matched",
    "params": { "to": ["operasyon@lab.local"], "subject": "[ALARM] {{rule.name}}: {{context.value}} adet 5xx",
      "message": "{{context.conditions}}\nOlculen: {{context.value}}\nZaman: {{context.date}}" },
    "frequency": { "summary": false, "notify_when": "onActionGroupChange", "throttle": null } } ]
}
```

<details>
<summary><strong>Çıktının tamamı (8 satır)</strong></summary>

```json
{
  "id": "apache-5xx",
  "enabled": true,
  "name": "Apache 5xx artışı",
  "rule_type_id": ".es-query",
  "schedule": { "interval": "1m" },
  ...
}
```

</details>

Arızayı üretin: bakımdaki bir sayfaya (`/cgi-bin/unavailable.sh`, 503 döner) 60 istek:

```bash
python3 scripts/generate_burst.py --path /cgi-bin/unavailable.sh --requests 60
timeout 180 bash -c 'until [ "$(curl -s 127.0.0.1:8025/api/v1/messages | jq .total)" -ge 1 ]; do printf .; sleep 5; done'; echo
curl -s 127.0.0.1:8025/api/v1/messages | jq -c '.messages[0] | {Subject, To: [.To[].Address], From: .From.Address}'
```

Beklenen çıktı:

```text
requests=60 concurrency=8 ip=195.175.39.39 elapsed_seconds=0.44 statuses={503: 60}
.............
{"Subject":"[ALARM] Apache 5xx artışı: 65 adet 5xx","To":["operasyon@lab.local"],"From":"alarm@lab.local"}
```

Kural dakikada bir çalıştığı için e-posta testte yaklaşık 1 dakikada geldi. Sayı sizde farklıdır: 60 arıza isteğine trafik üretecinin arada ürettiği hatalar da eklenir. Mailpit
arayüzü yalnız sunucudan açılır. Kendi bilgisayarınızdan bir SSH tüneliyle açın, sonra tarayıcıda
`http://127.0.0.1:8025`:

<!-- runner:skip -->
```bash
ssh -f -N -L 8025:127.0.0.1:8025 student@<sunucu-ip>
```

![Mailpit: 1 alarm e-postası; sağda konu ve ölçülen değer](../../assets/screenshots/LAB-27/03-mailpit.png)

İşiniz bitince tüneli kapatın: `pkill -f "\-L 8025:127.0.0.1:8025"`.

### 5. Gerçek e-posta (Resend) ve Slack

Bu adım bir Resend hesabınız ve bir Slack çalışma alanınız varsa yapılır. Yoksa alarm akışını 4. adımda
Mailpit ile görmüş olmanız yeterlidir; 6. adıma geçin.

<details>
<summary><strong>Resend ve Slack hesabınız varsa: adımlar</strong></summary>

Gerçek kanallar için iki gizli bilgi gerekir: Resend API
anahtarı ve Slack webhook adresi.

<details>
<summary><strong>Resend anahtarı ve Slack webhook nasıl alınır?</strong></summary>

- **Resend API anahtarı:** [resend.com](https://resend.com)'da ücretsiz hesap açın; **API Keys › Create
  API Key**. Hesap doğrulanmış bir alan adı olmadan yalnız kendi e-posta adresinize gönderir; test için
  yeterlidir. Gönderen adres `onboarding@resend.dev` olur.
- **Slack webhook:** [api.slack.com/apps](https://api.slack.com/apps) › **Create New App › From scratch**
  › **Incoming Webhooks** › **Activate** › **Add New Webhook to Workspace** › kanal seçin. Adres
  `https://hooks.slack.com/services/T…/B…/…` biçimindedir.

</details>

İkisi de parola gibidir: bilen herkes sizin adınıza e-posta ya da mesaj gönderir. Komuta, repoya ya da ekran
görüntüsüne yazmayın; yalnız sizin okuyabildiğiniz bir dosyaya koyun. Dosyayı önce yalnız size açık
oluşturun (var olan dosyaya dokunmaz):

```bash
[ -e ~/.lab24-gizli ] || install -m 600 /dev/null ~/.lab24-gizli
chmod 600 ~/.lab24-gizli; stat -L -c %A ~/.lab24-gizli
```

Beklenen çıktı:

```text
-rw-------
```

Sonra bir metin editörüyle (örneğin `nano ~/.lab24-gizli`) üç satırı yazın:

```text
RESEND_API_KEY=re_...
SLACK_WEBHOOK=https://hooks.slack.com/services/...
ALARM_TO=sizin@adresiniz.com
```

Değerleri ortama alın ve iki connector'ı kurun. Anahtar komut satırına yazılmaz, çünkü komut satırı çalışırken
`ps` ile başkalarına görünür: `jq` JSON'u ortam değişkeninden (`$ENV`) üretir, `scripts/kbn.sh` onu standart
girdiden Kibana API'sine gönderir. En sondaki `unset` anahtarları shell'den siler; `ALARM_TO` kalır:

```bash
set -a; . ~/.lab24-gizli; set +a
jq -n '{name:"apache-eposta", connector_type_id:".email", config:{service:"other", host:"smtp.resend.com", port:465, secure:true, from:"onboarding@resend.dev", hasAuth:true}, secrets:{user:"resend", password:$ENV.RESEND_API_KEY}}' | ./scripts/kbn.sh POST /api/actions/connector/apache-eposta @- | jq -c '{id, connector_type_id}'
jq -n '{name:"apache-slack", connector_type_id:".slack", secrets:{webhookUrl:$ENV.SLACK_WEBHOOK}}' | ./scripts/kbn.sh POST /api/actions/connector/apache-slack @- | jq -c '{id, connector_type_id}'
unset RESEND_API_KEY SLACK_WEBHOOK
```

Beklenen çıktı:

```text
{"id":"apache-eposta","connector_type_id":".email"}
{"id":"apache-slack","connector_type_id":".slack"}
```

<details>
<summary><strong>Connector kurulumu yarıda kaldıysa</strong></summary>

Dosya ortama okunmadan komut çalıştırılırsa ya da iki komuttan biri hata verirse connector'lardan biri
kurulur, diğeri kurulmaz. Aynı bloğu yeniden çalıştırmak çözmez: kurulmuş olan için Kibana `409 Conflict`
döndürür, çünkü o id zaten vardır. İkisini de silip yeniden kurun:

```bash
set -a; . ~/.lab24-gizli; set +a
./scripts/kbn.sh DELETE /api/actions/connector/apache-eposta; echo " apache-eposta silindi"
./scripts/kbn.sh DELETE /api/actions/connector/apache-slack; echo " apache-slack silindi"
jq -n '{name:"apache-eposta", connector_type_id:".email", config:{service:"other", host:"smtp.resend.com", port:465, secure:true, from:"onboarding@resend.dev", hasAuth:true}, secrets:{user:"resend", password:$ENV.RESEND_API_KEY}}' | ./scripts/kbn.sh POST /api/actions/connector/apache-eposta @- | jq -c '{id, connector_type_id}'
jq -n '{name:"apache-slack", connector_type_id:".slack", secrets:{webhookUrl:$ENV.SLACK_WEBHOOK}}' | ./scripts/kbn.sh POST /api/actions/connector/apache-slack @- | jq -c '{id, connector_type_id}'
unset RESEND_API_KEY SLACK_WEBHOOK
```

Beklenen çıktı:

```text
 apache-eposta silindi
 apache-slack silindi
{"id":"apache-eposta","connector_type_id":".email"}
{"id":"apache-slack","connector_type_id":".slack"}
```

</details>

Kibana gizli bilgileri şifreli saklar; connector listesi onları bir daha göstermez. Bağlantıyı kural
beklemeden deneyin; e-posta kutunuza ve Slack kanalınıza birer test mesajı düşer:

```bash
./scripts/kbn.sh POST /api/actions/connector/apache-eposta/_execute "{\"params\":{\"to\":[\"$ALARM_TO\"],\"subject\":\"LAB-27 e-posta testi\",\"message\":\"Kibana connector testi\"}}" | jq -c '{status, connector_id}'
./scripts/kbn.sh POST /api/actions/connector/apache-slack/_execute '{"params":{"message":"LAB-27 Slack testi"}}' | jq -c '{status, connector_id}'
```

Beklenen çıktı:

```text
{"status":"ok","connector_id":"apache-eposta"}
{"status":"ok","connector_id":"apache-slack"}
```

Kurala iki aksiyonu da ekleyin. Kural güncellemesi bütün tanımı ister; en kısa yol kuralı yeniden kurmaktır:

```bash
./scripts/kbn.sh DELETE /api/alerting/rule/apache-5xx; echo
jq -n --arg to "$ALARM_TO" -f scripts/kural.jq | ./scripts/kbn.sh POST /api/alerting/rule/apache-5xx @- | jq -c '{id, actions: [.actions[].id]}'
```

Beklenen çıktı:

```text
{"id":"apache-5xx","actions":["apache-mailpit","apache-eposta","apache-slack"]}
```

Kural yeni kurulduğu için alarm durumu sıfırdır. Arızayı hemen tekrar üretin; kural bir sonraki kontrolde
alarmı açar ve üç kanala birer mesaj gider:

```bash
python3 scripts/generate_burst.py --path /cgi-bin/unavailable.sh --requests 60
timeout 180 bash -c 'until curl -s -u elastic:"DevOps2026!" -H "kbn-xsrf: true" http://127.0.0.1:5601/api/alerting/rule/apache-5xx | jq -e ".last_run.alerts_count.active == 1" >/dev/null; do printf .; sleep 10; done'; echo " alarm acildi"
```

Beklenen çıktı:

```text
requests=60 concurrency=8 ip=195.175.39.39 elapsed_seconds=0.34 statuses={503: 60}
. alarm acildi
```

Testte alarm 10 saniye içinde açıldı: önceki arıza 2 dakikalık pencerede hâlâ duruyorsa kural ilk kontrolde açar, durmuyorsa en geç 1 dakika sürer. E-posta kutunuza ve Slack kanalınıza `[ALARM] Apache 5xx artışı` mesajı düşer. Kibana'da **Stack Management ›
Connectors** listesinde bu labın üç connector'ı görünür (başka labların connector'ları da listede olabilir):

![Connector'lar: 1 Mailpit, 2 gerçek e-posta, 3 Slack](../../assets/screenshots/LAB-27/04-connectorlar.png)

Gerçek kanallara sonradan gereksiz mesaj gitmesin diye denemeden sonra kuralı kapatın. Kural silinmez;
Stack Management › Rules'tan yeniden açılabilir:

```bash
./scripts/kbn.sh POST /api/alerting/rule/apache-5xx/_disable; echo " kural kapatildi"
```

Beklenen çıktı:

```text
 kural kapatildi
```

<details>
<summary><strong>Resend yerine Gmail</strong></summary>

Gmail için Google hesabında iki adımlı doğrulama açık olmalı ve **Google Hesabı › Güvenlik › Uygulama
şifreleri** ile 16 karakterlik bir uygulama şifresi üretilir. Connector'da `"host": "smtp.gmail.com"`,
`"port": 465`, `"secure": true`, `"from"` ve `"user"` Gmail adresiniz, `"password"` uygulama şifresidir.
Hesap parolanız kullanılmaz.

</details>

</details>

### 6. PDF rapor

Panoyu açın; üst menüde **Export › PDF reports**. Açılan panelin (1) altındaki **Export PDF** (2) düğmesine basın:

![PDF: 1 Export dashboard as PDF paneli, 2 Export PDF](../../assets/screenshots/LAB-27/05-pdf-olustur.png)

Rapor arka planda tarayıcıyla çizilir; birkaç saniye sonra **Stack Management › Reporting**'de görünür ve
indirilir (3):

![Reporting: 3 tamamlanan PDF](../../assets/screenshots/LAB-27/06-reporting.png)

Raporun durumu ve boyutu Kibana'nın rapor kaydında da görülür:

```bash
curl -s -u elastic:'DevOps2026!' -H 'Content-Type: application/json' 'http://127.0.0.1:9200/.kibana-reporting*/_search?expand_wildcards=all' \
  -d '{"size":1,"sort":[{"created_at":"desc"}],"query":{"term":{"jobtype":"printable_pdf_v2"}},"_source":["status","output.content_type","output.size"]}' \
  | jq -c '.hits.hits[0]._source'
```

Beklenen çıktı:

```text
{"status":"completed","output":{"content_type":"application/pdf","size":567696}}
```

<details>
<summary><strong>İsteğe bağlı: ML ile anomali tespiti ve SLO</strong></summary>

Sabit eşik "40'tan fazla 5xx" gibi önceden bilinen bir koşulu yakalar. Machine learning ise her IP'nin olağan
istek sayısını kendisi öğrenir ve bir IP'den beklenmedik çok istek gelince anomali işaretler. SLO de hizmetin
hedefini (örneğin isteklerin %99,9'u 5xx olmasın) ve bu hedeften ne kadar pay kaldığını izler. İkisi de ücretli
özelliktir; trial lisansla çalışır:

```bash
python3 scripts/provision_insights.py
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/_ml/anomaly_detectors/apache-ip-istek-anomali/_stats?filter_path=jobs.state' | jq -c .
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:5601/api/observability/slos' | jq -c '[.results[] | {id, hedef: .objective.target}]'
```

Beklenen çıktı:

```text
ML işi: apache-ip-istek-anomali (açık, veri akışı başladı)
SLO: apache-web-erisilebilirlik
SLO: apache-web-gecikme-500ms
{"jobs":[{"state":"opened"}]}
[{"id":"apache-web-erisilebilirlik","hedef":0.999},{"id":"apache-web-gecikme-500ms","hedef":0.95}]
```

Kibana'da **Machine Learning › Anomaly Detection › Jobs** işi, **Observability › SLOs** iki hedefi gösterir.
İş 5 dakikalık bucket'larla öğrendiği için anlamlı sonuç birkaç saat veri biriktikten sonra gelir. Temizlik ikisini
de siler.

</details>

---

## Temizlik

Yalnız bu labın container'larını ve volume'lerini, `apache-web-*` index'lerini ve şablonunu, Metricbeat'in
data stream'ini, kuralını, üç connector'ını, data view'larını, panosunu ve haritasını siler. Ana cluster'a,
`~/.lab24-gizli` dosyanıza ve Reporting listesindeki PDF kaydına dokunmaz:

```bash
./teardown.sh
```

<details>
<summary><strong>Çıktının tamamı (14 satır)</strong></summary>

```text
kural apache-5xx -> 204
ML isi -> 200
SLO apache-web-erisilebilirlik -> 204
SLO apache-web-gecikme-500ms -> 204
connector apache-mailpit -> 204
connector apache-eposta -> 204
connector apache-slack -> 204
Kibana nesneleri -> 6 silindi
data view apache-web-logs -> 200
data view apache-web-metrics -> 200
index'ler -> 200
sablon apache-web -> 200
metricbeat data stream -> 200
metricbeat sablonu -> 200
```

</details>

Gizli bilgi dosyası işiniz bitince silinebilir: `rm ~/.lab24-gizli`.

Bu, çekirdek akışın son labıdır. İleri konular `labs/advanced/` altındadır: **[ADV-01 — Data stream kuralları ve Data Stream Lifecycle](../advanced/ADV-01-data-stream-kurallari-dsl/README.md)**

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

