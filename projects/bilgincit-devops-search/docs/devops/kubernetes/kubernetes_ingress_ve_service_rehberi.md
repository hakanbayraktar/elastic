# Kubernetes Ingress ve Service Mimarisi

Kubernetes cluster içerisindeki mikroservislerin dış dünyaya güvenli şekilde açılması (Ingress) ve Pod'lar arası yük dengeleme (Service).

## 1. Kubernetes Service Türleri
- **ClusterIP:** Sadece cluster içi erişim (varsayılan).
- **NodePort:** Her Kubernetes Worker Node'unun belirli bir portunu (30000-32767) dışarı açar.
- **LoadBalancer:** Bulut sağlayıcının (AWS NLB, GCP Load Balancer) harici IP'sini bağlar.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

## 2. Ingress Controller ve TLS Sonlandırma
Nginx Ingress Controller ile path tabanlı yönlendirme ve Let's Encrypt SSL:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.bilginc.com
      secretName: api-tls-cert
  rules:
    - host: api.bilginc.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
```
