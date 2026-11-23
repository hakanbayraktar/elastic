#!/usr/bin/env python3
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Targeted replacement pairs
REPLACEMENTS = [
    # Index -> Index (Root replacement)
    (r"\bİndeks", "Index"),
    (r"\bIndeks", "Index"),
    (r"\bindeks", "index"),

    # Cluster -> Cluster (Inflected forms)
    (r"\bcluster'ınızın\b", "cluster'ınızın"),
    (r"\bcluster'ınız\b", "cluster'ınız"),
    (r"\bcluster'lardeki\b", "cluster'lardaki"),
    (r"\bcluster'larde\b", "cluster'larda"),
    (r"\bcluster'larin\b", "cluster'ların"),
    (r"\bcluster'lari\b", "cluster'ları"),
    (r"\bcluster'lar\b", "cluster'lar"),
    (r"\bcluster'ındaki\b", "cluster'ındaki"),
    (r"\bcluster'ında\b", "cluster'ında"),
    (r"\bcluster'ına\b", "cluster'ına"),
    (r"\bcluster'ının\b", "cluster'ının"),
    (r"\bcluster'ını\b", "cluster'ını"),
    (r"\bcluster'ı\b", "cluster'ı"),
    (r"\bcluster'daki\b", "cluster'daki"),
    (r"\bcluster'da\b", "cluster'da"),
    (r"\bcluster'a\b", "cluster'a"),
    (r"\bcluster'ın\b", "cluster'ın"),
    (r"\bcluster\b", "cluster"),
    (r"\bCluster\b", "Cluster"),
    (r"\bdüğümleri\b", "node'ları"),
    (r"\bdüğüm\b", "node"),

    # Ters dizin -> Inverted Index
    (r"ters dizin \(inverted index / BM25\)", "Inverted Index (BM25)"),
    (r"ters dizindeki \(inverted index\)", "Inverted Index'teki"),
    (r"ters dizindeki", "Inverted Index'teki"),
    (r"ters dizinde", "Inverted Index'te"),
    (r"ters dizini", "Inverted Index'i"),
    (r"ters dizinin", "Inverted Index'in"),
    (r"ters dizin", "Inverted Index"),
    (r"Ters dizin", "Inverted Index"),
    (r"Ters Dizin", "Inverted Index"),

    # Sınıf/Eğitim kelimeleri -> Profesyonel terimler
    (r"Her öğrenci için", "Her kullanıcı için"),
    (r"öğrenci numaranızı", "kullanıcı numaranızı"),
    (r"öğrenci demo lab", "kullanıcı demo lab"),
    (r"öğrenci", "kullanıcı"),
    (r"Öğrenci", "Kullanıcı"),
    (r"eğitim hostu", "çalışma sunucusu"),
]

TARGET_EXTENSIONS = ('.md', '.http', '.sh', '.py', '.yml', '.yaml', '.conf')

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
    for folder in ['labs', 'projects', 'docs']:
        folder_path = os.path.join(ROOT, folder)
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules', '.venv')]
            for file in files:
                if file.endswith(TARGET_EXTENSIONS):
                    p = os.path.join(root, file)
                    if clean_file(p):
                        changed_count += 1
                        print(f"Temizlendi: {os.path.relpath(p, ROOT)}")
    
    # Root README.md
    root_readme = os.path.join(ROOT, "README.md")
    if clean_file(root_readme):
        changed_count += 1
        print(f"Temizlendi: README.md")

    print(f"\nToplam {changed_count} dosyada terminoloji standardizasyonu tamamlandı.")

if __name__ == '__main__':
    main()
