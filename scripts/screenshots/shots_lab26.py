"""LAB-26 isaretli Kibana ekran goruntusu: Security > Alerts (siem-lab kurallarinin alarmlari).

Kullanim (yerelde, sunucuya SSH tuneli acikken; LAB-26 Adim 1-4 calismis olmali):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab23.py
Cikti: assets/screenshots/LAB-26/<ad>.png
"""
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-26"


def lab26(page):
    page.goto(k.BASE + "/app/security/alerts", wait_until="domcontentloaded")
    k.settle(page, 12)
    for txt in ("Got it", "Dismiss", "Close"):
        try: page.get_by_role("button", name=txt).first.click(timeout=1500)
        except Exception: pass
    page.mouse.move(800, 60); time.sleep(2)
    k.shoot(page, LAB, "01-security-alerts", [
        (("testsubj", "severity-level-table"), 1, "down"),
        (("testsubj", "alerts-by-rule-table"), 2, "down"),
        (("text", "Ihlal: basarisiz denemelerin", False), 3, "left"),
    ])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        lab26(page)
        br.close()
