"""LAB-17 Kibana Spaces ve saved objects: isaretli ekran goruntuleri (README sirasiyla, GERCEKTEN yapilir).

Kullanim (yerelde, sunucuya SSH tuneli acikken; LAB-04 ornek verisi kurulu):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py olustur    # Adim 1
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py ozellik    # Adim 2
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py kopya      # Adim 3
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py export     # Adim 4 (dosya: /tmp yerine EXPORT_DOSYA)
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py import     # Adim 5 (Pazarlama API ile acilmis olmali)
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py dogrula    # Adim 6
Cikti: assets/screenshots/LAB-17/<ad>.png; olculenler stdout'a yazilir.
"""
import os
import sys
import tempfile
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-17"
PANO = "[eCommerce] Revenue Dashboard"
EXPORT = os.environ.get("EXPORT_DOSYA", os.path.join(tempfile.gettempdir(), "lab17-export.ndjson"))


def subj(page, *w):
    return sorted(set(x for x in (e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all())
                      if x and (not w or any(s in x.lower() for s in w))))


def olustur(page):
    page.goto(k.BASE + "/app/management/kibana/spaces/create", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="addSpaceName"]').fill("Satış ekibi"); time.sleep(1)
    u = page.locator('[data-test-subj="spaceURLDisplay"]').first
    print("URL identifier (otomatik):", u.input_value())
    u.fill("satis-ekibi"); time.sleep(0.5)
    page.locator('[data-test-subj="solutionViewSelect"]').first.click(); time.sleep(1)
    secenek = [o.inner_text().strip().split("\n")[0] for o in page.locator('[role="option"]').all()]
    print("solution view secenekleri:", secenek)
    page.locator('[role="option"]:has-text("Classic")').first.click(); time.sleep(1)
    ini = page.locator('[data-test-subj="spaceLetterInitial"]').first
    ini.scroll_into_view_if_needed(); ini.fill("SE"); time.sleep(1)
    page.locator('[data-test-subj="addSpaceName"]').scroll_into_view_if_needed(); time.sleep(1)
    k.shoot(page, LAB, "01-space-olustur", [
        (("testsubj", "addSpaceName"), 1, "left"),
        (("testsubj", "spaceURLDisplay"), 2, "left"),
        (("testsubj", "solutionViewSelect"), 3, "left"),
    ], scroll_to=("testsubj", "addSpaceName"))
    page.locator('[data-test-subj="save-space-button"]').first.click(); k.settle(page, 5)
    hatalar = [e.inner_text() for e in page.locator(".euiFormErrorText, .euiCallOut--danger").all() if e.is_visible()]
    print("kaydedildi:", page.url.replace(k.BASE, ""), "| hata:", hatalar)


def ozellik(page):
    page.goto(k.BASE + "/app/management/kibana/spaces/edit/satis-ekibi", wait_until="domcontentloaded"); k.settle(page, 6)
    for kat in ("observability", "securitySolution"):
        cb = page.locator(f'[data-test-subj="featureCategoryCheckbox_{kat}"]').first
        cb.scroll_into_view_if_needed()
        if cb.is_checked(): cb.click(); time.sleep(0.5)
    page.locator('[data-test-subj="featureCategoryButton_kibana"]').first.click(); time.sleep(1)
    ml = page.locator('[data-test-subj="featureCheckbox_ml"]').first
    if ml.is_checked(): ml.click(); time.sleep(0.5)
    page.locator('[data-test-subj="featureCategoryCheckbox_observability"]').first.scroll_into_view_if_needed(); time.sleep(1)
    k.shoot(page, LAB, "02-space-ozellik", [
        (("testsubj", "featureCategoryCheckbox_observability"), 4, "left"),
        (("testsubj", "featureCategoryCheckbox_securitySolution"), None, "left"),
        (("testsubj", "featureCheckbox_ml"), None, "left"),
    ], scroll_to=("testsubj", "featureCategoryCheckbox_observability"))
    kaydet = page.locator('[data-test-subj="save-space-button"]')
    if kaydet.count():  # ayar zaten kayitliysa (ikinci kosu) dugme cikmaz
        kaydet.first.click(); time.sleep(2)
    for t in ("Update space", "Confirm", "Apply changes"):
        b = page.get_by_role("button", name=t)
        if b.count() and b.first.is_visible():
            b.first.click(); time.sleep(2)
    k.settle(page, 4)
    # menuler
    for space, ad in (("", "03-menu-default"), ("/s/satis-ekibi", "04-menu-satis")):
        page.goto(k.BASE + space + "/app/home", wait_until="domcontentloaded"); k.settle(page, 6)
        for t in ("Explore on my own", "Skip"):  # yeni Space'in karsilama ekrani tiklamayi engelliyor
            try: page.get_by_text(t, exact=True).first.click(timeout=2000); k.settle(page, 3)
            except Exception: pass
        page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
        menu = sorted(set(a.inner_text().strip() for a in page.locator("nav a, nav button").all() if a.is_visible() and a.inner_text().strip()))
        print(ad, "menu:", menu)
        isaret = [(("testsubj", "spacesNavSelector"), 5, "right"), (("css", '[data-test-subj="collapsibleNav"], .euiCollapsibleNav, [data-test-subj="projectLayoutSideNav"]'), 6, "right")] if space else []
        k.shoot(page, LAB, ad, isaret)


