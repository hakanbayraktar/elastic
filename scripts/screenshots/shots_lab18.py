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
    shot(page, "02g-harita", [(("testsubj", "mapLayerTOC"), 1, "left"), (("testsubj", "mapContainer"), 2, None)])  # 2: harita alani; numara kutunun icinde
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

def aktif(page):
    yonetim(page, "triggersActions")
    if not page.locator('[data-test-subj="rulesList"]').count():   # 9.5: liste ilk giriste bos kalabiliyor
        page.locator('[role="tab"]:has-text("Logs")').first.click(); k.settle(page, 4)
        page.locator('[role="tab"]:has-text("Rules")').first.click(); k.settle(page, 8)
    ara = page.locator('[data-test-subj="ruleSearchField"]').first
    ara.fill("Ödeme"); ara.press("Enter"); k.settle(page, 4)   # listede baska labların kurallari da var
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


def isaretle(loc, ad):
    loc.evaluate(f"e => e.setAttribute('data-isaret', '{ad}')")
    return ("css", f'[data-isaret="{ad}"]')


# ------------------------------------------------------------------ Adim 3 kutusu: Index connector arayuzde
def baglayici_arayuz(page):
    """Form doldurulur, KAYDEDILMEZ (connector Dev Tools ile zaten var; sunucuda hicbir sey silinmez/degismez)."""
    yonetim(page, "triggersActionsConnectors", "03a-connectors-menu")
    olustur = page.get_by_role("button", name="Create connector").first
    shot(page, "03b-create-connector", [(isaretle(olustur, "cc"), 1, "left")])
    olustur.click(); time.sleep(3)
    ara = page.locator('.euiFlyout input[type="search"], .euiFlyout [placeholder*="Search"]').first
    ara.fill("Index"); time.sleep(1.5)
    shot(page, "03c-index-turu", [(isaretle(ara, "ctara"), 1, "up"), (("css", '[data-test-subj=".index-card"]'), 2, "left")])
    page.locator('[data-test-subj=".index-card"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="nameInput"]').fill("alarm-gecmisi-yaz")
    page.locator('[data-test-subj="connectorIdInput"]').fill("alarm-gecmisi-yaz")
    page.locator('[data-test-subj="connectorIndexesComboBox"] input').first.click()
    page.keyboard.type("alarm-gecmisi"); time.sleep(2)
    page.locator('[role="option"]').filter(has_text="alarm-gecmisi").first.click(); time.sleep(2)
    # Connector Dev Tools ile zaten kurulu: id cakisma uyarisi bu cift kurulumdan gelir; arayuz yolunu secen gormez
    page.evaluate("""() => { const row = document.querySelector('[data-test-subj="connectorIdInput"]').closest('.euiFormRow');
        row.querySelectorAll('.euiFormErrorText, .euiFormControlLayoutIcons').forEach(e => e.style.display = 'none');
        row.querySelectorAll('.euiFormLabel').forEach(e => { e.classList.remove('euiFormLabel-isInvalid'); e.style.color = 'inherit'; });
        const i = row.querySelector('input'); i.removeAttribute('aria-invalid'); i.style.backgroundImage = 'none'; i.style.boxShadow = 'none'; }""")
    shot(page, "03d-index-connector", [(("testsubj", "nameInput"), 1, "left"), (("testsubj", "connectorIdInput"), 2, "left"),
                                       (("testsubj", "connectorIndexesComboBox"), 3, "left"),
                                       (("testsubj", "create-connector-flyout-save-btn"), 4, "up")])
    page.keyboard.press("Escape"); time.sleep(1)
    print("connector formu kapatildi (kaydedilmedi)")


