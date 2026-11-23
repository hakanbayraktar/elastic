#!/usr/bin/env python3
"""
NovaShop E-Commerce Dashboard - Annotation Events Seeder
Creates 'novashop-events' index with DevOps deployments and marketing campaigns,
and registers 'novashop-events*' Data View in Kibana.
"""
import base64
import json
import os
import ssl
import sys
import time
from urllib import error, request

ES_URL = os.environ.get("ELASTICSEARCH_URL", os.environ.get("ELASTIC_URL", "http://127.0.0.1:9200")).rstrip("/")
KB_URL = os.environ.get("KIBANA_URL", "http://127.0.0.1:5601").rstrip("/")
USER = os.environ.get("ELASTIC_USER", "elastic")
PASSWORD = os.environ.get("ELASTIC_PASSWORD", "DevOps2026!")

AUTH_HEADER = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
HEADERS_ES = {"Content-Type": "application/json", "Authorization": AUTH_HEADER}
HEADERS_KB = {"Content-Type": "application/json", "Authorization": AUTH_HEADER, "kbn-xsrf": "novashop-annotations"}
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE


def call_es(path, method="GET", body=None):
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(ES_URL + path, data=payload, headers=HEADERS_ES, method=method)
    try:
        with request.urlopen(req, context=CONTEXT, timeout=30) as resp:
            data = resp.read()
            return resp.status, json.loads(data) if data else {}
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(details)
        except Exception:
            return exc.code, {"error": details}


def call_kb(path, method="GET", body=None):
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(KB_URL + path, data=payload, headers=HEADERS_KB, method=method)
    try:
        with request.urlopen(req, context=CONTEXT, timeout=30) as resp:
            data = resp.read()
            return resp.status, json.loads(data) if data else {}
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(details)
        except Exception:
            return exc.code, {"error": details}


def main():
    print(f"Connecting to Elasticsearch ({ES_URL}) and Kibana ({KB_URL}) ...")

    # 1. Create novashop-events Index with Explicit Mapping
    index_name = "novashop-events"
    mapping = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},  # tek node: replica 0
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "event": {
                    "properties": {
                        "action": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "description": {"type": "text"}
                    }
                },
                "author": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "severity": {"type": "keyword"}
            }
        }
    }

    # Delete index if exists to ensure clean state
    call_es(f"/{index_name}", "DELETE")
    status, res = call_es(f"/{index_name}", "PUT", mapping)
    print(f"✓ '{index_name}' indexi oluşturuldu.")

    # 2. Seed High-Impact Real-World Events (Deployments, Outages, Flash Sales)
    # Timestamps are aligned with the sales trend timeline (2026-10 to 2026-11)
    events = [
        {
            "@timestamp": "2026-11-02T10:00:00Z",
            "event": {
                "action": "NovaShop v2.4.0 Release Deployed",
                "category": "deployment",
                "description": "Yeni mikroservis mimarisi ve hızlı Elasticsearch 9 arama motoru yayına alındı."
            },
            "author": "sre-team@novashop.com",
            "environment": "production",
            "severity": "info"
        },
        {
            "@timestamp": "2026-11-06T14:30:00Z",
            "event": {
                "action": "Flash Sale %40 İndirim Kampanyası Başlatıldı",
                "category": "marketing",
                "description": "Tüm elektronik ve giyim kategorisinde 24 saatlik indirim kuponları aktif edildi."
            },
            "author": "growth@novashop.com",
            "environment": "production",
            "severity": "notice"
        },
        {
            "@timestamp": "2026-11-10T02:15:00Z",
            "event": {
                "action": "Ödeme Ağ Geçidi (Payment Gateway) Kesintisi ve Çözümü",
                "category": "incident",
                "description": "Banka sanal POS entegrasyonunda 12 dakikalık timeout yaşandı, yedek gateway devreye alındı."
            },
            "author": "oncall-devops@novashop.com",
            "environment": "production",
            "severity": "warning"
        },
        {
            "@timestamp": "2026-11-18T09:00:00Z",
            "event": {
                "action": "Black Friday Erken Erişim Kampanyası",
                "category": "marketing",
                "description": "Sadakat kulübü üyelerine özel erken erişim indirimleri açıldı."
            },
            "author": "marketing@novashop.com",
            "environment": "production",
            "severity": "notice"
        }
    ]

    for i, ev in enumerate(events, start=1):
        call_es(f"/{index_name}/_doc/{i}?refresh=true", "PUT", ev)
    print(f"✓ {len(events)} adet kritik olay (Deployment, Campaign, Incident) başarıyla kaydedildi.")

    # 3. Create or Update Kibana Data View
    dv_id = "novashop-events-dataview"
    dv_name = "NovaShop Event Annotations (Deployments & Campaigns)"
    spec = {"title": "novashop-events*", "name": dv_name, "timeFieldName": "@timestamp"}

    # Guncelleme ucu (POST .../data_view/<id>) data view yoksa 404 doner ve
    # govdesinde 'id' kabul etmez. Once varligini sorup olusturma ile
    # guncellemeyi ayirmak gerekiyor; aksi halde temiz bir sistemde data view
    # hic olusmadigi halde script basarili gorunuyordu.
    status, _ = call_kb(f"/api/data_views/data_view/{dv_id}")
    if status == 404:
        status, dv_res = call_kb("/api/data_views/data_view", "POST",
                                 {"data_view": {"id": dv_id, **spec}})
        action = "oluşturuldu"
    else:
        status, dv_res = call_kb(f"/api/data_views/data_view/{dv_id}", "POST",
                                 {"data_view": spec, "refresh_fields": True})
        action = "güncellendi"
    if status not in (200, 201):
        raise RuntimeError(f"Kibana Data View '{dv_id}' hazırlanamadı: HTTP {status}: {dv_res}")
    print(f"✓ Kibana Data View '{dv_name}' {action}.")

    print("\n" + "=" * 65)
    print(" 🎉 ANNOTATION EVENTS KURULUMU TAMAMLANDI!")
    print("=" * 65)
    print("Kibana Dashboard'da Dikey Olay Çizgilerini Görmek İçin:")
    print("1. 'Analytics ➔ Dashboards' altından 'NovaShop E-Commerce' panosunu açın.")
    print("2. 'Edit' butonuna tıklayın.")
    print("3. Üstteki 'Options' (veya 'Annotations') menüsünden 'Add annotation group' seçin:")
    print("   - Data View: 'NovaShop Event Annotations (Deployments & Campaigns)'")
    print("   - Time field: '@timestamp'")
    print("   - Tooltip field: 'event.action'")
    print("4. Kaydedin. Satış trendi grafiğinde deploy ve indirim anlarının")
    print("   dikey bayraklarla tam olay anında nasıl belirdiğini inceleyin!")
    print("=" * 65)


if __name__ == "__main__":
    main()
