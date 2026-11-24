# LAB-18 — Harita, Alerting ve Raporlama: Sorun Olunca Kibana Haber Versin

| Kullanılan Araçlar | Açık / Kullanılan Portlar |
|---|---|
| Kibana Maps, `geo_distance`, Alerting (Elasticsearch query kuralı, Index connector), Reporting | 9200 / 5601 (ana cluster) |

---

## Bu lab ne öğretiyor?

Pano ancak biri bakarken işe yarar: ödeme sayfası gece 03:00'te 500 dönmeye başlarsa sabah panoyu açan kişi sorunu
saatler sonra görür. "Sorun nerede?" sorusu da çoğu zaman bir konum sorusudur. Bu labda web loglarıyla:

- İstekleri **Maps** ile haritada gösterip konuma göre sorgulayacağız.
- 5 dakikada 10'dan fazla 5xx olunca tetiklenen bir **kural** kuracağız.
- Arızayı kendimiz üretip alarmın açıldığını, geçmişe yazıldığını ve kendiliğinden kapandığını izleyeceğiz.
- Sonucu **CSV** ve panonun **PDF** raporu olarak alacağız.

Her arayüz adımı kırmızı kutu ve numarayla gösterilir.

---

## Ön Koşullar

- LAB-01 ana cluster'ı çalışıyor ve trial lisans açık (raporlama için). LAB-16'yı atladıysanız da lab çalışır;
  veri bu labın kendi betiğiyle gelir.

```bash
cd ~/elastic/labs/LAB-18-alerting-raporlama
```

Kibana adresini sunucuda hesaplayın:

```bash
IP=$(curl -s https://api.ipify.org); H=$(hostname -s)
echo "Kibana: http://$IP:5601   https://$H-kibana.devopsatolyesi.com"
```

Beklenen çıktı:

```text
Kibana: http://<IP>:5601   https://<host>-kibana.devopsatolyesi.com
```

---

## Kavramlar: kural, connector, alarm

- **Kural (rule):** belirli aralıkla bir sorgu çalıştırır, koşul sağlanınca alarm üretir; burada her dakika "son 5 dakikada 5xx sayısı 10'dan fazla mı?".
- **Connector:** alarmın nereye gideceği; burada Index connector, `alarm-gecmisi` index'ine document yazar.
- **Action:** kuralı connector'a bağlar; ne zaman ve hangi mesajla yazılacağını söyler.
- **Alarm (alert):** koşul sürdükçe **active**, bitince **recovered** olur.

Index connector gizli bilgi istemez ve alarm geçmişini aranabilir tutar. Slack ve e-posta aynı action yapısıyla
çalışır; ayrıntısı en sondaki açılır kutudadır.

---

## Adım Adım Uygulama Rehberi

### 1. Veri

**Soru: Alarm hangi veriye bakacak?**

Bir mağazanın web sunucusu logu `alarm-apache` index'ine yazılır (6000 olay, son 7 gün, şehir ve
konum field'larıyla):

```bash
python3 scripts/veri_uret.py
```

Beklenen çıktı:

```text
[+] 6000 olay yazildi (alarm-apache), hata: False
    durum kodu : 200=5612, 404=329, 500=59
    ilk 3 ulke : Turkey=3220, Germany=808, United States=483
```

Data view'ı kurun. Kibana › Dev Tools'a yapıştırın:

```http
POST kbn:/api/data_views/data_view
{ "data_view": { "id": "alarm-apache", "title": "alarm-apache", "name": "Apache logları (alarm)", "timeFieldName": "@timestamp" } }
```

### 2. Harita: istekler nereden geliyor?

**Soru: İstekler hangi şehirlerden geliyor?**

`source.geo.location` bir `geo_point` field'ıdır: enlem ve boylam. Kibana Maps bu field'ı haritaya çizer.

1. Menü düğmesi (1), **Analytics** altında **Maps** (2):

![Menü: 1 menü düğmesi, 2 Maps](../../assets/screenshots/LAB-18/02a-menu-maps.png)

2. Sağ üstte **Create map** (1):

![Maps: 1 Create map](../../assets/screenshots/LAB-18/02b-create-map.png)

3. Zaman kutusunda **Last 7 days**'i seçin (1), sonra **Add layer** (2):

