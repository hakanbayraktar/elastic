"""
Router: Autocomplete & Search Bar Önerileri
===========================================
Kurumsal E-Ticaret 4-Clause Bool Should Arama Mimarisi:

Clause 1: match (Edge N-gram, boost: 5, operator: and)
Clause 2: term (search_autocomplete.keyword, boost: 100) -> Tam ürün adı eşleşmesi
Clause 3: multi_match phrase (fields: product_name, brand, slop: 5, boost: 5)
Clause 4: match_phrase (search_autocomplete, boost: 1)
"""

from fastapi import APIRouter, Query, HTTPException
from app.es_client import get_elasticsearch_client
from app.config import settings
from app.schemas.search_models import AutocompleteResponse, AutocompleteSuggestion

router = APIRouter(prefix="/api/v1/search", tags=["Search Bar & Autocomplete"])

@router.get("/autocomplete", response_model=AutocompleteResponse)
def get_autocomplete_suggestions(
    q: str = Query(..., min_length=1, description="Arama çubuğuna yazılan ön ek / kelime (örn: 'cas', 'dress', 'shoes')"),
    limit: int = Query(10, ge=1, le=30, description="Döndürülecek maksimum öneri adedi")
):
    client = get_elasticsearch_client()
    clean_query = q.strip()
    
    # 4-Clause Bool Query İnşası
    es_query = {
        "bool": {
            "should": [
                # 1. Clause: Edge N-Gram Match (Prefix arama)
                {
                    "match": {
                        "search_autocomplete.autocomplete": {
                            "query": clean_query,
                            "operator": "and",
                            "boost": 5.0
                        }
                    }
                },
                # 2. Clause: Birebir Tam Eşleşme (Keyword Term Boost)
                {
                    "term": {
                        "search_autocomplete.keyword": {
                            "value": clean_query,
                            "boost": 100.0
                        }
                    }
                },
                # 3. Clause: Marka ve Ürün Adında Sıralı Kelime (Slop Phrase)
                {
                    "multi_match": {
                        "query": clean_query,
                        "fields": ["product_name", "brand"],
                        "type": "phrase",
                        "slop": 5,
                        "boost": 5.0
                    }
                },
                # 4. Clause: Katı Cümle Eşleşmesi (Match Phrase)
                {
                    "match_phrase": {
                        "search_autocomplete": {
                            "query": clean_query,
                            "boost": 1.0
                        }
                    }
                }
            ]
        }
    }
    
    try:
        # Aday sonuç havuzu için 30 kayıt çekiyoruz
        resp = client.search(
            index=settings.PRODUCT_INDEX,
            query=es_query,
            size=30,
            _source=["product_id", "product_name", "brand", "search_autocomplete"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch arama hatası: {str(e)}")
    
    hits = resp.get("hits", {}).get("hits", [])
    took_ms = resp.get("took", 0)
    
    # Backend Post-Processing: Tekilleştirme (Deduplication)
    seen_texts = set()
    suggestions = []
    
    for hit in hits:
        source = hit.get("_source", {})
        score = hit.get("_score", 0.0)
        prod_id = source.get("product_id")
        
        # Tercih sırası: search_autocomplete veya product_name
        suggest_text = source.get("search_autocomplete") or source.get("product_name")
        if not suggest_text:
            continue
            
        suggest_key = suggest_text.lower().strip()
        if suggest_key not in seen_texts:
            seen_texts.add(suggest_key)
            suggestions.append(
                AutocompleteSuggestion(
                    text=suggest_text,
                    product_id=prod_id,
                    score=round(score, 2)
                )
            )
            if len(suggestions) >= limit:
                break
                
    return AutocompleteResponse(
        query=clean_query,
        total_suggestions=len(suggestions),
        took_ms=took_ms,
        suggestions=suggestions
    )
