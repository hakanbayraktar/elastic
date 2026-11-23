"""ADV-02 isaretli Kibana ekran goruntuleri: APM Service inventory ve hatali siparisin trace akisi.

Kullanim (yerelde, sunucuya SSH tuneli acikken; ADV-02 Adim 1-4 calismis olmali):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_adv02.py
Cikti: assets/screenshots/ADV-02/<ad>.png
"""
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "ADV-02"
HATALI_TRACE = "0f927e9d6892d8ca9613aef16cbbae30"   # siparis 5 (betikte kimlik siparis numarasindan turetilir)


def adv05(page):
    page.goto(k.BASE + "/app/apm/services?rangeFrom=now-1h&rangeTo=now&environment=ENVIRONMENT_ALL",
              wait_until="domcontentloaded"); k.settle(page, 10)
    k.shoot(page, LAB, "01-service-inventory", [
        (("union", ("role", "link", "checkout-service"), ("role", "link", "payment-service")), 1, "left"),
        (("text", "Failed transaction rate", True), 2, "up"),
    ])
    page.goto(k.BASE + f"/app/apm/link-to/trace/{HATALI_TRACE}?rangeFrom=now-1h&rangeTo=now",
              wait_until="domcontentloaded"); k.settle(page, 12)
    odeme = page.get_by_text("POST /odeme", exact=True).last
    odeme.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(2)
    k.shoot(page, LAB, "02-trace-akisi", [
        (("text", "POST /odeme", True), 3, "left"),
    ])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        adv05(page)
        br.close()
