#!/usr/bin/env python3
"""
BilgincIT DevOps & Cloud Search Engine - Eğitim Odaklı Arama Web Portalı

Bu uygulama bir arama motorunun Elasticsearch tarafında nasıl kurulduğunu gösterir:
- Match, Multi-Match, Fuzzy, Nested ve Match Phrase arama tipleri (her biri için Query DSL).
- Facet'ler: kategori ve etiket sayıları aynı istekteki aggregation'lardan gelir; seçilen
  filtre post_filter ile uygulanır, böylece diğer facet'in sayıları kaybolmaz.
- Analyzer paneli: aranan ifadenin Türkçe analyzer ve standard analyzer ile hangi
  token'lara dönüştüğü (_analyze API).
- Her sorgu Kibana Dev Tools'a veya terminale (curl) kopyalanabilir.
"""

import json
import os

import markdown
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from flask import Flask, abort, jsonify, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
load_dotenv(os.path.join(BASE_DIR, ".env"))

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://127.0.0.1:9200")
ES_USER = os.getenv("ELASTICSEARCH_USER", "elastic")
ES_PASS = os.getenv("ELASTICSEARCH_PASSWORD", "DevOps2026!")
INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX", "bilgincit_docs")
VERIFY_CERTS = os.getenv("ELASTICSEARCH_VERIFY_CERTS", "false").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", 19003))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
TURKISH_ANALYZER = "turkish_bilginc_analyzer"

app = Flask(__name__)


def get_es_client():
    kwargs = {"hosts": [ES_URL], "verify_certs": VERIFY_CERTS, "request_timeout": 10}
    if ES_USER and ES_PASS:
        kwargs["basic_auth"] = (ES_USER, ES_PASS)
    return Elasticsearch(**kwargs)


es = get_es_client()

# Arama tipleri: arayüzde sekme olarak gösterilir. "example" hızlı test çipinde kullanılır.
SEARCH_TYPES = {
    "multi_match": {
        "name": "Multi-Match",
        "badge": "Varsayılan",
        "description": "Başlık, etiket, dosya adı ve içerikte birlikte arar. Başlık eşleşmesi "
                       "4 kat (title^4) ağırlıklıdır; operator: and ile tüm kelimeler geçmelidir.",
    },
    "fuzzy": {
        "name": "Fuzzy",
        "badge": "Yazım hatası toleransı",
        "description": "fuzziness: AUTO ile her kelimede 1-2 harflik hata (Levenshtein mesafesi) "
                       "tolere edilir; prefix_length: 2 ilk iki harfin doğru yazılmasını ister. "
                       "'kuberntes' yazsanız da 'kubernetes' bulunur.",
    },
    "match_phrase": {
        "name": "Match Phrase",
        "badge": "Sıralı kalıp",
        "description": "Kelimeler girilen sırada ve yan yana geçmelidir (slop: 1 ile araya en fazla "
                       "bir kelime girebilir). 'control plane' kalıbını arar, iki kelimenin ayrı "
                       "yerlerde geçtiği dokümanı getirmez.",
    },
    "nested": {
        "name": "Nested",
        "badge": "Alt nesneler",
        "description": "Dokümanın 'commands' (kod blokları) ve 'sections' (alt başlıklar) dizileri "
                       "nested tipindedir: her eleman bağımsız sorgulanır ve eşleşen eleman "
                       "inner_hits ile ayrıca döner.",
    },
    "match": {
        "name": "Match",
        "badge": "Türkçe analyzer",
        "description": "Yalnızca 'content' alanında, Türkçe analyzer'dan geçmiş token'larla arar. "
                       "'kümeler' → 'küme' gibi çoğul ekleri kök bulma (stemmer) ile atar; "
                       "Analyzer sekmesinde token'ları görün.",
    },
}

