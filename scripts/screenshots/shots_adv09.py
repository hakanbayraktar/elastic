"""ADV-09 isaretli Kibana ekran goruntusu: ECK Kibana'sinda Index Management, eck-siparis index'i.

Kullanim (yerelde; ADV-09 Adim 1-5 calismis olmali, tunel README Adim 6'daki gibi acik):
    ssh -f -N -L 30086:127.0.0.1:30086 student@<sunucu>
    KB_BASE=https://127.0.0.1:30086 KB_PASS='<Adim 4 PW>' python3 scripts/screenshots/shots_adv09.py
Cikti: assets/screenshots/ADV-09/01-index-management.png
"""
import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "ADV-09"


def adv09(page):
    page.goto(k.BASE + "/app/management/data/index_management/indices", wait_until="domcontentloaded")
    k.settle(page, 8)
    k.shoot(page, LAB, "01-index-management", [
        (("role", "button", "eck-siparis"), 1, "left"),
        (("text", "Documents count", True), 2, "up"),
    ])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE,
                           ignore_https_errors=True)   # ECK'nin kendi CA'si; tarayicida da uyari cikar
        k.login(page)
        adv09(page)
        br.close()
