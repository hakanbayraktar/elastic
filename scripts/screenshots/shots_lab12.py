"""LAB-12 isaretli Kibana ekran goruntuleri, README sirasiyla ve GERCEKTEN yapilir.

    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab12.py rol     # Adim 2 kutusu (Dev Tools yerine)
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab12.py kibana  # Adim 6: data view + Discover
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab12.py upload  # Adim 7: Upload file
Cikti: assets/screenshots/LAB-12/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-12.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-12"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-12")
CSV = os.path.join(k.ROOT, "labs", "LAB-12-logstash-excel", "sample-data", "uygulama-loglari.csv")


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


def menu(page, ad, goruntu=None):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    page.locator(nav(ad)).first.scroll_into_view_if_needed(); time.sleep(0.5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "toggleNavButton"), 1, "right"), (("css", nav(ad)), 2, "right")])
    page.locator(nav(ad)).first.click(); k.settle(page, 6)


def isaretle(loc, ad):
    loc.evaluate(f"e => e.setAttribute('data-isaret', '{ad}')")
    return ("css", f'[data-isaret="{ad}"]')


def combo(page, subj, deger):
    page.locator(f'[data-test-subj="{subj}"] input').first.click(); time.sleep(0.5)
    page.keyboard.type(deger); time.sleep(1); page.keyboard.press("Enter"); time.sleep(0.8)


# ------------------------------------------------------------------ Adim 2 kutusu: rol ve kullanici arayuzde
def rol(page):
    menu(page, "Stack Management", "02a-menu-stack-management")
    shot(page, "02b-roles", [(("testsubj", "roles"), 1, "right")])
    page.locator('[data-test-subj="roles"]').first.click(); k.settle(page, 5)
    olustur = page.get_by_role("link", name="Create role").or_(page.get_by_role("button", name="Create role")).first
    shot(page, "02c-create-role", [(isaretle(olustur, "crole"), 1, "left")])
    olustur.click(); k.settle(page, 6)
    page.locator('[data-test-subj="roleFormNameInput"]').fill("excel-logstash-writer")
    combo(page, "cluster-privileges-combobox", "monitor")
    page.locator('[data-test-subj="indicesInput0"] input').first.click(); page.keyboard.type("excel-*"); page.keyboard.press("Enter"); time.sleep(0.8)
    page.locator('[data-test-subj="privilegesInput0"] input').first.click()
    for p in ("create_index", "index"):
        page.keyboard.type(p); time.sleep(1); page.keyboard.press("Enter"); time.sleep(0.8)
    page.keyboard.press("Escape"); time.sleep(0.5)
    print("cluster:", page.locator('[data-test-subj="cluster-privileges-combobox"]').first.inner_text().replace("\n", " "),
          "| indices:", page.locator('[data-test-subj="indicesInput0"]').first.inner_text().replace("\n", " "),
          "| privileges:", page.locator('[data-test-subj="privilegesInput0"]').first.inner_text().replace("\n", " "))
    shot(page, "02d-rol-form", [(("testsubj", "roleFormNameInput"), 1, "left"), (("testsubj", "cluster-privileges-combobox"), 2, "left")],
         scroll_to=("testsubj", "roleFormNameInput"))
    page.locator('[data-test-subj="indicesInput0"]').first.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "02d2-index-yetkileri", [(("testsubj", "indicesInput0"), 1, "up"), (("testsubj", "privilegesInput0"), 2, "up")],
         scroll_to=("testsubj", "indicesInput0"))
    kaydet = page.get_by_role("button", name="Create role").last
    kaydet.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "02e-rol-kaydet", [(isaretle(kaydet, "rkaydet"), 1, "up")], scroll_to=("css", '[data-isaret="rkaydet"]'))
    kaydet.click(); k.settle(page, 5)
    print("rol kaydedildi:", page.url.replace(k.BASE, "")[:70])

    page.locator('[data-test-subj="users"]').first.click(); k.settle(page, 5)
    yeni = page.get_by_role("link", name="Create user").or_(page.get_by_role("button", name="Create user")).first
    shot(page, "02f-create-user", [(("testsubj", "users"), 1, "right"), (isaretle(yeni, "cuser"), 2, "left")])
    yeni.click(); k.settle(page, 6)
    page.locator('[data-test-subj="userFormUserNameInput"]').fill("excel_logstash")
    page.locator('[data-test-subj="userFormFullNameInput"]').fill("Excel Logstash")
    page.locator('[data-test-subj="passwordInput"]').fill("Excel2026!")
    page.locator('[data-test-subj="passwordConfirmationInput"]').fill("Excel2026!")
    combo(page, "rolesDropdown", "excel-logstash-writer")
    page.keyboard.press("Escape"); time.sleep(0.5)
    page.locator('[data-test-subj="editUserFormSubmitButton"]').first.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "02g-kullanici-form", [(("testsubj", "userFormUserNameInput"), 1, "left"), (("testsubj", "userFormFullNameInput"), 2, "left"),
                                      (("testsubj", "passwordInput"), 3, "left"), (("testsubj", "passwordConfirmationInput"), 4, "left"),
                                      (("testsubj", "rolesDropdown"), 5, "left"), (("testsubj", "editUserFormSubmitButton"), 6, "right")],
         scroll_to=("testsubj", "editUserFormSubmitButton"))
    page.locator('[data-test-subj="editUserFormSubmitButton"]').first.click(); k.settle(page, 5)
    print("kullanici kaydedildi:", page.url.replace(k.BASE, "")[:70])


# ------------------------------------------------------------------ Adim 6: data view ve Discover
def kibana(page):
    menu(page, "Stack Management")
    shot(page, "06a-data-views", [(("testsubj", "dataViews"), 1, "right")])
    page.locator('[data-test-subj="dataViews"]').first.click(); k.settle(page, 5)
    btn = page.locator('[data-test-subj="createDataViewButton"]:visible')
    if not btn.count():
        btn = page.locator('[data-test-subj="noDataViewsPromptCreateDataView"]:visible')
    shot(page, "06b-create-data-view", [(isaretle(btn.first, "cdv"), 1, "left")])
    btn.first.click(); time.sleep(3)
    page.locator('[data-test-subj="createIndexPatternNameInput"]').fill("excel-satislar")
    page.locator('[data-test-subj="createIndexPatternTitleInput"]').fill("excel-satislar"); time.sleep(3)
    page.locator('[data-test-subj="timestampField"] [data-test-subj="comboBoxSearchInput"]').click(); time.sleep(1)
    page.get_by_role("option", name="@timestamp", exact=True).first.click(); time.sleep(1)
    shot(page, "06c-data-view-form", [(("testsubj", "createIndexPatternNameInput"), 1, "left"), (("testsubj", "createIndexPatternTitleInput"), 2, "left"),
                                      (("testsubj", "timestampField"), 3, "left"), (("testsubj", "saveIndexPatternButton"), 4, "up")])
    page.locator('[data-test-subj="saveIndexPatternButton"]').first.click(); time.sleep(4)

    menu(page, "Discover", "06d-menu-discover")
    page.locator('[data-test-subj="discover-dataView-switch-link"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="indexPattern-switcher--input"]').first.fill("excel"); time.sleep(1.5)
    shot(page, "06e-data-view-sec", [(("testsubj", "discover-dataView-switch-link"), 1, "down"), (("testsubj", "indexPattern-switcher--input"), 2, "right"),
                                     (("css", '[data-test-subj="dataView-excel-satislar"]'), 3, "right")])
    page.locator('[data-test-subj="dataView-excel-satislar"]').first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    shot(page, "06f-last-1-year", [(("testsubj", "dateRangePickerInput"), 1, "down"), (("testsubj", "dateRangePickerPresetItem-Last_1_year"), 2, "left")],
         scroll_to=("testsubj", "dateRangePickerPresetItem-Last_1_year"))
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_1_year"]').first.click(); k.settle(page, 5)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('il : "İstanbul"'); page.keyboard.press("Enter"); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    print("hits:", page.locator('[data-test-subj="discoverQueryHits"]').first.inner_text())
    shot(page, "06g-discover-istanbul", [(("testsubj", "queryInput"), 1, "down"), (("testsubj", "discoverQueryHits"), 2, "down")])


# ------------------------------------------------------------------ Adim 7: Upload file
def upload(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 5)
    link = page.get_by_role("link", name="Upload a file").or_(page.get_by_role("button", name="Upload a file")).first
    link.scroll_into_view_if_needed(); time.sleep(1)
    shot(page, "07a-upload-a-file", [(isaretle(link, "upl"), 1, "down")])
    link.click(); k.settle(page, 6)
    dosya = page.locator('input[type="file"]').first
    dosya.evaluate("e => (e.closest('.euiFilePicker') || e.parentElement).setAttribute('data-isaret', 'secici')")
    shot(page, "07b-dosya-sec", [(("css", '[data-isaret="secici"]'), 1, "down")])
    dosya.set_input_files(CSV); time.sleep(10)
    page.locator('[data-test-subj="dataVisualizerFileIndexNameInput"]').first.fill("excel-uygulama-loglari"); time.sleep(1)
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "07c-index-adi", [(("testsubj", "dataVisualizerFileIndexNameInput"), 1, "right"),
                                 (("testsubj", "mlFileUploadFileStatusMappingsTab-0"), 2, "down")],
         scroll_to=("testsubj", "dataVisualizerFileIndexNameInput"))
    page.locator('[data-test-subj="mlFileUploadFileStatusMappingsTab-0"]').first.click(); time.sleep(2)
    shot(page, "07d-mappings", [(("testsubj", "mlFileUploadFileStatusMappingsTab-0"), 1, "down")])
    page.get_by_text("Advanced options", exact=True).first.click(); time.sleep(2)
    shot(page, "07e-import", [(("text", "Create data view", True), 1, "right"), (("text", "Customize index settings", False), 2, "right"),
                              (("testsubj", "fileUploadImportButton"), 3, "right")], scroll_to=("testsubj", "fileUploadImportButton"))
    page.locator('[data-test-subj="fileUploadImportButton"]').first.click()
    page.locator('[data-test-subj="dataVisualizerFileResultsLinks"]').first.wait_for(timeout=120000); time.sleep(3)
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "07f-upload-sonuc", [(("testsubj", "dataVisualizerFileResultsLinks"), 1, "up")], scroll_to=("testsubj", "dataVisualizerFileResultsLinks"))
    print("yuklendi")


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"rol": rol, "kibana": kibana, "upload": upload}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
