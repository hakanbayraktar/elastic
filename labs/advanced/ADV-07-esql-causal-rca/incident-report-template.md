# Olay İnceleme ve Kök Neden Analizi Raporu (Şablon)

## 1. Olay Özeti (Executive Summary)
* **Olay Başlığı:** E-ticaret Ödeme ve Sipariş Akışında Zincirleme 5xx Arızası
* **Tarih & Saat Aralığı:** [Başlangıç Zamanı] - [Bitiş Zamanı]
* **Etkilenen Ortam:** Production (`deployment.environment: production`)
* **Önem Derecesi:** P1 (Kritik Gelir Kaybı)

---

## 2. Belirtiler ve İlk Gözlem (Symptom Analysis)
* Kullanıcılar `storefront` üzerinden sipariş tamamlarken HTTP 500 hataları aldı.
* Discover panosunda `storefront`, `checkout-service`, `payment-service` ve `ledger-service` servislerinin hepsinde eşzamanlı binlerce ERROR kaydı oluştu.

---

## 3. ES|QL Kanıt Zinciri (Forensic Evidence Chain)

### Adım A: Kaskad Etkisinin Tespiti
* **Sorgu:**
  ```sql
  FROM logs-incident.otel-prod
  | WHERE log.level == "ERROR"
  | STATS failed_services = COUNT_DISTINCT(service.name) BY trace.id
  | STATS total_traces = COUNT(*) BY failed_services
  ```
* **Bulgu:** Hataların %100'ünde aynı `trace.id` altında 4 servisin birden arızalandığı tespit edildi. Bu durum problemin bağımsız değil, zincirleme bir kaskad arıza olduğunu kanıtlar.

### Adım B: İlk Çöken Servisin İzolasyonu (`origin_service`)
* **Sorgu:**
  ```sql
  FROM logs-incident.otel-prod
  | WHERE log.level == "ERROR"
  | EVAL marker = CONCAT(DATE_FORMAT("yyyy-MM-dd HH:mm:ss.SSS", @timestamp), "|", service.name)
  | STATS origin_marker = MIN(marker), services = COUNT_DISTINCT(service.name) BY trace.id
  | WHERE services > 1
  | EVAL origin_service = SUBSTRING(origin_marker, 25)
  | STATS cascade_traces = COUNT(*) BY origin_service
  ```
* **Bulgu:** Tüm kaskad izlerinde (`cascade_traces`) zaman damgası en erken olan ve ilk çöken servisin istisnasız **`ledger-service`** olduğu kanıtlandı.

### Adım C: Nedensellik Çizgisi (Causal Graph)
* `storefront` -> `checkout-service` -> `payment-service` -> **`ledger-service` (KÖK)**

---

## 4. Kök Neden (Root Cause)
* **Teşhis:** `ledger-service` veritabanı bağlantı havuzu (`HikariPool-1`) 50 bağlantının tamamını tüketmiş (`db.connection_pool.available: 0`). 
* Yeni gelen istekler 3000ms zaman aşımına uğramış (`db_connection_pool_exhausted`) ve geriye doğru tüm servis zincirini kilitlemiştir.

---

## 5. Düzeltici ve Önleyici Faaliyetler (CAPA)
1. **Acil Aksiyon:** `ledger-service` podları restart edildi ve DB connection pool boyutu 50'den 150'ye çıkarıldı.
2. **Kısa Vadeli Aksiyon:** `payment-service` ve `checkout-service` arasına devre kesici (Circuit Breaker) ve exponential backoff timeout politikası konulması.
3. **İzleme & Uyarı (SLO/Alert):** `db.connection_pool.available < 5` olduğunda tetiklenen erken uyarı kuralı yazıldı.
