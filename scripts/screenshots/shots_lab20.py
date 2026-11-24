"""LAB-20 isaretli Kibana ekran goruntuleri, README sirasiyla ve GERCEKTEN yapilir.

Her kullanici ayri (temiz) tarayici oturumunda girer; her tiklama ayri goruntude.
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab20.py rol destek   # Adim 4 kutusu, Adim 5
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab20.py izleyici rapor  # Adim 6
Cikti: assets/screenshots/LAB-20/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-20.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-20"
PANO = "[eCommerce] Revenue Dashboard"
PAROLA = "Guvenlik2026!"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-20")


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def menu_ac(page):
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)


def nav(ad):
    return f'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("{ad}"))'


def giris(page, kullanici, goruntu=None):
    page.goto(k.BASE + "/login", wait_until="domcontentloaded"); time.sleep(2)
    page.fill('input[name="username"]', kullanici)
    page.fill('input[name="password"]', PAROLA)
    if goruntu:
        shot(page, goruntu, [(("css", 'input[name="username"]'), 1, "left"), (("css", 'input[name="password"]'), 2, "left"),
                             (("css", 'button[type="submit"]'), 3, "left")])
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/app/" in u or "space_selector" in u, timeout=60000)
    k.settle(page, 4)
    print(kullanici, "giris sonrasi:", page.url.replace(k.BASE, ""))


def pano_ac(page, goruntu=None):
    menu_ac(page)
    page.locator(nav("Dashboards")).first.click(); k.settle(page, 6)
    ara = page.locator('[data-test-subj="tableListSearchBox"], input[placeholder="Search…"], input[placeholder="Search..."]').first
    ara.fill("Revenue"); page.keyboard.press("Enter"); k.settle(page, 4)
    link = f'[data-test-subj="dashboardListingTitleLink-{PANO.replace(" ", "-")}"]'
    if goruntu:
        shot(page, goruntu, [(("css", '[data-test-subj="tableListSearchBox"], input[placeholder="Search…"], input[placeholder="Search..."]'), 1, "down"),
                             (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 10)
    dugmeler = [b.inner_text().strip() for b in page.get_by_role("button").all() if b.is_visible() and b.inner_text().strip()]
    print("Edit var mi:", "Edit" in dugmeler, "| Share:", "Share" in dugmeler, "| Export:", "Export" in dugmeler)
    page.mouse.move(800, 60); time.sleep(1)


# ------------------------------------------------------------------ Adim 4 kutusu: rol arayuzde (elastic)
def rol(page):
    k.login(page)
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    menu_ac(page); page.locator(nav("Stack Management")).first.scroll_into_view_if_needed()
    page.locator(nav("Stack Management")).first.click(); k.settle(page, 5)
    shot(page, "04a-roles-menu", [(("testsubj", "roles"), 1, "right")])
    page.locator('[data-test-subj="roles"]').first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="checkboxSelectRow-gvn-destek"]').first.scroll_into_view_if_needed()
    shot(page, "04b-roles-listesi", [(("css", 'a:text-is("gvn-destek")'), 1, "right")])
    page.locator('a:text-is("gvn-destek")').first.click(); k.settle(page, 6)
    shot(page, "04c-rol-index", [(("testsubj", "indicesInput0"), 1, "left"), (("testsubj", "privilegesInput0"), 2, "left"),
                                 (("testsubj", "deniedFieldInput0"), 3, "left"), (("testsubj", "queryInput0"), 4, "left")],
         scroll_to=("testsubj", "indicesInput0"))
    shot(page, "04d-rol-kibana", [(("testsubj", "spacesColumn"), 1, "down"), (("testsubj", "privilegeColumn"), 2, "down")],
         scroll_to=("testsubj", "spacesColumn"))
    page.locator('[data-test-subj="roleFormCancelButton"]').first.click(); time.sleep(2)


# ------------------------------------------------------------------ Adim 5: destek kullanicisi
def destek(page):
    giris(page, "gvn_destek", "05a-giris")
    menu_ac(page)
    menu = sorted(set(a.inner_text().strip() for a in page.locator("nav a").all() if a.is_visible() and a.inner_text().strip()))
    print("destek menu:", menu)
    shot(page, "05b-destek-menu", [(("testsubj", "spacesNavSelector"), 1, "right"), (("css", nav("Discover")), 2, "right")])
    page.locator(nav("Discover")).first.click(); k.settle(page, 8)
    sw = page.locator('[data-test-subj="discover-dataView-switch-link"]').first
    if "Destek talepleri" not in sw.inner_text():
        sw.click(); time.sleep(2)
        shot(page, "05c-data-view", [(("testsubj", "discover-dataView-switch-link"), 1, "down"), (("text", "Destek talepleri", True), 2, "right")])
        page.get_by_text("Destek talepleri", exact=True).last.click(); k.settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    p = page.locator('[data-test-subj="dateRangePickerPresetItem-Last_30_days"]').first
    p.scroll_into_view_if_needed()
    shot(page, "05d-zaman", [(("testsubj", "dateRangePickerInput"), 1, "down"),
                             (("testsubj", "dateRangePickerPresetItem-Last_30_days"), 2, "left")],
         scroll_to=("testsubj", "dateRangePickerPresetItem-Last_30_days"))
    p.click(); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    print("hits:", page.locator('[data-test-subj="discoverQueryHits"]').first.inner_text())
    alanlar = [e.inner_text().strip() for e in page.locator('[data-test-subj="fieldListGroupedAvailableFields"] [data-test-subj^="field-"]').all()]
    print("alanlar:", alanlar[:20])
    shot(page, "05e-destek-sonuc", [(("testsubj", "discoverQueryHits"), 1, "down"),
                                    (("testsubj", "fieldListGroupedAvailableFields"), 2, "right")])


# ------------------------------------------------------------------ Adim 6: viewer ve gvn-rapor
def izleyici(page):
    giris(page, "gvn_izleyici")
    if "space_selector" in page.url:
        shot(page, "06a-space-secim", [(("testsubj", "space-card-default"), 1, "down")])
        page.locator('[data-test-subj="space-card-default"]').first.click()
        page.wait_for_url(lambda u: "/app/" in u, timeout=60000); k.settle(page, 4)
    menu_ac(page)
    shot(page, "06b-izleyici-menu", [(("css", '[data-test-subj="collapsibleNav"], .euiCollapsibleNav'), 1, "right")])
    page.keyboard.press("Escape"); time.sleep(1)
    pano_ac(page, "06c-pano-ara")
    shot(page, "06c-izleyici-pano", [(("testsubj", "shareTopNavButton"), 1, "down"), (("testsubj", "exportTopNavButton"), 2, "down")])


def rapor(page):
    giris(page, "gvn_rapor")
    menu_ac(page)
    menu = sorted(set(a.inner_text().strip() for a in page.locator("nav a").all() if a.is_visible() and a.inner_text().strip()))
    print("rapor menu:", menu)
    shot(page, "06d-rapor-menu", [(("css", nav("Dashboards")), 1, "right")])
    page.keyboard.press("Escape"); time.sleep(1)
    pano_ac(page)
    shot(page, "06e-rapor-pano", [(("testsubj", "exportTopNavButton"), 1, "down")])
    page.goto(k.BASE + "/app/dev_tools", wait_until="domcontentloaded"); k.settle(page, 6)
    print("dev_tools:", page.locator("body").inner_text()[:120].replace("\n", " | "))
    shot(page, "06f-devtools-yok", [(("text", "You do not have permission to access the requested page", False), 1, "down")])
    page.goto(k.BASE + "/app/management", wait_until="domcontentloaded"); k.settle(page, 6)
    print("management:", page.locator("body").inner_text()[:80].replace("\n", " | "))


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        for parca in sys.argv[1:]:
            ctx = br.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)   # her kullanici temiz oturum
            page = ctx.new_page()
            {"rol": rol, "destek": destek, "izleyici": izleyici, "rapor": rapor}[parca](page)
            ctx.close()
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
