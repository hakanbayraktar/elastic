import os
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from logger import setup_logger

# ------------------------------------------------------------------------------
# Ortam Değişkenleri & Konfigürasyon
# ------------------------------------------------------------------------------
SERVICE_NAME = os.getenv("SERVICE_NAME", "fastapi-order-service")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
LOGSTASH_HOST = os.getenv("LOGSTASH_HOST", "logstash-app2")
LOGSTASH_PORT = int(os.getenv("LOGSTASH_PORT", "5000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Logger Kurulumu
logger = setup_logger(
    service_name=SERVICE_NAME,
    environment=ENVIRONMENT,
    logstash_host=LOGSTASH_HOST,
    logstash_port=LOGSTASH_PORT,
    log_level=LOG_LEVEL,
)

# ------------------------------------------------------------------------------
# Özel İstisna (Exception) Sınıfları
# ------------------------------------------------------------------------------
class PaymentGatewayTimeoutException(Exception):
    """Ödeme ağ geçidinden zaman aşımı (Timeout) alındığında fırlatılır."""
    pass


class DatabaseDeadlockException(Exception):
    """Veritabanı transaction çakışması ve deadlock durumunda fırlatılır."""
    pass


# ------------------------------------------------------------------------------
# Pydantic Veri Modelleri
# ------------------------------------------------------------------------------
class OrderItem(BaseModel):
    item_id: str
    item_name: str
    quantity: int = Field(gt=0, description="Ürün adedi 0'dan büyük olmalıdır")
    unit_price: float = Field(gt=0, description="Birim fiyat 0'dan büyük olmalıdır")


class CreateOrderRequest(BaseModel):
    user_id: str
    items: List[OrderItem]
    currency: str = "TRY"


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    payment_method: str = "CREDIT_CARD"
    gateway: str = "stripe_mock"  # "timeout_gateway" verilirse kasıtlı 500 fırlatılır


# ------------------------------------------------------------------------------
# FastAPI Uygulaması
# ------------------------------------------------------------------------------
app = FastAPI(
    title="FastAPI ELK Observability & Error Monitoring Service",
    description="FastAPI, Logstash TCP Socket ve Elasticsearch entegrasyonu ile merkezi hata izleme servisi.",
    version="1.0.0",
)

# Bellek içi sahte veri tabanı
ORDERS_DB: Dict[str, Dict[str, Any]] = {
    "ord-1001": {
        "order_id": "ord-1001",
        "user_id": "usr-882",
        "total_amount": 1450.50,
        "status": "COMPLETED",
        "currency": "TRY",
    },
    "ord-1002": {
        "order_id": "ord-1002",
        "user_id": "usr-914",
        "total_amount": 320.00,
        "status": "PROCESSING",
        "currency": "TRY",
    },
}


# ------------------------------------------------------------------------------
# Middleware: Request ID ve HTTP İsteği Loglama
# ------------------------------------------------------------------------------
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Correlation ID (X-Request-ID) kontrolü veya üretimi
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    try:
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # HTTP İstek Kaydı (2xx ve 3xx için INFO, 4xx için WARNING)
        status_code = response.status_code
        log_level = logger.info if status_code < 400 else logger.warning

        extra_data = {
            "request_id": request_id,
            "method": request.method,
            "route": request.url.path,
            "status_code": status_code,
            "client_ip": client_ip,
            "duration_ms": duration_ms,
        }

        log_level(
            f"HTTP {request.method} {request.url.path} -> {status_code} ({duration_ms}ms)",
            extra=extra_data,
        )
        return response

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # 500 Uncaught Exception durumu: stack trace ile birlikte ERROR seviyesinde loglanır
        extra_data = {
            "request_id": request_id,
            "method": request.method,
            "route": request.url.path,
            "status_code": 500,
            "client_ip": client_ip,
            "duration_ms": duration_ms,
        }

        logger.error(
            f"Unhandled exception during HTTP {request.method} {request.url.path}: {str(exc)}",
            exc_info=True,
            extra=extra_data,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "request_id": request_id,
                "path": request.url.path,
            },
            headers={"X-Request-ID": request_id},
        )


# ------------------------------------------------------------------------------
# API Endpoint'leri
# ------------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": SERVICE_NAME,
        "environment": ENVIRONMENT,
        "version": "1.0.0",
        "description": "FastAPI + Logstash TCP + Elasticsearch Error Monitoring Lab",
        "endpoints": {
            "health": "GET /api/v1/health",
            "create_order": "POST /api/v1/orders",
            "get_order": "GET /api/v1/orders/{order_id}",
            "payment_checkout": "POST /api/v1/checkout/payment",
            "calculate_discount": "GET /api/v1/calculate/discount?price=100&ratio=0",
            "database_deadlock": "GET /api/v1/database/deadlock",
        },
    }


