# Flashcard 09: Veri Toplama, Ingestion, Logstash ve Beats

---

### Soru 1: Beats, Logstash ve Ingest Node arasındaki görev paylaşımı nasıldır?
**Cevap:**
* **Beats (Filebeat, Metricbeat vb.):**
  * Uç noktalarda (sunucu, pod, container) çalışan, kaynak tüketimi çok düşük (Go tabanlı) hafif veri toplayıcı ajanlardır. Görevleri log/metrik dosyasını okuyup güvenle iletmektir.
* **Logstash:**
  * Ağır dönüşümler, yüzlerce farklı giriş/çıkış eklentisi (Kafka, S3, JDBC, Syslog), bellek içi kuyruk (persistent queue) ve gelişmiş DLQ gerektiren merkezi veri işleme hattıdır.
* **Elasticsearch Ingest Node / Ingest Pipelines:**
  * Logstash kurmaya gerek kalmadan, doğrudan Elasticsearch içerisinde hafif dönüşümler (Grok, GeoIP, Date, Maskeleme, CRM zenginleştirme) yapan yerleşik işlemcidir.

---

### Soru 2: Elastic Common Schema (ECS) standardı neden kritiktir?
**Cevap:**
* Farklı kaynaklardan gelen loglardaki alan adlarını standartlaştırır.
  * *Örnek:* Bir sunucuda `ip_address`, diğerinde `src_ip`, diğerinde `client_ip` demek yerine hepsi `source.ip` olur.
* **Faydası:** Tek bir Kibana dashboard'u veya alerting kuralı, logun Apache, Nginx, Kubernetes veya Firewall'dan gelmesine bakılmaksızın tüm altyapıda sorunsuz çalışır.

---

### Soru 3: Dead Letter Queue (DLQ) nedir ve neden kullanılır?
**Cevap:**
* **Sorun:** Logstash Elasticsearch'e 1.000 adet log gönderdiğinde, 1 adet belgede tip uyumsuzluğu (örn: `status` alanı sayı beklenirken metin gelmesi) varsa Elasticsearch bu belgeyi `400 Mapping Exception` ile reddeder.
* **Çözüm (DLQ):** Logstash bu hatalı belgeyi çöpe atmaz veya tüm boru hattını durdurmaz; yerel diskteki DLQ dosyasına yazar. Diğer 999 belge indexlenir.
* Mühendisler DLQ'daki hatalı belgeleri inceleyip mapping'i düzelttikten sonra tekrar sisteme besleyebilir.

---

### Soru 4: Dissect Filter ile Grok Filter arasındaki fark ve performans etkisi nedir?
**Cevap:**
* **Grok Filter:** Düzenli ifadeler (Regex) kullanır. Çok esnektir ancak CPU tüketimi yüksektir.
* **Dissect Filter:** Regex kullanmaz; sabit ayraçlara (delimiter: boşluk, virgül, köşeli parantez) göre doğrudan metin dilimleme yapar.
* **Performans:** Dissect, Grok'a göre **3 ila 5 kat daha az CPU tüketir** ve çok daha hızlıdır. Log formatı katı ve öngörülebilirse daima Dissect tercih edilmelidir.
