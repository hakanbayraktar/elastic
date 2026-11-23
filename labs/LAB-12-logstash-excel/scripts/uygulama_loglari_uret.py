"""uygulama-loglari.csv: bir Spring Boot uygulamasinin 2024 subat-mart loglari (sabit tohum, 2000 satir)."""
import csv, random, string, sys
from datetime import datetime, timedelta
rng = random.Random(8)
LOGGER = ["com.example.Controller", "com.example.Service", "com.example.Tasks", "com.example.Utils", "com.example.Repository"]
MESAJ = {"INFO": ["User logged in", "User logged out", "Order created", "Payment received"],
         "DEBUG": ["Performing database query", "Cache lookup", "Sending email notification"],
         "WARN": ["Potential performance issue detected", "Retrying request"],
         "ERROR": ["Database connection timeout", "Payment gateway error"]}
bas = datetime(2024, 2, 26)
w = csv.writer(sys.stdout, lineterminator="\n")
w.writerow(["event_date", "log_level", "logger", "thread_id", "user_id", "request_id", "message"])
satir = []
for _ in range(2000):
    t = bas + timedelta(seconds=rng.randrange(7 * 86400))
    lv = rng.choices(["INFO", "DEBUG", "WARN", "ERROR"], [50, 30, 14, 6])[0]
    satir.append([t.strftime("%Y-%m-%d %H:%M:%S"), lv, rng.choice(LOGGER), rng.randrange(1000, 9999),
                  rng.randrange(100, 999), "".join(rng.choices(string.ascii_lowercase, k=8)), rng.choice(MESAJ[lv])])
for s in sorted(satir):
    w.writerow(s)
