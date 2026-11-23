# Kubernetes Helm Paket Yöneticisi ve Chart Geliştirme

Helm, Kubernetes uygulamalarını paketlemek, yapılandırmak ve dağıtmak için kullanılan resmi paket yöneticisidir.

## 1. Temel Helm Komutları
- `helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx`: Repo ekleme.
- `helm install my-release ingress-nginx/ingress-nginx -f values.yaml`: Kurulum yapma.
- `helm upgrade --install my-app ./chart -n production`: Güncelleme veya kurulum.
- `helm rollback my-app 1`: Önceki sürüme geri dönüş.

## 2. values.yaml ile Esnek Yapılandırma
```yaml
replicaCount: 3

image:
  repository: registry.bilginc.com/app
  pullPolicy: IfNotPresent
  tag: "v2.1.0"

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
```
