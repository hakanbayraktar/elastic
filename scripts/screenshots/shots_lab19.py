"""LAB-19 "Bu cluster'a Kibana baglamak" kutusu: giris ve Dev Tools'ta uc node (yalniz okuma istegi).

    ssh -f -N -L 35608:127.0.0.1:15608 student@<sunucu>
    SUNUM_EKRAN=/yok KB_BASE=http://127.0.0.1:35608 python3 scripts/screenshots/shots_lab19.py kibana
Cikti: assets/screenshots/LAB-19/<ad>.png
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-19"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/yok/LAB-19")


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def kibana(page):
    page.goto(k.BASE + "/login", wait_until="domcontentloaded"); time.sleep(4)
    page.fill('input[name="username"]', "elastic")
    page.fill('input[name="password"]', "DevOps2026!")
    shot(page, "07a-giris", [(("css", 'input[name="username"]'), 1, "left"), (("css", 'input[name="password"]'), 2, "left"),
                             (("css", 'button[type="submit"]'), 3, "left")])
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/app/" in u or "space_selector" in u, timeout=60000); k.settle(page, 5)
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    for ad in ("Explore on my own", "Skip", "Dismiss"):   # ilk giriste karsilama ekrani
        try:
            page.get_by_role("button", name=ad).first.click(timeout=2000); k.settle(page, 3); break
        except Exception:
            pass
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = 'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("Dev Tools"))'
    page.locator(link).first.scroll_into_view_if_needed(); time.sleep(0.5)
    shot(page, "07b-menu-dev-tools", [(("testsubj", "toggleNavButton"), 1, "right"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)
    for txt in ("Dismiss", "Got it", "Close"):
        try:
            page.get_by_role("button", name=txt).first.click(timeout=1500)
        except Exception:
            pass
    ed = page.locator('[data-test-subj="consoleMonacoEditor"] .monaco-editor, .conApp__editor .monaco-editor').first
    ed.click(); page.keyboard.press("Meta+A"); page.keyboard.press("Backspace")
    page.keyboard.type("GET _cat/nodes?v&h=name,ip,node.role,master"); time.sleep(1)
    page.locator('[data-test-subj="sendRequestButton"]').first.click(); time.sleep(4)
    cikti = page.locator('[data-test-subj="consoleMonacoOutput"], .conApp__output').first
    print("cikti:", cikti.inner_text()[:300].replace("\n", " | "))
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "07c-cat-nodes", [(("testsubj", "sendRequestButton"), 1, "down"), (("css", '[data-test-subj="consoleMonacoOutput"], .conApp__output'), 2, "left")])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        for parca in sys.argv[1:]:
            {"kibana": kibana}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
