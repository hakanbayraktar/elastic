"""
NovaCommerce E-Ticaret Arama Servisi (FastAPI)
==============================================
Mimari: Kurumsal E-Ticaret Arama ve Alaka Düzeyi (Relevance) Servisi
Erişim Slotu: App1 (Port 19001)
DNS: https://studentXX-app1.devopsatolyesi.com
Doğrudan IP: http://<SUNUCU_PUBLIC_IP>:19001 veya http://<SUNUCU_PUBLIC_IP>/app1
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.es_client import get_elasticsearch_client, check_cluster_health
from app.schemas.search_models import HealthResponse
from app.routers import autocomplete, search, analytics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Başlangıçta ES bağlantısını test et
    logger.info("NovaCommerce Arama Servisi başlatılıyor...")
    try:
        client = get_elasticsearch_client()
        if client.ping():
            info = client.info()
            logger.info(f"✅ Elasticsearch bağlantısı başarılı! Sürüm: {info.get('version', {}).get('number')}")
        else:
            logger.warning(f"⚠️ Elasticsearch ping başarısız: {settings.ELASTIC_URL}")
    except Exception as e:
        logger.warning(f"⚠️ Elasticsearch bağlantı kontrolü sırasında uyarı: {e}")
    yield
    logger.info("NovaCommerce Arama Servisi kapatılıyor...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## 🛍️ NovaCommerce Elasticsearch 9.x Arama Motoru API
    
    Bu servis, büyük ölçekli modern e-ticaret arama mimarisini uygular:
    * **Search Bar & Autocomplete:** 4-Clause `bool.should` (Edge N-Gram + Term Boost + Phrase Slop).
    * **Katalog Arama:** Multi-Match, Boosting (`product_name^3`, `brand^2`), Fuzziness, Filtreler (Facets) ve Sıralama.
    * **ES|QL Analitik:** Elasticsearch 9.x boru hattı (`|`) tabanlı SQL analitiği.
    
    ### 🌐 Erişim Kanalları
    * **DNS (HTTPS):** `https://studentXX-app1.devopsatolyesi.com`
    * **Doğrudan IP (Yol):** `http://<SUNUCU_PUBLIC_IP>/app1`
    * **Doğrudan IP (Port):** `http://<SUNUCU_PUBLIC_IP>:19001`
    """,
    root_path=settings.ROOT_PATH,
    lifespan=lifespan
)

# CORS İzinleri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Entegrasyonları
app.include_router(autocomplete.router)
app.include_router(search.router)
app.include_router(analytics.router)

@app.get("/api/v1/health", response_model=HealthResponse, tags=["Sistem"])
def health_check():
    """Elasticsearch ve servis sağlık kontrolü."""
    client = get_elasticsearch_client()
    try:
        health = check_cluster_health()
        return HealthResponse(
            status="healthy" if health.get("status") in ["green", "yellow"] else "degraded",
            cluster_name=health.get("cluster_name", "unknown"),
            cluster_status=health.get("status", "unknown"),
            number_of_nodes=health.get("number_of_nodes", 1),
            app_version=settings.APP_VERSION
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            cluster_name="offline",
            cluster_status="red",
            number_of_nodes=0,
            app_version=settings.APP_VERSION
        )

@app.get("/", response_class=HTMLResponse, tags=["Sistem"])
def root_index():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{settings.APP_NAME}</title>
        <style>
            body {{ font-family: system-ui, sans-serif; background: #0b1120; color: #f8fafc; padding: 40px 20px; }}
            .card {{ max-width: 650px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; }}
            h1 {{ color: #38bdf8; font-size: 22px; margin-top: 0; }}
            p {{ color: #94a3b8; line-height: 1.5; }}
            .btn {{ display: inline-block; background: #0284c7; color: white; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 12px; }}
            .btn:hover {{ background: #0369a1; }}
            ul {{ color: #cbd5e1; line-height: 1.8; }}
            code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #38bdf8; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 {settings.APP_NAME} Hazır!</h1>
            <p>Bu servis, Elasticsearch 9.x üzerinde çalışan profesyonel bir e-ticaret arama mikroservisidir (App1 Port {settings.PORT}).</p>
            <ul>
                <li><strong>Autocomplete Uç Noktası:</strong> <code>GET /api/v1/search/autocomplete?q=cas</code></li>
                <li><strong>Katalog Arama Uç Noktası:</strong> <code>GET /api/v1/search?q=dress&category=Women's Clothing</code></li>
                <li><strong>ES|QL Analitik Uç Noktası:</strong> <code>GET /api/v1/analytics/top-categories</code></li>
            </ul>
            <a href="docs" class="btn">📖 İnteraktif Swagger Dokümantasyonunu Aç</a>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