# ------------------------------------------------------------------ Adim 4 kutusu: kurali arayuzde kurmak
def kural_arayuz(page):
    """Form doldurulur, KAYDEDILMEZ (kural Dev Tools ile zaten var)."""
    yonetim(page, "triggersActions", "04f-rules-menu")
    shot(page, "04g-create-rule", [(("testsubj", "createRuleButton"), 1, "left")])
    page.locator('[data-test-subj="createRuleButton"]').first.click(); time.sleep(4)
    page.locator('[data-test-subj="ruleTypeModalSearch"]').first.fill("Elasticsearch query"); time.sleep(2)
    shot(page, "04h-kural-turu", [(("testsubj", "ruleTypeModalSearch"), 1, "left"), (("testsubj", ".es-query-SelectOption"), 2, "left")])
    page.locator('[data-test-subj=".es-query-SelectOption"]').first.click(); k.settle(page, 8)
    shot(page, "04i-query-dsl", [(("testsubj", "queryFormType_esQuery"), 1, "left")])
    page.locator('[data-test-subj="queryFormType_esQuery"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="selectIndexExpression"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="thresholdIndexesComboBox"] input').first.click()
    page.keyboard.type("alarm-apache"); time.sleep(3)
    page.locator('[role="option"]').filter(has_text="alarm-apache").first.click(); time.sleep(3)
    zs = page.locator('[data-test-subj="thresholdAlertTimeFieldSelect"]').first
    zs.select_option(value="@timestamp"); time.sleep(1)
    shot(page, "04j-index-zaman", [(("testsubj", "thresholdIndexesComboBox"), 1, "left"), (("testsubj", "thresholdAlertTimeFieldSelect"), 2, "left")])
    page.locator('[data-test-subj="closePopover"]').first.click(); time.sleep(1)
    ed = page.locator('[data-test-subj="queryJsonEditor"] .monaco-editor').first
    ed.click(); page.keyboard.press("Meta+A"); page.keyboard.press("Backspace")
    page.keyboard.type('{"query":{"term":{"http.response.status_class":"5xx"', delay=5); time.sleep(1)
    print("sorgu:", page.locator('[data-test-subj="queryJsonEditor"] .view-lines').first.inner_text().replace("\n", " "))
    page.locator('[data-test-subj="thresholdPopover"]').first.click(); time.sleep(1.5)
    pop = page.locator('.euiPopover__panel').last
    print("esik popover:", pop.inner_text()[:120].replace("\n", " | "))
    sec = pop.locator("select").first
    if sec.count():
        sec.select_option(label="Is above")
    pop.locator('input[type="number"]').first.fill("10"); time.sleep(0.5)
    page.keyboard.press("Escape"); time.sleep(0.5)
    page.locator('[data-test-subj="forLastExpression"]').first.click(); time.sleep(1.5)
    pop = page.locator('.euiPopover__panel').last
    pop.locator('input[type="number"]').first.fill("5")
    s2 = pop.locator("select").first
    if s2.count():
        s2.select_option(label="minutes")
    page.keyboard.press("Escape"); time.sleep(0.5)
    page.locator('[data-test-subj="queryJsonEditor"]').first.evaluate("e => e.scrollIntoView({block: 'start'})"); time.sleep(1)
    shot(page, "04k-sorgu-esik", [(("testsubj", "queryJsonEditor"), 1, "left"), (("testsubj", "thresholdPopover"), 2, "left"),
                                  (("testsubj", "forLastExpression"), 3, "left")], scroll_to=("testsubj", "queryJsonEditor"))
    page.locator('[data-test-subj="ruleScheduleNumberInput"]').first.fill("1")
    page.locator('[data-test-subj="ruleScheduleUnitInput"]').first.select_option("m"); time.sleep(0.5)
    page.locator('[data-test-subj="ruleScheduleNumberInput"]').first.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "04l-zamanlama", [(("testsubj", "ruleScheduleNumberInput"), 1, "left")], scroll_to=("testsubj", "ruleScheduleNumberInput"))
    page.locator('[data-test-subj="ruleActionsAddActionButton"]').first.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "04m-add-action", [(("testsubj", "ruleActionsAddActionButton"), 1, "left")], scroll_to=("testsubj", "ruleActionsAddActionButton"))
    page.locator('[data-test-subj="ruleActionsAddActionButton"]').first.click(); time.sleep(3)
    print("aksiyon penceresi:", page.locator('[role="dialog"]').last.inner_text()[:200].replace("\n", " | "))
    bag = page.locator('[role="dialog"]').last.get_by_text("alarm-gecmisi-yaz", exact=True).first
    shot(page, "04n-connector-sec", [(isaretle(bag, "bag"), 1, "left")])
    bag.click(); time.sleep(3)
    print("aksiyon formu:", page.locator('[data-test-subj="ruleActions"]').first.inner_text()[:300].replace("\n", " | "))
    ed = page.locator('[data-test-subj="ruleActions"] .monaco-editor').first
    ed.click(); time.sleep(0.5)
    page.keyboard.type('{"kural": "{{rule.name}}", "adet": "{{context.value}}", "kosul": "{{context.conditions}}", "zaman": "{{context.date}}"', delay=5)
    time.sleep(1)
    print("document:", page.locator('[data-test-subj="ruleActions"] .monaco-editor .view-lines').first.inner_text().replace("\n", " "))
    ne_zaman = page.locator('[data-test-subj="ruleActions"] .euiFormRow:has(label:text-is("Run when"))').first
    siklik = page.locator('[data-test-subj="ruleActions"] .euiFormRow:has(label:text-is("Action frequency"))').first
    print("satirlar:", ne_zaman.count(), siklik.count())
    page.locator('[data-test-subj="ruleActions"]').first.evaluate("e => e.scrollIntoView({block: 'start'})"); time.sleep(1)
    shot(page, "04o-aksiyon", [(isaretle(ne_zaman, "nezaman"), 1, "left"), (isaretle(siklik, "siklik"), 2, "down"),
                               (isaretle(ed, "doc"), 3, "left")], scroll_to=("testsubj", "ruleActions"))
    ad = page.locator('[data-test-subj="ruleDetailsNameInput"]').first
    ad.fill("Ödeme 5xx patlaması"); ad.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "04p-ad", [(("testsubj", "ruleDetailsNameInput"), 1, "left")], scroll_to=("testsubj", "ruleDetailsNameInput"))
    kb = page.locator('[data-test-subj="rulePageFooterSaveButton"]').first
    kb.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    print("kaydet dugmesi:", kb.inner_text())
    shot(page, "04q-kaydet", [(("testsubj", "rulePageFooterSaveButton"), 1, "up")], scroll_to=("testsubj", "rulePageFooterSaveButton"))
    page.locator('[data-test-subj="rulePageFooterCancelButton"]').first.click(); time.sleep(2)
    try:
        page.locator('[data-test-subj="confirmModalConfirmButton"]').first.click(timeout=3000)
    except Exception:
        pass
    print("kural formu kapatildi (kaydedilmedi)")


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"harita": harita, "aktif": aktif, "rapor": rapor, "pdf": pdf,
             "baglayici_arayuz": baglayici_arayuz, "kural_arayuz": kural_arayuz}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