@app.get("/api/v1/health")
def health_check(request: Request):
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "environment": ENVIRONMENT,
        "logstash_target": f"{LOGSTASH_HOST}:{LOGSTASH_PORT}",
        "request_id": getattr(request.state, "request_id", None),
    }


@app.post("/api/v1/orders", status_code=201)
def create_order(order: CreateOrderRequest, request: Request):
    total = sum(item.quantity * item.unit_price for item in order.items)
    new_id = f"ord-{uuid.uuid4().hex[:6]}"

    record = {
        "order_id": new_id,
        "user_id": order.user_id,
        "total_amount": total,
        "currency": order.currency,
        "status": "CREATED",
        "item_count": len(order.items),
    }
    ORDERS_DB[new_id] = record

    logger.info(
        f"Order {new_id} successfully placed by {order.user_id} with total {total} {order.currency}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "order_id": new_id,
            "user_id": order.user_id,
            "total_amount": total,
        },
    )

    return record


@app.get("/api/v1/orders/{order_id}")
def get_order(order_id: str, request: Request):
    if order_id not in ORDERS_DB:
        logger.warning(
            f"Order not found: {order_id}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "order_id": order_id,
            },
        )
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' was not found in the database")

    return ORDERS_DB[order_id]


# ------------------------------------------------------------------------------
# Hata Simülasyonu Endpoint'leri (500 Error Triggers for ELK Monitoring)
# ------------------------------------------------------------------------------
@app.post("/api/v1/checkout/payment")
def process_payment(payment: PaymentRequest, request: Request):
    """
    Ödeme gateway simülasyonu.
    gateway='timeout_gateway' ise kasıtlı PaymentGatewayTimeoutException fırlatılır.
    """
    if payment.gateway in ["timeout_gateway", "mock_timeout"]:
        time.sleep(0.1)  # Simüle edilmiş ağ gecikmesi
        raise PaymentGatewayTimeoutException(
            f"External Payment Provider [{payment.gateway}] timed out after 5000ms while processing order {payment.order_id}"
        )

    logger.info(
        f"Payment of {payment.amount} processed for order {payment.order_id} via {payment.gateway}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "order_id": payment.order_id,
            "amount": payment.amount,
            "gateway": payment.gateway,
        },
    )
    return {
        "status": "PAYMENT_SUCCESS",
        "order_id": payment.order_id,
        "transaction_id": f"txn-{uuid.uuid4().hex[:8]}",
    }


@app.get("/api/v1/calculate/discount")
def calculate_discount(price: float, ratio: float, request: Request):
    """
    Kasıtlı ZeroDivisionError simülasyonu (ratio=0 verildiğinde).
    """
    if ratio == 0:
        # Doğrudan Python çalışma zamanı hatası ve stack trace üretir
        return 100 / ratio

    discounted = price - (price * ratio)
    return {"original_price": price, "discount_ratio": ratio, "final_price": discounted}


@app.get("/api/v1/database/deadlock")
def simulate_deadlock(request: Request):
    """
    Veritabanı deadlock hatası simülasyonu.
    """
    raise DatabaseDeadlockException(
        "Transaction (Process ID 74) was deadlocked on lock resources with another process (ID 91) "
        "and has been chosen as the deadlock victim. Rerun the transaction."
    )