QUICK_TESTS = [
    {"type": "fuzzy", "q": "kuberntes", "label": "Fuzzy", "hint": "yazım hatası"},
    {"type": "nested", "q": "docker run", "label": "Nested", "hint": "kod bloğunda komut"},
    {"type": "match_phrase", "q": "control plane", "label": "Phrase", "hint": "sıralı kalıp"},
    {"type": "match", "q": "kümeler", "label": "Türkçe kök", "hint": "çoğul eki"},
    {"type": "multi_match", "q": "vm.max_map_count", "label": "Kernel ayarı", "hint": "noktalı terim"},
]

HIGHLIGHT = {
    # encoder: html -> doküman içindeki < > karakterleri kaçırılır; yalnız <mark> HTML olarak kalır.
    "encoder": "html",
    "pre_tags": ["<mark>"],
    "post_tags": ["</mark>"],
}


def build_query(search_type, query_term):
    """Seçilen arama tipine göre 'query' bölümünü üretir. Boş ifade: match_all."""
    if not query_term:
        return {"match_all": {}}

    if search_type == "fuzzy":
        return {"multi_match": {
            "query": query_term,
            "fields": ["title^4", "filename^3", "tags^2", "content"],
            "fuzziness": "AUTO",
            "prefix_length": 2,
            "operator": "and",
        }}
    if search_type == "match_phrase":
        return {"multi_match": {
            "query": query_term,
            "type": "phrase",
            "fields": ["title^3", "content"],
            "slop": 1,
        }}
    if search_type == "nested":
        def nested(path, title_field, body_field):
            # Vurgu: önce satır/başlık; eşleşme bloğun devamındaysa gövdeden kısa bir parça
            return {"nested": {
                "path": path,
                "query": {"multi_match": {"query": query_term, "fields": [title_field, body_field], "operator": "and"}},
                "inner_hits": {"size": 3, "highlight": {**HIGHLIGHT, "fields": {
                    title_field: {"number_of_fragments": 0},
                    body_field: {"fragment_size": 120, "number_of_fragments": 1},
                }}},
            }}
        return {"bool": {
            "should": [
                nested("commands", "commands.command", "commands.full_code"),
                nested("sections", "sections.heading", "sections.body"),
            ],
            "minimum_should_match": 1,
        }}
    if search_type == "match":
        return {"match": {"content": {"query": query_term, "operator": "and"}}}

    return {"multi_match": {
        "query": query_term,
        "fields": ["title^4", "tags^3", "filename^2", "content"],
        "operator": "and",
    }}


def build_search_body(search_type, query_term, category="", tag=""):
    """
    Arama gövdesi. Facet deseni:
    - aggs, ana sorgunun TÜM sonuçları üzerinden sayılır;
    - her facet yalnızca DİĞER facet'in seçimiyle süzülür (kategori seçiliyken etiket sayıları
      o kategoriye göre, kategori sayıları ise etiket seçimine göre);
    - seçilen filtreler sonuç listesine post_filter ile uygulanır.
    """
    cat_filter = {"term": {"category": category}} if category else None
    tag_filter = {"term": {"tags": tag}} if tag else None

    body = {
        "query": build_query(search_type, query_term),
        "size": 20,
        "track_total_hits": True,
        "_source": {"excludes": ["content", "sections", "commands"]},  # liste için özet yeter
        "highlight": {**HIGHLIGHT, "fields": {
            "title": {"number_of_fragments": 0},
            "content": {"fragment_size": 180, "number_of_fragments": 2},
        }},
        "aggs": {
            "by_category": {
                "filter": tag_filter or {"match_all": {}},
                "aggs": {"values": {"terms": {"field": "category", "size": 30}}},
            },
            "by_tag": {
                "filter": cat_filter or {"match_all": {}},
                "aggs": {"values": {"terms": {"field": "tags", "size": 30}}},
            },
        },
    }
    filters = [f for f in (cat_filter, tag_filter) if f]
    if filters:
        body["post_filter"] = {"bool": {"filter": filters}}
    return body


