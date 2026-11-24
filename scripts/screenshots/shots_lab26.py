"""LAB-26 Adim 5 isaretli Kibana ekran goruntuleri: Security > Alerts, alarm ayrintisi, Mark as acknowledged.

    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab26.py alarm         # Adim 5.1-5.4
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab26.py ack-goster    # kutu: menu acilir, tiklanmaz
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab26.py ack           # kutu: GERCEKTEN isaretler
Cikti: assets/screenshots/LAB-26/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-26.
"""
import os
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-26"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-26")
SORGU = 'kibana.alert.severity : "critical"'


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


def kapat(page):
    for txt in ("Got it", "Dismiss", "Close"):
        try:
            page.get_by_role("button", name=txt).first.click(timeout=1500)
        except Exception:
            pass


def alarmlar(page, goruntu=None):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    link = 'nav a[href*="/app/security/alert_detections"]'   # Observability altinda da "Alerts" var; Security'deki secilir
    page.locator(link).first.scroll_into_view_if_needed(); time.sleep(0.5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "toggleNavButton"), 1, "right"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)
    kart = page.locator('a:has-text("Alerts"), button:has-text("Alerts")').filter(has_text="Review individual").first
    if not kart.count():
        kart = page.get_by_role("link", name="Alerts", exact=True).first
    if goruntu:
        shot(page, "05a2-detections-alerts", [(isaretle(kart, "kart"), 1, "left")])
    kart.click(); k.settle(page, 15)
    kapat(page)


def isaretle(loc, ad):
    loc.evaluate(f"e => e.setAttribute('data-isaret', '{ad}')")
    return ("css", f'[data-isaret="{ad}"]')


def kritik(page):
    q = page.locator('[data-test-subj="unifiedQueryInput"] textarea').first
    q.click(); q.fill(SORGU); page.keyboard.press("Enter"); k.settle(page, 8)
    satir = page.locator('.euiDataGridRow').filter(has_text="Ihlal").first
    print("kritik satir:", satir.count())
    return satir


def alarm(page):
    alarmlar(page, "05a-menu-alerts")
    page.mouse.move(800, 60); time.sleep(1)
    shot(page, "05b-security-alerts", [(("testsubj", "severity-level-table"), 1, "down"), (("testsubj", "alerts-by-rule-table"), 2, "down"),
                                       (("text", "Ihlal: basarisiz denemelerin", False), 3, "left")])
    satir = kritik(page)
    genislet = page.locator('[data-test-subj="expand-event"]').first   # sorgudan sonra tek satir kalir
    shot(page, "05c-alarm-ac", [(("testsubj", "unifiedQueryInput"), 1, "down"), (("testsubj", "expand-event"), 2, "right")])
    genislet.click(); time.sleep(5)
    rehber = page.get_by_text("Investigation guide", exact=False).first
    print("flyout:", page.locator(".euiFlyout").first.inner_text()[:200].replace("\n", " | "))
    shot(page, "05d-alarm-ayrinti", [(("text", "Investigation guide", False), 1, "left")])
    page.keyboard.press("Escape"); time.sleep(1)


def ack(page, tikla):
    alarmlar(page)
    satir = kritik(page)
    page.locator('[data-test-subj="timeline-context-menu-button"]').first.click(); time.sleep(2)
    shot(page, "05e-alarm-menu", [(("testsubj", "timeline-context-menu-button"), 1, "right")])
    oge = page.get_by_role("button", name="Mark as acknowledged").or_(page.get_by_text("Mark as acknowledged")).first
    oge.evaluate("e => e.setAttribute('data-isaret', 'ack')")
    shot(page, "05f-acknowledged", [(("css", '[data-isaret="ack"]'), 1, "right")])
    if tikla:
        oge.click(); k.settle(page, 5)
        print("isaretlendi")
    else:
        page.keyboard.press("Escape"); time.sleep(1)
        print("menu kapatildi (tiklanmadi)")


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"alarm": alarm, "ack-goster": lambda p: ack(p, False), "ack": lambda p: ack(p, True)}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
