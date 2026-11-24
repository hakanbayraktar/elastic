"""LAB-16 isaretli Kibana ekran goruntuleri: Visualize library, Lens, pano, Control, kaydet/paylas/disa aktar.

Her tiklama ayri goruntude gosterilir; kutular README'deki numaralarla ayni sirada. Akislar README sirasiyla:
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab16.py lens    # Adim 2-3
    ... agg (Adim 4), pano (Adim 5-6), kaydet (Adim 7)
On kosul: Adim 1 (veri_uret.py + pano-apache data view). Cikti: assets/screenshots/LAB-16/<ad>.png;
isaretsiz sunum kopyalari assets/screenshots/sunum/lab16-*.png.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-16"
DV = "Apache erişim logları"
HATA = []
# Sunum destesi icin isaretsiz kopyalar (ayni ad, 1600 px); README isaretli olanlari kullanir.
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-16")


def ipucu(page, filt):
    v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]:visible").all()]
    print("  subj:", sorted(set(x for x in v if x and any(f.lower() in x.lower() for f in filt)))[:50])


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def nav(page, ad):
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    return f'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("{ad}"))'


def zaman_7g(page, ad=None):
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    if ad:
        shot(page, ad, [(("testsubj", "dateRangePickerInput"), 1, "down"),
                        (("css", '[data-test-subj="dateRangePickerPresetItem-Last_7_days"]:visible'), 2, "left")],
             scroll_to=("testsubj", "dateRangePickerPresetItem-Last_7_days"))   # liste kaydirilir
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); k.settle(page, 3)


def alan(page, ad, goruntu=None):
    """Field listesinde arayip + ile ekler; goruntu verilirse arama kutusu (1) ve + (2) isaretlenir."""
    s = page.locator('[data-test-subj="lnsIndexPatternFieldSearch"]').first
    s.fill(ad.split(".")[-1].lstrip("@")); time.sleep(1.5)
    page.locator(f'[data-test-subj="lnsFieldListPanelField-{ad}"]').first.hover(); time.sleep(0.7)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "lnsIndexPatternFieldSearch"), 1, "right"),
                             (("testsubj", f"fieldToggle-{ad}"), 2, "right")])
    page.locator(f'[data-test-subj="fieldToggle-{ad}"]').first.click(); k.settle(page, 3)
    s.fill(""); time.sleep(1)


def lens_kaydet(page, baslik, goruntu=None):
    page.locator('[data-test-subj="lnsApp_saveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill(baslik)
    try:
        page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("None")').first.click(); time.sleep(0.5)
    except Exception:
        pass
    page.locator('[data-test-subj="add-to-library-checkbox"] input').first.check(force=True); time.sleep(1)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "savedObjectTitle"), 1, "left"),
                             (("testsubj", "add-to-library-checkbox"), 2, "left"),
                             (("css", '[data-test-subj="add-to-dashboard-options"] label:has-text("None")'), 3, "left"),
                             (("testsubj", "confirmSaveSavedObjectButton"), 4, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 5)
    print("kaydedildi:", baslik)


def tur_sec(page, tur, goruntu=None, ara=None):
    page.locator('[data-test-subj="lnsChartSwitchPopover"]').first.click(); time.sleep(1.5)
    if ara:   # listede asagida kalan tur aranarak gorunur yapilir
        page.get_by_placeholder("Search visualizations").first.fill(ara); time.sleep(1.5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "lnsChartSwitchPopover"), 1, "left"),
                             (("css", 'input[placeholder="Search visualizations"]'), 2, "left"),
                             (("testsubj", f"lnsChartSwitchPopover_{tur}"), 3, "left")])
    page.locator(f'[data-test-subj="lnsChartSwitchPopover_{tur}"]').first.click(); time.sleep(2)


def lens_ac(page):
    """Visualize library > Create visualization > Visualization; data view ve son 7 gun."""
    page.goto(k.BASE + "/app/visualize", wait_until="domcontentloaded"); k.settle(page, 5)
    page.locator('[data-test-subj="newItemButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="visType-lens"]').first.click(); k.settle(page, 8)
    if DV not in page.locator('[data-test-subj="lns-dataView-switch-link"]').first.inner_text():
        page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
        page.get_by_text(DV, exact=True).last.click(); k.settle(page, 4)
    zaman_7g(page)


def calisma(page):
    page.mouse.move(800, 60); time.sleep(1)
    return ("css", '[data-test-subj="lnsWorkspace"]')


# ------------------------------------------------------------------ Adim 2-3
def lens(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = nav(page, "Visualize library")
    shot(page, "02a-menu-visualize-library", [(("testsubj", "toggleNavButton"), 1, "right"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 5)
    shot(page, "02b-create-visualization", [(("testsubj", "newItemButton"), 1, "left")])
    page.locator('[data-test-subj="newItemButton"]').first.click(); time.sleep(2)
    shot(page, "02c-tur-penceresi", [(("testsubj", "visType-lens"), 1, "left"), (("testsubj", "visType-maps"), 2, "left"),
                                      (("testsubj", "groupModalLegacyTab"), 3, "right")])
    page.locator('[data-test-subj="groupModalLegacyTab"]').first.click(); time.sleep(1.5)
    shot(page, "02d-legacy", [(("testsubj", "groupModalLegacyTab"), 1, "right")])
    page.locator('[data-test-subj="groupModalRecommendedTab"]').first.click(); time.sleep(1)
    page.locator('[data-test-subj="visType-lens"]').first.click(); k.settle(page, 8)

    page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
    shot(page, "03a-data-view-sec", [(("testsubj", "lns-dataView-switch-link"), 1, "down"), (("text", DV, True), 2, "right")])
    page.get_by_text(DV, exact=True).last.click(); k.settle(page, 4)
    zaman_7g(page, "03b-zaman-7-gun")
    # Lens ekraninin parcalari (veri secildikten sonra: ipucu kutusu cikmaz, field listesi dolu)
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "03c-lens-ekrani", [(("testsubj", "lns-dataView-switch-link"), 1, "right"),
                                   (("testsubj", "lnsIndexPatternFieldGroups"), 2, "right"),
                                   (("testsubj", "lnsWorkspace"), 3, None),
                                   (("testsubj", "lnsChartSwitchPopover"), 4, "down"),
                                   (("testsubj", "lns-layerPanel-0"), 5, "left"),
                                   (("testsubj", "lnsApp_saveButton"), 6, "down")])
    alan(page, "@timestamp", "03d-timestamp-ekle")
    w = calisma(page)
    shot(page, "03e-ilk-grafik", [(("testsubj", "lnsXY_xDimensionPanel"), 1, "left"),
                                  (("testsubj", "lnsXY_yDimensionPanel"), 2, "left"), (w, 3, None)])
    alan(page, "http.response.status_class", "03f-status-class-ekle")
    w = calisma(page)
    shot(page, "03g-kirilimli-grafik", [(("testsubj", "lnsXY_splitDimensionPanel"), 1, "left"), (w, 2, None)])
    page.locator('[data-test-subj="lnsChartSwitchPopover"]').first.click(); time.sleep(1.5)
    shot(page, "03h-grafik-turu", [(("testsubj", "lnsChartSwitchPopover"), 1, "down")])
    page.keyboard.press("Escape"); time.sleep(1)
    lens_kaydet(page, "Zaman içinde istekler (durum sınıfı)", "03i-kaydet")


# ------------------------------------------------------------------ Adim 4
def agg(page):
    # a) tablo
    lens_ac(page)
    tur_sec(page, "lnsDatatable", "04a-tablo-turu", "Table")
    alan(page, "source.geo.country_name")
    alan(page, "response_time_ms")
    w = calisma(page)
    ipucu(page, ["lnsDatatable", "dimension"])
    shot(page, "04b-tablo-alanlar", [(("testsubj", "lnsDatatable_rows"), 1, "left"),
                                     (("testsubj", "lnsDatatable_metrics"), 2, "left"), (w, 3, None)])
    page.get_by_text("Median of response_time_ms").last.click(); time.sleep(2)
    shot(page, "04c-quick-functions", [(("testsubj", "lens-dimensionTabs-quickFunctions"), 1, "down"),
                                       (("testsubj", "lns-indexPatternDimension-percentile"), 2, "left")])
    page.locator('[data-test-subj="lns-indexPatternDimension-percentile"]').first.click(); k.settle(page, 3)
    try:
        page.get_by_role("button", name="Close", exact=True).last.click(timeout=2000)
    except Exception:
        page.keyboard.press("Escape")
    time.sleep(1)
    w = calisma(page)
    shot(page, "04d-tablo-sonuc", [(w, 1, None)])
    lens_kaydet(page, "Ülke bazında istek ve yanıt süresi")

    # b) heat map
    lens_ac(page)
    tur_sec(page, "heatmap", "04e-heatmap-turu", "Heat")
    alan(page, "@timestamp"); alan(page, "url.path")
    w = calisma(page)
    ipucu(page, ["Heatmap", "heatmap"])
    shot(page, "04f-heatmap", [(("testsubj", "lnsHeatmap_xDimensionPanel"), 1, "left"),
                               (("testsubj", "lnsHeatmap_yDimensionPanel"), 2, "left"), (w, 3, None)])
    lens_kaydet(page, "Sayfa ve saat yoğunluğu")

    # c) metric + formula
    lens_ac(page)
    tur_sec(page, "lnsMetric", "04g-metric-turu", "Metric")
    bos = '[data-test-subj="lnsMetric_primaryMetricDimensionPanel"] [data-test-subj="lns-empty-dimension"]'
    shot(page, "04h-primary-metric", [(("css", bos), 1, "left")])
    page.locator(bos).first.click(); time.sleep(2)
    page.locator('[data-test-subj="lens-dimensionTabs-formula"]').first.click(); time.sleep(2)
    ed = page.locator('[data-test-subj="lnsFormulaWidget"] .monaco-editor, .lnsFormula .monaco-editor').first
    ed.click(); time.sleep(0.5)
    page.keyboard.press("ControlOrMeta+A"); page.keyboard.press("Delete")
    # Monaco tirnak/parantezi kendisi kapatir; formul panodan yapistirilir.
    page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=k.BASE)
    page.evaluate("t => navigator.clipboard.writeText(t)", "count(kql='http.response.status_class : \"5xx\"') / count() * 100")
    page.keyboard.press("ControlOrMeta+V"); time.sleep(1)
    page.keyboard.press("Escape"); time.sleep(3)
    print("  formul:", ed.inner_text()[:120].replace("\n", " "))
    ad = page.locator('[data-test-subj="lns-indexPattern-dimensionContainerBody"] input[type="text"]').last
    try:
        ad = page.get_by_label("Name", exact=True).last if page.get_by_label("Name", exact=True).count() else ad
        ad.fill("Hata oranı (%)"); time.sleep(2)
    except Exception as e:
        print("HATA ad", str(e)[:120]); ipucu(page, ["label", "name", "appearance", "column"])
    shot(page, "04i-formula", [(("testsubj", "lens-dimensionTabs-formula"), 1, "down"),
                               (("css", '[data-test-subj="lnsFormulaWidget"], .lnsFormula'), 2, "left"),
                               (("css", 'input[value="Hata oranı (%)"]'), 3, "left")])
    try:
        page.get_by_role("button", name="Close", exact=True).last.click(timeout=2000)
    except Exception:
        page.keyboard.press("Escape")
    k.settle(page, 3)
    w = calisma(page)
    print("  metric:", page.locator('[data-test-subj="lnsWorkspace"]').first.inner_text()[:80].replace("\n", " "))
    shot(page, "04j-metric-sonuc", [(w, 1, None)])
    lens_kaydet(page, "Hata oranı (5xx, %)")


# ------------------------------------------------------------------ Adim 5-6
def pano(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    link = nav(page, "Dashboards")
    shot(page, "05a-menu-dashboards", [(("css", link), 1, "right")])
    page.locator(link).first.click(); k.settle(page, 5)
    shot(page, "05b-create-dashboard", [(("css", '[data-test-subj="dashboardListingCreateButton"], [data-test-subj="createDashboardPromptButton"]'), 1, "left")])
    page.locator('[data-test-subj="dashboardListingCreateButton"], [data-test-subj="createDashboardPromptButton"]').first.click(); k.settle(page, 6)
    zaman_7g(page)
    shot(page, "05c-add", [(("testsubj", "dashboardAddTopNavButton"), 1, "down")])
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(4)
    ipucu(page, ["addToDashboard", "create-action", "dashboardAdd"])
    fl = page.locator('[data-test-subj="dashboardAddPanel"]').first
    page.locator('[data-test-subj="addToDashboardTab-library"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="savedObjectFinderSearchInput"]').first.fill("istek")
    page.keyboard.press("Enter"); time.sleep(4)
    shot(page, "05d-from-library", [(("testsubj", "addToDashboardTab-library"), 1, "right"),
                                    (("testsubj", "savedObjectFinderSearchInput"), 2, "left"),
                                    (("css", '[data-test-subj="savedObjectsFinderTable"] button:has-text("Zaman içinde istekler")'), 3, "left")])
    def ekle(t):
        fl.get_by_role("button", name=t).first.click(); time.sleep(3)
    ekle("Zaman içinde istekler (durum sınıfı)")
    shot(page, "05e-panel-eklendi", [(("css", '[data-test-subj="dashboardPanel"]'), 1, "right")])
    ekle("Ülke bazında istek ve yanıt süresi")
    for ara, t in (("yoğunluğu", "Sayfa ve saat yoğunluğu"), ("Hata oranı", "Hata oranı (5xx, %)")):
        page.locator('[data-test-subj="savedObjectFinderSearchInput"]').first.fill(ara)
        page.keyboard.press("Enter"); time.sleep(3)
        ekle(t)
    try:
        page.locator('[data-test-subj="euiFlyoutCloseButton"]').first.click(); time.sleep(2)
    except Exception:
        page.keyboard.press("Escape")
    k.settle(page, 5)
    page.mouse.move(800, 60); time.sleep(1)
    print("panel sayisi:", page.locator('[data-test-subj="dashboardPanel"]').count())
    shot(page, "05f-dort-panel", [(("css", '[data-test-subj^="embeddablePanelHeading-Zaman"]'), 1, "right"),
                                  (("css", '[data-test-subj^="embeddablePanelHeading-Ülke"]'), 2, "right"),
                                  (("css", '[data-test-subj^="embeddablePanelHeading-Sayfa"]'), 3, "right"),
                                  (("css", '[data-test-subj^="embeddablePanelHeading-Hata"]'), 4, "right")])
    # panel tasima / boyutlandirma
    p0 = page.locator('[data-test-subj="dashboardPanel"]').nth(0)
    p0.hover(); time.sleep(1.5)
    ipucu(page, ["drag", "resize", "panelHeader", "embeddablePanel"])
    shot(page, "05g-panel-tasi-boyutla", [(("css", '[data-test-subj="dashboardPanel"] >> nth=0 >> [data-test-subj="embeddablePanelDragHandle"]'), 1, "down"),
                                          (("css", '.kbnGridPanel--resizeHandle >> nth=0'), 2, "left")])

    # Adim 6: Control
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(4)
    shot(page, "06a-add-control", [(("testsubj", "create-action-Control"), 1, "left")])
    page.locator('[data-test-subj="create-action-Control"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="field-search-input"]').first.fill("country"); time.sleep(1)
    page.locator('[data-test-subj="field-picker-select-source.geo.country_name"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="create__options_list_control"]').first.click(); time.sleep(1)
    shot(page, "06b-control-ayar", [(("testsubj", "field-search-input"), 1, "left"),
                                    (("testsubj", "field-picker-select-source.geo.country_name"), 2, "left"),
                                    (("testsubj", "create__options_list_control"), 3, "left"),
                                    (("testsubj", "control-editor-save"), 4, "up")])
    page.locator('[data-test-subj="control-editor-save"]').first.click(); k.settle(page, 4)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Apache atölye")
    shot(page, "06c-pano-kaydet", [(("testsubj", "savedObjectTitle"), 1, "left"),
                                   (("testsubj", "confirmSaveSavedObjectButton"), 2, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 6)
    page.locator('[data-test-subj^="optionsList-control-"]').first.click(); time.sleep(2)
    shot(page, "06d-control-sec", [(("css", '[data-test-subj^="optionsList-control-"]'), 1, "down"),
                                   (("css", '[data-test-subj="optionsList-control-selection-Germany"]'), 2, "right")])
    page.get_by_text("Germany", exact=True).last.click(); time.sleep(1)
    page.keyboard.press("Escape"); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    tablo = page.locator('[data-test-subj="dashboardPanel"]:has-text("Ülke bazında")').first.inner_text()
    print("  suzulmus tablo:", tablo[:160].replace("\n", " | "))
    shot(page, "06e-pano-suzuldu", [(("css", '[data-test-subj^="optionsList-control-"]'), 1, "down"),
                                    (("css", '[data-test-subj="dashboardPanel"]:has-text("Ülke bazında")'), 2, None)])
    # Adim 6 sonu: secimi kaldir, duzenleme modundan cik (Adim 7 Edit dugmesiyle baslar)
    page.locator('[data-test-subj^="optionsList-control-"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="optionsList-control-selection-Germany"]').first.click(); time.sleep(1)
    page.keyboard.press("Escape"); k.settle(page, 4)
    shot(page, "06f-exit-edit", [(("css", '[data-test-subj^="optionsList-control-"]'), 1, "down"),
                                 (("testsubj", "dashboardViewOnlyMode"), 2, "down")])
    page.locator('[data-test-subj="dashboardViewOnlyMode"]').first.click(); k.settle(page, 4)
    for t in ("Discard changes", "Leave", "Discard"):
        try:
            page.get_by_role("button", name=t, exact=True).last.click(timeout=800); print("modal:", t)
        except Exception:
            pass
    print("edit dugmesi:", page.locator('[data-test-subj="dashboardEditMode"]').count())
    page.mouse.move(800, 60); time.sleep(1)
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        k.shoot(page, SUNUM, "06g-pano-tam", [])   # yalniz sunum: bitmis pano, okuma modu
    print("pano kaydedildi")


# ------------------------------------------------------------------ Adim 7
def kaydet(page):
    def ac(p):
        p.goto(k.BASE + "/app/dashboards", wait_until="domcontentloaded"); k.settle(p, 5)
        p.locator('[data-test-subj="dashboardListingTitleLink-Apache-atölye"]').first.click(); k.settle(p, 8)

    def temiz_pencerede():
        ctx = page.context.browser.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        p = ctx.new_page(); k.login(p); ac(p)
        z = p.locator('[data-test-subj="dateRangePickerControlButton"]').first.inner_text().strip()
        ctx.close(); return z
    print("ZAMAN once (temiz pencere):", temiz_pencerede())
    ac(page)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); k.settle(page, 6)
    shot(page, "07a-edit", [(("testsubj", "dashboardEditMode"), 1, "down")])
    page.locator('[data-test-subj="dashboardEditMode"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="app-menu-overflow-button"]').first.click(); time.sleep(1.5)
    shot(page, "07b-settings-menu", [(("testsubj", "app-menu-overflow-button"), 1, "left"), (("role", "menuitem", "Settings"), 2, "left")])
    page.get_by_role("menuitem", name="Settings").first.click(); time.sleep(2)
    sw = page.locator('[data-test-subj="storeTimeWithDashboard"]').first
    if sw.get_attribute("aria-checked") != "true":
        sw.click(); time.sleep(1)
    shot(page, "07c-zaman-kaydi", [(("testsubj", "storeTimeWithDashboard"), 1, "left"), (("testsubj", "applyCustomizeDashboardButton"), 2, "up")])
    k.shoot(page, "sunum", "lab16-pano-zaman-kaydi", [])
    page.locator('[data-test-subj="applyCustomizeDashboardButton"]').first.click(); time.sleep(2)
    shot(page, "07d-save-exit", [(("testsubj", "dashboardQuickSaveMenuItem"), 1, "down"), (("testsubj", "dashboardViewOnlyMode"), 2, "down")])
    page.locator('[data-test-subj="dashboardQuickSaveMenuItem"]').first.click(); k.settle(page, 4)
    page.locator('[data-test-subj="dashboardViewOnlyMode"]').first.click(); k.settle(page, 4)
    print("ZAMAN sonra (temiz pencere):", temiz_pencerede())
    page.locator('[data-test-subj="shareTopNavButton"]').first.click(); time.sleep(2.5)
    shot(page, "07e-share", [(("text", "Everybody in the space", False), 1, "left"), (("css", '[role="dialog"] [role="switch"]'), 2, "left"),
                             (("testsubj", "copyShareUrlButton"), 3, "up")])
    k.shoot(page, "sunum", "lab16-pano-share", [])
    page.keyboard.press("Escape"); time.sleep(1)
    page.goto("about:blank"); ac(page)
    page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
    shot(page, "07f-export", [(("testsubj", "exportMenuItem-JSON"), 1, "left"), (("testsubj", "exportMenuItem-PDF"), 2, "left"),
                              (("testsubj", "exportMenuItem-PNG"), 3, "left"), (("testsubj", "scheduleExport"), 4, "left")])
    k.shoot(page, "sunum", "lab16-pano-export", [])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"lens": lens, "agg": agg, "pano": pano, "kaydet": kaydet}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
