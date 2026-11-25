"""LAB-17 Kibana Spaces ve saved objects: isaretli ekran goruntuleri, README sirasiyla ve GERCEKTEN yapilir.

Her tiklama ayri goruntude; sayfalara adresle degil menuden gidilir (README'deki yol).
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py olustur ozellik kopya export
    (Adim 5'teki Pazarlama Space'i README'deki Dev Tools istegiyle acildiktan sonra)
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab17.py import dogrula sil geri
On kosul: LAB-04 ornek e-ticaret verisi. Cikti: assets/screenshots/LAB-17/<ad>.png.
"""
import os
import sys
import tempfile
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-17"
PANO = "[eCommerce] Revenue Dashboard"
PANO_ID = "722b74f0-b882-11e8-a6d9-e546fe2bba5f"
EXPORT = os.environ.get("EXPORT_DOSYA", os.path.join(tempfile.gettempdir(), "lab17-export.ndjson"))
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-17")


def subj(page, *w):
    return sorted(set(x for x in (e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]:visible").all())
                      if x and (not w or any(s in x.lower() for s in w))))


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):   # sunum icin isaretsiz kopya
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def karsilama(page):
    for t in ("Explore on my own", "Skip"):   # yeni Space'in karsilama ekrani tiklamayi engeller
        try:
            page.get_by_text(t, exact=True).first.click(timeout=2000); k.settle(page, 3)
        except Exception:
            pass


def menu_link(page, ad):
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    return f'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("{ad}"))'


def yonetim(page, bolum, ad_menu, ad_bolum, space=""):
    """Menu > Stack Management > sol listeden bolum (spaces, objects)."""
    page.goto(k.BASE + space + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4); karsilama(page)
    link = menu_link(page, "Stack Management")
    page.locator(link).first.scroll_into_view_if_needed(); time.sleep(1)
    if ad_menu:
        shot(page, ad_menu, [(("testsubj", "toggleNavButton"), 1, "right"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 5)
    sol = f'[data-test-subj="{bolum}"]'
    if ad_bolum:
        shot(page, ad_bolum, [(("css", sol), 1, "right")])
    page.locator(sol).first.click(); k.settle(page, 5)


def space_sec(page, ad, goruntu=None):
    page.locator('[data-test-subj="spacesNavSelector"]').first.click(); time.sleep(2)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "spacesNavSelector"), 1, "right"),
                             (("css", f'[role="option"]:has-text("{ad}")'), 2, "right")])
    page.locator(f'[role="option"]:has-text("{ad}")').first.click(); k.settle(page, 6); karsilama(page)


# ------------------------------------------------------------------ Adim 1
def olustur(page):
    yonetim(page, "spaces", "01a-menu-stack-management", "01b-spaces")
    print("spaces sayfasi:", subj(page, "create", "space")[:10])
    yeni = '[data-test-subj="createSpace"], button:has-text("Create space"), a:has-text("Create space")'
    shot(page, "01c-create-space", [(("css", yeni), 1, "left")])
    page.locator(yeni).first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="addSpaceName"]').fill("Satış ekibi"); time.sleep(1)
    u = page.locator('[data-test-subj="spaceURLDisplay"]').first
    print("URL identifier (otomatik):", u.input_value())
    u.fill("satis-ekibi"); time.sleep(0.5)
    page.locator('[data-test-subj="solutionViewSelect"]').first.click(); time.sleep(1)
    print("solution view secenekleri:", [o.inner_text().strip().split("\n")[0] for o in page.locator('[role="option"]').all()])
    shot(page, "01d-solution-view", [(("css", '[role="option"]:has-text("Classic")'), 1, "left")])
    page.locator('[role="option"]:has-text("Classic")').first.click(); time.sleep(1)
    page.locator('[data-test-subj="addSpaceName"]').scroll_into_view_if_needed(); time.sleep(1)
    shot(page, "01e-space-formu", [(("testsubj", "addSpaceName"), 1, "left"), (("testsubj", "spaceURLDisplay"), 2, "left"),
                                   (("testsubj", "solutionViewSelect"), 3, "left")], scroll_to=("testsubj", "addSpaceName"))
    ini = page.locator('[data-test-subj="spaceLetterInitial"]').first
    ini.scroll_into_view_if_needed(); ini.fill("SE"); time.sleep(1)
    page.locator('[data-test-subj="save-space-button"]').first.scroll_into_view_if_needed(); time.sleep(1)
    shot(page, "01f-avatar-kaydet", [(("testsubj", "spaceLetterInitial"), 1, "left"), (("testsubj", "save-space-button"), 2, "up")],
         scroll_to=("testsubj", "save-space-button"))
    page.locator('[data-test-subj="save-space-button"]').first.click(); k.settle(page, 5)
    print("kaydedildi:", page.url.replace(k.BASE, ""))
    shot(page, "01g-space-listesi", [(("css", 'a:has-text("Satış ekibi"), button:has-text("Satış ekibi")'), 1, "right")])


