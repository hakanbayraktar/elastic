"""LAB-14 isaretli Kibana ekran goruntuleri: Grok Debugger, pano, paneli elle kurmak, ingest pipeline arayuzu,
index'e varsayilan pipeline. Her tiklama ayri goruntude; sayfalara menuden gidilir. README sirasiyla:
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab14.py grok          # Adim 2
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab14.py pano elle     # Adim 6 (logs + pano sonrasi)
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab14.py ingest varsayilan  # Adim 7 kutusu
Cikti: assets/screenshots/LAB-14/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-14.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-14"
DV = "Logstash Grok Logları"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-14")
SATIR_TAM = ('2026-11-02 10:14:09 [ERROR] payment-gateway: {"error":"Payment timeout",'
             '"order_id":"ORD-9912","response_time_ms":30000}')
DESEN = "^%{TIMESTAMP_ISO8601:ts} \\[%{LOGLEVEL:loglevel}\\] %{NOTSPACE:service}: %{GREEDYDATA:rest_msg}$"


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def menu(page, ad, goruntu=None):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = f'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("{ad}"))'
    page.locator(link).first.scroll_into_view_if_needed(); time.sleep(0.5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "toggleNavButton"), 1, "right"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)


def yonetim(page, bolum, goruntu=None):
    menu(page, "Stack Management")
    sol = f'[data-test-subj="{bolum}"]'
    if goruntu:
        shot(page, goruntu, [(("css", sol), 1, "right")])
    page.locator(sol).first.click(); k.settle(page, 6)


# ------------------------------------------------------------------ Adim 2: Grok Debugger
def grok(page):
    menu(page, "Dev Tools", "02a-menu-dev-tools")
    sekme = '[role="tab"]:has-text("Grok Debugger"), button:has-text("Grok Debugger")'
    shot(page, "02b-grok-debugger-sekme", [(("css", sekme), 1, "down")])
    page.locator(sekme).first.click(); k.settle(page, 4)
    for subj, text in (("eventInput", SATIR_TAM), ("patternInput", DESEN)):
        page.locator(f'[data-test-subj="{subj}"] .monaco-editor').first.click(); time.sleep(0.5)
        page.keyboard.insert_text(text); time.sleep(0.5)   # Monaco: yapistirma gibi, parantez kapatmaz
    page.locator('[data-test-subj="btnSimulate"]').first.click(); time.sleep(3)
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "02c-grok-debugger", [(("text", "Sample Data", True), 1, "right"), (("text", "Grok Pattern", True), 2, "right"),
                                     (("testsubj", "btnSimulate"), 3, "right"), (("text", "Structured Data", True), 4, "right")],
         scroll_to=("testsubj", "eventInput"))


# ------------------------------------------------------------------ Adim 6: pano
def pano(page):
    menu(page, "Dashboards", "06a-menu-dashboards")
    ara = page.locator('[data-test-subj="tableListSearchBox"]').first
    ara.fill("Grok"); page.keyboard.press("Enter"); k.settle(page, 4)
    link = '[data-test-subj="dashboardListingTitleLink-Logstash-Grok-Ayrıştırma-ve-Log-Analizi"]'
    shot(page, "06b-pano-ara", [(("testsubj", "tableListSearchBox"), 1, "down"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 10)
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "06c-grok-pano", [(("text", "Ayrıştırılamayan Olay (Karantina)", True), 1, "right"),
                                 (("text", "Servis Bazında Hata Sayısı", True), 2, "right"),
                                 (("text", "Zaman İçinde Log Seviyesi Dağılımı", True), 3, "right")])


def elle(page):
    menu(page, "Discover")
    page.locator('[data-test-subj="discover-dataView-switch-link"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="indexPattern-switcher--input"]').first.fill("Grok"); time.sleep(1.5)   # liste sanal: once arama
    shot(page, "06d-data-view", [(("testsubj", "discover-dataView-switch-link"), 1, "down"), (("testsubj", "indexPattern-switcher--input"), 2, "right"),
                                 (("css", f'[data-test-subj="dataView-{DV}"]'), 3, "right")])
    page.locator(f'[data-test-subj="dataView-{DV}"]').first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    p = page.locator('[data-test-subj="dateRangePickerPresetItem-Last_1_hour"]').first
    shot(page, "06e-zaman", [(("testsubj", "dateRangePickerInput"), 1, "down"), (("testsubj", "dateRangePickerPresetItem-Last_1_hour"), 2, "left")],
         scroll_to=("testsubj", "dateRangePickerPresetItem-Last_1_hour"))
    p.click(); k.settle(page, 4)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('loglevel : "error"'); page.keyboard.press("Enter"); k.settle(page, 5)
    page.locator('[data-test-subj="field-service-showDetails"]').first.click(); time.sleep(2)
    shot(page, "06f-service-visualize", [(("testsubj", "queryInput"), 1, "down"), (("testsubj", "field-service-showDetails"), 2, "right"),
                                         (("testsubj", "fieldVisualize-service"), 3, "right")])
    page.locator('[data-test-subj="fieldVisualize-service"]').first.click(); k.settle(page, 8)
    for txt in ("Don't show again", "Got it", "Dismiss"):
        try:
            page.get_by_text(txt).first.click(timeout=1500)
        except Exception:
            pass
    page.mouse.move(800, 60); time.sleep(1)
    print("lens:", page.locator('[data-test-subj="lnsWorkspace"]').first.inner_text()[:120].replace("\n", " | "))
    shot(page, "06g-lens-servis-hata", [(("css", '[data-test-subj="lnsWorkspace"]'), 1, None), (("testsubj", "lnsApp_saveButton"), 2, "down")])


# ------------------------------------------------------------------ Adim 7 kutusu: ingest pipeline arayuzu
def ingest(page):
    AD = "grok-ayristir-arayuz"
    SATIR = "2026-11-02 10:14:09 [ERROR] payment-gateway: Payment timeout"
    yonetim(page, "ingest_pipelines", "07a-ingest-menu")
    page.get_by_role("button", name="Create pipeline").first.click(); time.sleep(1.5)
    shot(page, "07b-create-pipeline", [(("role", "button", "Create pipeline"), 1, "left"), (("role", "menuitem", "New pipeline"), 2, "left")])
    page.get_by_role("menuitem", name="New pipeline").first.click(); k.settle(page, 4)
    page.locator('[data-test-subj="nameField"] input').first.fill(AD)
    page.locator('[data-test-subj="descriptionField"] textarea, [data-test-subj="descriptionField"] input').first.fill("Uygulama logu: grok, kucuk harf"); time.sleep(1)
    shot(page, "07c-pipeline-ad", [(("testsubj", "nameField"), 1, "left"), (("testsubj", "addProcessorButton"), 2, "right")])

    def isle(tip):
        page.locator('[data-test-subj="addProcessorButton"]').first.click(); time.sleep(2)
        page.locator('[data-test-subj="processorTypeSelector"]').first.click(); time.sleep(1)
        page.keyboard.type(tip); time.sleep(1.5); page.keyboard.press("Enter"); time.sleep(2)
    isle("Grok")
    page.locator('[data-test-subj="fieldNameField"] input').first.fill("message")
    page.locator('[data-test-subj="input-0"]').first.fill(DESEN); time.sleep(1)
    shot(page, "07d-grok-processor", [(("testsubj", "processorTypeSelector"), 1, "left"), (("testsubj", "fieldNameField"), 2, "left"),
                                      (("testsubj", "input-0"), 3, "left"), (("css", 'role=button[name="Add processor"s]'), 4, "up")])
    page.locator('role=button[name="Add processor"s]').first.click(); time.sleep(2)
    isle("Lowercase")
    page.locator('[data-test-subj="fieldNameField"] input').first.fill("loglevel"); time.sleep(1)
    shot(page, "07e-lowercase", [(("testsubj", "processorTypeSelector"), 1, "left"), (("testsubj", "fieldNameField"), 2, "left"),
                                 (("css", 'role=button[name="Add processor"s]'), 3, "up")])
    page.locator('role=button[name="Add processor"s]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="onFailure"] [data-test-subj="addProcessorButton"], [data-test-subj="onFailure"] button:has-text("Add a processor")').first.click(); time.sleep(2)
    page.locator('[data-test-subj="processorTypeSelector"]').first.click(); time.sleep(1); page.keyboard.type("Append"); time.sleep(1.5); page.keyboard.press("Enter"); time.sleep(2)
    page.locator('[data-test-subj="fieldNameField"] input').first.fill("tags")
    deger = page.locator('.euiFlyout [data-test-subj="comboBoxSearchInput"]').nth(1)
    deger.click(); page.keyboard.type("_grokparsefailure"); page.keyboard.press("Enter"); time.sleep(1)
    deger.evaluate("e => e.closest('.euiComboBox').setAttribute('data-deger-isaret', '1')")
    shot(page, "07f-on-failure", [(("testsubj", "processorTypeSelector"), 1, "left"), (("testsubj", "fieldNameField"), 2, "left"),
                                  (("css", '[data-deger-isaret="1"]'), 3, "left"), (("css", 'role=button[name="Add processor"s]'), 4, "up")])
    page.locator('role=button[name="Add processor"s]').first.click(); time.sleep(2)
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "07g-add-documents", [(("testsubj", "addDocumentsButton"), 1, "down")])
    page.locator('[data-test-subj="addDocumentsButton"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="testPipelineFlyout"] .monaco-editor').first.click(); time.sleep(0.5)
    page.keyboard.press("Meta+A"); page.keyboard.press("Backspace")
    # Monaco parantezleri kendisi kapatir: insert_text bozulur, tus tus yazmak dogru sonuc verir
    page.keyboard.type('[{"_source": {"message": "' + SATIR + '"}}, {"_source": {"message": "bozuk satir: seviye ve servis yok"}}]', delay=10); time.sleep(1)
    shot(page, "07h-test-dokuman", [(("css", '[data-test-subj="testPipelineFlyout"] .monaco-editor'), 1, "left"), (("testsubj", "runPipelineButton"), 2, "up")])
    page.locator('[data-test-subj="runPipelineButton"]').first.click(); time.sleep(4)
    cikti = page.locator('[data-test-subj="outputTabContent"]').first.inner_text().replace("\n", " ")
    print("TEST CIKTI:", all(s in cikti for s in ('"ts"', '"loglevel": "error"', '"service": "payment-gateway"')), "| hata etiketi:", "_grokparsefailure" in cikti)
    shot(page, "07i-test-cikti", [(("testsubj", "outputTab"), 1, "down"), (("testsubj", "outputTabContent"), 2, "left")])
    page.locator('[data-test-subj="euiFlyoutCloseButton"]').first.click(); time.sleep(1.5)
    kaydet = '[data-test-subj="submitButton"]:has-text("Create pipeline")'
    page.locator(kaydet).first.scroll_into_view_if_needed(); time.sleep(1)
    shot(page, "07j-pipeline-kaydet", [(("css", kaydet), 1, "up")], scroll_to=("css", kaydet))
    page.locator(kaydet).first.click(); k.settle(page, 5)
    print("kaydedildi:", page.url.replace(k.BASE, "")[:90])


def varsayilan(page):
    IDX = "grok-varsayilan"
    yonetim(page, "index_management", "07k-index-management")
    ara = page.locator('[data-test-subj="indicesSearch"]').first
    ara.fill(IDX); ara.press("Enter"); k.settle(page, 3)
    ad = f'[data-test-subj="indexTableIndexNameLink"]:text-is("{IDX}")'
    shot(page, "07l-index-listesi", [(("testsubj", "indicesSearch"), 1, "left"), (("css", ad), 2, "left")])
    page.locator(ad).first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="indexDetailsTab-settings"]').first.click(); k.settle(page, 3)
    page.locator('[data-test-subj="indexDetailsSettingsEditModeSwitch"]').first.click(); time.sleep(2)
    satir = page.locator('.monaco-editor .view-line', has_text='"index.default_pipeline"').first
    satir.click(); time.sleep(0.5); page.keyboard.press("End")
    geri = 2 if satir.inner_text().replace("\xa0", " ").rstrip().endswith('",') else 1
    for _ in range(geri):
        page.keyboard.press("ArrowLeft")
    page.keyboard.type("-arayuz"); time.sleep(1)
    print("SATIR:", satir.inner_text().replace("\xa0", " ").strip())
    shot(page, "07m-index-ayar", [(("testsubj", "indexDetailsTab-settings"), 1, "down"), (("testsubj", "indexDetailsSettingsEditModeSwitch"), 2, "left"),
                                  (("css", '.monaco-editor .view-line:has-text("index.default_pipeline")'), 3, "left"),
                                  (("testsubj", "indexDetailsSettingsSave"), 4, "left")])
    page.locator('[data-test-subj="indexDetailsSettingsSave"]').first.click(); k.settle(page, 4)
    print("BILDIRIM:", [t.inner_text().replace("\n", " ")[:120] for t in page.locator(".euiToast").all()])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"grok": grok, "pano": pano, "elle": elle, "ingest": ingest, "varsayilan": varsayilan}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
