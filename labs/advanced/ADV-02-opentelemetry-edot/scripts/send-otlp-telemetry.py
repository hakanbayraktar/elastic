#!/usr/bin/env python3
"""OTLP/HTTP ile EDOT Collector'a (127.0.0.1:4318) sipariş başına bir trace, bir log ve bir metrik gönderir.

Her trace iki servisten geçer: checkout-service kök span'i (POST /siparis) payment-service'i çağırır (alt span,
parentSpanId ile bağlı). Log kaydı checkout span'inin trace.id/span.id'sini taşır. Kimlikler sipariş numarasından
türetilir (tekrarlanabilir); zaman damgaları gönderim anıdır. Bütün sinyaller data_stream.namespace=otellab ile
gider, böylece bu labın data stream'leri *-otellab adını alır. 5. sipariş ödeme hatasıyla biter.
Yalnız standart kütüphane kullanır.
"""
import hashlib
import json
import time
import urllib.request

COLLECTOR = "http://127.0.0.1:4318"
NAMESPACE = [{"key": "data_stream.namespace", "value": {"stringValue": "otellab"}}]


def kimlik(metin, uzunluk):
    return hashlib.sha256(metin.encode()).hexdigest()[:uzunluk]


def kaynak(servis):
    return {"attributes": [{"key": "service.name", "value": {"stringValue": servis}}] + NAMESPACE}


def gonder(yol, govde):
    istek = urllib.request.Request(f"{COLLECTOR}/{yol}", data=json.dumps(govde).encode(),
                                   headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(istek, timeout=5) as cevap:
        return cevap.status


def span(trace, sid, parent, ad, basla, ms, durum):
    return {"traceId": trace, "spanId": sid, "parentSpanId": parent, "name": ad, "kind": 2,
            "startTimeUnixNano": str(basla), "endTimeUnixNano": str(basla + ms * 1_000_000), "status": durum}


def siparis(no):
    trace = kimlik(f"siparis-{no}", 32)
    kok, odeme = kimlik(f"checkout-{no}", 16), kimlik(f"payment-{no}", 16)
    basla = time.time_ns()
    hata = no == 5
    odeme_ms = 900 if hata else 120
    durum = {"code": 2, "message": "kart reddedildi"} if hata else {"code": 1}
    izler = {"resourceSpans": [
        {"resource": kaynak("checkout-service"), "scopeSpans": [{"scope": {"name": "adv05"},
            "spans": [span(trace, kok, "", "POST /siparis", basla, odeme_ms + 30, durum)]}]},
        {"resource": kaynak("payment-service"), "scopeSpans": [{"scope": {"name": "adv05"},
            "spans": [span(trace, odeme, kok, "POST /odeme", basla + 10_000_000, odeme_ms, durum)]}]}]}
    loglar = {"resourceLogs": [{"resource": kaynak("checkout-service"), "scopeLogs": [{"scope": {"name": "adv05"},
        "logRecords": [{"timeUnixNano": str(basla), "severityText": "ERROR" if hata else "INFO",
                        "body": {"stringValue": f"siparis {no} " + ("odeme reddedildi" if hata else "onaylandi")},
                        "traceId": trace, "spanId": kok}]}]}]}
    metrik = {"resourceMetrics": [{"resource": kaynak("checkout-service"), "scopeMetrics": [{"scope": {"name": "adv05"},
        "metrics": [{"name": "siparis.tutar", "unit": "TRY", "gauge": {"dataPoints": [
            {"timeUnixNano": str(basla), "asDouble": 100.0 * no}]}}]}]}]}
    kodlar = [gonder("v1/traces", izler), gonder("v1/logs", loglar), gonder("v1/metrics", metrik)]
    print(f"siparis {no}  trace {trace}  {'HATA' if hata else 'ok  '}  HTTP {kodlar}")


if __name__ == "__main__":
    for n in range(1, 6):
        siparis(n)
