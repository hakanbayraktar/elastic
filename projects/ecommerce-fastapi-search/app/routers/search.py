"""
Router: Tam Katalog Arama, Filtreler (Facets) ve Sıralama
=========================================================
Bu modül, e-ticaret arama motorunun ana listeleme, alaka mühendisliği (boosting),
dinamik filtreleme (aggregations) ve sayfalama bileşenlerini sağlar.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.es_client import get_elasticsearch_client
from app.config import settings
from app.schemas.search_models import (
    SearchResponse,
    ProductItem,
    SearchFacets,
    FacetBucket
)

router = APIRouter(prefix="/api/v1/search", tags=["Katalog Arama ve Filtreler"])

@router.get("", response_model=SearchResponse)
def search_products(
    q: Optional[str] = Query(None, description="Arama terimi (örn: 'dress', 'shoes')"),
    category: Optional[str] = Query(None, description="Kategori filtresi (örn: 'Women\\'s Clothing')"),
    brand: Optional[str] = Query(None, description="Marka filtresi (örn: 'Elitelligence')"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum fiyat"),
    max_price: Optional[float] = Query(None, ge=0, description="Maksimum fiyat"),
    sort_by: Optional[str] = Query("relevance", pattern="^(relevance|price_asc|price_desc|units_sold)$", description="Sıralama kriteri"),
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    size: int = Query(10, ge=1, le=50, description="Sayfa başına ürün sayısı")
):
    client = get_elasticsearch_client()
    from_offset = (page - 1) * size
    
    must_clauses = []
    filter_clauses = []
    
    # 1. Full-Text Query (Arama Metni Varsa)
    if q and q.strip():
        must_clauses.append({
            "multi_match": {
                "query": q.strip(),
                "fields": [
                    "product_name^3",
                    "brand^2",
                    "category",
                    "search_autocomplete"
                ],
                "fuzziness": "AUTO",
                "operator": "and"
            }
        })
    else:
        must_clauses.append({"match_all": {}})
        
    # 2. Dinamik Filtreler (Term & Range)
    if category:
        filter_clauses.append({"term": {"category.keyword": category}})
    if brand:
        filter_clauses.append({"term": {"brand.keyword": brand}})
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price
        filter_clauses.append({"range": {"price": price_range}})
        
    # 3. Sıralama (Sort)
    sort_config = []
    if sort_by == "price_asc":
        sort_config.append({"price": {"order": "asc"}})
    elif sort_by == "price_desc":
        sort_config.append({"price": {"order": "desc"}})
    elif sort_by == "units_sold":
        sort_config.append({"units_sold": {"order": "desc"}})
    else:
        sort_config.append({"_score": {"order": "desc"}})
        
    # 4. Aggregations (Filtreler / Facets)
    aggs_config = {
        "categories": {
            "terms": {"field": "category.keyword", "size": 10}
        },
        "brands": {
            "terms": {"field": "brand.keyword", "size": 10}
        },
        "price_ranges": {
            "range": {
                "field": "price",
                "ranges": [
                    {"to": 50.0, "key": "Ekonomik (< 50 $)"},
                    {"from": 50.0, "to": 100.0, "key": "Orta (50 - 100 $)"},
                    {"from": 100.0, "key": "Premium (> 100 $)"}
                ]
            }
        }
    }
    
    es_body = {
        "from": from_offset,
        "size": size,
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        },
        "sort": sort_config,
        "aggs": aggs_config,
        "highlight": {
            "fields": {
                "product_name": {},
                "brand": {}
            }
        }
    }
    
    try:
        resp = client.search(index=settings.PRODUCT_INDEX, body=es_body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arama yürütülürken hata: {str(e)}")
        
    hits_data = resp.get("hits", {})
    total_hits = hits_data.get("total", {}).get("value", 0)
    took_ms = resp.get("took", 0)
    
    products = []
    for hit in hits_data.get("hits", []):
        src = hit.get("_source", {})
        highlights = hit.get("highlight")
        products.append(ProductItem(
            product_id=src.get("product_id"),
            product_name=src.get("product_name"),
            brand=src.get("brand"),
            category=src.get("category"),
            price=src.get("price", 0.0),
            discount_percentage=src.get("discount_percentage", 0.0),
            currency=src.get("currency", "EUR"),
            in_stock=src.get("in_stock", True),
            units_sold=src.get("units_sold", 0),
            score=hit.get("_score"),
            highlights=highlights
        ))
        
    # Aggregations parse
    raw_aggs = resp.get("aggregations", {})
    facets = SearchFacets(
        categories=[FacetBucket(key=b["key"], doc_count=b["doc_count"]) for b in raw_aggs.get("categories", {}).get("buckets", [])],
        brands=[FacetBucket(key=b["key"], doc_count=b["doc_count"]) for b in raw_aggs.get("brands", {}).get("buckets", [])],
        price_ranges=[FacetBucket(key=b["key"], doc_count=b["doc_count"]) for b in raw_aggs.get("price_ranges", {}).get("buckets", [])]
    )
    
    return SearchResponse(
        query=q,
        page=page,
        size=size,
        total_hits=total_hits,
        took_ms=took_ms,
        products=products,
        facets=facets
    )
