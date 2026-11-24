"""LAB-04 Discover ve KQL: isaretli ekran goruntuleri ve arayuz adimlari (README sirasiyla, GERCEKTEN yapilir).

Kullanim (yerelde, sunucuya SSH tuneli acikken):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab03.py veri       # Adim 1: ornek veri
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab03.py discover   # Adim 2-6
Isaret numaralari sunumdaki "Discover'in 12 parcasi" ile aynidir (1 data view, 2 KQL, 3 filtre, 4 zaman,
6 field listesi, 8 Documents, 10 document acma, 12 kaydetme); Inspect 13-15.
Cikti: assets/screenshots/LAB-04/<ad>.png; olculen sayilar stdout'a yazilir.
"""
import json
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-04"
DV = "ff959d40-b880-11e8-a6d9-e546fe2bba5f"
ANA = 'customer_gender : "FEMALE" and taxful_total_price > 100'
SORULAR = [
    ("Ürün adında \"jacket\" geçen siparişler", "products.product_name : jacket"),
    ("Women's Shoes kategorisi (tam değer)", "category.keyword : \"Women's Shoes\""),
    ("Tutarı 50 ile 100 dolar arası", "taxful_total_price >= 50 and taxful_total_price <= 100"),
    ("Adı \"Ed\" ile başlayan müşteriler", "customer_first_name.keyword : Ed*"),
    ("Hafta sonu siparişleri", "day_of_week : (Saturday or Sunday)"),
    ("Men's Clothing içermeyen siparişler", "not category.keyword : \"Men's Clothing\""),
]


def sayi(page):
    k.settle(page, 3)
    return page.locator('[data-test-subj="discoverQueryTotalHits"]').first.inner_text().strip()


def sorgu(page, q):
    inp = page.locator('[data-test-subj="queryInput"]').first
    inp.click(); inp.fill(q); page.keyboard.press("Enter"); k.settle(page, 5)


