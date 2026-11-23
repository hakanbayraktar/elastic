#!/usr/bin/env python3
"""
NovaCommerce: FastAPI Arama API Uç Noktaları Otomatik Test Scripti
-----------------------------------------------------------
Bu test scripti:
1. Servis sağlık durumunu (/api/v1/health)
2. 4-Clause Autocomplete sorgusunu (/api/v1/search/autocomplete?q=cas)
3. Katalog arama ve facet aggregations (/api/v1/search?q=shoes)
4. ES|QL analitik endpoint'ini (/api/v1/analytics/top-categories)
test ederek HTTP yanıt kodlarını ve dönen JSON verilerini doğrular.
"""

import sys
import json
import requests

BASE_URL = "http://localhost:19001"

def print_result(title, success, details):
    status = "✅ BAŞARILI" if success else "❌ BAŞARISIZ"
    print(f"\n[{status}] {title}")
    print("-" * 50)
    print(details)

def main():
    print("=" * 60)
    print("🧪 NovaCommerce: NovaCommerce FastAPI Arama API Testleri Başlatılıyor...")
    print(f"   Hedef Uç Nokta: {BASE_URL}")
    print("=" * 60)
    
    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        success = r.status_code == 200 and r.json().get("status") == "healthy"
        print_result("1. Sağlık Kontrolü (/api/v1/health)", success, json.dumps(r.json(), indent=2))
        if not success:
            sys.exit(1)
    except Exception as e:
        print_result("1. Sağlık Kontrolü (/api/v1/health)", False, f"Bağlantı hatası: {e}")
        print("\n⚠️ Lütfen önce servisi './run-search-api.sh' ile başlattığınızdan emin olun!")
        sys.exit(1)
        
    # 2. Autocomplete (Ön ek 'cas')
    try:
        r = requests.get(f"{BASE_URL}/api/v1/search/autocomplete?q=cas&limit=5", timeout=5)
        data = r.json()
        success = r.status_code == 200 and len(data.get("suggestions", [])) > 0
        details = f"Sorgu: 'cas' | Toplam Öneri: {data.get('total_suggestions')} | Süre: {data.get('took_ms')}ms\n"
        for i, s in enumerate(data.get("suggestions", []), 1):
            details += f"  {i}. {s['text']} (Skor: {s['score']})\n"
        print_result("2. 4-Clause Autocomplete (/api/v1/search/autocomplete)", success, details.strip())
    except Exception as e:
        print_result("2. Autocomplete", False, str(e))

    # 3. Katalog Arama ve Facets ('dress')
    try:
        r = requests.get(f"{BASE_URL}/api/v1/search?q=dress&page=1&size=5", timeout=5)
        data = r.json()
        success = r.status_code == 200 and data.get("total_hits", 0) > 0
        details = f"Sorgu: 'dress' | Eşleşen Ürün: {data.get('total_hits')} | Süre: {data.get('took_ms')}ms\n"
        details += "Kategori Facets:\n"
        for cat in data.get("facets", {}).get("categories", []):
            details += f"  - {cat['key']}: {cat['doc_count']} adet\n"
        details += "Örnek İlk Ürün:\n"
        if data.get("products"):
            p0 = data["products"][0]
            details += f"  Ad: {p0['product_name']} | Marka: {p0['brand']} | Fiyat: {p0['price']} {p0['currency']} | Skor: {p0['score']}"
        print_result("3. Katalog Arama & Facets (/api/v1/search)", success, details.strip())
    except Exception as e:
        print_result("3. Katalog Arama", False, str(e))

    # 4. ES|QL Analitik
    try:
        r = requests.get(f"{BASE_URL}/api/v1/analytics/top-categories", timeout=5)
        data = r.json()
        success = r.status_code == 200 and len(data.get("values", [])) > 0
        details = f"Kolonlar: {', '.join(data.get('columns', []))}\n"
        details += "Veriler (İlk 3):\n"
        for row in data.get("values", [])[:3]:
            details += f"  {row}\n"
        print_result("4. ES|QL Kategori Analitiği (/api/v1/analytics/top-categories)", success, details.strip())
    except Exception as e:
        print_result("4. ES|QL Analitiği", False, str(e))

    print("\n" + "=" * 60)
    print("🎉 Tüm Temel API Testleri Tamamlandı!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
