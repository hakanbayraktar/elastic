"""LAB-20 isaretli Kibana ekran goruntuleri (README sirasiyla, GERCEKTEN yapilir).

Kullanim (yerelde, sunucuya SSH tuneli acikken):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab20.py destek     # Adim 5 (Adim 1-4 sonrasi)
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab20.py izleyici   # Adim 7, viewer
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab20.py rapor      # Adim 7, gvn-rapor
Cikti: assets/screenshots/LAB-20/<ad>.png; olculenler stdout'a yazilir.
"""
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-20"
PANO = "722b74f0-b882-11e8-a6d9-e546fe2bba5f"   # [eCommerce] Revenue Dashboard (LAB-03 ornek verisi)
PAROLA = "Guvenlik2026!"


def giris(page, kullanici):
    page.goto(k.BASE + "/login", wait_until="domcontentloaded")
    page.fill('input[name="username"]', kullanici)
    page.fill('input[name="password"]', PAROLA)
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/app/" in u or "space_selector" in u, timeout=60000)
    k.settle(page, 4)
    print(kullanici, "giris sonrasi:", page.url.replace(k.BASE, ""))


def destek(page):
    giris(page, "gvn_destek")
    page.goto(k.BASE + "/s/gvn-destek/app/discover", wait_until="domcontentloaded"); k.settle(page, 8)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_30_days"]').first.click(); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    k.shoot(page, LAB, "01-destek-discover", [
        (("testsubj", "spacesNavSelector"), 1, "right"),
        (("testsubj", "discover-dataView-switch-link"), 2, "down"),
        (("testsubj", "discoverQueryHits"), 3, "down"),
        (("testsubj", "fieldListGroupedAvailableFields"), 4, "right"),
    ])
    print("hits:", page.locator('[data-test-subj="discoverQueryHits"]').first.inner_text())


def pano_ac(page):
    page.goto(k.BASE + "/app/dashboards#/view/" + PANO, wait_until="domcontentloaded"); k.settle(page, 10)
    dugmeler = [b.inner_text().strip() for b in page.get_by_role("button").all() if b.is_visible() and b.inner_text().strip()]
    print("Edit dugmesi var mi:", any(d == "Edit" for d in dugmeler), "| Share:", "Share" in dugmeler, "| Export:", "Export" in dugmeler)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    menu = sorted(set(a.inner_text().strip() for a in page.locator("nav a").all() if a.is_visible() and a.inner_text().strip()))
    print("menu:", menu)


def izleyici(page):
    giris(page, "gvn_izleyici")
    secici = page.url.endswith("space_selector")
    print("Space secim ekrani:", secici)
    if secici:
        page.locator('[data-test-subj="space-card-default"]').first.click()
        page.wait_for_url(lambda u: "/app/" in u, timeout=60000); k.settle(page, 4)
    pano_ac(page)
    k.shoot(page, LAB, "02-izleyici-pano", [
        (("text", "Analytics", True), 1, "right"),
        (("testsubj", "exportTopNavButton"), 2, "down"),
    ])


def rapor(page):
    giris(page, "gvn_rapor")
    pano_ac(page)
    k.shoot(page, LAB, "03-rapor-pano", [
        (("css", 'nav >> role=link[name="Dashboards"s]'), 3, "right"),
        (("testsubj", "exportTopNavButton"), 4, "down"),
    ])
    page.keyboard.press("Escape")
    page.goto(k.BASE + "/app/dev_tools", wait_until="domcontentloaded"); k.settle(page, 6)
    print("dev_tools:", page.url.replace(k.BASE, ""), "::", page.locator("body").inner_text()[:120].replace("\n", " | "))
    k.shoot(page, LAB, "04-rapor-devtools", [
        (("text", "You do not have permission to access the requested page", False), 5, "down"),
    ])
    page.goto(k.BASE + "/app/management", wait_until="domcontentloaded"); k.settle(page, 6)
    print("management:", page.locator("body").inner_text()[:80].replace("\n", " | "))


if __name__ == "__main__":
    parca = sys.argv[1]
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        {"destek": destek, "izleyici": izleyici, "rapor": rapor}[parca](page)
        br.close()
