# Prometheus ve Grafana ile Gözlemlenebilirlik (Observability)

Sistemlerin metrik, log ve trace ekseninde izlenmesi ve alarm (alerting) kuralları.

## 1. Prometheus Scraping Mimarisi
Prometheus "pull-based" bir mimariye sahiptir. Hedef sunuculardaki `/metrics` endpoint'lerini periyodik olarak sorgular.

```yaml
# prometheus.yml örnek yapılandırması
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "elasticsearch_exporter"
    static_configs:
      - targets: ["elasticsearch-exporter:9114"]

  - job_name: "node_exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
```

## 2. PromQL Temel Sorguları
- `rate(node_cpu_seconds_total{mode="idle"}[5m])`: 5 dakikalık boşta CPU oranı.
- `100 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100)`: Bellek kullanım yüzdesi.

```bash
# Alertmanager alarm durumu testi
curl -X GET "http://localhost:9093/api/v2/alerts"
```
