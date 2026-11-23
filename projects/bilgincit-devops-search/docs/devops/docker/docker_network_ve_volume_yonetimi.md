# Docker Network ve Volume Yönetimi

Konteynerler arası güvenli iletişim ve kalıcı veri depolama stratejileri.

## 1. Docker Network Sürücüleri
- **bridge:** Tek bir Docker hostu üzerindeki konteynerler için varsayılan izole ağ.
- **host:** Konteynerin ağ izolasyonunu kaldırır, doğrudan sunucunun ağ kartını kullanır.
- **overlay:** Docker Swarm veya çoklu sunucu kümelerinde konteynerler arası iletişimi sağlar.
- **none:** Tüm ağ bağlantısını devre dışı bırakır (güvenlik ve batch işlemler için).

```bash
# Özel bir bridge ağ oluşturma
docker network create --driver bridge --subnet 172.28.0.0/16 app-net
```

## 2. Docker Volume ve Veri Güvenliği
Konteyner silinse dahi verinin kaybolmaması için Docker Volume veya Bind Mount kullanılır.

```bash
docker volume create pg_data
docker run -d --name db -v pg_data:/var/lib/postgresql/data postgres:16
```