# ------------------------------------------------------------------ Adim 2
def ozellik(page):
    page.locator('a:has-text("Satış ekibi"), button:has-text("Satış ekibi")').first.click(); k.settle(page, 6)
    for kat in ("observability", "securitySolution"):
        cb = page.locator(f'[data-test-subj="featureCategoryCheckbox_{kat}"]').first
        cb.scroll_into_view_if_needed()
        if cb.is_checked():
            cb.click(); time.sleep(0.5)
    page.locator('[data-test-subj="featureCategoryButton_kibana"]').first.click(); time.sleep(1)
    ml = page.locator('[data-test-subj="featureCheckbox_ml"]').first
    if ml.is_checked():
        ml.click(); time.sleep(0.5)
    page.locator('[data-test-subj="featureCategoryCheckbox_observability"]').first.scroll_into_view_if_needed(); time.sleep(1)
    shot(page, "02a-ozellikler", [(("testsubj", "featureCategoryCheckbox_observability"), 1, "left"),
                                  (("testsubj", "featureCategoryCheckbox_securitySolution"), 2, "left"),
                                  (("testsubj", "featureCategoryButton_kibana"), 3, "left"),
                                  (("testsubj", "featureCheckbox_ml"), 4, "left")],
         scroll_to=("testsubj", "featureCategoryCheckbox_observability"))
    kaydet = page.locator('[data-test-subj="save-space-button"]')
    kaydet.first.scroll_into_view_if_needed(); time.sleep(1)
    shot(page, "02b-apply", [(("testsubj", "save-space-button"), 1, "up")], scroll_to=("testsubj", "save-space-button"))
    kaydet.first.click(); time.sleep(2)
    for t in ("Update space", "Confirm", "Apply changes"):
        b = page.get_by_role("button", name=t)
        if b.count() and b.first.is_visible():
            shot(page, "02c-onay", [(("role", "button", t), 1, "up")])
            b.first.click(); time.sleep(2)
    k.settle(page, 4)
    # menuleri karsilastir
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 5); karsilama(page)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    shot(page, "02d-menu-default", [(("testsubj", "spacesNavSelector"), 1, "right")])
    page.keyboard.press("Escape"); time.sleep(1)
    space_sec(page, "Satış ekibi", "02e-space-sec")
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    menu = sorted(set(a.inner_text().strip() for a in page.locator("nav a, nav button").all() if a.is_visible() and a.inner_text().strip()))
    print("satis menu:", menu)
    shot(page, "02f-menu-satis", [(("testsubj", "spacesNavSelector"), 1, "right"),
                                  (("css", '[data-test-subj="collapsibleNav"], .euiCollapsibleNav'), 2, "right")])
    page.keyboard.press("Escape"); time.sleep(1)


# ------------------------------------------------------------------ Adim 3
def kopya(page):
    page.goto(k.BASE + "/s/satis-ekibi/app/home", wait_until="domcontentloaded"); k.settle(page, 4); karsilama(page)
    space_sec(page, "Default", "03a-default-don")
    yonetim(page, "objects", None, "03b-saved-objects")
    page.locator('[data-test-subj="savedObjectSearchBar"]').first.fill("Revenue"); page.keyboard.press("Enter"); k.settle(page, 4)
    satir = page.locator(f'tr:has-text("{PANO}")').first
    shot(page, "03c-arama", [(("testsubj", "savedObjectSearchBar"), 1, "down"),
                             (("css", f'tr:has-text("{PANO}") [data-test-subj="euiCollapsedItemActionsButton"]'), 2, "left")])
    satir.locator('[data-test-subj="euiCollapsedItemActionsButton"]').first.click(); time.sleep(1.5)
    kopyala = '[data-test-subj*="copy_saved_objects_to_space"], button:has-text("Copy to space")'
    shot(page, "03d-copy-menu", [(("css", kopyala), 1, "left")])
    page.locator(kopyala).first.click(); time.sleep(3)
    hedef = '[data-test-subj="cts-space-selector-row-satis-ekibi"], [role="dialog"] li:has-text("Satış ekibi")'
    page.locator(hedef).first.click(); time.sleep(1)
    shot(page, "03e-copy-hedef", [(("css", hedef), 1, "left"), (("testsubj", "cts-initiate-button"), 2, "up")])
    page.locator('[data-test-subj="cts-initiate-button"]').first.click(); time.sleep(6)
    print("sonuc:", page.locator('[role="dialog"]').first.inner_text()[:300].replace("\n", " | "))
    shot(page, "03f-copy-sonuc", [(("testsubj", "cts-finish-button"), 1, "up")])
    if page.locator('[data-test-subj="cts-finish-button"]').count():
        page.locator('[data-test-subj="cts-finish-button"]').first.click(); time.sleep(2)


