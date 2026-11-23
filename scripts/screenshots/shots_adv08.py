"""ADV-08 isaretli Kibana ekran goruntusu: Kibana 8.19 Upgrade Assistant.

Kullanim (yerelde; ADV-08 Adim 1-5 calismis olmali):
    ssh -f -N -L 25608:127.0.0.1:5608 student@<sunucu>
    KB_BASE=http://127.0.0.1:25608 python3 scripts/screenshots/shots_adv08.py
Cikti: assets/screenshots/ADV-08/01-upgrade-assistant.png
"""
import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "ADV-08"


def adv08(page):
    page.goto(k.BASE + "/app/management/stack/upgrade_assistant", wait_until="domcontentloaded")
    k.settle(page, 10)
    page.get_by_text("Review deprecated settings and resolve issues").evaluate("e => e.scrollIntoView({block: 'center'})")
    k.settle(page, 2)
    k.shoot(page, LAB, "01-upgrade-assistant", [
        (("text", "System indices migration not needed.", True), 1, "left"),
        (("text", "No issues", True), 2, "left"),
        (("text", "Analyze logs in Discover", True), 3, "left"),
    ])


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        adv08(page)
        br.close()
