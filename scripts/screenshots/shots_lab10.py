"""LAB-10 Adim 6 isaretli Kibana ekran goruntuleri: data view (arayuz kutusu) ve Discover'da 404 istekleri.

    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab10.py dataview   # kutu: form doldurulur, kaydedilmez
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab10.py discover
Cikti: assets/screenshots/LAB-10/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-10.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-10"
DV = "Beats logları"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-10")
SORGU = 'container.name : "nginx-beats-lab" and http.response.status_code >= 400'


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


def dataview(page):
    menu(page, "Stack Management", "06k-menu-stack-management")
    shot(page, "06l-data-views", [(("testsubj", "dataViews"), 1, "right")])
    page.locator('[data-test-subj="dataViews"]').first.click(); k.settle(page, 5)
    btn = page.locator('[data-test-subj="createDataViewButton"]:visible').first
    btn.evaluate("e => e.setAttribute('data-isaret', 'cdv')")
    shot(page, "06m-create-data-view", [(("css", '[data-isaret="cdv"]'), 1, "left")])
    btn.click(); time.sleep(3)
    page.locator('[data-test-subj="createIndexPatternNameInput"]').fill(DV)
    page.locator('[data-test-subj="createIndexPatternTitleInput"]').fill("beats-log-*"); time.sleep(3)
    page.locator('[data-test-subj="timestampField"] [data-test-subj="comboBoxSearchInput"]').click(); time.sleep(1)
    page.get_by_role("option", name="@timestamp", exact=True).first.click(); time.sleep(1)
    # Test sunucusunda data view Dev Tools ile de kuruldugu icin "already exists" uyarisi cikar; arayuz yolunu
    # secen kisi bu uyariyi gormez. Yalniz goruntu icin uyari gizlenir, form kaydedilmez.
    page.evaluate("""() => { const row = document.querySelector('[data-test-subj="createIndexPatternNameInput"]').closest('.euiFormRow');
        row.querySelectorAll('.euiFormErrorText, .euiFormControlLayoutIcons').forEach(e => e.style.display = 'none');
        row.querySelectorAll('.euiFormLabel').forEach(e => { e.classList.remove('euiFormLabel-isInvalid'); e.style.color = 'inherit'; });
        const i = row.querySelector('input'); i.removeAttribute('aria-invalid'); i.style.backgroundImage = 'none'; i.style.boxShadow = 'none'; }""")
    time.sleep(0.5)
    shot(page, "06n-data-view-form", [(("testsubj", "createIndexPatternNameInput"), 1, "left"), (("testsubj", "createIndexPatternTitleInput"), 2, "left"),
                                      (("testsubj", "timestampField"), 3, "left"), (("testsubj", "saveIndexPatternButton"), 4, "up")])
    page.get_by_role("button", name="Close").or_(page.locator('[data-test-subj="closeFlyoutButton"]')).first.click(); time.sleep(1)
    print("form kapatildi (kaydedilmedi; data view Dev Tools ile zaten var)")


def discover(page):
    menu(page, "Discover", "06a-menu-discover")
    page.locator('[data-test-subj="discover-dataView-switch-link"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="indexPattern-switcher--input"]').first.fill("Beats"); time.sleep(1.5)
    shot(page, "06b-data-view-sec", [(("testsubj", "discover-dataView-switch-link"), 1, "down"), (("testsubj", "indexPattern-switcher--input"), 2, "right"),
                                     (("css", f'[data-test-subj="dataView-{DV}"]'), 3, "right")])
    page.locator(f'[data-test-subj="dataView-{DV}"]').first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    shot(page, "06c-last-1-hour", [(("testsubj", "dateRangePickerInput"), 1, "down"), (("testsubj", "dateRangePickerPresetItem-Last_1_hour"), 2, "left")],
         scroll_to=("testsubj", "dateRangePickerPresetItem-Last_1_hour"))
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_1_hour"]').first.click(); k.settle(page, 5)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill(SORGU); page.keyboard.press("Enter"); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    print("hits:", page.locator('[data-test-subj="discoverQueryHits"]').first.inner_text())
    shot(page, "06d-discover-404", [(("testsubj", "queryInput"), 1, "down"), (("testsubj", "discoverQueryHits"), 2, "down")])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"dataview": dataview, "discover": discover}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