# ------------------------------------------------------------------ Adim 4
def export(page):
    page.locator('[data-test-subj="savedObjectSearchBar"]').first.fill("Revenue"); page.keyboard.press("Enter"); k.settle(page, 4)
    kutu = f'[data-test-subj="checkboxSelectRow-dashboard:{PANO_ID}"]'
    page.locator(kutu).first.click(); time.sleep(1.5)
    shot(page, "04a-export-sec", [(("css", kutu), 1, "right"), (("role", "button", "Export", True), 2, "down")])
    page.get_by_role("button", name="Export", exact=True).first.click(); time.sleep(2)
    print("modal:", page.locator('[role="dialog"]').first.inner_text()[:300].replace("\n", " | "))
    shot(page, "04b-export-ayar", [(("css", '.euiPopover__panel [role="switch"]'), 1, "left"),
                                   (("css", 'role=button[name="Export"s] >> nth=1'), 2, "left")],
         scroll_to=("css", '.euiPopover__panel [role="switch"], [role="switch"]'))
    with page.expect_download() as d:
        page.locator('role=button[name="Export"s] >> nth=1').evaluate("e => e.click()")
    d.value.save_as(EXPORT)
    print("indirilen:", d.value.suggested_filename, "satir:", sum(1 for _ in open(EXPORT)))


# ------------------------------------------------------------------ Adim 5 (Pazarlama Space'i Dev Tools ile acilmis olmali)
def import_(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4); karsilama(page)
    space_sec(page, "Pazarlama", "05a-space-pazarlama")
    yonetim(page, "objects", None, None, space="/s/pazarlama")
    shot(page, "05b-import-dugme", [(("testsubj", "importObjects"), 1, "down")])
    page.locator('[data-test-subj="importObjects"]').first.click(); time.sleep(2)
    page.locator('[role="dialog"] input[type="file"]').first.set_input_files(EXPORT); time.sleep(2)
    shot(page, "05c-import", [(("css", '[role="dialog"] input[type="file"]'), 1, "left"),
                              (("css", '[role="dialog"] fieldset'), 2, "left"),
                              (("testsubj", "importSavedObjectsImportBtn"), 3, "up")])
    page.locator('[data-test-subj="importSavedObjectsImportBtn"]').first.click(); time.sleep(6)
    print("import sonucu:", page.locator('[role="dialog"]').first.inner_text()[:300].replace("\n", " | "))
    shot(page, "05d-import-sonuc", [(("css", '[data-test-subj="importSavedObjectsDoneBtn"], [data-test-subj="importSavedObjectsConfirmBtn"]'), 1, "up")])
    for t in ("importSavedObjectsDoneBtn", "importSavedObjectsConfirmBtn"):
        if page.locator(f'[data-test-subj="{t}"]').count():
            page.locator(f'[data-test-subj="{t}"]').first.click(); time.sleep(2)


# ------------------------------------------------------------------ Adim 6
def dogrula(page):
    page.goto(k.BASE + "/s/pazarlama/app/home", wait_until="domcontentloaded"); k.settle(page, 4); karsilama(page)
    link = menu_link(page, "Dashboards")
    shot(page, "06a-menu-dashboards", [(("css", link), 1, "right")])
    page.locator(link).first.click(); k.settle(page, 5)
    satir = f'[data-test-subj="dashboardListingTitleLink-{PANO.replace(" ", "-")}"]'
    shot(page, "06b-pano-listesi", [(("css", satir), 1, "right")])
    page.locator(satir).first.click(); k.settle(page, 12)
    hata = page.locator('[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"]').count()
    print("pano:", page.url.replace(k.BASE, "")[:60], "| hatali panel:", hata)
    shot(page, "06c-pazarlama-pano", [(("css", '[data-test-subj="spacesNavSelector"]'), 1, "right"),
                                      (("css", '[data-test-subj="dashboardPanel"]'), 2, "right")])


