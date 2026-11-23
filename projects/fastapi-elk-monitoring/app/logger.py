import json
import logging
import socket
import sys
import threading
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class LogstashTCPHandler(logging.Handler):
    """
    Güvenilir TCP Socket Log Handler.
    Log kayıtlarını newline-delimited JSON (json_lines) olarak Logstash TCP portuna (örn: 5000) iletir.
    Logstash geçici olarak erişilemez olduğunda uygulamanın kilitlenmesini veya çökmesini engeller;
    arka planda yeniden bağlanmayı dener ve stdout'a fallback log düşer.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5000, timeout: float = 2.0):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self._lock = threading.Lock()

    def _connect(self) -> bool:
        if self.sock is not None:
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            self.sock = sock
            return True
        except Exception:
            self.sock = None
            return False

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            payload = (msg + "\n").encode("utf-8")

            with self._lock:
                sent = False
                for _ in range(2):  # İlk deneme başarısız olursa bir kez yeniden bağlanıp dene
                    if self._connect():
                        try:
                            assert self.sock is not None
                            self.sock.sendall(payload)
                            sent = True
                            break
                        except (socket.error, BrokenPipeError):
                            if self.sock:
                                try:
                                    self.sock.close()
                                except Exception:
                                    pass
                            self.sock = None
                if not sent:
                    # Logstash'e ulaşılamıyorsa stdout'a yaz
                    sys.stderr.write(f"[LOGSTASH-TCP-FAIL] {msg}\n")
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        with self._lock:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
        super().close()


class ECSJsonFormatter(logging.Formatter):
    """
    Elastic Common Schema (ECS) ve JSON Lines uyumlu log formatlayıcı.
    Kayıtları Elasticsearch ve Logstash'in doğrudan ayrıştırabileceği yapılandırılmış JSON nesnesine dönüştürür.
    """

    def __init__(self, service_name: str = "fastapi-order-service", environment: str = "production"):
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        # ISO8601 UTC timestamp
        now = datetime.now(timezone.utc).isoformat()

        log_data: Dict[str, Any] = {
            "timestamp": now,
            "log": {
                "level": record.levelname,
                "logger": record.name,
            },
            "message": record.getMessage(),
            "service": {
                "name": self.service_name,
                "environment": self.environment,
                "version": "1.0.0",
            },
            "process": {
                "pid": record.process,
                "thread_name": record.threadName,
            },
        }

        # HTTP Context alanları (ECS standardı: http.request.id, http.request.method, http.response.status_code)
        http_fields: Dict[str, Any] = {}
        req_id = getattr(record, "request_id", None)
        method = getattr(record, "method", None)
        if req_id or method:
            http_fields["request"] = {}
            if req_id:
                http_fields["request"]["id"] = req_id
            if method:
                http_fields["request"]["method"] = method

        status_code = getattr(record, "status_code", None)
        if status_code is not None:
            http_fields["response"] = {"status_code": status_code}
            # Geriye dönük sorgu kolaylığı için status_code üst seviyede de tutulabilir:
            http_fields["status_code"] = status_code

        for attr in ["route", "client_ip", "duration_ms"]:
            if hasattr(record, attr):
                http_fields[attr] = getattr(record, attr)
        if http_fields:
            log_data["http"] = http_fields

        # Hata ve Exception (Stack Trace) Detayları
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_data["error"] = {
                "class": exc_type.__name__ if exc_type else "Exception",
                "message": str(exc_value) if exc_value else "",
                "stack_trace": "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
            }
        elif hasattr(record, "error_details"):
            log_data["error"] = getattr(record, "error_details")

        # Extra context (Geliştiricinin logger.info(..., extra={...}) ile geçtiği alanlar)
        reserved_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "request_id", "method", "route",
            "status_code", "client_ip", "duration_ms", "error_details",
        }
        custom_extra = {}
        for key, val in record.__dict__.items():
            if key not in reserved_attrs and not key.startswith("_"):
                try:
                    # JSON serializable kontrolü
                    json.dumps(val)
                    custom_extra[key] = val
                except (TypeError, OverflowError):
                    custom_extra[key] = str(val)

        if custom_extra:
            log_data["custom"] = custom_extra

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    service_name: str = "fastapi-order-service",
    environment: str = "production",
    logstash_host: str = "127.0.0.1",
    logstash_port: int = 5000,
    log_level: str = "INFO",
) -> logging.Logger:
    """
    FastAPI uygulaması için hem Logstash TCP hem de Console (stdout) handler'larına sahip logger kurar.
    """
    logger = logging.getLogger("fastapi_app")
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Önceki handler'ları temizle
    logger.handlers.clear()

    formatter = ECSJsonFormatter(service_name=service_name, environment=environment)

    # 1. Console (Stdout) Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # 2. Logstash TCP Handler (Network logging)
    if logstash_host:
        tcp_handler = LogstashTCPHandler(host=logstash_host, port=logstash_port)
        tcp_handler.setFormatter(formatter)
        tcp_handler.setLevel(level)
        logger.addHandler(tcp_handler)

    # Root logger yayılımını engelle
    logger.propagate = False
    return logger
