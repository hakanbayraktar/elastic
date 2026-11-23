# Elasticsearch 9.x Python Otomasyonu ve İstemci Kılavuzu

Bu eklenti dizini, Elasticsearch 9.5.5 cluster'ı üzerinde Python ile programatik olarak yönetim, CRUD operasyonları, Query DSL aramaları, aggregations ve SQL sorguları çalıştırmak isteyen mühendisler için hazırlanmıştır.

---

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Yükleyin

```bash
cd scripts/python-automation
pip install -r requirements.txt
```

### 2. Bağlantı Bilgilerini Yapılandırın (Opsiyonel)

Varsayılan olarak `http://localhost:9200` adresine `elastic:DevOps2026!` kimlik bilgileriyle bağlanır. Farklı bir host veya port kullanıyorsanız ortam değişkenlerini ayarlayabilirsiniz:

```bash
export ELASTIC_URL="http://127.0.0.1:9200"
export ELASTIC_USER="elastic"
export ELASTIC_PASSWORD="DevOps2026!"
```

### 3. Scriptleri Çalıştırın

1. **Bağlantı ve CRUD Testi:**
   ```bash
   python3 01_verify_cluster_and_crud.py
   ```
   *Cluster sağlığını denetler, `training-python-crud` index'ini oluşturur, belge ekler, OCC ile güvenli güncelleme yapar ve bulk veri basar.*

2. **Arama, Analitik ve SQL Sorgulama:**
   ```bash
   python3 02_search_and_aggregations.py
   ```
   *Query DSL `bool` araması yapar, `terms` ve `avg` aggregasyonları çalıştırır ve doğrudan Elasticsearch SQL API'sine sorgu gönderir.*

3. **Matplotlib ile Görsel Analitik ve Raporlama (Offline Grafikler):**
   ```bash
   python3 03_aggregations_matplotlib_export.py
   ```
   *Kategori bazında ciro ve sipariş aggregations sonuçlarını çekip yüksek çözünürlüklü Bar ve Donut grafikleri (`ecommerce_category_analytics.png`) üretir. Kibana arayüzü olmadan programatik analitik raporlama sağlar.*