def veri(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    try:
        page.get_by_text("Explore on my own", exact=True).first.click(timeout=3000); k.settle(page, 3)
    except Exception:
        pass
    k.shoot(page, LAB, "01-sample-data-link", [(("text", "Try sample data", True), 1, "left")])
    page.get_by_text("Try sample data", exact=True).first.click(); k.settle(page, 4)
    k.shoot(page, LAB, "02-sample-data-install", [(("testsubj", "addSampleDataSetecommerce"), 2, "left")])
    page.locator('[data-test-subj="addSampleDataSetecommerce"]').first.click()
    page.get_by_text("View data").first.wait_for(timeout=180000); time.sleep(2)
    print("ornek veri kuruldu")


def discover(page):
    # Adim 2: gezinti
    page.goto(k.BASE + "/app/discover", wait_until="domcontentloaded"); k.settle(page, 6)
    k.pick_dataview(page, 'Kibana Sample Data eCommerce'); k.settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_30_days"]').first.click(); k.settle(page, 5)
    print("Last 30 days toplam:", sayi(page))
    page.locator('[data-test-subj="field-customer_gender-showDetails"]').first.click(); time.sleep(2)
    k.shoot(page, LAB, "03-discover-tur", [
        (("testsubj", "discover-dataView-switch-link"), 1, "down"),
        (("testsubj", "dateRangePickerControlButton"), 2, "down"),
        (("testsubj", "field-customer_gender-showDetails"), 3, "right"),
        (("css", '[data-test-subj="docTableExpandToggleColumn"] button, [data-test-subj="docTableExpandToggleColumn"]'), 4, "right"),
    ])
    page.keyboard.press("Escape"); time.sleep(1)

    # Adim 3: KQL
    sorgu(page, ANA)
    ana = sayi(page)
    print("ANA", ana)
    k.shoot(page, LAB, "04-discover-kql", [
        (("testsubj", "queryInput"), 1, "down"),
        (("testsubj", "discoverQueryHits"), 2, "down"),
    ])
    for soru, q in SORULAR:
        sorgu(page, q)
        print(f"SORU | {soru} | `{q}` | {sayi(page)}")

    # Adim 4: filtre
    sorgu(page, "")
    def filtre(field, op, degerler):
        page.locator('[data-test-subj="addFilter"]').first.click(); time.sleep(2)
        fld = page.locator('[data-test-subj="filterFieldSuggestionList"] [data-test-subj="comboBoxSearchInput"]').first
        fld.click(); fld.fill(field); time.sleep(1)
        page.locator(f'[data-test-subj="filterFieldOption-{field}"]').first.click(); time.sleep(1)
        opr = page.locator('[data-test-subj="filterOperatorList"] [data-test-subj="comboBoxSearchInput"]').first
        opr.click(); time.sleep(1)
        page.locator(f'[data-test-subj="filterOperatorOption-{op}"]').first.click(); time.sleep(1)
        girdiler = page.locator('[data-test-subj="filterParams"] input')
        for i, d in enumerate(degerler):
            girdiler.nth(i).click(); girdiler.nth(i).fill(d); time.sleep(0.5)
            if op == "is":
                time.sleep(1); page.keyboard.press("Enter"); time.sleep(0.5)
        return page.locator('[data-test-subj="saveFilter"]').first
    kaydet = filtre("customer_gender", "is", ["FEMALE"])
    k.shoot(page, LAB, "05-filtre", [
        (("testsubj", "addFilter"), 1, "down"),
        (("testsubj", "filterParams"), None, "left"),
    ])
    kaydet.click(); k.settle(page, 4)
    once = sayi(page)
    filtre("taxful_total_price", "is between", ["100"]).click(); k.settle(page, 5)
    for _ in range(30):  # sonuc yenilenmeden ekran alinmasin (Cancel kalkip sayi degisene kadar)
        if sayi(page) != once and not page.get_by_role("button", name="Cancel").count():
            break
        time.sleep(1)
    fsay = sayi(page)
    print(f"FILTRE KQL={ana} filtre={fsay}")
    k.shoot(page, LAB, "06-filtre-etiket", [
        (("css", '[data-test-subj^="filter-badge"]'), None, "down"),
        (("testsubj", "discoverQueryHits"), None, "down"),
    ])

    # Adim 4 devam: etiket menusu (Exclude, Temporarily disable, Pin); sonunda iki filtre eski haline doner
    rozet = '[data-test-subj*="filter-key-customer_gender"]'
    def menu():
        page.keyboard.press("Escape"); time.sleep(0.5)
        page.locator(rozet).first.click(); time.sleep(1.5)
    def degisince(eski):
        for _ in range(30):
            if sayi(page) != eski and not page.get_by_role("button", name="Cancel").count():
                break
            time.sleep(1)
        return sayi(page)
    menu()
    k.shoot(page, LAB, "06b-filtre-menu", [
        (("testsubj", "negateFilter"), 1, "right"),
        (("testsubj", "disableFilter"), 2, "right"),
        (("testsubj", "pinFilter"), 3, "right"),
    ])
    page.locator('[data-test-subj="negateFilter"]').first.click(); k.settle(page, 3)
    haric = degisince(fsay)
    menu()
    geri = page.locator('[data-test-subj="negateFilter"]').first.inner_text().strip()
    print(f"EXCLUDE sayi={haric} geri_alma_dugmesi={geri!r} rozet={page.locator(rozet).first.inner_text()!r}")
    page.locator('[data-test-subj="negateFilter"]').first.click(); k.settle(page, 3)
    degisince(haric)
    menu()
    page.locator('[data-test-subj="disableFilter"]').first.click(); k.settle(page, 3)
    kapali = degisince(fsay)
    menu()
    geri = page.locator('[data-test-subj="disableFilter"]').first.inner_text().strip()
    print(f"DISABLE sayi={kapali} geri_alma_dugmesi={geri!r}")
    page.locator('[data-test-subj="disableFilter"]').first.click(); k.settle(page, 3)
    print("geri alindi:", degisince(kapali))
    menu()
    page.locator('[data-test-subj="pinFilter"]').first.click(); k.settle(page, 3)
    # Pinli filtre uygulama icinde gezinince tasinir; sayfayi yeniden yuklemek (goto) onu dusurur.
    page.keyboard.press("Escape"); time.sleep(0.5)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    page.locator('nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("Dashboards"))').first.click(); k.settle(page, 5)
    yeni = page.locator('[data-test-subj="dashboardListingCreateButton"], [data-test-subj="createDashboardPromptButton"]').first
    yeni.click(); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    print("panoda pinli rozet:", page.locator(rozet).count(), page.locator(rozet).first.get_attribute("data-test-subj")[-40:])
    k.shoot(page, LAB, "06c-filtre-pin-pano", [(("css", rozet), 4, "down")])
    for _ in range(4):
        if "/app/discover" in page.url:
            break
        page.go_back(); k.settle(page, 4)
    k.settle(page, 4)
    menu()
    geri = page.locator('[data-test-subj="pinFilter"]').first.inner_text().strip()
    print(f"PIN geri_alma_dugmesi={geri!r}")
    page.locator('[data-test-subj="pinFilter"]').first.click(); k.settle(page, 4)
    page.keyboard.press("Escape"); time.sleep(0.5)
    print("son durum:", sayi(page), [page.locator('[data-test-subj^="filter-badge"]').nth(i).get_attribute("data-test-subj").split(" filter-id")[0][-60:]
                                    for i in range(page.locator('[data-test-subj^="filter-badge"]').count())])

    # Adim 5: kaydet
    page.locator('[data-test-subj="discoverSaveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Kadın 100 dolar üstü siparişler")
    st = page.locator('[data-test-subj="storeTimeWithSearch"]').first
    print("STORE_TIME varsayilan:", st.get_attribute("aria-checked"), st.is_checked() if st.count() else None)
    k.shoot(page, LAB, "07-discover-kaydet", [
        (("testsubj", "savedObjectTitle"), 1, "left"),
        (("testsubj", "storeTimeWithSearch"), None, "left"),
    ])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 5)

    # Adim 6: Inspect
    page.locator('[data-test-subj="app-menu-overflow-button"]').first.click(); time.sleep(1.5)
    k.shoot(page, LAB, "08-discover-inspect-menu", [
        (("role", "menuitem", "Inspect tab"), 1, "left"),
    ])
    page.get_by_role("menuitem", name="Inspect tab").first.click(); time.sleep(3)
    if page.locator('[data-test-subj="inspectorViewChooser"]').count():
        page.locator('[data-test-subj="inspectorViewChooser"]').first.click(); time.sleep(1)
        page.locator('[data-test-subj="inspectorViewChooserRequests"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="inspectorRequestDetailRequest"]').first.click(); time.sleep(2)
    k.shoot(page, LAB, "09-discover-inspect", [
        (("testsubj", "inspectorRequestDetailRequest"), 2, "up"),
        (("testsubj", "inspectorRequestCodeViewerContainer"), 3, None),
    ])
    metin = page.locator('[data-test-subj="inspectorRequestCodeViewerContainer"]').first.inner_text()
    try:
        q = json.loads(metin).get("query")
        print("INSPECT_QUERY", json.dumps(q, ensure_ascii=False)[:1500])
    except Exception:
        print("INSPECT_RAW", metin[:1500].replace("\n", " "))
    page.keyboard.press("Escape"); time.sleep(1)


def pano(page):
    """Adim 5 kutusu: kayitli aramayi (Discover session) yeni panoya eklemek."""
    page.goto(k.BASE + "/app/dashboards#/create", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="addToDashboardTab-library"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectFinderSearchInput"]').first.fill("Kadın")
    page.keyboard.press("Enter")  # arama Enter ile calisir
    hedef = '[data-test-subj="savedObjectTitleKadın-100-dolar-üstü-siparişler"]'
    page.locator(hedef).first.wait_for(timeout=15000); time.sleep(1)
    k.shoot(page, LAB, "10-pano-from-library", [
        (("testsubj", "addToDashboardTab-library"), 1, "right"),
        (("testsubj", "savedObjectFinderSearchInput"), 2, "left"),
        (("css", hedef), 3, "left")])
    page.locator(hedef).first.click(); k.settle(page, 4)
    page.keyboard.press("Escape"); time.sleep(1)
    for b in ('[data-test-subj="euiFlyoutCloseButton"]',):
        if page.locator(b).count(): page.locator(b).first.click(); time.sleep(1)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_30_days"]').first.click(); k.settle(page, 6)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Kadın siparişleri")
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    print("panel sayisi:", page.locator('[data-test-subj="dashboardPanel"]').count())
    k.shoot(page, LAB, "11-pano-kayitli-arama", [(("css", '[data-test-subj="dashboardPanel"]'), 4, "right")])


if __name__ == "__main__":
    parca = sys.argv[1]
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        {"veri": veri, "discover": discover, "pano": pano}[parca](page)
        br.close()
