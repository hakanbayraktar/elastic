# Flashcard 07: Arama Sorguları, Query DSL ve Puanlama

---

### Soru 1: `term` sorgusu ile `match` sorgusu arasındaki fark nedir?
**Cevap:**
* **`match` Sorgusu:**
  * Girilen arama terimini **indexleme anındaki analyzer ile analiz eder** (küçük harfe çevirir, parçalar).
  * `text` alanlarında tam metin arama yapmak için kullanılır.
* **`term` Sorgusu:**
  * Girilen değeri **hiçbir analize tabi tutmadan** doğrudan Inverted Index'te arar.
  * `keyword`, `integer`, `date`, `boolean` gibi analiz edilmemiş alanlarda tam eşleşme için kullanılır.
  * **Kritik Hata:** `text` alanında büyük harfli bir arama terimiyle `term` sorgusu çalıştırırsanız, Inverted Index'teki kelimeler küçük harf olduğu için eşleşme bulunamaz!

---

### Soru 2: `bool` sorgusunun 4 temel maddesi (`must`, `filter`, `should`, `must_not`) nasıl çalışır?
**Cevap:**
1. **`must`:** Koşul mutlaka sağlanmalıdır (AND). Alaka puanına (`_score`) etki eder.
2. **`filter`:** Koşul mutlaka sağlanmalıdır (AND). Alaka puanına **etki etmez**, sonuçlar önbelleğe alınır.
3. **`should`:** Koşulun sağlanması tercih edilir (OR). Eşleşirse belgenin alaka puanını artırır. Eğer `must` veya `filter` yoksa en az bir `should` maddesi eşleşmek zorundadır (`minimum_should_match: 1`).
4. **`must_not`:** Koşulu sağlayan belgeler kesinlikle elenir (NOT). Puanlamaya etki etmez.

---

### Soru 3: BM25 Alakadarlık Puanlaması (`_score`) neye göre hesaplanır?
**Cevap:**
Üç ana faktör belirleyicidir:
1. **Term Frequency (TF):** Aranan kelime belgede kaç kez geçiyor? (Ne kadar çok geçerse puan o kadar artar, ancak doygunluk sınırı vardır).
2. **Inverse Document Frequency (IDF):** Aranan kelime index'teki tüm belgelerde ne kadar yaygın? (Nadir bulunan özel kelimeler çok daha yüksek puan kazandırır).
3. **Field Length Normalization:** Alanın uzunluğu nedir? (Kısa bir başlıkta geçen kelime, 10 sayfalık uzun bir makalede geçen kelimeden daha değerlidir).

---

### Soru 4: `dis_max` ve `boosting` sorgusu ne işe yarar?
**Cevap:**
* **`dis_max` (Disjunction Max):** Birden fazla alanda arama yaparken, skorları toplamak yerine en yüksek puanı alan alanın skorunu baz alır. `tie_breaker` parametresiyle (örn: 0.3) diğer eşleşen alanlardan küçük bir katkı puanı ekler.
* **`boosting` Sorgusu:** Belgeleri `must_not` ile tamamen silip atmak istemediğiniz, ancak bazı belgelerin (örn: eski ürünler, spam kayıtları) sıralamada en alta düşmesini istediğiniz durumlarda `negative_boost` (örn: 0.2) uygulayarak puanını kırar.

---

### Soru 5: Derin Sayfalama (Deep Pagination) neden `from/size` ile yapılmamalıdır?
**Cevap:**
* `from: 10000, size: 10` dendiğinde, her shard en iyi 10.010 belgeyi coordinating node'a göndermek zorundadır. Bellek tükenmesine yol açar (`index.max_result_window` sınırı varsayılan 10.000'dir).
* **Çözüm:** Derin sayfalama için **Point-in-Time (PIT)** ile birlikte **`search_after`** kullanılmalıdır.
