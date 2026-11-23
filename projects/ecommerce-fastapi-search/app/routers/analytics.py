"""
Router: ES|QL ile E-Ticaret Analitiği
=====================================
Bu modül, Elasticsearch 8.11+ / 9.x ile gelen boru hattı (|) tabanlı
ES|QL sorgularını Python SDK üzerinden çalıştırır ve sonuçları tablo formatında sunar.
"""

from fastapi import APIRouter, HTTPException, Query
from app.es_client import get_elasticsearch_client
from app.schemas.search_models import ESQLQueryResult

router = APIRouter(prefix="/api/v1/analytics", tags=["ES|QL Analitik"])

@router.get("/top-categories", response_model=ESQLQueryResult)
def get_top_categories_analytics(
    min_price: float = Query(0.0, description="Dikkate alınacak taban fiyat")
):
    """
    ES|QL kullanarak kategori bazında ortalama fiyat, max fiyat ve ürün adetlerini hesaplar.
    """
    client = get_elasticsearch_client()
    query_str = f"""
        FROM ecommerce_search_products
        | WHERE price >= {min_price}
        | STATS count = COUNT(), avg_price = AVG(price), max_price = MAX(price) BY category
        | SORT avg_price DESC
        | LIMIT 10
    """
    try:
        resp = client.esql.query(query=query_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ES|QL sorgu hatası: {str(e)}")
        
    columns = [col["name"] for col in resp.get("columns", [])]
    values = resp.get("values", [])
    
    return ESQLQueryResult(
        columns=columns,
        values=values,
        total_rows=len(values),
        took_ms=resp.get("took", 0)
    )

@router.post("/custom-esql", response_model=ESQLQueryResult)
def execute_custom_esql(payload: dict):
    """
    Gelen serbest ES|QL sorgusunu Elasticsearch üzerinde çalıştırır.
    Örnek Payload: {"query": "FROM ecommerce_search_products | LIMIT 5"}
    """
    client = get_elasticsearch_client()
    query_str = payload.get("query")
    if not query_str:
        raise HTTPException(status_code=400, detail="'query' alanı zorunludur.")
        
    try:
        resp = client.esql.query(query=query_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ES|QL sorgu hatası: {str(e)}")
        
    columns = [col["name"] for col in resp.get("columns", [])]
    values = resp.get("values", [])
    
    return ESQLQueryResult(
        columns=columns,
        values=values,
        total_rows=len(values),
        took_ms=resp.get("took", 0)
    )