def kopya(page):
    page.goto(k.BASE + "/app/management/kibana/objects", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="savedObjectSearchBar"]').first.fill("Revenue"); page.keyboard.press("Enter"); k.settle(page, 4)
    satir = page.locator(f'tr:has-text("{PANO}")').first
    satir.locator('[data-test-subj="euiCollapsedItemActionsButton"]').first.click(); time.sleep(1.5)
    print("aksiyonlar:", subj(page, "action", "copy", "space"))
    k.shoot(page, LAB, "05-copy-menu", [
        (("css", '[data-test-subj*="copy_saved_objects_to_space"], button:has-text("Copy to space")'), 7, "left"),
    ])
    page.locator('[data-test-subj*="copy_saved_objects_to_space"], button:has-text("Copy to space")').first.click(); time.sleep(3)
    print("flyout:", subj(page, "cts", "space"))
    page.locator('[data-test-subj="cts-space-selector-row-satis-ekibi"], [role="dialog"] li:has-text("Satış ekibi")').first.click(); time.sleep(1)
    k.shoot(page, LAB, "06-copy-hedef", [
        (("css", '[data-test-subj="cts-space-selector-row-satis-ekibi"], [role="dialog"] li:has-text("Satış ekibi")'), 8, "left"),
        (("testsubj", "cts-initiate-button"), 9, "up"),
    ])
    page.locator('[data-test-subj="cts-initiate-button"]').first.click(); time.sleep(6)
    print("sonuc:", page.locator('[role="dialog"]').first.inner_text()[:300].replace("\n", " | "))
    for t in ("cts-finish-button",):
        if page.locator(f'[data-test-subj="{t}"]').count(): page.locator(f'[data-test-subj="{t}"]').first.click(); time.sleep(2)


def export(page):
    page.goto(k.BASE + "/app/management/kibana/objects", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="savedObjectSearchBar"]').first.fill("Revenue"); page.keyboard.press("Enter"); k.settle(page, 4)
    page.locator('[data-test-subj="checkboxSelectRow-dashboard:722b74f0-b882-11e8-a6d9-e546fe2bba5f"]').first.click(); time.sleep(1.5)
    print("ust dugmeler:", subj(page, "export"))
    page.get_by_role("button", name="Export", exact=True).first.click(); time.sleep(2)
    print("modal:", page.locator('[role="dialog"]').first.inner_text()[:300].replace("\n", " | "))
    k.shoot(page, LAB, "07-export", [
        (("testsubj", "checkboxSelectRow-dashboard:722b74f0-b882-11e8-a6d9-e546fe2bba5f"), 10, "right"),
        (("css", '.euiPopover__panel [role="switch"]'), 11, "left"),
        (("css", 'role=button[name="Export"s] >> nth=1'), 12, "left"),
    ], scroll_to=("css", '.euiPopover__panel [role="switch"], [role="switch"]'))
    with page.expect_download() as d:
        page.locator('role=button[name="Export"s] >> nth=1').evaluate("e => e.click()")
    d.value.save_as(EXPORT)
    print("indirilen:", d.value.suggested_filename, "satir:", sum(1 for _ in open(EXPORT)))


def import_(page):
    page.goto(k.BASE + "/s/pazarlama/app/management/kibana/objects", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="importObjects"]').first.click(); time.sleep(2)
    page.locator('[role="dialog"] input[type="file"]').first.set_input_files(EXPORT); time.sleep(2)
    print("import flyout:", subj(page, "import", "overwrite", "conflict", "radio"))
    k.shoot(page, LAB, "08-import", [
        (("css", '[role="dialog"] input[type="file"]'), 13, "left"),
        (("css", '[role="dialog"] fieldset, [data-test-subj="savedObjectsManagement-importModeControl-createNewCopiesEnabled"]'), 14, "left"),
        (("testsubj", "importSavedObjectsImportBtn"), 15, "up"),
    ])
    page.locator('[data-test-subj="importSavedObjectsImportBtn"]').first.click(); time.sleep(6)
    print("import sonucu:", page.locator('[role="dialog"]').first.inner_text()[:300].replace("\n", " | "))
    for t in ("importSavedObjectsDoneBtn", "importSavedObjectsConfirmBtn"):
        if page.locator(f'[data-test-subj="{t}"]').count(): page.locator(f'[data-test-subj="{t}"]').first.click(); time.sleep(2)


