# Flashcard 06: Metin Analizi, Tokenization ve Analyzer Mimarisi

---

### Soru 1: Analyzer (Metin Çözümleyici) bileşenleri nelerdir?
**Cevap:**
Bir Analyzer üç temel parçanın ardışık çalışmasıyla oluşur:
1. **Character Filters (0 veya daha fazla):** Ham metin henüz kelimelere ayrılmadan önce karakter seviyesinde temizlenir (Örn: HTML etiketlerini temizleme `html_strip`, özel simgeleri değiştirme).
2. **Tokenizer (Tam olarak 1 adet):** Metni belirli kurallara göre kelimelere (token / term) böler (Örn: `standard`, `whitespace`, `letter`, `edge_ngram`).
3. **Token Filters (0 veya daha fazla):** Çıkan kelimeleri dönüştürür, siler veya zenginleştirir (Örn: Küçük harfe çevirme `lowercase`, durak kelimeleri atma `stop`, kök bulma `stemmer`, eş anlamlı ekleme `synonym`).

---

### Soru 2: `text` ile `keyword` veri tipleri arasındaki fark nedir?
**Cevap:**
| Özellik | `text` | `keyword` |
|---|---|---|
| **Analiz Süreci** | Analyzer'dan geçer (küçük harf, kök bulma, kelimelere bölme). | **Hiçbir analizden geçmez**, metin olduğu gibi tek bir token olarak saklanır. |
| **Arama Tipi** | Tam metin arama (Full-text search, `match` sorgusu). | Tam eşleşme (Exact match, `term` sorgusu). |
| **Büyük/Küçük Harf** | Duyarsızdır (varsayılan analyzer küçük harfe çevirdiği için). | Duyarlıdır (`"Admin"` ile `"admin"` eşleşmez). |
| **Kullanım Alanları** | Makale içeriği, ürün açıklaması, serbest arama. | Durum kodları (`status: "ACTIVE"`), e-posta, ID, aggregation, sıralama. |

---

### Soru 3: Multi-field (Çoklu Alan) nedir, neden kullanılır?
**Cevap:**
* Bir metin alanının hem tam metin aramada hem de sıralama/gruplamada (aggregation) kullanılabilmesi için aynı alanın iki farklı tiple indexlenmesidir:
  ```json
  "title": {
    "type": "text",
    "fields": {
      "keyword": { "type": "keyword", "ignore_above": 256 }
    }
  }
  ```
* Bu sayede `title` alanında "kablosuz kulaklık" diye arama yapabilirken, `title.keyword` alanında alfabetik sıralama veya aggregation yapabilirsiniz.

---

### Soru 4: Autocomplete (Otomatik Tamamlama) için Edge N-gram nasıl çalışır?
**Cevap:**
* Bir kelimeyi baştan başlayarak hece/harf parçalarına (n-gram) böler:
  * Kelime: `"elma"`
  * Edge N-Gram (`min_gram: 2, max_gram: 4`): `["el", "elm", "elma"]`
* Kullanıcı arama kutusuna sadece `"el"` yazdığında, henüz arama tuşuna basmadan "elma" kelimesi Inverted Index'te anında bulunur.
