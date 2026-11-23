# Demo API: /api/pay 200, /api/fail 500 doner; her istekte stdout'a tek satir JSON log yazar.
import json, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, level = (200, "info") if self.path == "/api/pay" else (500, "error")
        if self.path not in ("/api/pay", "/api/fail"):
            status, level = 404, "warn"
        print(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "level": level,
                          "service": "payment-api", "path": self.path, "http_status": status}),
              flush=True)
        self.send_response(status)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):  # varsayilan stderr erisim logunu kapat; tek satir JSON yeter
        pass


HTTPServer(("0.0.0.0", 3000), Handler).serve_forever()
