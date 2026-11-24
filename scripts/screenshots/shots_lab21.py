"""LAB-21 Adim 3: Index Management'ta red index, menuden gidilerek. On kosul: Adim 3'teki saglik-arizali index'i.
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab21.py
Cikti: assets/screenshots/LAB-21/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-21.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-21"
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-21")
HATA = []


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def index_management(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = 'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("Stack Management"))'
    page.locator(link).first.scroll_into_view_if_needed(); page.locator(link).first.click(); k.settle(page, 5)
    shot(page, "03a-index-management-menu", [(("testsubj", "index_management"), 1, "right")])
    page.locator('[data-test-subj="index_management"]').first.click(); k.settle(page, 6)
    arama = page.locator('[data-test-subj="indicesSearch"]').first
    arama.fill("saglik-arizali"); page.keyboard.press("Enter"); time.sleep(2)
    for _ in range(10):
        if page.locator('tr:has-text("saglik-arizali")').count():
            break
        page.get_by_role("button", name="Reload indices").first.click(); time.sleep(3)
    print("satir:", page.locator('tr:has-text("saglik-arizali")').first.inner_text().replace("\n", " | ")[:200])
    shot(page, "03b-index-management-red", [(("testsubj", "indicesSearch"), 1, "down"), (("css", 'tr:has-text("saglik-arizali")'), 2, "left")])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        index_management(page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
