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
        (("testsubj", "dateRangePickerControlButton"), 4, "down"),
        (("testsubj", "field-customer_gender-showDetails"), 6, "right"),
        (("css", '[data-test-subj="docTableExpandToggleColumn"] button, [data-test-subj="docTableExpandToggleColumn"]'), 10, "right"),
    ])
    page.keyboard.press("Escape"); time.sleep(1)

    # Adim 3: KQL
    sorgu(page, ANA)
    ana = sayi(page)
    print("ANA", ana)
    k.shoot(page, LAB, "04-discover-kql", [
        (("testsubj", "queryInput"), 2, "down"),
        (("testsubj", "discoverQueryHits"), 8, "down"),
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
        (("testsubj", "addFilter"), 3, "down"),
        (("testsubj", "filterParams"), None, "left"),
    ])
    kaydet.click(); k.settle(page, 4)
    filtre("taxful_total_price", "is between", ["100"]).click(); k.settle(page, 5)
    fsay = sayi(page)
    print(f"FILTRE KQL={ana} filtre={fsay}")
    k.shoot(page, LAB, "06-filtre-etiket", [
        (("css", '[data-test-subj^="filter-badge"]'), None, "down"),
        (("testsubj", "discoverQueryHits"), None, "down"),
    ])

    # Adim 5: kaydet
    page.locator('[data-test-subj="discoverSaveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Kadın 100 dolar üstü siparişler")
    st = page.locator('[data-test-subj="storeTimeWithSearch"]').first
    print("STORE_TIME varsayilan:", st.get_attribute("aria-checked"), st.is_checked() if st.count() else None)
    k.shoot(page, LAB, "07-discover-kaydet", [
        (("testsubj", "savedObjectTitle"), 12, "left"),
        (("testsubj", "storeTimeWithSearch"), None, "left"),
    ])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 5)

    # Adim 6: Inspect
    page.locator('[data-test-subj="app-menu-overflow-button"]').first.click(); time.sleep(1.5)
    k.shoot(page, LAB, "08-discover-inspect-menu", [
        (("role", "menuitem", "Inspect tab"), 13, "left"),
    ])
    page.get_by_role("menuitem", name="Inspect tab").first.click(); time.sleep(3)
    if page.locator('[data-test-subj="inspectorViewChooser"]').count():
        page.locator('[data-test-subj="inspectorViewChooser"]').first.click(); time.sleep(1)
        page.locator('[data-test-subj="inspectorViewChooserRequests"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="inspectorRequestDetailRequest"]').first.click(); time.sleep(2)
    k.shoot(page, LAB, "09-discover-inspect", [
        (("testsubj", "inspectorRequestDetailRequest"), 14, "up"),
        (("testsubj", "inspectorRequestCodeViewerContainer"), 15, None),
    ])
    metin = page.locator('[data-test-subj="inspectorRequestCodeViewerContainer"]').first.inner_text()
    try:
        q = json.loads(metin).get("query")
        print("INSPECT_QUERY", json.dumps(q, ensure_ascii=False)[:1500])
    except Exception:
        print("INSPECT_RAW", metin[:1500].replace("\n", " "))
    page.keyboard.press("Escape"); time.sleep(1)


if __name__ == "__main__":
    parca = sys.argv[1]
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        {"veri": veri, "discover": discover}[parca](page)
        br.close()
