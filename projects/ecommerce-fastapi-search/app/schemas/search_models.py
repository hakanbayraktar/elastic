from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AutocompleteSuggestion(BaseModel):
    text: str = Field(..., description="Kullanıcıya gösterilecek tamamlanmış öneri metni")
    product_id: Optional[str] = Field(None, description="Eşleşen ürünün ID'si")
    score: float = Field(..., description="Elasticsearch BM25 + Boosting alaka skoru")

class AutocompleteResponse(BaseModel):
    query: str
    total_suggestions: int
    took_ms: int
    suggestions: List[AutocompleteSuggestion]

class ProductItem(BaseModel):
    product_id: str
    product_name: str
    brand: str
    category: str
    price: float
    discount_percentage: float = 0.0
    currency: str = "EUR"
    in_stock: bool = True
    units_sold: int = 0
    score: Optional[float] = None
    highlights: Optional[Dict[str, List[str]]] = None

class FacetBucket(BaseModel):
    key: str
    doc_count: int

class SearchFacets(BaseModel):
    categories: List[FacetBucket] = []
    brands: List[FacetBucket] = []
    price_ranges: List[FacetBucket] = []

class SearchResponse(BaseModel):
    query: Optional[str]
    page: int
    size: int
    total_hits: int
    took_ms: int
    products: List[ProductItem]
    facets: SearchFacets

class ESQLQueryResult(BaseModel):
    columns: List[str]
    values: List[List[Any]]
    total_rows: int
    took_ms: int

class HealthResponse(BaseModel):
    status: str
    cluster_name: str
    cluster_status: str
    number_of_nodes: int
    app_version: str
