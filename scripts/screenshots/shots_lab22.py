"""LAB-22 Adim 4 kutusu: ILM politikasini ve data stream'i Kibana arayuzunde gormek (degistirmeden).
On kosul: Adim 1-4 (rollover olmus). KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab22.py
Cikti: assets/screenshots/LAB-22/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-22.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-22"
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-22")
HATA = []


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def yonetim(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = 'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("Stack Management"))'
    page.locator(link).first.scroll_into_view_if_needed(); page.locator(link).first.click(); k.settle(page, 5)


def ilm(page):
    yonetim(page)
    shot(page, "04a-ilm-menu", [(("testsubj", "index_lifecycle_management"), 1, "right")])
    page.locator('[data-test-subj="index_lifecycle_management"]').first.click(); k.settle(page, 6)
    ara = page.get_by_placeholder("Search...").first   # ustteki genel arama cubugu degil, tablonun kutusu
    ara.fill("ilm-politika"); page.keyboard.press("Enter"); k.settle(page, 3)
    ara.evaluate("e => e.setAttribute('data-ara-isaret', '1')")
    link = 'a:text-is("ilm-politika"), button:text-is("ilm-politika")'
    shot(page, "04b-ilm-listesi", [(("css", '[data-ara-isaret="1"]'), 1, "down"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)
    v = sorted(set(e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]:visible").all() if e.get_attribute("data-test-subj")))
    print("ILM edit:", [x for x in v if any(w in x.lower() for w in ("phase", "rollover", "readonly", "delete", "hot", "warm", "min"))][:40])
    page.locator('[data-test-subj="ilmTimelinePhase-hot"]').first.scroll_into_view_if_needed(); time.sleep(1)
    shot(page, "04c-ilm-fazlar", [(("testsubj", "ilmTimelinePhase-hot"), 1, "down"), (("testsubj", "ilmTimelinePhase-warm"), 2, "down"),
                                  (("testsubj", "ilmTimelinePhase-delete"), 3, "down")])
    yonetim(page)
    shot(page, "04e-index-management", [(("testsubj", "index_management"), 1, "right")])
    page.locator('[data-test-subj="index_management"]').first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="data_streamsTab"]').first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="dataStreamSearch"] input, input[data-test-subj="dataStreamSearch"]').first.fill("ilm-uygulama"); k.settle(page, 3)
    satir = 'tr:has-text("ilm-uygulama")'
    print("satir:", page.locator(satir).first.inner_text().replace("\n", " | ")[:200])
    shot(page, "04f-data-stream", [(("testsubj", "data_streamsTab"), 1, "down"), (("css", '[data-test-subj="dataStreamSearch"]'), 2, "down"),
                                   (("css", satir), 3, "left")])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        ilm(page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
