# Kubernetes Mimarisi ve Pod Troubleshooting Rehberi

Kubernetes kümesinde sorun tespiti (debugging) ve Control Plane mimarisi kılavuzu.

## 1. Kubernetes Control Plane Bileşenleri
- **kube-apiserver:** Kümenin beynidir, tüm REST isteklerini doğrular ve etcd ile konuşur.
- **etcd:** Kümenin tüm konfigürasyonunu ve durumunu saklayan dağıtık anahtar-değer (KV) deposu.
- **kube-scheduler:** Yeni oluşturulan Pod'ları kaynaklara göre en uygun Node'a atar.
- **kube-controller-manager:** NodeController, DeploymentController gibi döngüleri çalıştırır.

## 2. Pod Hata Durumları ve Çözümleri
1. **CrashLoopBackOff:** Uygulama başlatıldıktan hemen sonra çöküyor.
   ```bash
   kubectl logs <pod-name> --previous
   kubectl describe pod <pod-name>
   ```
2. **ImagePullBackOff / ErrImagePull:** İmaj adı yanlış veya Private Registry kimlik bilgisi (ImagePullSecret) eksik.
3. **Pending:** Yeterli CPU/Memory kaynağı yok (Resource Quota / Limits) veya uygun Node bulunamıyor.
4. **OOMKilled:** Pod tahsis edilen bellek sınırını (Memory Limit) aştığı için Linux OOM Killer tarafından sonlandırıldı.

```bash
# Hızlı teşhis komutları
kubectl get pods -A -o wide --field-selector status.phase!=Running
kubectl top nodes
kubectl top pods
```
