"""LAB-27 isaretli Kibana ekran goruntuleri, README sirasiyla ve GERCEKTEN yapilir (tiklama basina bir goruntu).

    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 SUNUM_EKRAN=/yok python3 scripts/screenshots/shots_lab27.py pano harita   # Adim 3
    ... pdf        Adim 6: PDF raporu ve Reporting
    ... insights   Adim 6 kutusu: ML isi ve SLO'lar (provision_insights.py calismis olmali)
Mailpit (03-mailpit) ve connector listesi (04-connectorlar) kibana_shots.py lab27_mailpit / lab27_connector ile alinir.
Cikti: assets/screenshots/LAB-27/<ad>.png
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-27"
PANO = "Apache Web Trafiği ve GeoIP"
DV = "Apache Web İstek ve Hata Logları"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/yok/LAB-27")


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def nav(ad):
    return f'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("{ad}"))'


def menu(page, ad, goruntu=None, link=None):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = link or nav(ad)
    page.locator(link).first.scroll_into_view_if_needed(); time.sleep(0.5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "toggleNavButton"), 1, "right"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)


def zaman(page, preset, goruntu=None):
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "dateRangePickerInput"), 1, "down"), (("testsubj", f"dateRangePickerPresetItem-{preset}"), 2, "left")],
             scroll_to=("testsubj", f"dateRangePickerPresetItem-{preset}"))
    page.locator(f'[data-test-subj="dateRangePickerPresetItem-{preset}"]').first.click(); k.settle(page, 4)


def pano_ac(page, goruntu=False):
    menu(page, "Dashboards", "03a-menu-dashboards" if goruntu else None)
    if not page.locator('[data-test-subj="tableListSearchBox"]').count():   # son acilan pano dogrudan gelebilir
        page.locator('[data-test-subj="breadcrumbs"] a:has-text("Dashboards")').first.click(); k.settle(page, 5)
    ara = page.locator('[data-test-subj="tableListSearchBox"]').first
    ara.fill("Apache"); page.keyboard.press("Enter"); k.settle(page, 4)
    link = f'[data-test-subj="dashboardListingTitleLink-{PANO.replace(" ", "-")}"]'
    if goruntu:
        shot(page, "03b-pano-ara", [(("testsubj", "tableListSearchBox"), 1, "left"), (("css", link), 2, "left")])
    page.locator(link).first.click(); k.settle(page, 10)


def pano(page):
    pano_ac(page, True)
    page.mouse.move(800, 60); time.sleep(1)
    print("paneller:", page.locator('[data-test-subj="dashboardPanel"]').count(), "hata:", page.locator('[data-test-subj="embeddableError"]').count())
    shot(page, "03c-pano", [(("css", '[data-test-subj^="embeddablePanelHeading-"] >> nth=0'), 1, "ic")])


def harita(page):
    menu(page, "Maps", "03d-menu-maps")
    yeni = '[data-test-subj="newItemButton"], [data-test-subj="createFirstMapButton"], button:has-text("Create map")'
    if page.locator(yeni).count():
        shot(page, "03e-create-map", [(("css", yeni), 1, "left")])
        page.locator(yeni).first.click(); k.settle(page, 8)
    zaman(page, "Last_1_hour")
    shot(page, "03f-add-layer", [(("testsubj", "dateRangePickerControlButton"), 1, "down"), (("testsubj", "addLayerButton"), 2, "left")])
    page.locator('[data-test-subj="addLayerButton"]').first.click(); time.sleep(3)
    shot(page, "03g-clusters", [(("testsubj", "clusters"), 1, "left")])
    page.locator('[data-test-subj="clusters"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="mapGeoIndexPatternSelect"] [data-test-subj="comboBoxSearchInput"], [data-test-subj="mapGeoIndexPatternSelect"]').first.click(); time.sleep(1)
    page.keyboard.type("Apache Web", delay=30); time.sleep(1.5)
    page.get_by_role("option").first.click(); time.sleep(4)
    shot(page, "03h-add-and-close", [(("testsubj", "mapGeoIndexPatternSelect"), 1, "left"), (("role", "button", "Add and close", True), 2, "up")])
    page.get_by_role("button", name="Add and close", exact=True).first.click(); k.settle(page, 8)
    page.mouse.move(700, 450); time.sleep(1)
    shot(page, "03i-harita", [(("testsubj", "mapLayerTOC"), 1, "left")])
    page.locator('[data-test-subj="mapSaveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Apache ziyaretçileri")
    try:
        page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("None")').first.click(); time.sleep(0.5)
    except Exception:
        pass
    shot(page, "03j-harita-kaydet", [(("testsubj", "savedObjectTitle"), 1, "left"),
                                     (("css", '[data-test-subj="add-to-dashboard-options"] label:has-text("None")'), 2, "left"),
                                     (("testsubj", "confirmSaveSavedObjectButton"), 3, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 4)
    print("harita kaydedildi")


def pdf(page):
    pano_ac(page)
    page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
    shot(page, "06a-export-pdf", [(("testsubj", "exportTopNavButton"), 1, "left"), (("testsubj", "exportMenuItem-PDF"), 2, "left")])
    page.locator('[data-test-subj="exportMenuItem-PDF"]').first.click(); time.sleep(3)
    shot(page, "06b-generate-pdf", [(("testsubj", "generateReportButton"), 1, "up")])
    page.locator('[data-test-subj="generateReportButton"]').first.click(); time.sleep(5)
    menu(page, "Stack Management")
    shot(page, "06c-reporting-menu", [(("testsubj", "reporting"), 1, "right")])
    page.locator('[data-test-subj="reporting"]').first.click(); k.settle(page, 6)
    satir = f'tr:has-text("{PANO}") >> nth=0'
    for _ in range(60):
        if page.locator(satir).count() and "Done" in page.locator(satir).inner_text():
            break
        time.sleep(5); page.reload(); k.settle(page, 4)
    print("PDF satiri:", page.locator(satir).inner_text().replace("\n", " | ")[:160])
    shot(page, "06d-reporting-pdf", [(("css", satir), 1, "left")])


def insights(page):
    page.goto(k.BASE + "/app/ml/jobs", wait_until="domcontentloaded"); k.settle(page, 10)
    satir = 'tr:has-text("apache-ip-istek-anomali") >> nth=0'
    print("ML:", page.locator(satir).inner_text().replace("\n", " | ")[:160] if page.locator(satir).count() else "yok")
    shot(page, "06e-ml-isi", [(("css", satir), 1, "left")])
    page.goto(k.BASE + "/app/slos", wait_until="domcontentloaded"); k.settle(page, 12)
    print("SLO:", page.locator("main").first.inner_text()[:200].replace("\n", " | "))
    kartlar = []
    for i, ad in enumerate(("Apache erişilebilirlik", "Apache isteklerinin"), 1):
        kart = page.get_by_text(ad, exact=False).first.locator("xpath=ancestor::*[contains(@class,'euiPanel')][1]")
        kart.evaluate(f"e => e.setAttribute('data-isaret', 'slo{i}')")
        kartlar.append((("css", f'[data-isaret="slo{i}"]'), i, "down"))
    shot(page, "06f-slolar", kartlar)


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"pano": pano, "harita": harita, "pdf": pdf, "insights": insights}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
