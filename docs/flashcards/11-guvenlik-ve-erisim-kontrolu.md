# Flashcard 11: Güvenlik, TLS/SSL ve Erişim Kontrolü (RBAC)

---

### Soru 1: Elasticsearch'te Güvenlik Katmanının (Elasticsearch Security) 3 temel bileşeni nedir?
**Cevap:**
1. **Şifreleme (Encryption / TLS/SSL):**
   * *Transport Layer (Port 9300):* Node'ların birbiri arasındaki cluster trafiğinin TLS ile şifrelenmesi (Üretim ortamında zorunludur).
   * *HTTP Layer (Port 9200):* İstemcilerin (Kibana, Logstash, API) Elasticsearch ile iletişiminin HTTPS üzerinden şifrelenmesi.
2. **Kimlik Doğrulama (Authentication):**
   * İstek atan kişinin kimliğinin doğrulanması (Kullanıcı adı/şifre, API Key, SAML, LDAP, OIDC).
3. **Yetkilendirme (Authorization / RBAC):**
   * Doğrulanan kullanıcının hangi işlemleri yapabileceğinin kısıtlanması (Roller, Index yetkileri, Cluster yetkileri).

---

### Soru 2: Role-Based Access Control (RBAC) nasıl yapılandırılır?
**Cevap:**
* **Cluster Privileges:** Cluster düzeyindeki yetkiler (örn: `monitor`, `manage`, `all`).
* **Index Privileges:** Index düzeyindeki yetkiler (örn: `read`, `write`, `create_index`, `delete`).
* **Field Level Security (FLS):** Kullanıcının bir belgedeki sadece belirli alanları (örn: maaş veya kredi kartı hariç alanları) görmesini kısıtlama.
* **Document Level Security (DLS):** Kullanıcının yalnızca belirli bir kritere uyan belgeleri (örn: `department: "HR"`) görmesini sağlayan filtre.

---

### Soru 3: API Key kullanımı neden kullanıcı adı/şifreye göre daha güvenlidir?
**Cevap:**
* **Bağımsız Yetki Kapsamı:** Ana kullanıcı şifresini üçüncü parti araçlara (Logstash, mikroservisler) vermek yerine, sadece belirli index'lere yazma yetkisi olan bir API Key üretilir.
* **Son Kullanma Tarihi (Expiration):** İstenirse API Key'e son kullanma tarihi verilebilir (`expiration: "30d"`).
* **Anında İptal (Revocation):** Servis ele geçirilirse sadece o API Key iptal edilir (`DELETE /_security/api_key`), ana şifreyi değiştirmeye gerek kalmaz.
