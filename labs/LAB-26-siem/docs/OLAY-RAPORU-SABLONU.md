# Olay Raporu (Incident Report) — LAB-26

> SIEM'in çıktısı alarm değil, **karardır**. Bu şablon alarmdan karara giden yolu
> kanıtla birlikte kaydeder. Her alanı labda topladığınız gerçek veriyle doldurun.

## 1. Özet

| Alan | Değer |
|---|---|
| Olay kimliği | `INC-<tarih>-<sira>` |
| Tespit eden kural | (Security → Alerts → `kibana.alert.rule.name`) |
| İlk alarm zamanı | |
| Şiddet / risk skoru | |
| Durum | İnceleniyor / Doğrulandı / Yanlış pozitif / Kapandı |

## 2. Ne oldu?

İki cümleyle, teknik olmayan bir yöneticinin anlayacağı dille:

> Örnek: "203.0.113.77 adresinden `devops` hesabına 18 başarısız parola denemesi
> yapıldı ve ardından bir giriş başarılı oldu. Giriş sonrası `sudo` ile root
> yetkisi alınıp `svc-backup` adında yeni bir kullanıcı açıldı."

## 3. Kanıt zinciri

| Sıra | Zaman | `event.action` | Kullanıcı | Kaynak IP | Kanıt |
|---|---|---|---|---|---|
| 1 | | `ssh_invalid_user` | | | kullanıcı taraması |
| 2 | | `ssh_login_failed` ×N | | | brute force |
| 3 | | `ssh_login_success` | | | **ihlal anı** |
| 4 | | `sudo_command` | | | yetki yükseltme |
| 5 | | `user_created` | | | kalıcılık |

Kanıt sorgusu (kapsam belirleme):

```esql
FROM siem-auth-*
| WHERE source.ip == "<KAYNAK_IP>"
| KEEP @timestamp, event.action, event.outcome, user.name, process.command_line
| SORT @timestamp ASC
| LIMIT 50
```

## 4. Bağlam (zenginleştirme çıktısı)

| Alan | Değer |
|---|---|
| Ülke (`source.geo.country_name`) | |
| Ağ sahibi (`source.as.organization.name`) | |
| IOC eşleşmesi (`threat.indicator.provider` / `confidence`) | |
| En yüksek risk skoru (`event.risk_score`) | |

## 5. Etki ve kapsam

- Etkilenen hesap(lar):
- Etkilenen sunucu(lar):
- Saldırganın eriştiği veri / yaptığı değişiklik:
- Hâlâ açık oturum var mı?

## 6. Müdahale adımları

| # | Adım | Sorumlu | Durum |
|---|---|---|---|
| 1 | Kaynak IP'yi güvenlik duvarında engelle | | |
| 2 | Hesabın parolasını sıfırla, oturumları sonlandır | | |
| 3 | Yetkisiz açılan hesabı kaldır | | |
| 4 | SSH için parola yerine anahtar zorunlu kıl | | |

## 7. Tespit kalitesi değerlendirmesi

- Kural olayı **kaç dakika** sonra yakaladı?
- Yanlış pozitif miydi? Değilse hangi sinyal belirleyiciydi?
- Kuralda ayar (tuning) gerekiyor mu? (örn. meşru otomasyon IP'sinin istisnaya alınması)
