# Docker Best Practices ve Konteyner Optimizasyonu

Modern bulut ve mikroservis mimarilerinde güvenli, hafif ve hızlı Docker imajları oluşturma kılavuzu.

## 1. Multi-Stage Build Kullanımı
Uygulama derleme araçlarını nihai imajda tutmamak için çok aşamalı (multi-stage) derleme zorunludur:

```dockerfile
# Aşama 1: Derleyici (Builder)
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server .

# Aşama 2: Üretim (Runtime)
FROM alpine:3.19
RUN adduser -D -u 10001 appuser
WORKDIR /app
COPY --from=builder /app/server /app/server
USER appuser
EXPOSE 8080
ENTRYPOINT ["/app/server"]
```

## 2. Docker Daemon ve Konteyner Yönetim Komutları
Günlük operasyonlarda sık kullanılan Docker komutları:

```bash
docker run -d --name app-container -p 8080:8080 --restart unless-stopped my-app:latest
docker logs -f --tail 100 app-container
docker system prune -af --volumes
```

## 3. Güvenlik Tavsiyeleri
- Asla `root` kullanıcısı ile konteyner çalıştırmayın (`USER appuser`).
- Sabit etiketler (`v1.2.0`) kullanın, asla `latest` etiketine güvenmeyin.
- `.dockerignore` dosyası oluşturarak gizli dosyaları (`.env`, `.git`) imaja dahil etmeyin.
