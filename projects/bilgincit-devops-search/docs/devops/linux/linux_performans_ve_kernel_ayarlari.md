# Linux Sunucu Performansı ve Kernel Ayarları Rehberi

Yüksek trafikli Elasticsearch, veritabanı ve web sunucuları için önerilen Linux çekirdek (kernel) optimizasyonları.

## 1. Bellek ve Virtual Memory Ayarları
Elasticsearch gibi yoğun memory map kullanan sistemlerde `vm.max_map_count` değeri en az 262144 olmalıdır.

```bash
# Geçici olarak ayarlama
sudo sysctl -w vm.max_map_count=262144
sudo sysctl -w vm.swappiness=1

# Kalıcı hale getirmek için /etc/sysctl.conf dosyasına ekleyin
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
echo "vm.swappiness=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 2. File Descriptor Limitleri (limits.conf)
Sistemde açık dosya limitlerinin (ulimit) yetersiz olması `Too many open files` hatasına yol açar.

```ini
# /etc/security/limits.conf içine ekleyin:
* soft nofile 65536
* hard nofile 65536
* soft memlock unlimited
* hard memlock unlimited
```

## 3. Sistem İzleme Komutları
- `htop`: CPU ve bellek kullanımını gerçek zamanlı izleme.
- `vmstat 1`: CPU, bellek ve disk I/O bekleme (wait) değerleri.
- `iostat -xz 1`: Disk yoğunluğu ve kuyruk süreleri.
