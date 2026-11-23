#!/usr/bin/env python3
"""
03_aggregations_matplotlib_export.py
------------------------------------
Elasticsearch Aggregation sonuçlarını Python ile çekip
Matplotlib kullanarak yerel analitik grafikler (PNG) üreten otomasyon scripti.

Bu senaryo:
1. 'kibana_sample_data_ecommerce' index'ine bağlanır.
2. Kategori bazında sipariş adedi ve ciro toplamını (Terms + Sum Aggregations) çeker.
3. Çekilen analitik veriyi yerel dosya sistemine yüksek çözünürlüklü
   grafik olarak ('ecommerce_category_analytics.png') kaydeder.
4. Matplotlib yüklü değilse konsola formatlı ASCII tablosu basarak rehberlik eder.

Kullanım:
  pip install matplotlib pandas
  python3 03_aggregations_matplotlib_export.py
"""

import sys
from pathlib import Path
from es_client_helper import get_es_client

def fetch_category_analytics(es, index_name="kibana_sample_data_ecommerce"):
    """
    Elasticsearch Aggregations API kullanarak kategori bazlı ciro ve sipariş adedini çeker.
    """
    if not es.indices.exists(index=index_name):
        print(f"⚠️  UYARI: '{index_name}' index'i bulunamadı!")
        print("Lütfen önce sample veriyi yükleyin: Kibana > Try sample data > Sample eCommerce orders > Install data (LAB-04 Adım 1)")
        return None

    query = {
        "size": 0,
        "aggs": {
            "categories": {
                "terms": {
                    "field": "category.keyword",
                    "size": 6,
                    "order": {"total_revenue": "desc"}
                },
                "aggs": {
                    "total_revenue": {
                        "sum": {
                            "field": "taxful_total_price"
                        }
                    },
                    "avg_order_value": {
                        "avg": {
                            "field": "taxful_total_price"
                        }
                    }
                }
            }
        }
    }

    resp = es.search(index=index_name, body=query)
    buckets = resp.get("aggregations", {}).get("categories", {}).get("buckets", [])
    
    data = []
    for b in buckets:
        data.append({
            "category": b["key"],
            "doc_count": b["doc_count"],
            "revenue": round(b["total_revenue"]["value"], 2),
            "avg_order": round(b["avg_order_value"]["value"], 2)
        })
    return data

def render_chart_with_matplotlib(data, output_file="ecommerce_category_analytics.png"):
    """
    Matplotlib ile 2 panelli (Bar Chart & Donut Chart) görsel oluşturur ve kaydeder.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # Başsız (headless) sunucular ve CI/CD ortamları için GUI gerektirmez
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n⚠️  'matplotlib' kütüphanesi kurulu değil!")
        print("Grafik çıktısı oluşturmak için: 'pip install matplotlib'\n")
        print("📊 Konsol Tablo Çıktısı:")
        print(f"{'Kategori':<30} | {'Sipariş Adedi':<14} | {'Toplam Ciro ($)':<16} | {'Ort. Sepet ($)':<14}")
        print("-" * 80)
        for row in data:
            print(f"{row['category']:<30} | {row['doc_count']:<14} | ${row['revenue']:<15,.2f} | ${row['avg_order']:<13,.2f}")
        return False

    categories = [d["category"] for d in data]
    revenues = [d["revenue"] for d in data]
    counts = [d["doc_count"] for d in data]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#f8f9fa")

    # 1. Panel: Kategori Bazında Toplam Ciro (Horizontal Bar Chart)
    colors = ["#2b5c8f", "#3c78d8", "#6fa8dc", "#9fc5e8", "#cfe2f3", "#d9d2e9"]
    bars = ax1.barh(categories[::-1], revenues[::-1], color=colors[:len(categories)][::-1], edgecolor="#1b3a5b")
    ax1.set_title("Kategori Bazında Toplam Ciro ($)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Ciro ($)", fontsize=11)
    ax1.grid(axis="x", linestyle="--", alpha=0.6)

    # Barların üzerine değer yazdırma
    for bar in bars:
        width = bar.get_width()
        ax1.text(width + (max(revenues) * 0.01), bar.get_y() + bar.get_height() / 2,
                 f"${width:,.0f}", ha="left", va="center", fontsize=9, fontweight="semibold")

    # 2. Panel: Ciro Dağılımı (Donut Chart)
    ax2.pie(revenues, labels=categories, autopct="%1.1f%%", startangle=140,
            colors=colors[:len(categories)],
            wedgeprops={"edgecolor": "white", "linewidth": 2, "antialiased": True},
            pctdistance=0.75)
    centre_circle = plt.Circle((0, 0), 0.55, fc="#f8f9fa")
    ax2.add_artist(centre_circle)
    ax2.set_title("Ciro Payı Dağılımı", fontsize=13, fontweight="bold", pad=12)

    plt.suptitle("Elasticsearch Aggregations Analitik Raporu", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout()

    out_path = Path(__file__).resolve().parent / output_file
    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()

    print(f"\n🎉 Analitik grafik başarıyla üretildi: {out_path.name}")
    print(f"   Dosya Konumu: {out_path}")
    return True

def main():
    print("=" * 65)
    print("📈 Elasticsearch Aggregations -> Python & Matplotlib Analiz Aracı")
    print("=" * 65)

    es = get_es_client()
    data = fetch_category_analytics(es)
    if not data:
        sys.exit(1)

    print(f"\n✅ Elasticsearch üzerinden {len(data)} kategori verisi çekildi:")
    for d in data:
        print(f"  • {d['category']:<25} : ${d['revenue']:>10,.2f} ({d['doc_count']} sipariş)")

    render_chart_with_matplotlib(data)

if __name__ == "__main__":
    main()
