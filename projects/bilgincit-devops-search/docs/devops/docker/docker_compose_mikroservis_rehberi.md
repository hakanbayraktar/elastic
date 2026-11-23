# Docker Compose ile Mikroservis Mimarisi Yönetimi

Docker Compose, çoklu konteyner uygulamalarını tanımlamak ve tek komutla çalıştırmak için kullanılan YAML tabanlı bir orkestrasyon aracıdır.

## 1. Temel Yapılandırma
Bir mikroservis mimarisinde API, Veritabanı ve Önbellek servislerinin birbirine bağlanması:

```yaml
version: '3.8'

services:
  web-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=postgres-db
      - REDIS_HOST=redis-cache
    depends_on:
      - postgres-db
      - redis-cache
    networks:
      - app-network

  postgres-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_PASSWORD: secretpassword
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis-cache:
    image: redis:7-alpine
    networks:
      - app-network

volumes:
  db_data:

networks:
  app-network:
    driver: bridge
```

## 2. Docker Compose Yönetim Komutları
- `docker compose up -d`: Arka planda servisleri başlatır.
- `docker compose down -v`: Servisleri ve bağlı volume'ları temizler.
- `docker compose logs -f web-api`: Servis loglarını canlı takip eder.
