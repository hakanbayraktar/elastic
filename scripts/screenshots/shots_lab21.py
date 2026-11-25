"""LAB-21: Index Management karsiliklari (Adim 1 yellow, Adim 2/4 arayuz yolu, Adim 3 red).
    Parcalar README sirasiyla: ilk_bakis, replica_arayuz (arayuz yolu), index_management, red_arayuz (arayuz yolu).
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab21.py
Cikti: assets/screenshots/LAB-21/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-21.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-21"
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-21")
HATA = []


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def index_management(page):
    """Adim 3: red index'in Index Management satiri (yalniz bakis)."""
    yonetim_ac(page)
    satir = index_ara(page, "saglik-arizali")
    shot(page, "03b-index-management-red", [(("testsubj", "indicesSearch"), 1, "ic"), (("css", satir), 2, "ic")])


# ------------------------------------------------------------------ Kibana Management karsiliklari
def yonetim_ac(page, goruntu=None):
    """Menu -> Stack Management -> Index Management."""
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = 'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("Stack Management"))'
    page.locator(link).first.scroll_into_view_if_needed(); page.locator(link).first.click(); k.settle(page, 5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "index_management"), 1, "right")])
    page.locator('[data-test-subj="index_management"]').first.click(); k.settle(page, 6)


def index_ara(page, idx):
    arama = page.locator('[data-test-subj="indicesSearch"]').first
    arama.fill(idx); page.keyboard.press("Enter"); time.sleep(2)
    satir = f'tr:has([data-test-subj="indexTableIndexNameLink"]:text-is("{idx}"))'
    for _ in range(10):
        if page.locator(satir).count():
            break
        page.get_by_role("button", name="Reload indices").first.click(); time.sleep(3)
    print("satir:", page.locator(satir).first.inner_text().replace("\n", " | ")[:200])
    return satir


def ayar_ac(page, idx, duzenle):
    page.locator(f'[data-test-subj="indexTableIndexNameLink"]:text-is("{idx}")').first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="indexDetailsTab-settings"]').first.click(); k.settle(page, 3)
    if duzenle:
        sw = page.locator('[data-test-subj="indexDetailsSettingsEditModeSwitch"]').first
        sw.wait_for(timeout=20000); time.sleep(1)
        for _ in range(3):
            if sw.get_attribute("aria-checked") != "true":
                sw.click(); time.sleep(2)
            try:
                page.locator('.monaco-editor .view-line').first.wait_for(timeout=8000); break
            except Exception:
                pass


def satir_degistir(page, anahtar, eski, yeni, tirnak_icinde):
    """Monaco'da "anahtar" satirinin degerini degistirir; tirnak yazilmaz (otomatik tirnak kapatma metni bozar).
    tirnak_icinde=True: "1" -> "0" (tirnaklar kalir). False: "olmayan-node" -> null (tirnaklar da silinir)."""
    satir = page.locator('.monaco-editor .view-line', has_text=f'"{anahtar}"').first
    once = satir.inner_text().replace("\xa0", " ").rstrip()
    satir.click(); time.sleep(0.5); page.keyboard.press("End")
    if once.endswith(","):
        page.keyboard.press("ArrowLeft")
    if tirnak_icinde:
        page.keyboard.press("ArrowLeft")
        silinecek = len(eski)
    else:
        silinecek = len(eski) + 2
    for _ in range(silinecek):
        page.keyboard.press("Backspace")
    page.keyboard.type(yeni, delay=30); time.sleep(1)
    if not tirnak_icinde:
        page.keyboard.press("Escape"); time.sleep(0.5)   # null'un otomatik tamamlama kutusu alttaki satiri ortmesin
    simdi = [l.inner_text().replace("\xa0", " ").strip() for l in page.locator('.monaco-editor .view-line').all()]
    print("SATIR:", once.strip(), "->", [t for t in simdi if anahtar in t] or simdi)


def kaydet(page):
    page.locator('[data-test-subj="indexDetailsSettingsSave"]').first.click(); k.settle(page, 4)
    print("BILDIRIM:", [t.inner_text().replace("\n", " ")[:120] for t in page.locator(".euiToast").all()])


def ayar_isaretleri(anahtar, sekme_ok):
    # sekme_ok: kisa index adinda "up" (numara basligin sagina duser), uzun adda "right"
    return [(("testsubj", "indexDetailsTab-settings"), 1, sekme_ok), (("testsubj", "indexDetailsSettingsEditModeSwitch"), 2, "left"),
            (("css", f'.monaco-editor .view-line:has-text("{anahtar}")'), 3, "left"), (("testsubj", "indexDetailsSettingsSave"), 4, "left")]


def ilk_bakis(page):
    """Adim 1: yellow index'i Index Management'ta gormek (yalniz bakis)."""
    yonetim_ac(page, "01a-index-management-menu")
    satir = index_ara(page, "kibana_sample_data_ecommerce")
    shot(page, "01b-index-yellow", [(("testsubj", "indicesSearch"), 1, "ic"), (("css", satir), 2, "ic")])


def replica_arayuz(page):
    """Adim 2 arayuz yolu: replica sayisini Settings'te 0 yapmak."""
    yonetim_ac(page)
    index_ara(page, "kibana_sample_data_ecommerce")
    ayar_ac(page, "kibana_sample_data_ecommerce", True)
    satir_degistir(page, "index.number_of_replicas", "1", "0", True)
    shot(page, "02a-replica-arayuz", ayar_isaretleri("index.number_of_replicas", "right"))
    kaydet(page)


def red_arayuz(page):
    """Adim 4 arayuz yolu: yerlesim kuralini Settings'te null yapmak."""
    yonetim_ac(page)
    index_ara(page, "saglik-arizali")
    ayar_ac(page, "saglik-arizali", True)
    satir_degistir(page, "index.routing.allocation.require._name", "olmayan-node", "null", False)
    shot(page, "04a-kural-arayuz", ayar_isaretleri("index.routing.allocation.require._name", "up"))
    kaydet(page)


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:] or ["index_management"]:
            {"index_management": index_management, "ilk_bakis": ilk_bakis, "replica_arayuz": replica_arayuz,
             "red_arayuz": red_arayuz}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
