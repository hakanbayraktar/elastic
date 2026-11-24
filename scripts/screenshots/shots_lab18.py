"""LAB-18 isaretli ekran goruntuleri: harita, kural formu, aktif alarm, CSV ve PDF raporu.

Her tiklama ayri goruntude; sayfalara menuden gidilir. README sirasiyla:
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab18.py harita   # Adim 2 (veri + data view sonra)
    ... kural (Adim 4 kutusu, kural API ile kurulduktan sonra), aktif (Adim 5, ariza sonrasi), rapor pdf (Adim 6)
Cikti: assets/screenshots/LAB-18/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-18.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-18"
DV = "Apache logları (alarm)"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-18")


def ipucu(page, filt):
    v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]:visible").all()]
    print("  subj:", sorted(set(x for x in v if x and any(f.lower() in x.lower() for f in filt)))[:40])


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


def zaman_7g(page):
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.scroll_into_view_if_needed()
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); k.settle(page, 3)


def yonetim(page, bolum, goruntu=None):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = menu(page, "Stack Management")
    page.locator(link).first.click(); k.settle(page, 5)
    sol = f'[data-test-subj="{bolum}"]'
    if goruntu:
        shot(page, goruntu, [(("css", sol), 1, "right")])
    page.locator(sol).first.click(); k.settle(page, 6)


# ------------------------------------------------------------------ Adim 2: harita
def harita(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = menu(page, "Maps")
    shot(page, "02a-menu-maps", [(("testsubj", "toggleNavButton"), 1, "right"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)
    ipucu(page, ["create", "new", "map"])
    yeni = '[data-test-subj="newItemButton"], [data-test-subj="createFirstMapButton"], button:has-text("Create map")'
    if page.locator(yeni).count():
        shot(page, "02b-create-map", [(("css", yeni), 1, "left")])
        page.locator(yeni).first.click(); k.settle(page, 8)
    zaman_7g(page)
    shot(page, "02c-add-layer", [(("testsubj", "dateRangePickerControlButton"), 1, "down"), (("testsubj", "addLayerButton"), 2, "left")])
    page.locator('[data-test-subj="addLayerButton"]').first.click(); time.sleep(3)
    shot(page, "02d-katman-turu", [(("testsubj", "clusters"), 1, "left"), (("testsubj", "documents"), 2, "left")])
    page.locator('[data-test-subj="clusters"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="mapGeoIndexPatternSelect"] [data-test-subj="comboBoxSearchInput"], [data-test-subj="mapGeoIndexPatternSelect"]').first.click(); time.sleep(1)
    page.keyboard.type("alarm", delay=30); time.sleep(1.5)
    page.get_by_role("option").first.click(); time.sleep(4)
    shot(page, "02f-add-and-close", [(("testsubj", "mapGeoIndexPatternSelect"), 1, "left"),
                                     (("role", "button", "Add and close", True), 2, "up")])
    page.get_by_role("button", name="Add and close", exact=True).first.click(); k.settle(page, 8)
    page.mouse.move(700, 450); time.sleep(1)
    shot(page, "02g-harita", [(("testsubj", "mapLayerTOC"), 1, "down"), (("testsubj", "mapContainer"), 2, None)])
    page.locator('[data-test-subj="mapSaveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Ziyaretçi haritası")
    try:
        page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("None")').first.click(); time.sleep(0.5)
    except Exception:
        pass
    shot(page, "02h-harita-kaydet", [(("testsubj", "savedObjectTitle"), 1, "left"),
                                     (("css", '[data-test-subj="add-to-dashboard-options"] label:has-text("None")'), 2, "left"),
                                     (("testsubj", "confirmSaveSavedObjectButton"), 3, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 4)
    print("harita kaydedildi")


# ------------------------------------------------------------------ Adim 4 kutusu: kural formu (API ile kurulan kural)
def kural(page):
    yonetim(page, "triggersActions", "04a-rules-menu")
    satir = 'a:has-text("Ödeme 5xx patlaması"), button:has-text("Ödeme 5xx patlaması")'
    shot(page, "04b-rules-listesi", [(("css", satir), 1, "right")])
    page.locator(satir).first.click(); k.settle(page, 6)
    ipucu(page, ["edit", "rule"])
    page.locator('[data-test-subj="ruleActionsButton"]').first.click(); time.sleep(1.5)   # sag ustteki ... menusu
    shot(page, "04c-edit", [(("testsubj", "ruleActionsButton"), 1, "left"), (("testsubj", "openEditRuleFlyoutButton"), 2, "left")])
    page.locator('[data-test-subj="openEditRuleFlyoutButton"]').first.click(); k.settle(page, 8)
    marks = []
    for hedef, no, ok in ((("text", "Elasticsearch query", False), 1, "right"),
                          (("text", "alarm-apache", False), 2, "right"),
                          (("css", 'button:has-text("is above"), button:has-text("IS ABOVE")'), 3, "right"),
                          (("css", 'button:has-text("for the last"), button:has-text("FOR THE LAST")'), 4, "right")):
        try:
            k.box_of(page, hedef); marks.append((hedef, no, ok))
        except Exception as e:
            print("isaret yok:", hedef, str(e)[:80])
    shot(page, "04d-kural-formu", marks, scroll_to=marks[0][0] if marks else None)
    shot(page, "04e-kural-aksiyon", [(("text", "alarm-gecmisi-yaz", False), 1, "right")], scroll_to=("text", "alarm-gecmisi-yaz", False))
    for t in ("Cancel", "Discard changes"):
        try:
            page.get_by_role("button", name=t, exact=True).last.click(timeout=1500); time.sleep(1)
        except Exception:
            pass


# ------------------------------------------------------------------ Adim 5: aktif alarm
def aktif(page):
    yonetim(page, "triggersActions")
    satir = 'a:has-text("Ödeme 5xx patlaması"), button:has-text("Ödeme 5xx patlaması")'
    page.locator(satir).first.click(); k.settle(page, 6)
    url = page.url
    for i in range(18):
        kutu = page.get_by_text("Active now", exact=True).first.locator("xpath=..").inner_text().replace("\n", " ").strip()
        print("deneme", i + 1, "->", kutu)
        if kutu.startswith("1"):
            break
        time.sleep(10); page.goto(url, wait_until="domcontentloaded"); k.settle(page, 6)
    shot(page, "05a-kural-aktif", [(("text", "Active now", True), 1, "right")])


# ------------------------------------------------------------------ Adim 6: CSV raporu
def rapor(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = menu(page, "Discover")
    page.locator(link).first.click(); k.settle(page, 6)
    k.pick_dataview(page, DV); k.settle(page, 5)
    zaman_7g(page)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('http.response.status_class : "5xx"'); page.keyboard.press("Enter"); k.settle(page, 5)
    shot(page, "06a-discover-sorgu", [(("testsubj", "discover-dataView-switch-link"), 1, "down"), (("testsubj", "queryInput"), 2, "down"),
                                      (("testsubj", "discoverQueryHits"), 3, "down")])
    page.locator('[data-test-subj="app-menu-overflow-button"]').first.click(); time.sleep(2)
    shot(page, "06b-menu-export", [(("testsubj", "app-menu-overflow-button"), 1, "left"), (("testsubj", "exportTopNavButton"), 2, "left")])
    page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
    shot(page, "06c-csv", [(("testsubj", "exportMenuItem-CSV"), 1, "left"), (("testsubj", "exportMenuItem-scheduledReports"), 2, "left")])
    page.locator('[data-test-subj="exportMenuItem-CSV"]').first.click(); time.sleep(3)
    gen = None
    for t in ("Generate CSV", "Export", "Generate export"):
        b = page.get_by_role("button", name=t, exact=True)
        if b.count() and b.last.is_visible():
            gen = t; break
    if gen:
        shot(page, "06d-generate-csv", [(("role", "button", gen, True), 1, "up")])
        page.get_by_role("button", name=gen, exact=True).last.click(); time.sleep(3)
    yonetim(page, "reporting", "06e-reporting-menu")
    for _ in range(20):
        if page.locator('tr:has-text("Done") >> nth=0').count():
            break
        time.sleep(3); page.reload(); k.settle(page, 4)
    print("  CSV satiri:", page.locator('tbody tr >> nth=0').inner_text().replace("\n", " | ")[:200])
    shot(page, "06f-reporting-csv", [(("css", 'tbody tr >> nth=0'), 1, "left")])


# ------------------------------------------------------------------ Adim 6: PDF raporu
def pdf(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = menu(page, "Dashboards")
    page.locator(link).first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="dashboardListingCreateButton"], [data-test-subj="createDashboardPromptButton"]').first.click(); k.settle(page, 6)
    zaman_7g(page)
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="addToDashboardTab-library"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectFinderSearchInput"]').first.fill("Ziyaretçi"); page.keyboard.press("Enter"); time.sleep(3)
    shot(page, "06g-pano-library", [(("testsubj", "addToDashboardTab-library"), 1, "right"), (("testsubj", "savedObjectFinderSearchInput"), 2, "left"),
                                    (("css", '[data-test-subj="savedObjectsFinderTable"] button:has-text("Ziyaretçi haritası")'), 3, "left")])
    page.locator('[data-test-subj="dashboardAddPanel"]').first.get_by_role("button", name="Ziyaretçi haritası").first.click(); time.sleep(3)
    try:
        page.locator('[data-test-subj="euiFlyoutCloseButton"]').first.click(); time.sleep(2)
    except Exception:
        page.keyboard.press("Escape")
    k.settle(page, 6)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Alarm panosu")
    shot(page, "06h-pano-kaydet", [(("testsubj", "savedObjectTitle"), 1, "left"), (("testsubj", "confirmSaveSavedObjectButton"), 2, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 8)
    shot(page, "06i-exit-edit", [(("testsubj", "dashboardViewOnlyMode"), 1, "down")])
    page.locator('[data-test-subj="dashboardViewOnlyMode"]').first.click(); k.settle(page, 4)
    page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
    shot(page, "06j-export-pdf", [(("testsubj", "exportTopNavButton"), 1, "left"), (("testsubj", "exportMenuItem-PDF"), 2, "left")])
    page.locator('[data-test-subj="exportMenuItem-PDF"]').first.click(); time.sleep(3)
    shot(page, "06k-generate-pdf", [(("testsubj", "generateReportButton"), 1, "up")])
    page.locator('[data-test-subj="generateReportButton"]').first.click(); time.sleep(5)
    yonetim(page, "reporting")
    satir = 'tr:has-text("Alarm panosu") >> nth=0'
    for _ in range(60):
        if page.locator(satir).count() and "Done" in page.locator(satir).inner_text():
            break
        time.sleep(5); page.reload(); k.settle(page, 4)
    print("  PDF_SATIRI:", page.locator(satir).inner_text().replace("\n", " | ")[:200])
    shot(page, "06l-reporting-pdf", [(("css", satir), 1, "left")])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"harita": harita, "kural": kural, "aktif": aktif, "rapor": rapor, "pdf": pdf}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
