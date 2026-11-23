"""LAB-08 ES|QL ve SQL: Discover ES|QL modu isaretli ekran goruntusu (Adim 4).

Kullanim (yerelde; LAB-04 ornek verisi kurulu):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab08.py
Cikti: assets/screenshots/LAB-08/01-discover-esql.png; dugme adlari stdout'a yazilir.
"""
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-08"
SORGU = "FROM kibana_sample_data_ecommerce | STATS siparis = COUNT(*) BY day_of_week | SORT siparis DESC"


def lab08(page):
    page.goto(k.BASE + "/app/discover", wait_until="domcontentloaded"); k.settle(page, 6)
    k.pick_dataview(page, 'Kibana Sample Data eCommerce'); k.settle(page, 5)
    btn = page.locator('[data-test-subj="select-text-based-language-btn"]').first
    print("DUGME_ONCE:", btn.inner_text().strip())
    btn.click(); k.settle(page, 5)
    v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all()]
    print("SUBJ:", sorted(set(x for x in v if x and any(f in x.lower() for f in ("classic", "text-based", "switch", "language")))))
    print("CLASSIC_METIN:", [b.inner_text().strip() for b in page.get_by_role("button").all() if "lassic" in (b.inner_text() or "")][:3])
    ed = page.locator('[data-test-subj="ESQLEditor"] .monaco-editor').first
    ed.click(); page.keyboard.press("ControlOrMeta+A"); page.keyboard.press("Delete")
    page.keyboard.type(SORGU)
    time.sleep(1); page.keyboard.press("Escape")
    sub = page.locator('[data-test-subj="querySubmitButton"]').first
    print("ARA_DUGMESI:", sub.inner_text().strip())
    sub.click(); k.settle(page, 8)
    page.mouse.move(1500, 850); time.sleep(1)
    k.shoot(page, LAB, "01-discover-esql", [
        (("text", "Switch to Classic", False), 1, "down"),
        (("testsubj", "ESQLEditor"), 2, "down"),
        (("testsubj", "querySubmitButton"), 3, "down"),
        (("css", '[data-test-subj="unifiedHistogramChart"], [data-test-subj="unifiedHistogramRendered"]'), 4, "left"),
    ])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        lab08(page)
        br.close()
