#!/usr/bin/env python3
"""
BilgincIT DevOps & Cloud Search Engine - Türkçe Destekli Eğitim İndeksleyicisi
Bu script;
1. Türkçe analizciler (Turkish Stemmer, Asciifolding, Lowercase) tanımlar.
2. 'nested' veri tiplerini (sections, commands, tags) destekleyen mapping kurar.
3. docs/ klasöründeki dokümanları ve içindeki kod bloklarını/bölümlerini parse ederek
   Elasticsearch'e bulk indeksler.
"""

import os
import sys
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://127.0.0.1:9200")
ES_USER = os.getenv("ELASTICSEARCH_USER", "elastic")
ES_PASS = os.getenv("ELASTICSEARCH_PASSWORD", "DevOps2026!")
INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX", "bilgincit_docs")
VERIFY_CERTS = os.getenv("ELASTICSEARCH_VERIFY_CERTS", "false").lower() == "true"

ALLOWED_EXTENSIONS = {
    ".md", ".txt", ".yaml", ".yml", ".json", ".sh", ".bash", 
    ".py", ".conf", ".sql", ".ini", ".dockerfile"
}

def get_es_client():
    kwargs = {
        "hosts": [ES_URL],
        "verify_certs": VERIFY_CERTS
    }
    if ES_USER and ES_PASS:
        kwargs["basic_auth"] = (ES_USER, ES_PASS)
    return Elasticsearch(**kwargs)

