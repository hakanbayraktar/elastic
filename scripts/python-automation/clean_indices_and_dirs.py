#!/usr/bin/env python3
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Exact phrase or regex replacements
REPLACEMENTS = [
    # Ambiguous "Bu dizin" when referring to directory / folder
    (r"\bBu dizin,", "Bu klasör,"),
    (r"\bBu dizin;", "Bu klasör;"),
    (r"## 📂 Klasör Yapısı", "## 📂 Klasör Yapısı"),
    (r"Çalışma Klasörüne Geçiş", "Çalışma Klasörüne Geçiş"),
    (r"çalışma klasörüne geçin", "çalışma klasörüne geçin"),
    (r"çalışma klasörü:", "çalışma klasörü:"),
    (r"Çalışma klasörü:", "Çalışma klasörü:"),
    (r"Herhangi bir klasördeyken", "Herhangi bir klasördeyken"),
    (r"lab klasöründeki", "lab klasöründeki"),
    (r"Klasör ve Rehber", "Klasör ve Rehber"),
    (r"`dev-tools/` klasörü", "`dev-tools/` klasörü"),
    (r"klasörü oluşturup", "klasörü oluşturup"),
    (r"klasörüne bakan", "klasörüne bakan"),
    (r"disk klasörüne", "disk klasörüne"),
    (r"klasör haritası:", "klasör haritası:"),

    # Index inflections -> index
    (r"[iİ]ndeksimizi", "index'imizi"),
    (r"[iİ]ndeksimiz", "index'imiz"),
    (r"[iİ]ndekslerdeki", "index'lerdeki"),
    (r"[iİ]ndekslerden", "index'lerden"),
    (r"[iİ]ndekslerde", "index'lerde"),
    (r"[iİ]ndekslere", "index'lere"),
    (r"[iİ]ndekslerin", "index'lerin"),
    (r"[iİ]ndeksleri", "index'leri"),
    (r"[iİ]ndeksler", "index'ler"),
    (r"[iİ]ndeksindeki", "index'indeki"),
    (r"[iİ]ndeksinden", "index'inden"),
    (r"[iİ]ndeksinde", "index'inde"),
    (r"[iİ]ndeksine", "index'ine"),
    (r"[iİ]ndeksinin", "index'inin"),
    (r"[iİ]ndeksini", "index'ini"),
    (r"[iİ]ndeksin", "index'in"),
    (r"[iİ]ndeksteki", "index'teki"),
    (r"[iİ]ndeksten", "index'ten"),
    (r"[iİ]ndekste", "index'te"),
    (r"[iİ]ndekse", "index'e"),
    (r"[iİ]ndeksi", "index'i"),
    (r"[iİ]ndekslendiğinde", "indexlendiğinde"),
    (r"[iİ]ndekslendiği", "indexlendiği"),
    (r"[iİ]ndekslendi", "indexlendi"),
    (r"[iİ]ndekslenirken", "indexlenirken"),
    (r"[iİ]ndekslenir", "indexlenir"),
    (r"[iİ]ndekslenen", "indexlenen"),
    (r"[iİ]ndekslenmesini", "indexlenmesini"),
    (r"[iİ]ndekslenmesine", "indexlenmesine"),
    (r"[iİ]ndekslenmesi", "indexlenmesi"),
    (r"[iİ]ndekslenmeden", "indexlenmeden"),
    (r"[iİ]ndekslenmez", "indexlenmez"),
    (r"[iİ]ndekslenmeyebilir", "indexlenmeyebilir"),
    (r"[iİ]ndekslenmek", "indexlenmek"),
    (r"[iİ]ndeksleme", "indexleme"),
    (r"[iİ]ndekslemek", "indexlemek"),
    (r"[iİ]ndeksleyelim", "indexleyelim"),
    (r"[iİ]ndeksleyin", "indexleyin"),
    (r"[iİ]ndeksleyecek", "indexleyecek"),
    (r"[iİ]ndekserken", "indexlerken"),
    (r"[iİ]ndeksle\b", "index'le"),
    (r"\bİndeks\b", "Index"),
    (r"\bIndeks\b", "Index"),
    (r"\bindeks\b", "index"),

    # Remaining cluster inflections -> cluster
    (r"cluster'ınızın", "cluster'ınızın"),
    (r"cluster'ınız", "cluster'ınız"),
    (r"cluster'lara", "cluster'lara"),
    (r"cluster'lar", "cluster'lar"),
    (r"cluster'ına", "cluster'ına"),
    (r"cluster'ında", "cluster'ında"),
    (r"cluster'ının", "cluster'ının"),
    (r"cluster'ını", "cluster'ını"),
    (r"cluster'ı", "cluster'ı"),
    (r"cluster'da", "cluster'da"),
    (r"cluster'dan", "cluster'dan"),
    (r"cluster'ın", "cluster'ın"),
    (r"cluster'a", "cluster'a"),
    (r"cluster\b", "cluster"),
    (r"Cluster\b", "Cluster"),
]

TARGET_EXTENSIONS = ('.md', '.http', '.sh', '.py', '.yml', '.yaml', '.conf', '.json')

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    for pattern, repl in REPLACEMENTS:
        new_content = re.sub(pattern, repl, new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    changed_count = 0
    for folder in ['labs', 'projects', 'docs', 'scripts']:
        folder_path = os.path.join(ROOT, folder)
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules', '.venv')]
            for file in files:
                if file.endswith(TARGET_EXTENSIONS):
                    p = os.path.join(root, file)
                    if clean_file(p):
                        changed_count += 1
                        print(f"Güncellendi: {os.path.relpath(p, ROOT)}")
    
    root_readme = os.path.join(ROOT, "README.md")
    if clean_file(root_readme):
        changed_count += 1
        print("Güncellendi: README.md")

    print(f"\nToplam {changed_count} dosyada index / klasör / cluster temizliği yapıldı.")

if __name__ == '__main__':
    main()
