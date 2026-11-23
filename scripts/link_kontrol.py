#!/usr/bin/env python3
"""Repodaki markdown dosyalarinda goreli linkleri ve gorselleri kontrol eder.

Kullanim (repo kokunden):  python3 scripts/link_kontrol.py
Cikis kodu: kirik link yoksa 0. AGENTS.md icindeki ornek sablonlar (LAB-XX, <dosya>) sayilmaz.
"""
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r'\]\(([^)#\s]+)(#[^)]*)?\)')
bad = []
# Yalniz repodaki (git'te izlenen) dosyalar; kullanicinin yerel taslaklari sayilmaz.
TRACKED = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True).stdout.split()
for md in sorted(ROOT / f for f in TRACKED):
    for m in LINK.finditer(md.read_text(errors="ignore")):
        link = m.group(1)
        if link.startswith(("http://", "https://", "mailto:")) or "XX" in link or "<" in link:
            continue
        if not (md.parent / link).resolve().exists():
            bad.append(f"{md.relative_to(ROOT)} -> {link}")
for b in bad:
    print("KIRIK:", b)
print(f"[SONUC] kirik link: {len(bad)}")
sys.exit(1 if bad else 0)