# ------------------------------------------------------------------ kutu: sil ve geri yukle
def sil(page):
    yonetim(page, "objects", None, None, space="/s/pazarlama")
    page.locator('[data-test-subj="savedObjectSearchBar"]').first.fill("Orders by Country"); page.keyboard.press("Enter"); k.settle(page, 4)
    page.locator('[data-test-subj^="checkboxSelectRow-map:"]').first.click(); time.sleep(1.5)
    shot(page, "07a-sil-harita", [(("css", '[data-test-subj^="checkboxSelectRow-map:"]'), 1, "right"),
                                  (("testsubj", "savedObjectsManagementDelete"), 2, "down")])
    page.locator('[data-test-subj="savedObjectsManagementDelete"]').first.click(); time.sleep(2)
    shot(page, "07b-sil-onay", [(("testsubj", "confirmModalConfirmButton"), 1, "up")])
    page.locator('[data-test-subj="confirmModalConfirmButton"]').first.click(); k.settle(page, 4)
    page.goto(k.BASE + "/s/pazarlama/app/dashboards", wait_until="domcontentloaded"); k.settle(page, 6)
    page.get_by_text(PANO, exact=True).first.click(); k.settle(page, 12)
    hata = '[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"], [data-test-subj="embeddablePanelError"]'
    print("hatali panel:", page.locator(hata).count())
    shot(page, "07c-eksik-panel", [(("css", hata), 1, "left")])


def geri(page):
    yonetim(page, "objects", None, None, space="/s/pazarlama")
    page.locator('[data-test-subj="importObjects"]').first.click(); time.sleep(2)
    page.locator('[role="dialog"] input[type="file"]').first.set_input_files(EXPORT); time.sleep(2)
    page.locator('label[for="overwriteEnabled"]').first.click(); time.sleep(1)
    shot(page, "07d-geri-yukle", [(("css", '[role="dialog"] input[type="file"]'), 1, "left"),
                                  (("css", 'label[for="overwriteEnabled"]'), 2, "left"),
                                  (("testsubj", "importSavedObjectsImportBtn"), 3, "up")])
    page.locator('[data-test-subj="importSavedObjectsImportBtn"]').first.click(); time.sleep(6)
    print("import sonucu:", page.locator('[role="dialog"]').first.inner_text()[:400].replace("\n", " | "))
    for t in ("importSavedObjectsDoneBtn", "importSavedObjectsConfirmBtn"):
        if page.locator(f'[data-test-subj="{t}"]').count():
            page.locator(f'[data-test-subj="{t}"]').first.click(); time.sleep(2)
    page.goto(k.BASE + "/s/pazarlama/app/dashboards", wait_until="domcontentloaded"); k.settle(page, 6)
    page.get_by_text(PANO, exact=True).first.click(); k.settle(page, 12)
    print("hatali panel (geri sonrasi):", page.locator('[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"], [data-test-subj="embeddablePanelError"]').count())


def geri_bak(page):
    """Kutunun son adimi: geri yuklemeden sonra panoyu acmak; yalniz okuma."""
    page.goto(k.BASE + "/s/pazarlama/app/dashboards", wait_until="domcontentloaded"); k.settle(page, 6)
    page.get_by_text(PANO, exact=True).first.click(); k.settle(page, 14)
    hata = '[data-test-subj="embeddableError"], [data-test-subj="embeddableStackError"], [data-test-subj="embeddablePanelError"]'
    harita = page.locator('[data-test-subj="dashboardPanel"]').filter(has=page.locator('[data-test-subj="mapContainer"], .mapboxgl-canvas, .maplibregl-canvas')).first
    print("hatali panel:", page.locator(hata).count(), "| harita paneli:", harita.count())
    harita.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(4)
    harita.evaluate("e => e.setAttribute('data-isaret', 'harita')")
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "07e-geri-pano", [(("css", '[data-isaret="harita"]'), 1, "ic")], scroll_to=("css", '[data-isaret="harita"]'))


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE, accept_downloads=True)
        k.login(page)
        for parca in sys.argv[1:]:
            {"olustur": olustur, "ozellik": ozellik, "kopya": kopya, "export": export, "import": import_,
             "dogrula": dogrula, "sil": sil, "geri": geri, "geri_bak": geri_bak}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