def run_search(search_type, query_term, category="", tag=""):
    body = build_search_body(search_type, query_term, category, tag)
    result = {"body": body, "hits": [], "total": 0, "took": 0, "max_score": None,
              "categories": [], "tags": [], "error": None}
    try:
        resp = es.search(index=INDEX_NAME, body=body)
    except Exception as exc:  # index yok, ES kapalı, sorgu hatası
        result["error"] = str(exc)
        return result
    hits = resp["hits"]
    result.update(
        hits=hits["hits"],
        total=hits["total"]["value"],
        took=resp.get("took", 0),
        max_score=hits.get("max_score"),
        categories=resp["aggregations"]["by_category"]["values"]["buckets"],
        tags=resp["aggregations"]["by_tag"]["values"]["buckets"],
    )
    return result


def analyze(text):
    """Aranan ifadenin iki analyzer'daki token'ları (Analyzer sekmesi)."""
    out = {"turkish": [], "standard": []}
    if not text:
        return out
    try:
        tr = es.indices.analyze(index=INDEX_NAME, analyzer=TURKISH_ANALYZER, text=text)
        st = es.indices.analyze(analyzer="standard", text=text)
        out["turkish"] = [t["token"] for t in tr["tokens"]]
        out["standard"] = [t["token"] for t in st["tokens"]]
    except Exception as exc:
        out["error"] = str(exc)
    return out


def devtools_text(body):
    return f"GET {INDEX_NAME}/_search\n{json.dumps(body, indent=2, ensure_ascii=False)}"


def curl_text(body):
    payload = json.dumps(body, ensure_ascii=False).replace("'", "'\\''")
    return (f"curl -s -u \"elastic:$ELASTIC_PASSWORD\" -H 'Content-Type: application/json' \\\n"
            f"  '{ES_URL}/{INDEX_NAME}/_search' -d '{payload}' | jq '.hits.hits[]._source.title'")


@app.template_global()
def search_url(**changes):
    """Mevcut arama parametrelerini koruyarak yalnız verilenleri değiştiren URL (boşlar atılır)."""
    args = {k: v for k, v in request.args.items() if k in ("q", "type", "category", "tag")}
    args.update(changes)
    return url_for("home", **{k: v for k, v in args.items() if v})


def es_alive():
    try:
        return es.ping()
    except Exception:
        return False


@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    search_type = request.args.get("type", "multi_match")
    if search_type not in SEARCH_TYPES:
        search_type = "multi_match"
    category = request.args.get("category", "")
    tag = request.args.get("tag", "")

    es_status = es_alive()
    searched = bool(query or category or tag)
    # Arama yapılmasa da facet'ler (tüm index üzerinden) sol panelde görünsün.
    result = run_search(search_type, query, category, tag) if es_status else None
    if result and not searched:
        result["hits"] = []

    return render_template(
        "index.html",
        query=query,
        search_type=search_type,
        search_types=SEARCH_TYPES,
        quick_tests=QUICK_TESTS,
        category=category,
        tag=tag,
        searched=searched,
        result=result,
        tokens=analyze(query) if (es_status and query) else None,
        devtools=devtools_text(result["body"]) if result and searched else "",
        curl=curl_text(result["body"]) if result and searched else "",
        es_status=es_status,
        es_url=ES_URL,
        index_name=INDEX_NAME,
    )


def doc_title(raw, fallback):
    for line in raw.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


@app.route("/view/<path:doc_path>")
def view_document(doc_path):
    safe_path = os.path.realpath(os.path.join(DOCS_DIR, doc_path))
    if not safe_path.startswith(os.path.realpath(DOCS_DIR) + os.sep) or not os.path.isfile(safe_path):
        abort(404, description="Doküman bulunamadı.")

    with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_content = f.read()

    filename = os.path.basename(safe_path)
    is_markdown = safe_path.endswith((".md", ".markdown"))
    rendered_html, toc = "", []
    if is_markdown:
        md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"])
        rendered_html = md.convert(raw_content)
        # İlk seviye (# Başlık) sayfa başlığıdır; içindekiler ## ve ### başlıklarından oluşur.
        for top in md.toc_tokens:
            for h2 in top.get("children", []) if top["level"] == 1 else [top]:
                toc.append({"id": h2["id"], "name": h2["name"], "level": 2})
                for h3 in h2.get("children", []):
                    toc.append({"id": h3["id"], "name": h3["name"], "level": 3})

    parts = doc_path.split("/")[:-1]
    category = " / ".join(p.replace("_", " ").title() for p in parts) or "Genel DevOps"
    return render_template(
        "document.html",
        title=doc_title(raw_content, filename),
        filename=filename,
        category=category,
        rel_path=doc_path,
        is_markdown=is_markdown,
        rendered_html=rendered_html,
        raw_content=raw_content,
        toc=toc,
        highlight_q=request.args.get("q", ""),
        line_count=raw_content.count("\n") + 1,
    )


