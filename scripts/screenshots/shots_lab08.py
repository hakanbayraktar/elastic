"""LAB-08 ES|QL ve SQL: Discover ES|QL modu isaretli ekran goruntusu (Adim 4).

Kullanim (yerelde; LAB-04 ornek verisi kurulu):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab08.py
Cikti: assets/screenshots/LAB-08/01-discover-esql.png; dugme adlari stdout'a yazilir.
"""
import sys
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



def lab08pano(page):
    """Adim 4 kutusu: ES|QL sorgusunu panoya panel olarak eklemek (Add > Visualization (query))."""
    page.goto(k.BASE + "/app/dashboards#/create", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(2)
    k.shoot(page, LAB, "02-pano-add-query", [
        (("testsubj", "dashboardAddTopNavButton"), 1, "down"),
        (("testsubj", "create-action-Visualization (query)"), 2, "left")])
    page.locator('[data-test-subj="create-action-Visualization (query)"]').first.click(); k.settle(page, 8)
    ed = page.locator('[data-test-subj="ESQLEditor"] .monaco-editor').first
    ed.click(); time.sleep(0.5)
    page.keyboard.press("ControlOrMeta+a"); page.keyboard.press("Delete"); time.sleep(0.5)
    page.keyboard.insert_text(SORGU); time.sleep(1)
    page.locator('[data-test-subj="ESQLEditor-run-query-button"]').first.click(); k.settle(page, 6)
    k.shoot(page, LAB, "03-pano-esql-panel", [
        (("testsubj", "ESQLEditor"), 1, "down"),
        (("testsubj", "ESQLEditor-run-query-button"), 2, "down"),
        (("testsubj", "lnsChartSwitchPopover"), 3, "left"),
        (("testsubj", "applyFlyoutButton"), 4, "up")])
    page.locator('[data-test-subj="applyFlyoutButton"]').first.click(); k.settle(page, 6)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("ES|QL özeti")
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    print("panel sayisi:", page.locator('[data-test-subj="dashboardPanel"]').count())
    k.shoot(page, LAB, "04-pano-esql", [(("css", '[data-test-subj="dashboardPanel"]'), 1, "right")])

if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        if len(sys.argv) > 1 and sys.argv[1] == "pano":
            lab08pano(page)
        else:
            lab08(page)
        br.close()