def parse_markdown_sections_and_commands(content):
    """
    Doküman içindeki alt başlıkları ve kod/komut bloklarını 
    'nested' sorgularda kullanılmak üzere ayıklar.
    """
    sections = []
    commands = []
    
    # Kod bloklarını regex ile bul: ```bash ... ``` vb.
    code_block_pattern = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)```", re.DOTALL)
    for match in code_block_pattern.finditer(content):
        lang = match.group(1).strip() or "bash"
        snippet = match.group(2).strip()
        if snippet:
            # İlk satırı komut veya açıklama olarak alalım
            first_line = snippet.splitlines()[0][:100]
            commands.append({
                "language": lang,
                "command": first_line,
                "full_code": snippet[:500]  # ilk 500 karakter
            })

    # Alt başlıkları parse et (## veya ###)
    current_subtitle = "Genel Bakış"
    current_text = []
    for line in content.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            if current_text:
                sections.append({
                    "heading": current_subtitle,
                    "body": "\n".join(current_text)[:400]
                })
                current_text = []
            current_subtitle = line.lstrip("#").strip()
        else:
            current_text.append(line)

    if current_text:
        sections.append({
            "heading": current_subtitle,
            "body": "\n".join(current_text)[:400]
        })

    return sections[:10], commands[:15]

def extract_metadata(file_path, content):
    rel_path = os.path.relpath(file_path, DOCS_DIR)
    path_parts = rel_path.split(os.sep)
    
    if len(path_parts) > 1:
        category = " / ".join(p.replace("_", " ").title() for p in path_parts[:-1])
    else:
        category = "Genel DevOps"

    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    
    title = filename
    tags = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break
        elif stripped.startswith("title:"):
            title = stripped.replace("title:", "").strip().strip('"').strip("'")
            break

    # İçerikten otomatik etiket çıkarımı (eğitimde filtreleme için)
    content_lower = content.lower()
    tag_candidates = [
        "elasticsearch", "kibana", "logstash", "docker", "kubernetes", 
        "k8s", "linux", "terraform", "prometheus", "grafana", "sharding", 
        "replication", "ilm", "cluster", "pipeline", "container", "pod"
    ]
    for candidate in tag_candidates:
        if candidate in content_lower:
            tags.append(candidate)

    sections, commands = parse_markdown_sections_and_commands(content)

    # Özet: başlık ve kod bloğu olmayan ilk paragraf
    summary = ""
    in_code = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped or stripped.startswith(("#", "|", ">", "-", "*", "title:")):
            continue
        summary = stripped[:240]
        break

    return {
        "title": title,
        "category": category,
        "filename": filename,
        "extension": ext.lower() if ext else ".txt",
        "rel_path": rel_path,
        "tags": list(set(tags)),
        "sections": sections,
        "commands": commands,
        "summary": summary
    }

def create_index_with_turkish_and_nested_mapping(es: Elasticsearch, recreate=True):
    """
    Türkçe Analyzer + Nested Object destekli mapping oluşturur.
    Eğitim amaçlı:
    - turkish_analyzer: kök bulma (stemmer), küçük harf (lowercase), asciifolding (ı->i, ş->s vb.)
    - nested: 'sections' ve 'commands' alanları bağımsız sorgulanabilir iç nesnelerdir.
    """
    if es.indices.exists(index=INDEX_NAME):
        if recreate:
            print(f"🔄 '{INDEX_NAME}' indeksi mevcut, yeniden oluşturmak üzere siliniyor...")
            es.indices.delete(index=INDEX_NAME)
        else:
            print(f"ℹ️ '{INDEX_NAME}' indeksi zaten var.")
            return

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "filter": {
                    "turkish_stop": {
                        "type": "stop",
                        "stopwords": "_turkish_"
                    },
                    "turkish_lowercase": {
                        "type": "lowercase",
                        "language": "turkish"
                    },
                    "turkish_stemmer": {
                        "type": "stemmer",
                        "language": "turkish"
                    },
                    "bilginc_asciifolding": {
                        "type": "asciifolding",
                        "preserve_original": True
                    }
                },
                "analyzer": {
                    # Sıra önemlidir (ölçülerek seçildi):
                    # - apostrophe: "Kubernetes'in" -> "kubernetes" (kesme işaretinden sonrasını atar)
                    # - turkish_lowercase: I -> ı, İ -> i (Türkçe kurallı küçük harf)
                    # - keyword_repeat: kelimenin orijinali de saklanır; Snowball Türkçe stemmer
                    #   bazı kelimeleri tuhaf köklere indirdiğinde (podları -> podu) tam kelime
                    #   eşleşmesi kaybolmaz
                    # - turkish_stemmer, asciifolding'den ÖNCE: stemmer ı/ş/ğ harflerini görmeli;
                    #   önce asciifolding yapılırsa "podları" -> "podlari" olur ve ek atılamaz
                    # - bilginc_asciifolding: ü -> u (orijinal korunur), kullanıcı "kume" yazsa da bulur
                    "turkish_bilginc_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "apostrophe",
                            "turkish_lowercase",
                            "turkish_stop",
                            "keyword_repeat",
                            "turkish_stemmer",
                            "bilginc_asciifolding",
                            "remove_duplicates"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "turkish_bilginc_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "category": {
                    "type": "keyword"
                },
                "filename": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "extension": {
                    "type": "keyword"
                },
                "rel_path": {
                    "type": "keyword"
                },
                # Sonuç listesinde gösterilen kısa özet: aranmaz, yalnızca saklanır.
                "summary": {
                    "type": "text",
                    "index": False
                },
                "tags": {
                    "type": "keyword"
                },
                "content": {
                    "type": "text",
                    "analyzer": "turkish_bilginc_analyzer",
                    "term_vector": "with_positions_offsets"
                },
                # NESTED ALAN 1: Doküman Bölümleri (Nested Query Eğitimi İçin)
                "sections": {
                    "type": "nested",
                    "properties": {
                        "heading": {
                            "type": "text",
                            "analyzer": "turkish_bilginc_analyzer"
                        },
                        "body": {
                            "type": "text",
                            "analyzer": "turkish_bilginc_analyzer"
                        }
                    }
                },
                # NESTED ALAN 2: Kod ve Komutlar (Nested Query Eğitimi İçin)
                "commands": {
                    "type": "nested",
                    "properties": {
                        "language": {
                            "type": "keyword"
                        },
                        "command": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "full_code": {
                            "type": "text",
                            "analyzer": "standard"
                        }
                    }
                },
                "indexed_at": {
                    "type": "date"
                }
            }
        }
    }
    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"✅ '{INDEX_NAME}' indeksi Türkçe Analyzer + Nested mapping ile başarıyla oluşturuldu.")

def run_indexer(recreate=True):
    print("=" * 70)
    print("🎓 BilgincIT Elasticsearch Eğitim & Arama Portalı - İndeksleyici")
    print(f"📂 Kaynak Klasör: {DOCS_DIR}")
    print(f"🔗 Elasticsearch: {ES_URL} | İndeks: {INDEX_NAME}")
    print("=" * 70)

    if not os.path.exists(DOCS_DIR):
        print(f"❌ Hata: {DOCS_DIR} klasörü bulunamadı!")
        sys.exit(1)

    try:
        es = get_es_client()
        if not es.ping():
            print("⚠️ Elasticsearch'e erişilemedi! Lütfen servisin çalıştığını doğrulayın.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        sys.exit(1)

    create_index_with_turkish_and_nested_mapping(es, recreate=recreate)

    actions = []
    indexed_count = 0

    for root, _, files in os.walk(DOCS_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            _, ext = os.path.splitext(filename)

            if ext.lower() not in ALLOWED_EXTENSIONS and not filename.startswith("."):
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                meta = extract_metadata(file_path, content)
                doc_id = meta["rel_path"].replace(os.sep, "_")

                actions.append({
                    "_index": INDEX_NAME,
                    "_id": doc_id,
                    "_source": {
                        "title": meta["title"],
                        "category": meta["category"],
                        "filename": meta["filename"],
                        "extension": meta["extension"],
                        "rel_path": meta["rel_path"],
                        "tags": meta["tags"],
                        "content": content,
                        "summary": meta["summary"],
                        "sections": meta["sections"],
                        "commands": meta["commands"],
                        "indexed_at": datetime.now(timezone.utc).isoformat()
                    }
                })
                indexed_count += 1
                print(f"  📄 İndekse Hazır: [{meta['category']}] {meta['title']} (Nested: {len(meta['sections'])} bölüm, {len(meta['commands'])} komut)")
            except Exception as ex:
                print(f"  ⚠️ Hata ({file_path}): {ex}")

    if actions:
        print(f"\n📦 Toplam {len(actions)} doküman Elasticsearch kümesine aktarılıyor...")
        success, failed = helpers.bulk(es, actions, stats_only=True)
        print(f"🎉 İndeksleme Tamamlandı: {success} başarılı, {failed} hatalı.")
        if failed:
            sys.exit(1)
    else:
        print("ℹ️ docs/ altında indekslenecek uygun dosya bulunamadı.")

if __name__ == "__main__":
    recreate = "--no-recreate" not in sys.argv
    run_indexer(recreate=recreate)
