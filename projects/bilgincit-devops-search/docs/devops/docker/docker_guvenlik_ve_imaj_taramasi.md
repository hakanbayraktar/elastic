# Docker Güvenlik ve İmaj Taraması Rehberi

Üretim ortamlarında konteyner güvenliği ve güvenlik açığı (vulnerability) tespit adımları.

## 1. Trivy ile Docker İmaj Taraması
Aqua Security Trivy, konteyner imajlarındaki CVE açıklarını tespit eder:

```bash
trivy image --severity HIGH,CRITICAL my-app:v1.0.0
```

## 2. Dockerfile Güvenlik Kontrol Listesi
- **Rootless:** `USER nonroot:nonroot` tanımlayın.
- **Minimal Base Image:** `ubuntu` yerine `alpine` veya `distroless` tercih edin.
- **Read-only Filesystem:** Konteyneri salt-okunur dosya sistemiyle çalıştırın:
  ```bash
  docker run --read-only --tmpfs /tmp my-secure-app
  ```
- **Gizli Bilgi (Secrets):** API anahtarları asla Dockerfile içine gömülmemelidir (`BuildKit secret mount` kullanın).