def dogrula(page):
    page.goto(k.BASE + "/s/pazarlama/app/dashboards", wait_until="domcontentloaded"); k.settle(page, 6)
    page.get_by_text(PANO, exact=True).first.click(); k.settle(page, 12)
    hata = page.locator('[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"]').count()
    print("pano:", page.url.replace(k.BASE, "")[:60], "| hatali panel:", hata)
    k.shoot(page, LAB, "09-pazarlama-pano", [
        (("css", '[data-test-subj="breadcrumb last"], [data-test-subj="breadcrumbs"]'), 16, "down"),
        (("css", '[data-test-subj="dashboardPanel"]'), 17, "right"),
    ])


def sil(page):
    """Kutu: Pazarlama'da haritayi silmek ve panoda eksik paneli gormek."""
    page.goto(k.BASE + "/s/pazarlama/app/management/kibana/objects", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="savedObjectSearchBar"]').first.fill("Orders by Country"); page.keyboard.press("Enter"); k.settle(page, 4)
    kutu = page.locator('[data-test-subj^="checkboxSelectRow-map:"]').first
    kutu.click(); time.sleep(1.5)
    print("sil dugmeleri:", subj(page, "delete"))
    k.shoot(page, LAB, "10-sil-harita", [
        (("css", '[data-test-subj^="checkboxSelectRow-map:"]'), 1, "right"),
        (("testsubj", "savedObjectsManagementDelete"), 2, "down")])
    page.locator('[data-test-subj="savedObjectsManagementDelete"]').first.click(); time.sleep(2)
    print("onay:", subj(page, "confirm", "delete"))
    page.locator('[data-test-subj="confirmModalConfirmButton"]').first.click(); k.settle(page, 4)
    page.goto(k.BASE + "/s/pazarlama/app/dashboards", wait_until="domcontentloaded"); k.settle(page, 6)
    page.get_by_text(PANO, exact=True).first.click(); k.settle(page, 12)
    hata = page.locator('[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"], [data-test-subj="embeddablePanelError"]')
    print("hatali panel:", hata.count(), subj(page, "error"))
    k.shoot(page, LAB, "11-eksik-panel", [(("css", '[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"], [data-test-subj="embeddablePanelError"]'), 3, "left")])


def geri(page):
    """Kutu: ayni export dosyasini Pazarlama'ya yeniden yuklemek (cakismalarin uzerine yaz)."""
    page.goto(k.BASE + "/s/pazarlama/app/management/kibana/objects", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="importObjects"]').first.click(); time.sleep(2)
    page.locator('[role="dialog"] input[type="file"]').first.set_input_files(EXPORT); time.sleep(2)
    print("secenekler:", subj(page, "overwrite", "conflict", "import"))
    page.locator('label[for="overwriteEnabled"]').first.click(); time.sleep(1)  # Automatically overwrite conflicts
    k.shoot(page, LAB, "12-geri-yukle", [
        (("css", '[role="dialog"] input[type="file"]'), 4, "left"),
        (("css", 'label[for="overwriteEnabled"]'), 5, "left"),
        (("testsubj", "importSavedObjectsImportBtn"), 6, "up")])
    page.locator('[data-test-subj="importSavedObjectsImportBtn"]').first.click(); time.sleep(6)
    print("import sonucu:", page.locator('[role="dialog"]').first.inner_text()[:400].replace("\n", " | "))
    for t in ("importSavedObjectsDoneBtn", "importSavedObjectsConfirmBtn"):
        if page.locator(f'[data-test-subj="{t}"]').count(): page.locator(f'[data-test-subj="{t}"]').first.click(); time.sleep(2)
    page.goto(k.BASE + "/s/pazarlama/app/dashboards", wait_until="domcontentloaded"); k.settle(page, 6)
    page.get_by_text(PANO, exact=True).first.click(); k.settle(page, 12)
    hata = page.locator('[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"], [data-test-subj="embeddablePanelError"]').count()
    print("hatali panel (geri sonrasi):", hata)


if __name__ == "__main__":
    parca = sys.argv[1]
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE, accept_downloads=True)
        k.login(page)
        {"olustur": olustur, "ozellik": ozellik, "kopya": kopya, "export": export, "import": import_, "dogrula": dogrula, "sil": sil, "geri": geri}[parca](page)
        br.close()
