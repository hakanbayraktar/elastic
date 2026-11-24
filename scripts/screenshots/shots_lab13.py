"""LAB-13 Adim 7: MySQL'den aktarilan siparisleri Kibana'da aramak ve kisa rapor (Lens + pano).

On kosul: LAB-13 Adim 1-6 ve Adim 7'deki data view istegi (mysql-siparisler).
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab13.py kibana
Cikti: assets/screenshots/LAB-13/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-13.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-13"
DV = "MySQL siparişleri"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-13")


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def menu(page, ad):
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = f'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("{ad}"))'
    page.locator(link).first.scroll_into_view_if_needed(); time.sleep(0.5)
    return link


def zaman(page, preset="Last_1_year"):
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    p = page.locator(f'[data-test-subj="dateRangePickerPresetItem-{preset}"]').first
    p.scroll_into_view_if_needed(); p.click(); k.settle(page, 3)


def alan(page, ad):
    s = page.locator('[data-test-subj="lnsIndexPatternFieldSearch"]').first
    s.fill(ad); time.sleep(1.5)
    page.locator(f'[data-test-subj="lnsFieldListPanelField-{ad}"]').first.hover(); time.sleep(0.7)
    page.locator(f'[data-test-subj="fieldToggle-{ad}"]').first.click(); k.settle(page, 3)
    s.fill(""); time.sleep(1)


def kibana(page):
    # Discover: arama
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = menu(page, "Discover")
    page.locator(link).first.click(); k.settle(page, 6)
    k.pick_dataview(page, DV); k.settle(page, 5)
    zaman(page)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('urun : kulaklık and il : "Antalya"'); page.keyboard.press("Enter"); k.settle(page, 5)
    print("hits:", page.locator('[data-test-subj="discoverQueryHits"]').first.inner_text())
    shot(page, "07a-discover-arama", [(("testsubj", "discover-dataView-switch-link"), 1, "down"),
                                      (("testsubj", "dateRangePickerControlButton"), 2, "down"),
                                      (("testsubj", "queryInput"), 3, "down"),
                                      (("testsubj", "discoverQueryHits"), 4, "down")])
    # Lens: il bazinda ciro
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = menu(page, "Visualize library")
    page.locator(link).first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="newItemButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="visType-lens"]').first.click(); k.settle(page, 8)
    if DV not in page.locator('[data-test-subj="lns-dataView-switch-link"]').first.inner_text():
        page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
        page.get_by_text(DV, exact=True).last.click(); k.settle(page, 4)
    zaman(page)
    alan(page, "il"); alan(page, "tutar")
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "07b-lens-il-tutar", [(("testsubj", "lns-dataView-switch-link"), 1, "right"),
                                     (("testsubj", "lnsXY_xDimensionPanel"), 2, "left"),
                                     (("testsubj", "lnsXY_yDimensionPanel"), 3, "left")])
    page.get_by_text("Median of tutar").last.click(); time.sleep(2)
    shot(page, "07c-sum", [(("testsubj", "lens-dimensionTabs-quickFunctions"), 1, "down"),
                           (("testsubj", "lns-indexPatternDimension-sum"), 2, "left")])
    page.locator('[data-test-subj="lns-indexPatternDimension-sum"]').first.click(); k.settle(page, 3)
    try:
        page.get_by_role("button", name="Close", exact=True).last.click(timeout=2000)
    except Exception:
        page.keyboard.press("Escape")
    k.settle(page, 3)
    # Lens dikey eksene kayit sayisini da koyar; yalniz ciro kalsin
    satir = page.locator('[data-test-subj="lnsXY_yDimensionPanel"] [data-test-subj="lns-dimensionTrigger"]', has_text="Count of records").first
    satir.hover(); time.sleep(1)
    kutu = satir.locator("xpath=ancestor::*[.//*[@data-test-subj='indexPattern-dimension-remove']][1]")
    sil = kutu.locator('[data-test-subj="indexPattern-dimension-remove"]').first
    sil.evaluate("e => e.setAttribute('data-sil-isaret', '1')")
    shot(page, "07c2-count-sil", [(("css", '[data-sil-isaret="1"]'), 1, "left")])
    sil.click(); k.settle(page, 3)
    page.mouse.move(800, 60); time.sleep(1)
    print("  grafik:", page.locator('[data-test-subj="lnsWorkspace"]').first.inner_text()[:120].replace("\n", " | "))
    shot(page, "07d-ciro-grafigi", [(("css", '[data-test-subj="lnsWorkspace"]'), 1, None)])
    # Kaydet: yeni panoya
    page.locator('[data-test-subj="lnsApp_saveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("İl bazında ciro")
    page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("New")').first.click(); time.sleep(1)
    page.locator('[data-test-subj="add-to-library-checkbox"] input').first.check(force=True); time.sleep(1)
    print("  kaydet dugmesi:", page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.inner_text())
    shot(page, "07e-kaydet-pano", [(("testsubj", "savedObjectTitle"), 1, "left"),
                                   (("css", '[data-test-subj="add-to-dashboard-options"] label:has-text("New")'), 2, "left"),
                                   (("testsubj", "add-to-library-checkbox"), 3, "left"),
                                   (("testsubj", "confirmSaveSavedObjectButton"), 4, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 8)
    zaman(page)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("MySQL siparişleri")
    sw = page.locator('[data-test-subj="storeTimeWithDashboard"]')
    if sw.count() and sw.first.get_attribute("aria-checked") != "true":
        sw.first.click(); time.sleep(1)
    shot(page, "07f-pano-kaydet", [(("testsubj", "savedObjectTitle"), 1, "left"), (("testsubj", "storeTimeWithDashboard"), 2, "left"),
                                   (("testsubj", "confirmSaveSavedObjectButton"), 3, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 6)
    try:
        page.locator('[data-test-subj="dashboardViewOnlyMode"]').first.click(timeout=5000); k.settle(page, 4)
    except Exception:
        pass
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "07g-pano", [(("css", '[data-test-subj="dashboardPanel"]'), 1, None)])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"kibana": kibana}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