@app.route("/api/search")
def api_search():
    """Arayüzdeki aramanın JSON karşılığı: terminalden curl ile test etmek için."""
    search_type = request.args.get("type", "multi_match")
    if search_type not in SEARCH_TYPES:
        return jsonify({"error": f"type şunlardan biri olmalı: {', '.join(SEARCH_TYPES)}"}), 400
    result = run_search(search_type, request.args.get("q", "").strip(),
                        request.args.get("category", ""), request.args.get("tag", ""))
    if result["error"]:
        return jsonify({"error": result["error"]}), 502
    return jsonify({
        "type": search_type,
        "took_ms": result["took"],
        "total": result["total"],
        "hits": [{
            "title": h["_source"]["title"],
            "category": h["_source"].get("category"),
            "score": h["_score"],
            "rel_path": h["_source"].get("rel_path"),
            "nested_matches": sum(len(v["hits"]["hits"]) for v in h.get("inner_hits", {}).values()),
        } for h in result["hits"]],
        "facets": {
            "category": {b["key"]: b["doc_count"] for b in result["categories"]},
            "tags": {b["key"]: b["doc_count"] for b in result["tags"]},
        },
        "query_dsl": result["body"],
    })


@app.route("/api/analyze")
def api_analyze():
    text = request.args.get("text", "").strip()
    if not text:
        return jsonify({"error": "text parametresi gerekli"}), 400
    return jsonify({"text": text, "analyzer": TURKISH_ANALYZER, **analyze(text)})


@app.route("/api/suggest")
def api_suggest():
    """Search-as-you-type: başlıkta önek eşleşmesi en yüksek ağırlığı alır."""
    prefix = request.args.get("q", "").strip()
    if len(prefix) < 2:
        return jsonify([])
    body = {
        "query": {"bool": {
            "should": [
                {"match_phrase_prefix": {"title": {"query": prefix, "boost": 5}}},
                {"match": {"tags": {"query": prefix, "boost": 4}}},
                {"match": {"title": {"query": prefix, "boost": 3, "operator": "and"}}},
                {"match": {"filename": {"query": prefix, "boost": 2}}},
                {"match": {"content": {"query": prefix, "operator": "and"}}},
            ],
            "minimum_should_match": 1,
        }},
        "_source": ["title", "category", "rel_path"],
        "highlight": {**HIGHLIGHT, "fields": {"title": {"number_of_fragments": 0}}},
        "size": 6,
    }
    try:
        resp = es.search(index=INDEX_NAME, body=body)
    except Exception:
        return jsonify([])
    return jsonify([{
        "title": h["_source"]["title"],
        "highlighted_title": h.get("highlight", {}).get("title", [None])[0],
        "category": h["_source"].get("category", "Genel"),
        "rel_path": h["_source"].get("rel_path", ""),
        "score": h["_score"],
    } for h in resp["hits"]["hits"]])


@app.route("/api/health")
def api_health():
    try:
        ping = es.ping()
        doc_count = 0
        if ping and es.indices.exists(index=INDEX_NAME):
            doc_count = es.count(index=INDEX_NAME).get("count", 0)
        return jsonify({
            "status": "healthy" if ping else "disconnected",
            "elasticsearch_url": ES_URL,
            "index": INDEX_NAME,
            "indexed_documents": doc_count,
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    print(f"BilgincIT DevOps Search Engine: http://127.0.0.1:{FLASK_PORT}")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=FLASK_DEBUG)
