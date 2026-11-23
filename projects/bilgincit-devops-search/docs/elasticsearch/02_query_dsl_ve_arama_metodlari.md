# Elasticsearch Query DSL ve Arama Metodları Rehberi

Elasticsearch Query DSL (Domain Specific Language), JSON tabanlı çok zengin bir sorgulama dilidir. Bu rehberde temel arama türleri ve kullanım senaryoları özetlenmiştir.

## 1. Match Query (Standart Metin Eşleme)
Match sorgusu, girilen metni indeksteki analyzer'dan geçirir (küçük harf, kök bulma, stop-words) ve terimleri arar.

```json
GET /bilgincit_docs/_search
{
  "query": {
    "match": {
      "content": {
        "query": "küme mimarisi",
        "operator": "and"
      }
    }
  }
}
```

## 2. Fuzzy Query (Yazım Hatalarını Tolere Eden Arama)
Kullanıcının klavye sürçmelerini (örneğin "kuberntes" veya "elastik") Damerau-Levenshtein Edit Distance algoritması ile çözer.

```json
GET /bilgincit_docs/_search
{
  "query": {
    "fuzzy": {
      "title": {
        "value": "kuberntes",
        "fuzziness": "AUTO",
        "prefix_length": 1
      }
    }
  }
}
```

## 3. Nested Query (İç İçe Nesnelerde Arama)
Normal dizilerde Elasticsearch nesneleri 'flatten' ettiği için `author: Ali` ve `book: Java` aynı nesnede miydi bilemez. `nested` tipi bu ilişkiyi korur.

```json
GET /bilgincit_docs/_search
{
  "query": {
    "nested": {
      "path": "commands",
      "query": {
        "bool": {
          "must": [
            { "match": { "commands.language": "bash" } },
            { "match": { "commands.command": "docker run" } }
          ]
        }
      }
    }
  }
}
```

## 4. Match Phrase Query (Tam Kalıp / Sıralı Arama)
Kelimelerin tam olarak yan yana ve verilen sırada geçtiği durumları bulur. `slop` parametresi araya kaç kelime girmesine izin verildiğini belirler.

```json
GET /bilgincit_docs/_search
{
  "query": {
    "match_phrase": {
      "content": {
        "query": "index lifecycle management",
        "slop": 0
      }
    }
  }
}
```
