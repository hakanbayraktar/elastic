"""LAB-23 Adim 4 kutusu: repository, snapshot'lar ve SLM politikasi LAB-19 cluster'inin Kibana'sinda (degistirmeden).
On kosul: LAB-19 Kibana kutusu (kibana-cluster, 15608) ve LAB-23 Adim 1-4.
    ssh -f -N -L 35608:127.0.0.1:15608 student@<sunucu>
    KB_BASE=http://127.0.0.1:35608 python3 scripts/screenshots/shots_lab23.py
Cikti: assets/screenshots/LAB-23/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-23.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-23"
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-23")
HATA = []


def shot(page, ad, marks, **kw):
    try:
        k.shoot(page, LAB, ad, marks, **kw)
    except Exception as e:
        HATA.append(ad); print("HATA", ad, str(e)[:160]); return
    if SUNUM and os.path.isdir(os.path.dirname(SUNUM)):
        os.makedirs(SUNUM, exist_ok=True)
        k.shoot(page, SUNUM, ad, [])


def sekme(page, ad):
    return f'[role="tab"]:has-text("{ad}")'


def snapshot(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    for t in ("Explore on my own", "Skip"):
        try:
            page.get_by_text(t, exact=True).first.click(timeout=2000); k.settle(page, 2)
        except Exception:
            pass
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = 'nav [data-test-subj="collapsibleNavAppLink"]:has(span:text-is("Stack Management"))'
    page.locator(link).first.scroll_into_view_if_needed(); page.locator(link).first.click(); k.settle(page, 5)
    shot(page, "04a-snapshot-menu", [(("testsubj", "snapshot_restore"), 1, "right")])
    page.locator('[data-test-subj="snapshot_restore"]').first.click(); k.settle(page, 6)
    print("sekmeler:", [t.inner_text() for t in page.locator('[role="tab"]').all()])
    page.locator(sekme(page, "Snapshots")).first.click(); k.settle(page, 4)
    shot(page, "04b-snapshots", [(("css", sekme(page, "Snapshots")), 1, "left"), (("css", 'tr:has-text("elle-1")'), 2, "left")])
    page.locator(sekme(page, "Repositories")).first.click(); k.settle(page, 4)
    shot(page, "04c-repositories", [(("css", sekme(page, "Repositories")), 1, "down"), (("css", 'tr:has-text("cluster-yedek")'), 2, "left")])
    page.locator(sekme(page, "Policies")).first.click(); k.settle(page, 4)
    print("politika:", page.locator('tr:has-text("cluster-gunluk")').first.inner_text().replace("\n", " | ")[:200])
    shot(page, "04d-slm-politika", [(("css", sekme(page, "Policies")), 1, "down"), (("css", 'tr:has-text("cluster-gunluk")'), 2, "left")])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        snapshot(page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