![Harita: 1 Last 7 days, 2 Add layer](../../assets/screenshots/LAB-18/02c-add-layer.png)

4. Katman türleri listelenir. **Clusters** (1) yakın noktaları sayıyla gruplar; **Documents** her document'i ayrı
   nokta çizer. **Clusters**'a tıklayın:

![Katman türü: 1 Clusters, 2 Add layer paneli](../../assets/screenshots/LAB-18/02d-katman-turu.png)

5. **Data view** kutusuna (1) `alarm` yazıp **Apache logları (alarm)**'ı seçin; **Cluster field** kendiliğinden
   `source.geo.location` olur. **Add and close** (2):

![Katman ayarı: 1 data view, 2 Add and close](../../assets/screenshots/LAB-18/02f-add-and-close.png)

6. Cluster'lar şehirlerde toplanır; daire içindeki sayı o bölgedeki istek sayısıdır (2). Katman listesinde (1) yeni
   katman ve renk ölçeği görünür:

![Harita: 1 katman listesi, 2 cluster'lar](../../assets/screenshots/LAB-18/02g-harita.png)

7. Sağ üstte **Save**: **Title** (1) `Ziyaretçi haritası`, **Add to dashboard** altında **None** (2), **Save and add to
   library** (3). Harita Library'ye kaydedilir; Adım 6'da panoya ekleyeceğiz:

![Harita kaydetme: 1 Title, 2 None, 3 Save and add to library](../../assets/screenshots/LAB-18/02h-harita-kaydet.png)

Aynı soru sorguyla: İstanbul merkezine 500 km içinde kaç istek var, bunların kaçı şehrin kendisinden (50 km)?

```http
GET alarm-apache/_search?size=0&filter_path=hits.total.value,aggregations.halka.buckets.key,aggregations.halka.buckets.doc_count
{
  "track_total_hits": true,
  "query": { "geo_distance": { "distance": "500km", "source.geo.location": { "lat": 41.01, "lon": 28.98 } } },
  "aggs": { "halka": { "geo_distance": { "field": "source.geo.location", "origin": { "lat": 41.01, "lon": 28.98 }, "unit": "km",
    "ranges": [ { "to": 50 }, { "from": 50, "to": 500 } ] } } }
}
```

```json
{"hits":{"total":{"value":3220}},"aggregations":{"halka":{"buckets":[{"key":"*-50.0","doc_count":1866},{"key":"50.0-500.0","doc_count":1354}]}}}
```

`geo_distance` sorgusu bir daireye düşen document'leri bulur; `geo_distance` aggregation'ı onları merkeze
uzaklığa göre halkalara ayırır. 50-500 km halkası Ankara ve İzmir'dir.

### 3. Connector: alarm nereye yazılsın?

**Soru: Alarm açılınca kayıt nereye düşsün?**

Alarm geçmişini tutacak Index connector'ı kurun. Kibana › Dev Tools'a yapıştırın:

```http
POST kbn:/api/actions/connector/alarm-gecmisi-yaz
{ "name": "alarm-gecmisi-yaz", "connector_type_id": ".index", "config": { "index": "alarm-gecmisi", "refresh": true } }
```

```json
{"id":"alarm-gecmisi-yaz","name":"alarm-gecmisi-yaz","config":{"index":"alarm-gecmisi","refresh":true,"executionTimeField":null},"connector_type_id":".index", ...}
```

<details>
<summary><strong>Dev Tools yerine arayüzden yapmak isterseniz</strong></summary>

**İkisinden birini yapın:** Dev Tools isteğini çalıştırdıysanız connector zaten var, bu kutuyu atlayın.
**Connector ID** mutlaka `alarm-gecmisi-yaz` olmalı: Adım 4'teki kural connector'ı bu kimlikle bulur.

1. Menüden **Management › Stack Management**'ı açın, soldaki listede **Connectors**'a (1) tıklayın:

   ![Stack Management: 1 Connectors](../../assets/screenshots/LAB-18/03a-connectors-menu.png)

2. **Create connector** (1):

   ![Connectors: 1 Create connector](../../assets/screenshots/LAB-18/03b-create-connector.png)

3. Arama kutusuna (1) `Index` yazın, **Index** (2) kartını seçin:

   ![Connector türü: 1 arama, 2 Index](../../assets/screenshots/LAB-18/03c-index-turu.png)

4. **Connector name** (1) `alarm-gecmisi-yaz`, **Connector ID** (2) `alarm-gecmisi-yaz`; **Index** (3) kutusuna
   `alarm-gecmisi` yazıp listeden seçin. **Save** (4):

   ![Index connector: 1 ad, 2 ID, 3 index, 4 Save](../../assets/screenshots/LAB-18/03d-index-connector.png)

Arayüz formunda `refresh` seçeneği yoktur: alarm document'i yaklaşık bir saniye sonra aramaya girer, Adım 5'in
sonucu değişmez.

</details>

### 4. Kural: 5 dakikada 10'dan fazla 5xx

**Soru: Kibana "çok fazla hata var" kararını nasıl verir?**

Kuralı Kibana › Dev Tools'tan kuruyoruz: tek istek her seferinde aynı kuralı kurar ve alanları tek bakışta gösterir.
Arayüzden kurmak isterseniz adımlar bu adımın sonundaki açılır kutudadır:

```http
POST kbn:/api/alerting/rule/alarm-5xx
{
  "name": "Ödeme 5xx patlaması", "rule_type_id": ".es-query", "consumer": "stackAlerts", "schedule": { "interval": "1m" },
  "params": { "searchType": "esQuery", "index": ["alarm-apache"], "timeField": "@timestamp",
    "esQuery": "{\"query\":{\"term\":{\"http.response.status_class\":\"5xx\"}}}",
    "threshold": [10], "thresholdComparator": ">", "timeWindowSize": 5, "timeWindowUnit": "m",
    "size": 0, "aggType": "count", "groupBy": "all", "excludeHitsFromPreviousRun": false },
  "actions": [ { "id": "alarm-gecmisi-yaz", "group": "query matched",
    "params": { "documents": [ { "kural": "{{rule.name}}", "adet": "{{context.value}}", "kosul": "{{context.conditions}}", "zaman": "{{context.date}}" } ] },
    "frequency": { "summary": false, "notify_when": "onActionGroupChange", "throttle": null } } ]
}
```

```json
{"id":"alarm-5xx","enabled":true,"name":"Ödeme 5xx patlaması","tags":[],"rule_type_id":".es-query","consumer":"stackAlerts","schedule":{"interval":"1m"}, ...}
```

- `schedule` ve `timeWindowSize`: her dakika son 5 dakikaya bakılır. Pencere kısalırsa kısa patlamalar
  kaçmaz ama gürültü artar.
- `threshold` / `thresholdComparator`: 10'dan fazla. Normal günde 5 dakikada 5xx sayısı 0-1'dir.
- `notify_when: onActionGroupChange`: alarm açıldığında bir kez yazar; her dakika aynı mesajı tekrarlamaz.
- `{{context.value}}`, `{{context.conditions}}`: kuralın o anki ölçümü. Yanlış yazılan değişken hata
  vermez, boş gelir.

<details>
<summary><strong>Dev Tools yerine arayüzden kurmak isterseniz</strong></summary>

**İkisinden birini yapın:** Dev Tools isteğini çalıştırdıysanız kural zaten var, bu kutuyu atlayın. Arayüz kuralın
kimliğini kendisi üretir; Adım 5'teki kapanma komutu `alarm-5xx` kimliğini kullanır. Arayüzden kurduysanız o komut
yerine kural sayfasındaki **Active now** sayısının 1'den 0'a düşmesini izleyin.

1. Menüden **Management › Stack Management**'ı açın, **Alerts and Insights** altında **Rules**'a (1) tıklayın:

   ![Stack Management: 1 Rules](../../assets/screenshots/LAB-18/04f-rules-menu.png)

2. **Create rule** (1):

   ![Rules: 1 Create rule](../../assets/screenshots/LAB-18/04g-create-rule.png)

3. Arama kutusuna (1) `Elasticsearch query` yazın, **Elasticsearch query** (2) türünü seçin:

   ![Kural türü: 1 arama, 2 Elasticsearch query](../../assets/screenshots/LAB-18/04h-kural-turu.png)

4. Sorgu biçimi olarak **Query DSL** (1):

   ![Sorgu biçimi: 1 Query DSL](../../assets/screenshots/LAB-18/04i-query-dsl.png)

5. **INDEX** ifadesine tıklayın. **Indices to query** (1) kutusuna `alarm-apache` yazıp listeden seçin, **Time
   field** (2) `@timestamp`; pencereyi **X** ile kapatın:

   ![Index penceresi: 1 index, 2 zaman field'ı](../../assets/screenshots/LAB-18/04j-index-zaman.png)

6. Sorgu kutusundaki örneği silip (1) `{"query":{"term":{"http.response.status_class":"5xx"}}}` yazın. **IS ABOVE**
   ifadesine (2) tıklayıp **Is above** ve `10` seçin; **FOR THE LAST** ifadesine (3) tıklayıp `5` **minutes**:

   ![Sorgu ve eşik: 1 sorgu, 2 IS ABOVE 10, 3 son 5 dakika](../../assets/screenshots/LAB-18/04k-sorgu-esik.png)

7. **Rule schedule**'da **Every** (1) `1` **minute**:

   ![Rule schedule: 1 her 1 dakika](../../assets/screenshots/LAB-18/04l-zamanlama.png)

8. **Actions** bölümünde **Add action** (1):

   ![Actions: 1 Add action](../../assets/screenshots/LAB-18/04m-add-action.png)

9. Açılan pencerede **alarm-gecmisi-yaz** (1):

   ![Select connector: 1 alarm-gecmisi-yaz](../../assets/screenshots/LAB-18/04n-connector-sec.png)

10. **Run when** (1) `Query matched`, **Action frequency** (2) `On status changes` kalsın (alarm açıldığında bir kez
    yazar). **Document to index** (3) kutusuna yazın:

    ```json
    {"kural": "{{rule.name}}", "adet": "{{context.value}}", "kosul": "{{context.conditions}}", "zaman": "{{context.date}}"}
    ```

    ![Aksiyon: 1 Run when, 2 Action frequency, 3 document](../../assets/screenshots/LAB-18/04o-aksiyon.png)

11. **Details** altında **Rule name** (1) `Ödeme 5xx patlaması`:

    ![Details: 1 Rule name](../../assets/screenshots/LAB-18/04p-ad.png)

12. Sayfanın altındaki **Create rule** (1):

    ![Kural formu: 1 Create rule](../../assets/screenshots/LAB-18/04q-kaydet.png)

</details>

### 5. Arızayı üretin ve alarmı izleyin

**Soru: Arıza olunca alarm gerçekten açılıyor ve kapanıyor mu?**

Betik ödeme sayfasına son bir dakika içinde 40 tane 500 yazar:

```bash
python3 scripts/veri_uret.py --ariza
timeout 180 bash -c 'until [ "$(curl -s -u elastic:"DevOps2026!" http://127.0.0.1:9200/alarm-gecmisi/_count 2>/dev/null | jq .count 2>/dev/null)" -ge 1 ] 2>/dev/null; do printf .; sleep 5; done'; echo
curl -s -u elastic:'DevOps2026!' 'http://127.0.0.1:9200/alarm-gecmisi/_search?size=1' | jq -c '.hits.hits[0]._source'
```

Beklenen çıktı:

```text
[+] 40 adet 500 olayi yazildi (/odeme, son 1 dakika) -> alarm-apache
.
{"kural":"Ödeme 5xx patlaması","adet":"40","kosul":"Number of matching documents is greater than 10","zaman":"2026-11-21T18:09:42.867Z"}
```

Kural bir sonraki çalışmasında (en çok 1 dakika) eşiği aşan sayıyı gördü ve aksiyon document'i yazdı. Zaman
sizde farklıdır. **Stack Management › Rules › Ödeme 5xx patlaması** sayfasında **Active now** kutusunda 1 görünür (1):

![Kural ayrıntısı: 1 Active now](../../assets/screenshots/LAB-18/05a-kural-aktif.png)

5 dakikalık pencere arızayı geride bırakınca alarm kendiliğinden kapanır:

```bash
timeout 600 bash -c 'until curl -s -u elastic:"DevOps2026!" -H "kbn-xsrf: true" http://127.0.0.1:5601/api/alerting/rule/alarm-5xx | jq -e ".last_run.alerts_count.recovered == 1" >/dev/null; do printf .; sleep 15; done'; echo
curl -s -u elastic:'DevOps2026!' -H 'kbn-xsrf: true' http://127.0.0.1:5601/api/alerting/rule/alarm-5xx | jq -c '.last_run.alerts_count'
```

Beklenen çıktı:

```text
....................
{"new":0,"ignored":0,"recovered":1,"active":0}
```

Ölçülen: arızadan sonra alarm yaklaşık 1 dakikada açıldı, 5 dakikalık pencere geçince 5-6 dakikada kapandı.
`notify_when: onActionGroupChange` olduğu için açılışta bir document yazıldı; her dakika tekrar yazılmadı.

### 6. Rapor: CSV ve PDF

**Soru: Hataların listesini ve panoyu yöneticiye nasıl göndeririz?**

**CSV: Discover sonucunun dosyası.**

1. Menüden **Discover**. Data view **Apache logları (alarm)** (1), zaman **Last 7 days**, arama kutusuna (2) aşağıdaki
   sorguyu yazıp Enter. 99 document gelir (3): geçmişteki 59 hata ve arızanın 40'ı:

```text
http.response.status_class : "5xx"
```

![Discover: 1 data view, 2 sorgu, 3 99 document](../../assets/screenshots/LAB-18/06a-discover-sorgu.png)

2. Sağ üstteki **⋮** düğmesi (1), **Export tab results** (2):

![Discover menüsü: 1 ⋮, 2 Export tab results](../../assets/screenshots/LAB-18/06b-menu-export.png)

3. **CSV** (1) raporu hemen üretir; **Schedule export** (2) aynı raporu belirli aralıkla e-postayla gönderir (e-posta
   connector'ı gerekir). **CSV**'ye tıklayın:

![Export: 1 CSV, 2 Schedule export](../../assets/screenshots/LAB-18/06c-csv.png)

4. Sağdaki panelde **Generate CSV** (1). **Post URL** aynı raporu betikten üretmek içindir:

![Export paneli: 1 Generate CSV](../../assets/screenshots/LAB-18/06d-generate-csv.png)

5. Rapor arka planda hazırlanır. Menü, **Stack Management**, **Alerts and Insights** altında **Reporting** (1):

![Stack Management: 1 Reporting](../../assets/screenshots/LAB-18/06e-reporting-menu.png)

6. Rapor satırı (1) **Done, warnings detected** der; sağdaki indirme simgesiyle indirilir. Uyarının sebebi: sütun adı
   `@timestamp` `@` ile başlar, Excel böyle başlayan hücreyi formül sanabileceği için Kibana raporu işaretler:

![Reporting: 1 CSV raporu](../../assets/screenshots/LAB-18/06f-reporting-csv.png)

**PDF: panonun çıktısı.** Yöneticiye giden rapor genelde panonun PDF'idir (deneme lisansı gerekir; LAB-01'de açıldı).

1. Menüden **Dashboards › Create dashboard**, zaman **Last 7 days**, sağ üstte **Add**. Açılan panelde **From library**
   (1), arama kutusuna (2) `Ziyaretçi` yazıp Enter, **Ziyaretçi haritası** (3); sonra paneli **×** ile kapatın:

![Add paneli: 1 From library, 2 arama, 3 Ziyaretçi haritası](../../assets/screenshots/LAB-18/06g-pano-library.png)

2. Sağ üstte **Save**: **Title** (1) `Alarm panosu`, **Save** (2):

![Pano kaydetme: 1 Title, 2 Save](../../assets/screenshots/LAB-18/06h-pano-kaydet.png)

3. **Exit edit** (1) ile düzenleme modundan çıkın:

![Pano: 1 Exit edit](../../assets/screenshots/LAB-18/06i-exit-edit.png)

4. Sağ üstte **Export** (1), **PDF reports** (2):

![Export menüsü: 1 Export, 2 PDF reports](../../assets/screenshots/LAB-18/06j-export-pdf.png)

5. Sağdaki panelde **Export PDF** (1). **Print format** açılırsa çok sayfalı çıktı üretir:

![PDF paneli: 1 Export PDF](../../assets/screenshots/LAB-18/06k-generate-pdf.png)

6. PDF arka planda bir tarayıcıyla çizilir; bu sunucuda birkaç dakikada hazırlandı. **Stack Management › Reporting**'de
   **Alarm panosu** satırı (1) **Done** olur, türü **PDF**; satır sonundaki menüden **Download report** ile indirilir:

![Reporting: 1 Alarm panosu PDF raporu](../../assets/screenshots/LAB-18/06l-reporting-pdf.png)

<details>
<summary><strong>Slack ve e-posta: hesap, anahtar ve connector</strong></summary>

Alarmı Slack kanalına ya da e-postaya göndermek için iki gizli bilgi gerekir: Slack webhook adresi ve Resend API
anahtarı. İkisi de parola gibidir; bilen herkes sizin adınıza mesaj ya da e-posta gönderir. Repoya, ekran görüntüsüne
ve sohbete yazılmaz; yalnız Kibana'nın connector formuna yapıştırılır.

**Slack: kanal için Incoming Webhook**

1. [api.slack.com/apps](https://api.slack.com/apps) adresinde **Create New App** (1). Açılan pencerede **From scratch**
   altındaki **Pick features** (2), **Continue** (3):

   ![Slack: 1 Create New App, 2 Pick features, 3 Continue](../../assets/screenshots/LAB-18/15a-slack-create-new-app.png)

2. **App name** (1) `Kibana Alarm`, **Workspace** (2) mesajların gideceği çalışma alanı, **Continue** (3):

   ![Slack: 1 App name, 2 Workspace, 3 Continue](../../assets/screenshots/LAB-18/15b-slack-app-adi.png)

3. Scope ve event eklemeyin; webhook izni 6. adımda kendiliğinden eklenir. İki ekranda da **Continue** (1):

   ![Slack: scope eklemeden Continue](../../assets/screenshots/LAB-18/15c-slack-scope-yok.png)

   ![Slack: event eklemeden Continue](../../assets/screenshots/LAB-18/15d-slack-event-yok.png)

4. Özet ekranında **Create** (1):

   ![Slack: 1 Create](../../assets/screenshots/LAB-18/15e-slack-create.png)

5. "Your app can't do anything yet" uyarısı scope olmadığı içindir; **Create Anyway** (1):

   ![Slack: 1 Create Anyway](../../assets/screenshots/LAB-18/15f-slack-create-anyway.png)

6. Uygulamanın sol menüsünde **Incoming Webhooks** (1), **Activate Incoming Webhooks** anahtarını (2) **On** yapın:

   ![Slack: 1 Incoming Webhooks, 2 Activate](../../assets/screenshots/LAB-18/16-slack-incoming-webhooks.png)

7. Sayfanın altında **Add New Webhook** (1):

   ![Slack: 1 Add New Webhook](../../assets/screenshots/LAB-18/17a-slack-add-new-webhook.png)

8. **Channel for webhook** (1) alanında kanalı seçin (örnek: `#devopsatolyesi`) ve **Allow** (2):

   ![Slack: 1 kanal, 2 Allow](../../assets/screenshots/LAB-18/17b-slack-kanal-allow.png)

9. Listeye eklenen adresin yanındaki **Copy** (1) ile adresi alın. Adres `https://hooks.slack.com/services/T…/B…/…`
   biçimindedir:

   ![Slack: 1 Copy; webhook adresi karartıldı](../../assets/screenshots/LAB-18/17c-slack-webhook-copy.png)

**Resend: SMTP için API anahtarı**

1. [resend.com](https://resend.com) adresinde ücretsiz hesap açın. Sol menüde **API keys** (1), **Create API key** (2):

   ![Resend: 1 API keys, 2 Create API key](../../assets/screenshots/LAB-18/18-resend-api-keys.png)

2. **Name** (1) `Kibana Alarm`; **Permission** listesinde **Sending access** (2). E-posta göndermek için yeterlidir;
   Full access anahtar sızarsa hesabın tamamını açar:

   ![Resend: 1 Name, 2 Sending access](../../assets/screenshots/LAB-18/19a-resend-ad-izin.png)

3. İzin **Sending access** (1) görünürken **Add** (2):

   ![Resend: 1 Sending access, 2 Add](../../assets/screenshots/LAB-18/19b-resend-add.png)

4. Anahtar (`re_…`) yalnız bu pencerede bir kez görünür. Kopyalama düğmesiyle (1) alın, güvenli bir yere koyun, sonra
   **Done** (2):

   ![Resend: 1 kopyala, 2 Done; anahtar karartıldı](../../assets/screenshots/LAB-18/19c-resend-anahtar-kopyala.png)

Doğrulanmış bir alan adınız yoksa Resend yalnız hesabınızın e-posta adresine gönderir ve gönderen
`onboarding@resend.dev` olur; deneme için yeterlidir.

**Kibana: iki connector**

1. **Stack Management › Connectors**'ta **Create connector** (1):

   ![Connectors: 1 Create connector](../../assets/screenshots/LAB-18/12-connectors-list.png)

2. Arama kutusuna `Slack` yazın ve **Slack** kartını (2) seçin. Slack (v2) değil; webhook ile çalışan sürüm budur:

   ![Connector türü: 2 Slack](../../assets/screenshots/LAB-18/13a-connector-select-slack.png)

3. **Webhook** sekmesinde **Connector name** (3) `alarm-slack`, **Webhook URL** (4) Slack'ten kopyaladığınız
   adres, **Save** (5):

   ![Slack connector: 3 Connector name, 4 Webhook URL, 5 Save](../../assets/screenshots/LAB-18/13-connector-create-slack.png)

4. Yeniden **Create connector**; arama kutusuna `Email` yazın ve **Email** kartını (1) seçin:

   ![Connector türü: 1 Email](../../assets/screenshots/LAB-18/14a-connector-select-email.png)

5. Formu doldurun ve **Save** (8):

   ![Email connector: 2 ad, 3 Sender, 4 Service, 5 Host ve Port, 6 Secure kapalı, 7 Username ve Password, 8 Save](../../assets/screenshots/LAB-18/14-connector-email-resend.png)

   | No | Alan | Değer |
   |---|---|---|
   | 2 | Connector name | `alarm-eposta` |
   | 3 | Sender | `onboarding@resend.dev` |
   | 4 | Service | `Other` |
   | 5 | Host / Port | `smtp.resend.com` / `587` |
   | 6 | Secure | **kapalı** bırakın |
   | 7 | Username / Password | `resend` / Resend API anahtarı |

   **Secure neden kapalı?** Bağlantı yine şifrelidir. Port 587'de Kibana önce normal bağlanır, sunucu izin verince
   bağlantıyı TLS'e yükseltir (STARTTLS). **Secure** anahtarı ise "baştan TLS ile bağlan" demektir ve yalnız port
   465 içindir. 587'de Secure'ü açarsanız bağlantı kurulamaz, test e-postası gitmez. Kural kısaca:
   587 → Secure kapalı, 465 → Secure açık.

6. Kaydedince açılan **Test** sekmesinde: Slack'te bir mesaj yazıp **Run**, mesaj kanala düşer; Email'de **To**
   alanına Resend hesabınızın e-posta adresini yazıp **Run**.

Kurala ikinci bir action olarak eklenir; mesajda aynı değişkenler kullanılır
(`{{rule.name}}`, `{{context.value}}`, `{{context.link}}`). Linklerin dolu gelmesi için Kibana'da
`server.publicBaseUrl` tanımlı olmalıdır; yoksa `{{context.link}}` boş gelir.

</details>

---

## Temizlik

Yalnız bu labın kuralını (arayüzden kurulduysa adıyla bulunur), connector'larını (`alarm-gecmisi-yaz`; kurduysanız
`alarm-slack` ve `alarm-eposta`), `alarm-apache` ve `alarm-gecmisi` index'lerini, şablonunu, data view'ını, haritasını
ve panosunu siler; ana cluster'a dokunmaz. Reporting listesindeki rapor Kibana'nın kendi kaydıdır
ve kalır:

```bash
./teardown.sh
```

Beklenen çıktı:

```text
kural alarm-5xx -> 204
connector alarm-gecmisi-yaz -> 204
Kibana nesneleri -> 2 silindi
data view alarm-apache -> 200
index'ler -> 200
sablon alarm-apache -> 200
sablon alarm-gecmisi -> 200
```

`2`, Adım 2'deki harita ve Adım 6'daki `Alarm panosu`'dur; yapmadığınız adımın nesnesi sayılmaz.

Labı aynı sunucuda yeniden yapacaksanız başlamadan önce `./teardown.sh` çalıştırın; README'deki sayılar temiz
başlangıca göredir.

---

Sonraki lab: **[LAB-19 — 3-Node TLS Cluster: Shard, Replica, Node Kaybı ve Yük Dengeleme](../LAB-19-3-node-tls-cluster/README.md)**
