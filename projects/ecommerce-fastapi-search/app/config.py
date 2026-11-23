import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Uygulama Konfigürasyonu
    - PORT: App1 slotu için 19001 varsayılan olarak belirlenmiştir.
    - HOST: 0.0.0.0 ile hem DNS (Nginx reverse proxy) hem de doğrudan PIP erişimi sağlanır.
    """
    APP_NAME: str = "NovaCommerce Search Engine API"
    APP_VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "19001"))
    
    # Elasticsearch Ayarları
    ELASTIC_URL: str = os.getenv("ELASTIC_URL", "http://localhost:9200")
    ELASTIC_USER: str = os.getenv("ELASTIC_USER", "elastic")
    ELASTIC_PASSWORD: str = os.getenv("ELASTIC_PASSWORD", "DevOps2026!")
    PRODUCT_INDEX: str = os.getenv("PRODUCT_INDEX", "ecommerce_search_products")
    
    # Reverse proxy alt yol desteği (/app1 altından çağrılırsa root_path='/app1')
    ROOT_PATH: str = os.getenv("ROOT_PATH", "")

settings = Settings()
