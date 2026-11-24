"""LAB-24 Adim 6 isaretli Kibana ekran goruntuleri: Stack Monitoring (Metricbeat veri toplamis olmali).

    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab24.py izleme
Cikti: assets/screenshots/LAB-24/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-24.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-24"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-24")


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


def izleme(page):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    page.locator(nav("Stack Monitoring")).first.scroll_into_view_if_needed(); time.sleep(0.5)
    shot(page, "06a-menu-stack-monitoring", [(("testsubj", "toggleNavButton"), 1, "right"), (("css", nav("Stack Monitoring")), 2, "right")])
    page.locator(nav("Stack Monitoring")).first.click(); k.settle(page, 12)
    if page.get_by_text("Create rules", exact=True).count():
        page.get_by_label("No", exact=True).check(); time.sleep(1)
        shot(page, "06b-create-rules", [(("css", 'label:text-is("No")'), 1, "left"), (("role", "button", "Continue"), 2, "up")])
        page.get_by_role("button", name="Continue").first.click(); k.settle(page, 6)
    else:
        print("Create rules penceresi gelmedi")
    print("OZET:", page.locator('[data-test-subj="esOverview"]').first.inner_text().replace("\n", " | ")[:200])
    shot(page, "06c-izleme-ozet", [(("testsubj", "esOverview"), 1, "right"), (("testsubj", "esNumberOfNodes"), 2, "left")])
    page.locator('[data-test-subj="esNumberOfNodes"]').first.click(); k.settle(page, 8)
    print("NODES:", [r.inner_text().replace("\n", " | ")[:120] for r in page.locator("tbody tr").all()])
    page.locator("tbody").first.evaluate("e => e.setAttribute('data-isaret', 'nodes')")
    shot(page, "06d-izleme-nodes", [(("css", '[data-isaret="nodes"]'), 1, "up")])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"izleme": izleme}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
