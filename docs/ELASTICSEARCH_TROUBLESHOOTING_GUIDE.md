# Elasticsearch Troubleshooting & Administration Guide

Bu kılavuz, Elasticsearch yöneticileri ve DevOps mühendisleri için cluster, node, index ve shard seviyesinde izleme, sorun giderme ve kurtarma operasyonlarında kullanılan en kritik **40 temel komutu** ve **5 altın kuralı** içerir. 

Tüm komutlar Kibana **Dev Tools ➔ Console** ekranına doğrudan kopyala-yapıştır yapılabilecek biçimde düzenlenmiştir.

---

## 📑 İçindekiler
1. [Cluster Genel Bakış ve Sağlık Kontrolleri (1–5)](#1-cluster-genel-bakış-ve-sağlık-kontrolleri)
2. [Node Yönetimi ve Kaynak İzleme (6–9)](#2-node-yönetimi-ve-kaynak-izleme)
3. [Index Yönetimi ve Bakım (10–15)](#3-index-yönetimi-ve-bakım)
4. [Shard Allocation ve Sorun Giderme (16–18)](#4-shard-allocation-ve-sorun-giderme)
5. [Loglama ve Yavaş Sorgular (Slow Logs) (19–20)](#5-loglama-ve-yavaş-sorgular-slow-logs)
6. [Snapshot ve Restore Operasyonları (21–23)](#6-snapshot-ve-restore-operasyonları)
7. [Cluster Ayarları ve Dinamik Yapılandırma (24–25)](#7-cluster-ayarları-ve-dinamik-yapılandırma)
8. [Görevler ve Bekleyen İşlemler (Tasks) (26–27)](#8-görevler-ve-bekleyen-işlemler-tasks)
9. [Güvenlik ve Kullanıcı Yönetimi (28–30)](#9-güvenlik-ve-kullanıcı-yönetimi)
10. [Sık Kullanılan Sorun Giderme Komutları (31–35)](#10-sık-kullanılan-sorun-giderme-komutları)
11. [Faydalı _cat API Komutları (36–40)](#11-faydalı-_cat-api-komutları)
12. [Yöneticiler İçin Altın İpuçları (Admin Tips)](#12-yöneticiler-için-altın-İpuçları-admin-tips)

---

## 1. Cluster Genel Bakış ve Sağlık Kontrolleri

### 1. Check cluster health
Cluster'ın genel sağlık durumunu (`green`, `yellow`, `red`), aktif shard sayılarını ve initialize/unassigned durumdaki shard'ları görüntüler.
```http
GET /_cluster/health
```

### 2. Cluster health per index
Hangi index'in `yellow` veya `red` durumda olduğunu index bazında ayrıntılı listeler.
```http
GET /_cluster/health?level=indices
```

### 3. Cluster statistics
Cluster genelindeki node sayısı, toplam shard adedi, disk kullanım oranları, bellek ve CPU istatistiklerini özetler.
```http
GET /_cluster/stats
```

### 4. View cluster settings
Cluster üzerinde geçerli olan dinamik ayarları (`persistent` ve `transient`) listeler. `include_defaults=true` ile sistem varsayılanları da dahil edilir.
```http
GET /_cluster/settings
GET /_cluster/settings?include_defaults=true
```

### 5. Cluster state
Cluster'ın routing tabloları, metadata, master node seçimi ve blokajlar dahil tüm durumunu döndürür.
```http
GET /_cluster/state
```

---

## 2. Node Yönetimi ve Kaynak İzleme

### 6. List all nodes
Cluster içerisindeki tüm node'ları rolleri (`master`, `data`, `ingest` vb.), IP adresleri ve temel bilgileriyle listeler.
```http
GET /_nodes
```

### 7. Node statistics
Node bazında CPU kullanımı, JVM heap bellek tüketimi, disk I/O ve thread pool durumlarının detaylı istatistiklerini verir.
```http
GET /_nodes/stats
```

### 8. Hot threads
Node'larda yüksek CPU tüketen, kilitlenen veya performans darboğazına yol açan Java iş parçacıklarını (thread stack trace) anlık olarak yakalar.
```http
GET /_nodes/hot_threads
```

### 9. Node allocation settings
Shard'ların node'lara dağıtılmasını etkileyen tahsis (allocation) filtrelerini ve eşik ayarlarını görüntüler.
```http
GET /_cluster/settings?filter_path=*.*allocation*
```

---

## 3. Index Yönetimi ve Bakım

### 10. List all indices
Tüm index'leri sağlık durumu (`green/yellow/red`), açık/kapalı durumu, doküman sayısı ve disk boyutuyla tablo halinde listeler.
```http
GET /_cat/indices?v
```

### 11. Index settings
Belirli bir index'in shard sayısı (`number_of_shards`), replica sayısı (`number_of_replicas`), refresh interval ve analiz ayarlarını görüntüler.
```http
GET /my_index/_settings
```

### 12. Index mappings
Belirli bir index'in alan tiplerini (`keyword`, `text`, `integer`, `geo_point` vb.) listeler.
```http
GET /my_index/_mapping
```

### 13. Force merge
Index segmentlerini optimize etmek, silinmiş dokümanların kapladığı alanı temizlemek ve arama performansını artırmak için segmentleri birleştirir.
```http
POST /my_index/_forcemerge?max_num_segments=1
```

### 14. Close and open index
Bir index'i bakım veya bellek tasarrufu amacıyla geçici olarak kapatır ya da yeniden okuma/yazmaya açar.
```http
POST /my_index/_close
POST /my_index/_open
```

### 15. Delete an index
Bir index'i ve barındırdığı tüm verileri fiziksel olarak kalıcı biçimde siler.
```http
DELETE /my_index
```

---

## 4. Shard Allocation ve Sorun Giderme

### 16. View shard allocation
Shard'ların hangi node üzerinde çalıştığını, durumunu (`STARTED`, `INITIALIZING`, `RELOCATING`, `UNASSIGNED`) ve primary/replica rolünü listeler.
```http
GET /_cat/shards?v
```

### 17. Explain unassigned shards
Bir shard'ın neden atanmadığını (unassigned kaldığını), disk sınırına mı takıldığını, replica kuralına mı takıldığını kesin olarak açıklar.
```http
POST /_cluster/allocation/explain
```
*Detaylı açıklama için gövde ile çalıştırma örneği:*
```http
POST /_cluster/allocation/explain
{
  "index": "my_index",
  "shard": 0,
  "primary": true
}
```

### 18. Manually reroute shards
Atanmamış bir shard'ı manuel olarak belirli bir node'a tahsis eder veya bir node'dan diğerine taşır.
```http
POST /_cluster/reroute
{
  "commands": [
    {
      "move": {
        "index": "my_index",
        "shard": 0,
        "from_node": "node-1",
        "to_node": "node-2"
      }
    }
  ]
}
```

---

## 5. Loglama ve Yavaş Sorgular (Slow Logs)

### 19. View slow query logs
Index seviyesinde yavaş sorgu loglama yapılandırmasını kontrol eder.
```http
GET /my_index/_settings?filter_path=*.search.slowlog*
```

### 20. Configure slow logs
Arama ve veri çekme işlemlerinde belirlenen süreyi aşan sorguların log dosyasına yazılması için eşik değerlerini belirler.
```http
PUT /my_index/_settings
{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.fetch.warn": "1s"
}
```

---

## 6. Snapshot ve Restore Operasyonları

### 21. List snapshot repositories
Yapılandırılmış tüm yedekleme depolarını (S3, MinIO, Shared File System) listeler.
```http
GET /_snapshot
```

### 22. Create a snapshot
Belirli index'leri veya tüm cluster'ı hedef depoya yedekler (`wait_for_completion=true` yedek bitene kadar bekler).
```http
PUT /_snapshot/my_backup/snapshot_1?wait_for_completion=true
{
  "indices": "my_index,logs-*",
  "ignore_unavailable": true,
  "include_global_state": false
}
```

### 23. Restore a snapshot
Alınmış bir yedeği cluster içerisine geri yükler.
```http
POST /_snapshot/my_backup/snapshot_1/_restore
{
  "indices": "my_index",
  "ignore_unavailable": true,
  "include_global_state": false
}
```

---

## 7. Cluster Ayarları ve Dinamik Yapılandırma

### 24. View cluster settings
Cluster üzerinde etkin olan transient ve persistent ayarları listeler.
```http
GET /_cluster/settings
```

### 25. Update cluster settings
Cluster seviyesinde shard dağıtımını etkinleştirir veya sınırlar.
```http
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}
```

---

## 8. Görevler ve Bekleyen İşlemler (Tasks)

### 26. List running tasks
Arka planda devam eden uzun süreli sorguları, reindex, snapshot veya update-by-query işlemlerini listeler.
```http
GET /_tasks?detailed=true&actions=*search
```

### 27. Cancel a task
Kilitlenen, cluster kaynaklarını tüketen veya iptal edilmesi gereken problemli bir görevi sonlandırır.
```http
POST /_tasks/<TASK_ID>/_cancel
```

---

## 9. Güvenlik ve Kullanıcı Yönetimi

### 28. List users
Cluster üzerinde tanımlı tüm yerel kullanıcıları ve bağlı rollerini listeler.
```http
GET /_security/user
```

### 29. List roles
Tanımlı güvenlik rollerini ve sahip oldukları index/cluster izinlerini listeler.
```http
GET /_security/role
```

### 30. Role mappings
LDAP, Active Directory veya SAML kullanıcı/gruplarının hangi Elasticsearch rollerine eşlendiğini kontrol eder.
```http
GET /_security/role_mapping
```

---

## 10. Sık Kullanılan Sorun Giderme Komutları

### 31. Check unassigned shards
Atanamayan shard'ları ve neden atanamadıklarının (`unassigned.reason`) gerekçesini listeler.
```http
GET /_cat/shards?h=index,shard,prirep,state,unassigned.reason
```

### 32. Disk usage per node
Node'ların disk doluluk oranlarını ve kalan boş alanlarını gösterir (High/Flood watermark tespitinde kritiktir).
```http
GET /_cat/allocation?v
```

### 33. Largest indices by storage
En çok disk alanı tüketen index'leri büyükten küçüğe sıralar.
```http
GET /_cat/indices?v&s=store.size:desc
```

### 34. Thread pool stats
Thread pool'lardaki aktif, kuyrukta bekleyen (`queue`) ve reddedilen (`rejected`) iş parçacığı sayılarını gösterir.
```http
GET /_cat/thread_pool?v
```

### 35. JVM heap usage
Node'ların JVM heap bellek tüketim yüzdelerini listeler (Out of Memory ve GC baskısını teşhis eder).
```http
GET /_nodes/stats/jvm?filter_path=nodes.*.jvm.mem.pools.old.used_in_bytes,nodes.*.jvm.mem.heap_used_percent
```

---

## 11. Faydalı _cat API Komutları

### 36. Node info summary
Node'ların bellek, CPU, load ve rollerini tek satırda özetler.
```http
GET /_cat/nodes?v&h=name,heapPercent,ramPercent,cpu,load_1m,nodeRole
```

### 37. Indices summary
Index'lerin sağlık, durum, doküman adedi ve boyutunu özetler.
```http
GET /_cat/indices?v&h=index,health,status,pri,rep,docs.count,store.size
```

### 38. Shards overview
Shard'ların primary/replica durumunu, doküman adedini ve bağlı olduğu node'u listeler.
```http
GET /_cat/shards?v&h=index,shard,prirep,state,docs,store,node
```

### 39. Allocation & disk usage
Node başına shard adedini, indexlerin kapladığı disk alanını ve toplam boş alanı listeler.
```http
GET /_cat/allocation?v&h=shards,disk.indices,disk.used,disk.avail,disk.total,node
```

### 40. Pending tasks
Master node kuyruğunda bekleyen cluster görevlerini listeler.
```http
GET /_cat/pending_tasks?v
```

---

## 12. Yöneticiler İçin Altın İpuçları (Admin Tips)

1. **Ağır Operasyonlardan Önce Cluster Sağlığını Kontrol Edin:**
   Büyük reindex, snapshot veya mapping güncellemelerine başlamadan önce `GET /_cluster/health` komutuyla durumun `green` olduğunu ve bekleyen görev bulunmadığını teyit edin.

2. **Hızlı Teşhis İçin Her Zaman `_cat` API'lerini Tercih Edin:**
   İnsan tarafından okunabilir, sütun bazlı filtrelenebilen (`?h=...`) ve sıralanabilen (`?s=...`) `_cat` komutları terminal veya Dev Tools'ta en hızlı yanıtı sunar.

3. **Yavaş Sorguları Erken Tespit Etmek İçin Slow Log Tanımlayın:**
   Performans şikayetleri başladığında önce index seviyesinde slow log eşiklerini (warn: 10s, fetch: 1s) ayarlayın ve log dosyasını izleyin.

4. **JVM Heap ve Disk Kullanımını Düzenli İzleyin:**
   Node heap kullanımı düzenli olarak %75'in üzerine çıkıyorsa GC darboğazı, disk kullanımı %85'i aşarsa watermark kilitlenmesi kapıdadır.

5. **Atanamayan Shard Sorunlarında `allocation/explain` Çiftini Kullanın:**
   `POST /_cluster/allocation/explain` komutunu çalıştırmadan rastgele shard taşımaya veya reroute yapmaya çalışmayın; komut size hatanın tam nedenini doğrudan söyleyecektir.
