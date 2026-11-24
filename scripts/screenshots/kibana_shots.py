"""Lab README'leri icin isaretli Kibana ekran goruntuleri.

Kullanim (yerelde, sunucuya SSH tuneli acikken):
    ssh -N -L 15601:127.0.0.1:5601 student@<sunucu> &
    python3 scripts/screenshots/kibana_shots.py lab12 [lab04 ...]

Her goruntude tiklanacak yerler kirmizi kutu + ok + adim numarasiyla isaretlenir.
Kutu konumu sabit koordinatla degil, Playwright'in buldugu ogenin olculen yeriyle
cizilir; Kibana arayuzu biraz kaysa da kutu dogru yere duser.
Cikti: assets/screenshots/<lab>/<ad>.png (genislik 1600 px).
"""
import os
import sys
import time

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE = os.environ.get("KB_BASE", "http://127.0.0.1:15601")
PW = os.environ.get("KB_PASS", "DevOps2026!")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCALE = 1.5          # device_scale_factor
OUT_W = 1600         # kaydedilen genislik
RED = (220, 38, 38)


def login(page):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.fill('input[name="username"]', "elastic")
    page.fill('input[name="password"]', PW)
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/app/" in u or "space_selector" in u, timeout=60000)
    if "space_selector" in page.url:
        page.goto(BASE + "/app/home", wait_until="domcontentloaded")
        time.sleep(3)


def settle(page, extra=3):
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    time.sleep(extra)
    for txt in ("Dismiss", "Got it", "Close tour", "Maybe later"):
        for loc in (page.get_by_role("button", name=txt), page.get_by_text(txt, exact=True)):
            try:
                loc.first.click(timeout=800)
            except Exception:
                pass
    time.sleep(0.5)


def locate(page, target):
    """target: ('text', 'Agents') | ('role', 'tab', 'Agents') | ('css', 'selector') | ('label', 'Period')."""
    kind = target[0]
    if kind == "text":
        loc = page.get_by_text(target[1], exact=target[2] if len(target) > 2 else False)
    elif kind == "role":
        loc = page.get_by_role(target[1], name=target[2], exact=target[3] if len(target) > 3 else False)
    elif kind == "label":
        loc = page.get_by_label(target[1])
    elif kind == "testsubj":
        loc = page.locator(f'[data-test-subj="{target[1]}"]')
    else:
        loc = page.locator(target[1])
    return loc.first


def box_of(page, target):
    if target[0] == "union":   # ('union', t1, t2, ...): hepsini saran tek kutu
        bs = [box_of(page, t) for t in target[1:]]
        x0 = min(b["x"] for b in bs); y0 = min(b["y"] for b in bs)
        x1 = max(b["x"] + b["width"] for b in bs); y1 = max(b["y"] + b["height"] for b in bs)
        return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
    b = locate(page, target).bounding_box(timeout=10000)
    if not b:
        raise RuntimeError(f"oge bulunamadi: {target}")
    return b


def draw(path, marks):
    """marks: [(bbox, no, arrow_dir)], bbox CSS px; arrow_dir: 'left'|'right'|'up'|'down'|None."""
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    pad = 6 * SCALE
    for b, no, arrow in marks:
        x0, y0 = b["x"] * SCALE - pad, b["y"] * SCALE - pad
        x1, y1 = (b["x"] + b["width"]) * SCALE + pad, (b["y"] + b["height"]) * SCALE + pad
        d.rounded_rectangle((x0, y0, x1, y1), radius=8, outline=RED, width=5)
        cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
        L = 110
        if arrow == "left":      # ok soldan saga, kutunun sol kenarina
            tip, tail = (x0 - 4, cy), (x0 - L, cy)
        elif arrow == "right":
            tip, tail = (x1 + 4, cy), (x1 + L, cy)
        elif arrow == "up":
            tip, tail = (cx, y0 - 4), (cx, y0 - L)
        elif arrow == "down":
            tip, tail = (cx, y1 + 4), (cx, y1 + L)
        else:
            tip = tail = None
        if tip:
            d.line((tail, tip), fill=RED, width=7)
            import math
            ang = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
            h = 26
            p1 = (tip[0] - h * math.cos(ang - 0.45), tip[1] - h * math.sin(ang - 0.45))
            p2 = (tip[0] - h * math.cos(ang + 0.45), tip[1] - h * math.sin(ang + 0.45))
            d.polygon([tip, p1, p2], fill=RED)
            nx, ny = tail
        else:
            nx, ny = x0, y0
        if no is None:
            continue
        r = 24
        d.ellipse((nx - r - 3, ny - r - 3, nx + r + 3, ny + r + 3), fill=(255, 255, 255))
        d.ellipse((nx - r, ny - r, nx + r, ny + r), fill=RED)
        t = str(no)
        tw, th = d.textbbox((0, 0), t, font=font)[2:]
        d.text((nx - tw / 2, ny - th / 2 - 3), t, fill=(255, 255, 255), font=font)
    if im.width > OUT_W:
        im = im.resize((OUT_W, int(im.height * OUT_W / im.width)), Image.LANCZOS)
    im.save(path, optimize=True)


def pick_dataview(page, name):
    """Discover'da data view secer. Liste sanallastirilmistir (ilk ~10 oge cizilir): once arama kutusuna yazilir."""
    page.locator('[data-test-subj="discover-dataView-switch-link"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="indexPattern-switcher--input"]').first.fill(name); time.sleep(1.5)
    page.locator(f'[data-test-subj="dataView-{name}"]').first.click()


def shoot(page, lab, name, marks_spec, scroll_to=None):
    """Once scroll_to (yoksa ilk isaret) gorunur yapilir, sonra butun kutular ayni anda olculur."""
    out_dir = os.path.join(ROOT, "assets", "screenshots", lab)
    os.makedirs(out_dir, exist_ok=True)
    first = scroll_to or (marks_spec[0][0] if marks_spec else None)
    while first and first[0] == "union":
        first = first[1]
    if first:
        locate(page, first).scroll_into_view_if_needed(timeout=10000)
        time.sleep(1)
    marks = []
    for target, no, arrow in marks_spec:
        marks.append((box_of(page, target), no, arrow))
    path = os.path.join(out_dir, name + ".png")
    page.screenshot(path=path)
    draw(path, marks)
    print("ok", os.path.relpath(path, ROOT))


# ---------------------------------------------------------------- lab akislari
def eski_fleet(page):
    """Eski Fleet labi (yeni numarasi LAB-11); goruntuler LAB-11 klasorune yazilir."""
    lab = "LAB-11"
    # Adim 2: ajan listesi
    page.goto(BASE + "/app/fleet/agents", wait_until="domcontentloaded"); settle(page, 6)
    shoot(page, lab, "01-fleet-agents", [
        (("css", 'tr:has-text("linux-agent-01")'), 1, "down"),
    ])
    # Adim 5: politika -> system-1 -> Change defaults -> Period -> Save
    page.goto(BASE + "/app/fleet/policies/linux-monitoring-policy", wait_until="domcontentloaded"); settle(page, 6)
    shoot(page, lab, "02-policy-system-1", [
        (("text", "system-1", True), 2, "left"),
    ])
    page.get_by_text("system-1", exact=True).first.click(); settle(page, 6)
    metrics = page.locator("div").filter(has=page.get_by_text("Collect metrics from System instances", exact=True)) \
                  .filter(has=page.get_by_text("Change defaults")).last
    metrics.get_by_text("Change defaults").click(); time.sleep(2)
    shoot(page, lab, "03-change-defaults-hostfs", [
        (("css", 'xpath=(//*[normalize-space(text())="Collect metrics from System instances"]/following::*[normalize-space(text())="Change defaults"])[1]'), 3, "left"),
        (("css", 'xpath=(//*[normalize-space(text())="Proc Filesystem Directory"]/following::input)[1]'), None, "left"),
    ], scroll_to=("text", "Collect metrics from System instances", True))
    shoot(page, lab, "04-process-period-save", [
        (("css", 'xpath=(//*[normalize-space(text())="System process metrics"]/following::input)[1]'), 4, "left"),
        (("role", "button", "Save integration"), 5, "up"),
    ], scroll_to=("text", "System process metrics", True))
    # Adim 5 (devam): degeri degistir, kaydet, onay penceresi. Deger once ve sonra ayni
    # kalmasin diye 10s <-> 30s arasinda gidip gelir; lab varsayilani 10s.
    inp = page.locator('xpath=(//*[normalize-space(text())="System process metrics"]/following::input)[1]')
    inp.fill("30s" if inp.input_value() == "10s" else "10s"); time.sleep(1)
    page.get_by_role("button", name="Save integration").click(); time.sleep(3)
    shoot(page, lab, "06-save-and-deploy", [
        (("role", "button", "Save and deploy changes"), 6, "down"),
    ])
    page.get_by_role("button", name="Cancel").last.click(); time.sleep(1)
    # Adim 8: Fleet-Agent etiketiyle filtrelenmis pano listesi
    page.goto(BASE + "/app/dashboards#/list", wait_until="domcontentloaded"); settle(page, 5)
    page.get_by_role("button", name="Tags").first.click(); time.sleep(1.5)
    page.get_by_role("option", name="Fleet-Agent").first.click(); time.sleep(1); page.keyboard.press("Escape"); time.sleep(2)
    shoot(page, lab, "05-dashboards-tag-filter", [
        (("role", "button", "Tags"), None, "down"),
    ])


def eski_3node(page):
    """KB_BASE 3-node cluster'in Kibana'sina (15608 tuneli) ve KB_PASS cluster parolasina ayarlanmali."""
    lab = "LAB-13B"
    page.goto(BASE + "/app/monitoring#/elasticsearch?_g=(time:(from:now-30m,to:now))", wait_until="domcontentloaded"); settle(page, 12)
    shoot(page, lab, "01-stack-monitoring-overview", [
        (("union", ("text", "Unassigned shards", True),
          ("css", 'xpath=(//*[normalize-space(text())="Unassigned shards"])[1]/following::*[normalize-space(text())!=""][1]')), 1, "down"),
        (("role", "tab", "Nodes"), 2, "down"),
    ])
    page.get_by_role("tab", name="Nodes").first.click(); settle(page, 10)
    shoot(page, lab, "02-stack-monitoring-nodes", [
        (("css", 'tr:has-text("es-b")'), 3, "down"),
    ])


def eski_alarm(page):
    """Eski Apache alarm akisi (eski LAB-21; yeni LAB-16/17 icin kaynak). LAB-21 alarm ekranlari. On kosul: LAB-21 kurulu, provision_kibana.py calismis, apache-slack-alerts /
    apache-email-resend connector'lari ve kapali apache-web-5xx-rate kurali var (gecici, sahte gizli bilgiyle)."""
    lab = "eski-alarm"  # eski akis; LAB-21 klasorune yazmaz
    CONN = BASE + "/app/management/insightsAndAlerting/triggersActionsConnectors/connectors"
    RULES = BASE + "/app/management/insightsAndAlerting/triggersActions/rules"

    def safe(name, fn):
        try:
            fn()
        except Exception as e:  # bir goruntu dusse de digerleri cekilsin
            print("HATA", name, str(e).splitlines()[0][:160])

    def connectors_list():
        page.goto(CONN, wait_until="domcontentloaded"); settle(page, 5)
        shoot(page, lab, "12-connectors-list", [
            (("role", "link", "Connectors", True), 2, "right"),
            (("role", "button", "Create connector"), 3, "down"),
        ])

    def slack_form():
        page.goto(CONN, wait_until="domcontentloaded"); settle(page, 5)
        page.get_by_role("button", name="Create connector").first.click(); time.sleep(3)
        dlg = page.locator('[role="dialog"]').last
        dlg.get_by_placeholder("Search").first.fill("Slack"); time.sleep(2)
        shoot(page, lab, "13a-connector-select-slack", [
            (("css", '[role="dialog"] button:has-text("Slack")'), 3, "down"),
        ])
        dlg.locator('button:has-text("Slack")').first.click(); time.sleep(3)
        page.locator('[data-test-subj="nameInput"]').fill("apache-slack-alerts"); time.sleep(1)
        shoot(page, lab, "13-connector-create-slack", [
            (("testsubj", "nameInput"), 4, "left"),
            (("testsubj", "slackWebhookUrlInput"), 4, "left"),
            (("role", "button", "Save", True), 5, "up"),
        ])

    def email_form():
        page.goto(CONN, wait_until="domcontentloaded"); settle(page, 5)
        page.get_by_role("button", name="Create connector").first.click(); time.sleep(3)
        dlg = page.locator('[role="dialog"]').last
        dlg.get_by_placeholder("Search").first.fill("Email"); time.sleep(2)
        dlg.locator('button:has-text("Email")').first.click(); time.sleep(3)
        page.locator('[data-test-subj="nameInput"]').fill("apache-email-resend")
        page.locator('[data-test-subj="emailFromInput"]').fill("onboarding@resend.dev")
        try:
            page.locator('[data-test-subj="emailServiceSelectInput"]').select_option("other")
        except Exception:
            pass
        time.sleep(1)
        page.locator('[data-test-subj="emailHostInput"]').fill("smtp.resend.com")
        page.locator('[data-test-subj="emailPortInput"]').fill("465")
        page.locator('[data-test-subj="emailUserInput"]').fill("resend"); time.sleep(1)
        shoot(page, lab, "14-connector-email-resend", [
            (("testsubj", "nameInput"), None, None),
            (("testsubj", "emailFromInput"), None, None),
            (("testsubj", "emailServiceSelectInput"), None, None),
            (("testsubj", "emailHostInput"), None, None),
            (("testsubj", "emailPortInput"), None, None),
            (("testsubj", "emailUserInput"), None, None),
            (("testsubj", "emailPasswordInput"), None, "left"),
        ], scroll_to=("testsubj", "emailFromInput"))

    def rule_type():
        page.goto(RULES, wait_until="domcontentloaded"); settle(page, 5)
        page.get_by_role("button", name="Create rule").first.click(); time.sleep(3)
        page.get_by_placeholder("Search rule types...").fill("Elasticsearch query"); time.sleep(2)
        shoot(page, lab, "15a-rule-type-es-query", [
            (("text", "Elasticsearch query", True), 2, "left"),
        ])

    def rule_edit():
        page.goto(BASE + "/app/management/insightsAndAlerting/triggersActions/edit/apache-web-5xx-rate",
                  wait_until="domcontentloaded"); settle(page, 8)
        shoot(page, lab, "15-rule-create-es-query", [
            (("css", 'button:has-text("Apache Web")'), 3, "left"),
            (("css", 'xpath=(//*[contains(normalize-space(.),"apache.access") and (self::textarea or self::input or self::div[@role="textbox"])])[1]'), 4, "left"),
            (("css", 'button:has-text("is above")'), 5, "left"),
            (("css", 'button:has-text("for the last")'), 5, "left"),
        ], scroll_to=("css", 'button:has-text("Apache Web")'))
        shoot(page, lab, "16-rule-actions-connectors", [
            (("text", "apache-slack-alerts", False), 7, "left"),
        ], scroll_to=("text", "apache-slack-alerts", False))

    def rules_list():
        page.goto(RULES, wait_until="domcontentloaded"); settle(page, 10)
        for _ in range(6):   # liste bazen ilk acilista bos cizilir; sekmeyi yeniden secince dolar
            if page.get_by_text("Apache 5xx Hata Patlaması Uyarısı").count():
                break
            page.get_by_role("tab", name="Logs").first.click(); time.sleep(2)
            page.get_by_role("tab", name="Rules").first.click(); time.sleep(5)
        shoot(page, lab, "18-rules-list", [
            (("text", "Apache 5xx Hata Patlaması Uyarısı", True), None, "down"),
        ])

    def rule_detail():
        page.goto(BASE + "/app/management/insightsAndAlerting/triggersActions/rule/apache-web-5xx-rate",
                  wait_until="domcontentloaded"); settle(page, 8)
        shoot(page, lab, "19-rule-detail", [])

    # LAB21_PHASE=forms: gecici connector'lar YOKKEN (form "ID zaten var" uyarisi gostermesin);
    # LAB21_PHASE=rule: gecici connector'lar ve kural VARKEN.
    phase = os.environ.get("LAB21_PHASE", "forms")
    steps = ([("slack", slack_form), ("email", email_form), ("ruletype", rule_type)] if phase == "forms" else
             [("connectors", connectors_list), ("ruleedit", rule_edit), ("rules", rules_list), ("detail", rule_detail)])
    for name, fn in steps:
        safe(name, fn)


def eski_lab04(page):
    """LAB-03 Modul 07: Lens ile pano (omurga, kibana_sample_data_ecommerce). Hicbir sey kaydedilmez."""
    lab = "LAB-03"
    page.goto(BASE + "/app/dashboards#/list", wait_until="domcontentloaded"); settle(page, 5)
    shoot(page, lab, "01-dashboards-create", [
        (("testsubj", "dashboardListingCreateButton"), 2, "down"),
    ])
    page.goto(BASE + "/app/dashboards#/create?_g=(time:(from:now-60d,to:now%2B30d))", wait_until="domcontentloaded"); settle(page, 6)
    shoot(page, lab, "02-empty-dashboard-create-visualization", [
        (("testsubj", "create-action-Visualization"), 3, "left"),
    ])
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(2)
    try:
        shoot(page, lab, "05-add-menu-controls", [
            (("testsubj", "dashboardAddTopNavButton"), 1, "down"),
            (("text", "Control", True), 1, "left"),
        ])
    except Exception as e:
        print("HATA controls", str(e).splitlines()[0][:120])
    page.keyboard.press("Escape"); time.sleep(1)
    page.locator('[data-test-subj="create-action-Visualization"]').first.click(); settle(page, 8)
    for txt in ("Don't show again",):
        try: page.get_by_text(txt).first.click(timeout=1500)
        except Exception: pass
    page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
    page.get_by_text("Kibana Sample Data eCommerce", exact=True).first.click(); settle(page, 6)
    page.locator('[data-test-subj="lnsIndexPatternFieldSearch"]').fill("taxful"); time.sleep(2)
    shoot(page, lab, "03-lens-editor", [
        (("testsubj", "lns-dataView-switch-link"), 4, "down"),
        (("testsubj", "lnsChartSwitchPopover"), None, "down"),
        (("css", '[data-test-subj="lnsFieldListPanelField-taxful_total_price"]'), None, "right"),
        (("testsubj", "lnsApp_saveAndReturnButton"), None, "down"),
    ])


def lab01(page):
    lab = "LAB-01"
    # 1) Giris ekrani: oturumsuz ayri bir sayfada
    anon = page.context.browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=SCALE)
    anon.goto(BASE + "/login", wait_until="domcontentloaded")
    anon.wait_for_selector('input[name="username"]', timeout=60000); time.sleep(2)
    shoot(anon, lab, "01-kibana-login", [
        (("css", 'input[name="username"]'), 1, "left"),
        (("css", 'input[name="password"]'), 2, "left"),
        (("css", 'button[type="submit"]'), 3, "left"),
    ])
    anon.close()
    # 2) Ana menu: ilk giriste cikan karsilama kartini kapat, menuyu ac
    page.goto(BASE + "/app/home", wait_until="domcontentloaded"); settle(page, 4)
    try:
        page.get_by_text("Explore on my own", exact=True).first.click(timeout=3000); settle(page, 3)
    except Exception:
        pass
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    nav = 'nav [data-test-subj="collapsibleNavAppLink"]'
    shoot(page, lab, "02-kibana-menu", [
        (("testsubj", "toggleNavButton"), 1, "right"),
        (("css", nav + ':has(span:text-is("Discover"))'), 2, "right"),
    ])
    page.locator(nav + ':has(span:text-is("Dev Tools"))').first.scroll_into_view_if_needed(); time.sleep(1)
    shoot(page, lab, "03-kibana-devtools", [
        (("css", nav + ':has(span:text-is("Dev Tools"))'), 3, "right"),
    ])
    page.keyboard.press("Escape"); time.sleep(1)
    # 3) Lisans sayfasi
    page.goto(BASE + "/app/management/stack/license_management", wait_until="domcontentloaded"); settle(page, 4)
    shoot(page, lab, "04-license-trial", [
        (("css", '[data-test-subj="licenseText"]'), 1, "left"),
    ])


def lab02(page):
    lab = "LAB-02"
    # Adim 1: Dev Tools Console
    page.goto(BASE + "/app/dev_tools#/console", wait_until="domcontentloaded"); settle(page, 5)
    page.locator('[data-test-subj="clearConsoleInput"]').first.click(); time.sleep(1)
    page.locator('[data-test-subj="consoleMonacoEditor"]').first.click(); time.sleep(0.5)
    page.keyboard.type("GET /_cluster/health"); time.sleep(1)
    page.locator('[data-test-subj="sendRequestButton"]').first.click(); time.sleep(4)
    out = '[data-test-subj="consoleMonacoOutput"]'
    if not page.locator(out).count():
        out = '[data-test-subj="consolePanel"] .monaco-editor >> nth=1'
    shoot(page, lab, "01-devtools-console", [
        (("testsubj", "consoleMonacoEditor"), 1, None),
        (("testsubj", "sendRequestButton"), 2, "up"),
        (("css", out), 3, None),
    ])

    def create_dv(name, pattern, ts, shot, marks_extra):
        page.goto(BASE + "/app/management/kibana/dataViews", wait_until="domcontentloaded"); settle(page, 4)
        btn = page.locator('[data-test-subj="createDataViewButton"]:visible')
        if not btn.count():
            btn = page.locator('[data-test-subj="noDataViewsPromptCreateDataView"]:visible')
        btn.first.click(); time.sleep(3)
        page.locator('[data-test-subj="createIndexPatternNameInput"]').fill(name)
        page.locator('[data-test-subj="createIndexPatternTitleInput"]').fill(pattern); time.sleep(3)
        if ts:
            cb = page.locator('[data-test-subj="timestampField"] [data-test-subj="comboBoxSearchInput"]')
            cb.click(); time.sleep(1)
            page.get_by_role("option", name=ts, exact=True).first.click(); time.sleep(1)
        marks = [(("testsubj", "createIndexPatternNameInput"), 1, "left"),
                 (("testsubj", "createIndexPatternTitleInput"), 2, "left")] + marks_extra
        shoot(page, lab, shot, marks)
        page.locator('[data-test-subj="saveIndexPatternButton"]').first.click(); time.sleep(4)

    # Adim 6a: zaman alanli data view
    create_dv("belge-talepler", "belge-talepler", "@timestamp", "02-dataview-talepler", [
        (("testsubj", "timestampField"), 3, "left"),
        (("testsubj", "saveIndexPatternButton"), 4, "up"),
    ])

    def pick_dv(name):
        pick_dataview(page, name); settle(page, 5)

    # Adim 6a: Discover, Last 15 minutes -> Last 1 year
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dv("belge-talepler")
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    shoot(page, lab, "03-discover-zaman-secici", [
        (("testsubj", "dateRangePickerInput"), 1, "left"),
        (("testsubj", "dateRangePickerPresetItem-Last_1_year"), 2, "left"),
    ], scroll_to=("testsubj", "dateRangePickerPresetItem-Last_1_year"))
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_1_year"]').first.click(); settle(page, 6)
    shoot(page, lab, "04-discover-talepler", [
        (("testsubj", "discoverQueryHits"), 3, "down"),
        (("testsubj", "unifiedHistogramChart"), 4, None),
    ])

    # Adim 6b: zaman alansiz data view
    create_dv("belge-urunler", "belge-urunler", None, "05-dataview-urunler", [
        (("testsubj", "timestampField"), 3, "left"),
        (("testsubj", "saveIndexPatternButton"), 4, "up"),
    ])
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dv("belge-urunler")
    shoot(page, lab, "06-discover-urunler", [
        (("testsubj", "discover-dataView-switch-link"), 1, "down"),
        (("testsubj", "discoverQueryHits"), 2, "down"),
    ])


def lab04(page):
    lab = "LAB-04"
    # Adim 1: ornek veriyi arayuzden kur
    page.goto(BASE + "/app/home", wait_until="domcontentloaded"); settle(page, 4)
    try:
        page.get_by_text("Explore on my own", exact=True).first.click(timeout=3000); settle(page, 3)
    except Exception:
        pass
    page.goto(BASE + "/app/home#/tutorial_directory/sampleData", wait_until="domcontentloaded"); settle(page, 4)
    if page.locator('[data-test-subj="addSampleDataSetecommerce"]').count():
        page.goto(BASE + "/app/home", wait_until="domcontentloaded"); settle(page, 4)
        shoot(page, lab, "01-sample-data-link", [(("text", "Try sample data", True), 1, "left")])
        page.get_by_text("Try sample data", exact=True).first.click(); settle(page, 4)
        shoot(page, lab, "02-sample-data-install", [(("testsubj", "addSampleDataSetecommerce"), 2, "left")])
        page.locator('[data-test-subj="addSampleDataSetecommerce"]').first.click()
        page.get_by_text("View data").first.wait_for(timeout=180000); time.sleep(2)
    else:
        print("ornek veri zaten kurulu; 01-02 atlandi")

    # Adim 2: Discover KQL
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dataview(page, 'Kibana Sample Data eCommerce'); settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_30_days"]').first.click(); settle(page, 4)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('customer_gender : "FEMALE" and taxful_total_price > 100'); page.keyboard.press("Enter"); settle(page, 6)
    shoot(page, lab, "03-discover-kql", [
        (("testsubj", "queryInput"), 1, "down"),
        (("testsubj", "discoverQueryHits"), 2, "down"),
    ])

    # Adim 2: Inspect -> Request
    page.locator('[data-test-subj="app-menu-overflow-button"]').first.click(); time.sleep(1.5)
    shoot(page, lab, "04-discover-inspect-menu", [
        (("testsubj", "app-menu-overflow-button"), 1, "down"),
        (("role", "menuitem", "Inspect tab"), 2, "left"),
    ])
    page.get_by_role("menuitem", name="Inspect tab").first.click(); time.sleep(3)
    subs = page.eval_on_selector_all('[data-test-subj]', 'els => [...new Set(els.filter(e=>e.offsetParent!==null).map(e=>e.getAttribute("data-test-subj")))].filter(s=>/nspector|equest/i.test(s))')
    print("INSPECTOR:", subs)
    if page.locator('[data-test-subj="inspectorViewChooser"]').count():
        page.locator('[data-test-subj="inspectorViewChooser"]').first.click(); time.sleep(1)
        page.locator('[data-test-subj="inspectorViewChooserRequests"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="inspectorRequestDetailRequest"]').first.click(); time.sleep(2)
    shoot(page, lab, "05-discover-inspect", [
        (("testsubj", "inspectorRequestDetailRequest"), 3, "up"),
        (("testsubj", "inspectorRequestCodeViewerContainer"), 4, None),
    ])
    page.keyboard.press("Escape"); time.sleep(1)


def sunum(page):
    """Sunumlar icin ISARETSIZ Kibana 9.5.5 ekran goruntuleri: assets/screenshots/sunum/<ad>.png."""
    lab = "sunum"
    def dv(name):
        pick_dataview(page, name); settle(page, 5)
    def zaman(preset):
        page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
        page.locator(f'[data-test-subj="dateRangePickerPresetItem-{preset}"]').first.click(); settle(page, 4)
    def kql(q):
        box = page.locator('[data-test-subj="queryInput"]').first
        box.click(); box.fill(q); page.keyboard.press("Enter"); settle(page, 5)
    # discover: KQL modu, e-ticaret, belge listesi
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    dv("Kibana Sample Data eCommerce"); zaman("Last_7_days"); kql("")
    shoot(page, lab, "discover", [])
    # discover-kql-5xx: web logs, response >= 500
    dv("Kibana Sample Data Logs"); zaman("Last_7_days"); kql("response >= 500")
    shoot(page, lab, "discover-kql-5xx", [])
    # lens-editor: alanin Visualize dugmesi bar grafikli Lens acar
    dv("Kibana Sample Data eCommerce"); kql("")
    page.locator('[data-test-subj="field-category-showDetails"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="fieldVisualize-category"]').first.click(); settle(page, 8)
    for txt in ("Don't show again", "Got it", "Dismiss"):
        try: page.get_by_text(txt).first.click(timeout=1500)
        except Exception: pass
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "lens-editor", [])
    # discover-esql: ES|QL modu, ornek sorgu ve tablo
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    dv("Kibana Sample Data eCommerce")
    page.get_by_text("Query in ES|QL").first.click(); settle(page, 5)
    ed = page.locator('[data-test-subj="ESQLEditor"] .monaco-editor').first
    ed.click(); page.keyboard.press("ControlOrMeta+A"); page.keyboard.press("Delete")
    page.keyboard.type("FROM kibana_sample_data_ecommerce | STATS siparis = COUNT(*) BY day_of_week | SORT siparis DESC")
    time.sleep(1); page.keyboard.press("Escape")
    page.locator('[data-test-subj="querySubmitButton"]').first.click(); settle(page, 6)
    shoot(page, lab, "discover-esql", [])
    # dataview-listesi
    page.goto(BASE + "/app/management/kibana/dataViews", wait_until="domcontentloaded"); settle(page, 5)
    shoot(page, lab, "dataview-listesi", [])
    # kibana-dashboard: hazir [Logs] Web Traffic panosu (ornek web logs verisi)
    page.goto(BASE + "/app/dashboards#/view/edf84fe0-e1a0-11e7-b6d5-4dc382ef7f5b", wait_until="domcontentloaded"); settle(page, 12)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "kibana-dashboard", [])
    # index-management
    page.goto(BASE + "/app/management/data/index_management/indices", wait_until="domcontentloaded"); settle(page, 6)
    shoot(page, lab, "index-management", [])


def lab07(page):
    lab = "LAB-07"
    def dv(name):
        pick_dataview(page, name); settle(page, 5)
    # Adim 4: Lens ve pano (ES|QL adimi LAB-08'e tasindi: shots_lab08.py)
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    dv("Kibana Sample Data eCommerce")
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); settle(page, 4)
    page.locator('[data-test-subj="field-category-showDetails"]').first.click(); time.sleep(2)
    shoot(page, lab, "02-field-visualize", [
        (("testsubj", "field-category-showDetails"), 1, "right"),
        (("testsubj", "fieldVisualize-category"), 2, "right"),
    ])
    page.locator('[data-test-subj="fieldVisualize-category"]').first.click(); settle(page, 8)
    for txt in ("Don't show again", "Got it", "Dismiss"):
        try: page.get_by_text(txt).first.click(timeout=1500)
        except Exception: pass
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "03-lens-bar", [
        (("css", '[data-test-subj="lnsWorkspace"], .lnsWorkspacePanelWrapper'), 3, None),
        (("testsubj", "lnsApp_saveButton"), 4, "down"),
    ])
    # Adim 4: breakdown
    page.locator('[data-test-subj="lnsXY_splitDimensionPanel"] [data-test-subj="lns-empty-dimension"]').first.click(); time.sleep(2)
    cb = page.locator('[data-test-subj="indexPattern-dimension-field"] input').first
    cb.click(); cb.fill("customer_gender"); time.sleep(1); page.keyboard.press("Enter"); settle(page, 4)
    page.locator('[data-test-subj="lns-indexPattern-dimensionContainerBack"]').first.click(); settle(page, 4)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "03b-lens-breakdown", [
        (("testsubj", "lnsXY_splitDimensionPanel"), "a", "left"),
        (("css", '[data-test-subj="lnsWorkspace"], .lnsWorkspacePanelWrapper'), "b", None),
    ])
    page.locator('[data-test-subj="lnsApp_saveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Kategori bazında sipariş")
    page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("New")').first.click(); time.sleep(1)
    shoot(page, lab, "04-lens-save", [
        (("testsubj", "savedObjectTitle"), 5, "left"),
        (("css", '[data-test-subj="add-to-dashboard-options"] label:has-text("New")'), 6, "right"),
        (("testsubj", "confirmSaveSavedObjectButton"), 7, "down"),
    ])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 10)
    page.mouse.move(800, 60); time.sleep(1)
    save = page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"], [data-test-subj="dashboardSaveMenuItem"]').first
    shoot(page, lab, "05-dashboard", [
        (("css", '[data-test-subj="dashboardInteractiveSaveMenuItem"], [data-test-subj="dashboardSaveMenuItem"]'), 8, "down"),
        (("css", '[data-test-subj="dashboardPanel"]'), 9, "right"),
    ])
    save.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Satış özeti")
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 5)
    print("pano kaydedildi")


def lab07canli(page):
    """Adim 5: canli akis Discover'da, Last 15 minutes + 10 sn otomatik yenileme."""
    lab = "LAB-07"
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dataview(page, 'Canlı siparişler'); settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_15_minutes"]').first.click(); settle(page, 4)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    # Settings dugmesinin yazisi yok, yalniz disli simgesi: once onu kirmizi kutuyla gosteriyoruz.
    shoot(page, lab, "06a0-canli-settings", [
        (("testsubj", "dateRangePickerSettingsButton"), 2, "left"),
    ])
    page.locator('[data-test-subj="dateRangePickerSettingsButton"]').first.click(); time.sleep(1.5)
    tg = page.locator('[data-test-subj="dateRangePickerAutoRefreshToggle"]').first
    if tg.get_attribute("aria-checked") != "true": tg.click(); time.sleep(1)
    c = page.locator('[data-test-subj="dateRangePickerAutoRefreshIntervalCount"]').first
    c.fill("10"); time.sleep(0.5)
    u = page.locator('[data-test-subj="dateRangePickerAutoRefreshIntervalUnit"]').first
    try: u.select_option(label="seconds")
    except Exception: print("birim secilemedi:", u.evaluate("e => e.tagName"))
    time.sleep(1)
    print("auto refresh:", tg.get_attribute("aria-checked"))
    shoot(page, lab, "06a-canli-ayar", [
        (("testsubj", "dateRangePickerAutoRefreshToggle"), 3, "left"),
    ])
    page.keyboard.press("Escape"); settle(page, 12)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "06-canli-discover", [
        (("testsubj", "dateRangePickerControlButton"), 1, "down"),
        (("css", '[data-test-subj="unifiedHistogramChart"], [data-test-subj="unifiedHistogramRendered"]'), 4, "left"),
    ])
    print("hits:", page.locator('[data-test-subj="discoverQueryTotalHits"]').first.inner_text())


def lab07runtime(page):
    """Adim 6: siparis_saati runtime field'i ornek data view'da."""
    lab = "LAB-07"
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dataview(page, 'Kibana Sample Data eCommerce'); settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); settle(page, 4)
    s = page.locator('[data-test-subj="fieldListFiltersFieldSearch"]').first
    s.fill("siparis"); time.sleep(2)
    page.locator('[data-test-subj="field-siparis_saati-showDetails"]').first.click(); time.sleep(3)
    shoot(page, lab, "07-runtime-field", [
        (("testsubj", "field-siparis_saati-showDetails"), 1, "right"),
        (("css", '[data-test-subj="unifiedFieldStats-topValueBuckets"], [data-test-subj*="fieldStats"]'), 2, "right"),
    ])


def lab21(page):
    lab = "LAB-21"
    page.goto(BASE + "/app/management/data/index_management/indices", wait_until="domcontentloaded"); settle(page, 6)
    # README: arama kutusuna index adi yazilir (sunucuda cok index olunca satir ilk sayfada olmaz)
    arama = page.locator('[data-test-subj="indicesSearch"]').first
    arama.fill("saglik-arizali"); page.keyboard.press("Enter"); time.sleep(2)
    for _ in range(10):
        if page.locator('tr:has-text("saglik-arizali")').count():
            break
        page.get_by_role("button", name="Reload indices").first.click(); time.sleep(3)
    shoot(page, lab, "01-index-management-red", [
        (("testsubj", "indicesSearch"), 1, "down"),
        (("css", 'tr:has-text("saglik-arizali")'), 2, "left"),
    ])


def lab14(page):
    """On kosul: LAB-14 adim 1-3 ve 6 calismis (grok-* verisi son 30 dk icinde, pano kurulu)."""
    lab = "LAB-14"
    line = ('2026-11-02 10:14:09 [ERROR] payment-gateway: {"error":"Payment timeout",'
            '"order_id":"ORD-9912","response_time_ms":30000}')
    pattern = ("^%{TIMESTAMP_ISO8601:ts} \\[%{LOGLEVEL:loglevel}\\] %{NOTSPACE:service}: "
               "%{GREEDYDATA:rest_msg}$")
    page.goto(BASE + "/app/dev_tools#/grokdebugger", wait_until="domcontentloaded"); settle(page, 6)
    for subj, text in (("eventInput", line), ("patternInput", pattern)):
        # Monaco: klavyeyle yazmak tirnak/parantezi otomatik kapatir; insert_text yapistirma gibidir.
        page.locator(f'[data-test-subj="{subj}"] .monaco-editor').first.click(); time.sleep(0.5)
        page.keyboard.insert_text(text); time.sleep(0.5)
    page.locator('[data-test-subj="btnSimulate"]').first.click(); time.sleep(3)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "01-grok-debugger", [
        (("text", "Sample Data", True), 1, "right"),
        (("text", "Grok Pattern", True), 2, "right"),
        (("testsubj", "btnSimulate"), 3, "right"),
        (("text", "Structured Data", True), 4, "right"),
    ], scroll_to=("testsubj", "eventInput"))
    page.goto(BASE + "/app/dashboards#/view/grok-logstash-overview", wait_until="domcontentloaded")
    settle(page, 10)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "02-grok-dashboard", [
        (("text", "Ayrıştırılamayan Olay (Karantina)", True), 1, "right"),
        (("text", "Servis Bazında Hata Sayısı", True), 2, "right"),
        (("text", "Zaman İçinde Log Seviyesi Dağılımı", True), 3, "right"),
    ])
    # Adim 6 <details>: paneli elle kurmak (Discover -> service -> Visualize -> Lens)
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dataview(page, 'Logstash Grok Logları'); settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_1_hour"]').first.click(); settle(page, 3)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('loglevel : "error"'); page.keyboard.press("Enter"); settle(page, 5)
    page.locator('[data-test-subj="field-service-showDetails"]').first.click(); time.sleep(2)
    shoot(page, lab, "03-discover-service-visualize", [
        (("testsubj", "discover-dataView-switch-link"), 1, "right"),
        (("testsubj", "queryInput"), 2, "down"),
        (("testsubj", "field-service-showDetails"), 3, "right"),
        (("testsubj", "fieldVisualize-service"), 4, "right"),
    ])
    page.locator('[data-test-subj="fieldVisualize-service"]').first.click(); settle(page, 8)
    for txt in ("Don't show again", "Got it", "Dismiss"):
        try: page.get_by_text(txt).first.click(timeout=1500)
        except Exception: pass
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "04-lens-service-errors", [
        (("css", '[data-test-subj="lnsWorkspace"], .lnsWorkspacePanelWrapper'), 5, None),
    ])


def lab10(page):
    """On kosul: LAB-10 adim 1-6 calismis (beats-log data view, trafik son 1 saat icinde)."""
    lab = "LAB-10"
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dataview(page, 'Beats logları'); settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_1_hour"]').first.click(); settle(page, 3)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('container.name : "nginx-beats-lab" and http.response.status_code >= 400')
    page.keyboard.press("Enter"); settle(page, 6)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "01-discover-404", [
        (("testsubj", "discover-dataView-switch-link"), 1, "right"),
        (("testsubj", "queryInput"), 2, "down"),
        (("css", '[data-test-subj="discoverQueryHits"], [data-test-subj="unifiedDataTableToolbar"] [data-test-subj="discoverQueryTotalHits"]'), 3, "right"),
    ])


def lab16(page, parca="1"):
    """LAB-16 Kibana pano atolyesi. On kosul: veri_uret.py ve pano-apache data view'i (Adim 1)."""
    lab = "LAB-16"
    DV = "Apache erişim logları"

    def ipucu(filt):
        v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all()]
        print("  subj:", sorted(set(x for x in v if x and any(f.lower() in x.lower() for f in filt)))[:60])

    def zaman_7g():
        page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
        page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); settle(page, 3)

    if parca == "2":
        return lab16_aggregation(page, lab, DV, ipucu, zaman_7g)
    # --- Adim 2: Visualize library ve Create visualization penceresi
    page.goto(BASE + "/app/visualize", wait_until="domcontentloaded"); settle(page, 6)
    shoot(page, lab, "01-visualize-library", [(("testsubj", "newItemButton"), 1, "left")])
    page.locator('[data-test-subj="newItemButton"]').first.click(); time.sleep(2)
    shoot(page, lab, "02-create-visualization", [
        (("testsubj", "visType-lens"), 2, "left"),
        (("testsubj", "visType-maps"), 3, "left"),
        (("testsubj", "groupModalLegacyTab"), 4, "right"),
    ])
    page.locator('[data-test-subj="groupModalLegacyTab"]').first.click(); time.sleep(1.5)
    shoot(page, lab, "03-legacy", [(("testsubj", "groupModalLegacyTab"), 4, "right")])
    page.locator('[data-test-subj="groupModalRecommendedTab"]').first.click(); time.sleep(1)

    # --- Adim 3: Lens ile ilk grafik
    page.locator('[data-test-subj="visType-lens"]').first.click(); settle(page, 8)
    page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
    page.get_by_text(DV, exact=True).last.click(); settle(page, 4)
    zaman_7g()
    page.locator('[data-test-subj="lnsFieldListPanelField-@timestamp"]').first.hover(); time.sleep(0.5)
    page.locator('[data-test-subj="fieldToggle-@timestamp"]').first.click(); settle(page, 4)
    page.locator('[data-test-subj="lnsFieldListPanelField-http.response.status_class"]').first.hover(); time.sleep(0.5)
    page.locator('[data-test-subj="fieldToggle-http.response.status_class"]').first.click(); settle(page, 5)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "04-lens-ilk-grafik", [
        (("testsubj", "lns-dataView-switch-link"), 1, "right"),
        (("testsubj", "lnsFieldListPanelField-@timestamp"), 2, "right"),
        (("testsubj", "lnsFieldListPanelField-http.response.status_class"), 3, "right"),
        (("css", '[data-test-subj="lnsWorkspace"], .lnsWorkspacePanelWrapper'), 4, None),
    ])
    try:
        page.locator('[data-test-subj="lnsChartSwitchPopover"]').first.click(); time.sleep(1.5)
        shoot(page, lab, "05-lens-grafik-turu", [
            (("testsubj", "lnsChartSwitchPopover"), 5, "down"),
        ])
        page.keyboard.press("Escape"); time.sleep(1)
    except Exception as e:
        print("HATA grafik turu", str(e)[:120]); ipucu(["chart", "switch", "type"])
    page.locator('[data-test-subj="lnsApp_saveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Zaman içinde istekler (durum sınıfı)")
    try:
        page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("None")').first.click(); time.sleep(0.5)
    except Exception:
        pass
    page.locator('[data-test-subj="add-to-library-checkbox"] input').first.check(force=True); time.sleep(1)
    shoot(page, lab, "06-lens-kaydet-library", [
        (("testsubj", "savedObjectTitle"), 6, "left"),
        (("testsubj", "add-to-library-checkbox"), 7, "left"),
        (("testsubj", "confirmSaveSavedObjectButton"), 8, "down"),
    ])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 6)
    print("lens kaydedildi")


def lab16_aggregation(page, lab, DV, ipucu, zaman_7g):
    """LAB-16 Adim 4: tablo, heat map, formula."""
    def modal_kapat():
        for t in ("Discard changes", "Leave", "Leave anyway", "Discard", "Confirm", "Got it", "Dismiss"):
            try:
                page.get_by_role("button", name=t, exact=True).last.click(timeout=800); time.sleep(1)
            except Exception:
                pass
        if page.locator(".euiOverlayMask").count():
            page.screenshot(path="/tmp/lab14-overlay-debug.png"); page.keyboard.press("Escape"); time.sleep(1)

    def yeni_lens(tur):
        page.goto(BASE + "/app/lens#/", wait_until="domcontentloaded"); settle(page, 8)
        modal_kapat()
        if DV not in page.locator('[data-test-subj="lns-dataView-switch-link"]').first.inner_text():
            page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
            page.get_by_text(DV, exact=True).last.click(); settle(page, 4)
        zaman_7g()
        page.locator('[data-test-subj="lnsChartSwitchPopover"]').first.click(); time.sleep(1.5)
        page.locator(f'[data-test-subj="lnsChartSwitchPopover_{tur}"]').first.click(); time.sleep(2)

    def alan(ad):
        page.locator(f'[data-test-subj="lnsFieldListPanelField-{ad}"]').first.hover(); time.sleep(0.5)
        page.locator(f'[data-test-subj="fieldToggle-{ad}"]').first.click(); settle(page, 3)

    def kaydet(baslik):
        page.locator('[data-test-subj="lnsApp_saveButton"]').first.click(); time.sleep(2)
        page.locator('[data-test-subj="savedObjectTitle"]').fill(baslik)
        try:
            page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("None")').first.click(); time.sleep(0.5)
        except Exception:
            pass
        page.locator('[data-test-subj="add-to-library-checkbox"] input').first.check(force=True); time.sleep(0.5)
        page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 5)
        print("kaydedildi:", baslik)

    # --- Adim 4a: tablo + quick functions
    yeni_lens("lnsDatatable")
    alan("source.geo.country_name"); alan("response_time_ms")
    page.mouse.move(800, 60); time.sleep(1)
    try:
        page.get_by_text("Median of response_time_ms").last.click(); time.sleep(2)
        shoot(page, lab, "07-quick-functions", [
            (("testsubj", "lens-dimensionTabs-quickFunctions"), 1, "up"),
            (("testsubj", "lns-indexPatternDimension-average"), 2, "left"),
            (("testsubj", "lns-indexPatternDimension-percentile"), 3, "left"),
            (("testsubj", "lens-dimensionTabs-formula"), 4, "up"),
        ])
        page.locator('[data-test-subj="lns-indexPatternDimension-percentile"]').first.click(); settle(page, 3)
        page.keyboard.press("Escape"); time.sleep(1)
        try: page.get_by_role("button", name="Close", exact=True).last.click(timeout=1500)
        except Exception: pass
    except Exception as e:
        print("HATA quick", str(e)[:150]); ipucu(["dimension", "lns-", "trigger"])
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "08-tablo", [(("css", '[data-test-subj="lnsWorkspace"], .lnsWorkspacePanelWrapper'), 5, None)])
    kaydet("Ülke bazında istek ve yanıt süresi")

    # --- Adim 4b: heat map
    yeni_lens("heatmap")
    alan("@timestamp"); alan("url.path")
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "09-heatmap", [(("css", '[data-test-subj="lnsWorkspace"], .lnsWorkspacePanelWrapper'), 6, None)])
    kaydet("Sayfa ve saat yoğunluğu")

    # --- Adim 4c: metric + formula
    yeni_lens("lnsMetric")
    page.locator('[data-test-subj="lnsMetric_primaryMetricDimensionPanel"] [data-test-subj="lns-empty-dimension"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="lens-dimensionTabs-formula"]').first.click(); time.sleep(2)
    try:
        ed = page.locator('[data-test-subj="lnsFormulaWidget"] .monaco-editor, .lnsFormula .monaco-editor').first
        ed.click(); time.sleep(0.5)
        page.keyboard.press("ControlOrMeta+A"); page.keyboard.press("Delete")
        # Monaco tirnak/parantezi kendisi kapatir; formul panodan yapistirilir.
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=BASE)
        page.evaluate("t => navigator.clipboard.writeText(t)", "count(kql='http.response.status_class : \"5xx\"') / count() * 100")
        page.keyboard.press("ControlOrMeta+V"); time.sleep(1)
        page.keyboard.press("Escape"); time.sleep(3)
        print("  formul:", ed.inner_text()[:120].replace("\n", " "))
        shoot(page, lab, "10-formula", [
            (("testsubj", "lens-dimensionTabs-formula"), 7, "down"),
            (("css", '[data-test-subj="lnsFormulaWidget"], .lnsFormula'), 8, "left"),
        ])
    except Exception as e:
        print("HATA formula", str(e)[:150]); ipucu(["formula", "monaco", "editor", "lns"])
    page.keyboard.press("Escape"); time.sleep(1)
    try: page.get_by_role("button", name="Close", exact=True).last.click(timeout=1500)
    except Exception: pass
    settle(page, 3); page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "11-metric", [(("css", '[data-test-subj="lnsWorkspace"], .lnsWorkspacePanelWrapper'), 9, None)])
    kaydet("Hata oranı (5xx, %)")


def lab24_izleme(page):
    """LAB-24 Adim 6: Stack Monitoring (Metricbeat veri toplamis olmali). Isaretli goruntuler LAB-24 klasorune,
    isaretsiz kopyalar assets/screenshots/sunum/stack-monitoring-*.png olarak yazilir."""
    lab = "LAB-24"
    page.goto(BASE + "/app/monitoring", wait_until="domcontentloaded"); settle(page, 12)
    if page.get_by_text("Create rules", exact=True).count():
        page.get_by_label("No", exact=True).check(); time.sleep(1)
        page.get_by_role("button", name="Continue").first.click(); settle(page, 6)
    shoot(page, lab, "01-izleme-ozet", [(("testsubj", "esOverview"), 1, "right"), (("testsubj", "esNumberOfNodes"), 2, "left")])
    shoot(page, "sunum", "stack-monitoring-cluster-ozet", [])
    print("OZET:", page.locator('[data-test-subj="esOverview"]').first.inner_text().replace("\n", " | ")[:300])
    page.locator('[data-test-subj="esNumberOfNodes"]').first.click(); settle(page, 8)
    print("NODES url:", page.url.replace(BASE, "")[:80])
    print("NODES tablo:", page.locator("tbody tr").first.inner_text().replace("\n", " | ")[:300])
    shoot(page, lab, "02-izleme-nodes", [(("css", "tbody tr >> nth=0"), 3, "left")])
    shoot(page, "sunum", "stack-monitoring-nodes", [])


def lab14_ingest_arayuz(page):
    """LAB-14 Adim 7 (details): ingest pipeline'i Kibana arayuzunden kurmak ve Test pipeline ile denemek.
    Isaretli goruntuler LAB-14 klasorune, isaretsiz kopyalar assets/screenshots/sunum/lab14-ingest-arayuz-*.png yazilir."""
    lab = "LAB-14"
    AD = "grok-ayristir-arayuz"
    SATIR = "2026-11-02 10:14:09 [ERROR] payment-gateway: Payment timeout"
    DESEN = "^%{TIMESTAMP_ISO8601:ts} \\[%{LOGLEVEL:loglevel}\\] %{NOTSPACE:service}: %{GREEDYDATA:rest_msg}$"
    page.goto(BASE + "/app/management/ingest/ingest_pipelines", wait_until="domcontentloaded"); settle(page, 6)
    page.get_by_role("button", name="Create pipeline").first.click(); time.sleep(1.5)
    page.get_by_role("menuitem", name="New pipeline").first.click(); settle(page, 4)
    page.locator('[data-test-subj="nameField"] input').first.fill(AD)
    page.locator('[data-test-subj="descriptionField"] textarea, [data-test-subj="descriptionField"] input').first.fill("Uygulama logu: grok, kucuk harf"); time.sleep(1)
    m = [(("testsubj", "nameField"), 1, "right"), (("testsubj", "addProcessorButton"), 2, "right")]
    shoot(page, lab, "18-ingest-arayuz-olustur", m); shoot(page, "sunum", "lab14-ingest-arayuz-olustur", [])
    def isle(tip):
        page.locator('[data-test-subj="addProcessorButton"]').first.click(); time.sleep(2)
        page.locator('[data-test-subj="processorTypeSelector"]').first.click(); time.sleep(1); page.keyboard.type(tip); time.sleep(1.5); page.keyboard.press("Enter"); time.sleep(2)
    isle("Grok")
    page.locator('[data-test-subj="fieldNameField"] input').first.fill("message")
    page.locator('[data-test-subj="input-0"]').first.fill(DESEN); time.sleep(1)
    shoot(page, lab, "19-ingest-arayuz-grok", [(("testsubj", "processorTypeSelector"), 1, "left"), (("testsubj", "fieldNameField"), 2, "left"),
                                               (("testsubj", "input-0"), 3, "left"), (("css", 'role=button[name="Add processor"s]'), 4, "up")])
    shoot(page, "sunum", "lab14-ingest-arayuz-grok", [])
    page.locator('role=button[name="Add processor"s]').first.click(); time.sleep(2)
    print("subj sonra:", sorted(set(x for x in (e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all()) if x and any(w in x.lower() for w in ("processor", "test", "failure", "document", "add", "submit")))))
    isle("Lowercase")
    page.locator('[data-test-subj="fieldNameField"] input').first.fill("loglevel")
    page.locator('role=button[name="Add processor"s]').first.click(); time.sleep(2)
    # hata durumu: Failure processors bolumune Append (tags alanina _grokparsefailure ekler)
    page.locator('[data-test-subj="onFailure"] [data-test-subj="addProcessorButton"], [data-test-subj="onFailure"] button:has-text("Add a processor")').first.click(); time.sleep(2)
    page.locator('[data-test-subj="processorTypeSelector"]').first.click(); time.sleep(1); page.keyboard.type("Append"); time.sleep(1.5); page.keyboard.press("Enter"); time.sleep(2)
    print("APPEND inputs:", [(e.get_attribute("data-test-subj"), e.get_attribute("type")) for e in page.locator(".euiFlyout input:visible, .euiFlyout textarea:visible").all()])
    page.locator('[data-test-subj="fieldNameField"] input').first.fill("tags")
    deger = page.locator('.euiFlyout [data-test-subj="comboBoxSearchInput"]').nth(1)
    deger.click(); page.keyboard.type("_grokparsefailure"); page.keyboard.press("Enter"); time.sleep(1)
    shoot(page, lab, "20-ingest-arayuz-onfailure", [(("testsubj", "processorTypeSelector"), 1, "left"), (("testsubj", "fieldNameField"), 2, "left"),
                                                     (("css", 'role=button[name="Add processor"s]'), 3, "up")])
    shoot(page, "sunum", "lab14-ingest-arayuz-onfailure", [])
    page.locator('role=button[name="Add processor"s]').first.click(); time.sleep(2)
    print("flyout acik mi:", page.locator(".euiFlyout").count(), "| hata:", [e.inner_text() for e in page.locator(".euiFormErrorText").all()])
    page.screenshot(path="/tmp/ing-sonrasi.png")
    # Test pipeline: ornek document
    page.locator('[data-test-subj="addDocumentsButton"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="testPipelineFlyout"] .monaco-editor').first.click(); time.sleep(0.5)
    page.keyboard.press("Meta+A"); page.keyboard.press("Backspace")
    # Monaco parantezleri kendisi kapatir: yapistirma (insert_text) bozulur, tus tus yazmak dogru sonuc verir
    page.keyboard.type('[{"_source": {"message": "' + SATIR + '"}}, {"_source": {"message": "bozuk satir: seviye ve servis yok"}}]', delay=10); time.sleep(1)
    shoot(page, lab, "21-ingest-arayuz-test", [(("css", '[data-test-subj="testPipelineFlyout"] .monaco-editor'), 1, "left"), (("testsubj", "runPipelineButton"), 2, "up")])
    shoot(page, "sunum", "lab14-ingest-arayuz-test", [])
    page.locator('[data-test-subj="runPipelineButton"]').first.click(); time.sleep(4)
    cikti = page.locator('[data-test-subj="outputTabContent"]').first.inner_text().replace("\n", " ")
    print("TEST CIKTI ts/loglevel/service:", all(s in cikti for s in ('"ts"', '"loglevel": "error"', '"service": "payment-gateway"')), "| hata etiketi:", "_grokparsefailure" in cikti)
    shoot(page, lab, "22-ingest-arayuz-cikti", [(("testsubj", "outputTab"), 1, "down"), (("testsubj", "outputTabContent"), 2, "left")])
    shoot(page, "sunum", "lab14-ingest-arayuz-cikti", [])
    page.locator('[data-test-subj="euiFlyoutCloseButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="submitButton"]:has-text("Create pipeline")').first.click(); settle(page, 5)
    print("kaydedildi:", page.url.replace(BASE, "")[:90])


def lab14_default_pipeline(page):
    """LAB-14 Adim 7 (details, ingest arayuzu sonrasi): grok-varsayilan index'inin default_pipeline ayarini
    Index Management > Settings > Edit mode ile grok-ayristir-arayuz yapmak. On kosul: lab14_ingest_arayuz."""
    lab = "LAB-14"
    IDX = "grok-varsayilan"
    page.goto(BASE + "/app/management/data/index_management/indices", wait_until="domcontentloaded"); settle(page, 6)
    ara = page.locator('[data-test-subj="indicesSearch"]').first
    ara.fill(IDX); ara.press("Enter"); settle(page, 3)
    ad = f'[data-test-subj="indexTableIndexNameLink"]:text-is("{IDX}")'
    shoot(page, lab, "23-index-listesi", [(("testsubj", "indicesSearch"), 1, "left"), (("css", ad), 2, "left")])
    page.locator(ad).first.click(); settle(page, 5)
    page.locator('[data-test-subj="indexDetailsTab-settings"]').first.click(); settle(page, 3)
    page.locator('[data-test-subj="indexDetailsSettingsEditModeSwitch"]').first.click(); time.sleep(2)
    satir = page.locator('.monaco-editor .view-line', has_text='"index.default_pipeline"').first
    satir.click(); time.sleep(0.5); page.keyboard.press("End")
    # satir sonu: "grok-ayristir", ya da "grok-ayristir" -> imleci kapanis tirnaginin onune al
    geri = 2 if satir.inner_text().replace("\xa0", " ").rstrip().endswith('",') else 1
    for _ in range(geri):
        page.keyboard.press("ArrowLeft")
    page.keyboard.type("-arayuz"); time.sleep(1)
    print("SATIR:", satir.inner_text().replace("\xa0", " ").strip())
    shoot(page, lab, "24-index-ayar-pipeline", [
        (("testsubj", "indexDetailsTab-settings"), 1, "up"),
        (("testsubj", "indexDetailsSettingsEditModeSwitch"), 2, "left"),
        (("css", '.monaco-editor .view-line:has-text("index.default_pipeline")'), 3, "left"),
        (("testsubj", "indexDetailsSettingsSave"), 4, "left")])
    page.locator('[data-test-subj="indexDetailsSettingsSave"]').first.click(); settle(page, 4)
    print("BILDIRIM:", [t.inner_text().replace("\n", " ")[:120] for t in page.locator(".euiToast").all()])


def lab16_kaydet(page):
    """LAB-16 Adim 7: panoyu kaydetmek (zaman kaydi), paylasmak (Share), disa aktarmak (Export). On kosul: Adim 1-6 (pano "Apache atolye").
    Isaretli goruntuler LAB-16 klasorune, isaretsiz kopyalar assets/screenshots/sunum/lab16-*.png olarak yazilir."""
    lab = "LAB-16"
    def ac(p):
        p.goto(BASE + "/app/dashboards", wait_until="domcontentloaded"); settle(p, 5)
        p.get_by_text("Apache atölye", exact=True).first.click(); settle(p, 8)
    def temiz_pencerede():
        ctx = page.context.browser.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=SCALE)
        p = ctx.new_page(); login(p); ac(p)
        z = p.locator('[data-test-subj="dateRangePickerControlButton"]').first.inner_text().strip()
        ctx.close(); return z
    print("ZAMAN once (temiz pencere):", temiz_pencerede())
    ac(page)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); settle(page, 6)
    page.locator('[data-test-subj="dashboardEditMode"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="app-menu-overflow-button"]').first.click(); time.sleep(1.5)
    page.get_by_role("menuitem", name="Settings").first.click(); time.sleep(2)
    sw = page.locator('[data-test-subj="storeTimeWithDashboard"]').first
    if sw.get_attribute("aria-checked") != "true": sw.click(); time.sleep(1)
    marks = [(("testsubj", "storeTimeWithDashboard"), 1, "left"), (("testsubj", "applyCustomizeDashboardButton"), 2, "up")]
    shoot(page, lab, "15-pano-zaman-kaydi", marks); shoot(page, "sunum", "lab16-pano-zaman-kaydi", [])
    page.locator('[data-test-subj="applyCustomizeDashboardButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="dashboardQuickSaveMenuItem"]').first.click(); settle(page, 4)
    page.locator('[data-test-subj="dashboardViewOnlyMode"]').first.click(); settle(page, 4)
    print("ZAMAN sonra (temiz pencere):", temiz_pencerede())
    page.locator('[data-test-subj="shareTopNavButton"]').first.click(); time.sleep(2.5)
    shoot(page, lab, "16-pano-share", [(("text", "Everybody in the space", False), 1, "left"), (("css", '[role="dialog"] [role="switch"]'), 2, "left"),
                                       (("testsubj", "copyShareUrlButton"), 3, "up")])
    shoot(page, "sunum", "lab16-pano-share", [])
    page.keyboard.press("Escape"); time.sleep(1)
    page.goto("about:blank"); ac(page)
    page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
    shoot(page, lab, "17-pano-export", [(("testsubj", "exportMenuItem-JSON"), 1, "left"), (("testsubj", "exportMenuItem-PDF"), 2, "left"),
                                         (("testsubj", "exportMenuItem-PNG"), 3, "left"), (("testsubj", "scheduleExport"), 4, "left")])
    shoot(page, "sunum", "lab16-pano-export", [])


def lab16_pano(page):
    """LAB-16 Adim 5-6: pano, From library aramasi, Control. On kosul: lab16 ve lab16_2 akislari (Library'de 4 grafik)."""
    lab = "LAB-16"
    def ipucu(filt):
        v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all()]
        print("  subj:", sorted(set(x for x in v if x and any(f.lower() in x.lower() for f in filt)))[:60])
    page.goto(BASE + "/app/dashboards#/create", wait_until="domcontentloaded"); settle(page, 6)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); settle(page, 3)
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(4)
    fl = page.locator('[data-test-subj="dashboardAddPanel"]').first
    page.locator('[data-test-subj="addToDashboardTab-library"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="savedObjectFinderSearchInput"]').first.fill("istek")
    page.keyboard.press("Enter"); time.sleep(4)
    shoot(page, lab, "12-from-library-arama", [
        (("testsubj", "addToDashboardTab-library"), 1, "down"),
        (("testsubj", "savedObjectFinderSearchInput"), 2, "left"),
        (("css", '[data-test-subj="savedObjectsFinderTable"]'), 3, None),
    ])
    def ekle(t):
        fl.get_by_role("button", name=t).first.click(); time.sleep(3)
    for t in ("Zaman içinde istekler (durum sınıfı)", "Ülke bazında istek ve yanıt süresi"):
        ekle(t)
    for ara, t in (("yoğunluğu", "Sayfa ve saat yoğunluğu"), ("Hata oranı", "Hata oranı (5xx, %)")):
        page.locator('[data-test-subj="savedObjectFinderSearchInput"]').first.fill(ara)
        page.keyboard.press("Enter"); time.sleep(3)
        ekle(t)
    try:
        page.locator('[data-test-subj="euiFlyoutCloseButton"]').first.click(); time.sleep(2)
    except Exception:
        pass
    settle(page, 5)
    # Control: ulke acilir listesi
    try:
        page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(4)
        page.locator('[data-test-subj="create-action-Control"]').first.click(); time.sleep(3)
        ipucu(["control", "field", "editor", "data"])
        fly = page.locator('[data-test-subj="control-editor-flyout"]').first
        page.locator('[data-test-subj="field-search-input"]').first.fill("country"); time.sleep(1)
        page.locator('[data-test-subj="field-picker-select-source.geo.country_name"]').first.click(); time.sleep(2)
        page.locator('[data-test-subj="create__options_list_control"]').first.click(); time.sleep(1)
        shoot(page, lab, "13-control", [
            (("testsubj", "field-picker-select-source.geo.country_name"), 4, "left"),
            (("testsubj", "create__options_list_control"), 5, "left"),
            (("testsubj", "control-editor-save"), 6, "up"),
        ])
        page.locator('[data-test-subj="control-editor-save"]').first.click(); settle(page, 4)
    except Exception as e:
        print("HATA control", str(e)[:200]); ipucu(["control", "field", "editor", "save"])
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Apache atölye")
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 6)
    try:
        page.locator('[data-test-subj^="optionsList-control-"]').first.click(); time.sleep(2)
        page.get_by_text("Germany", exact=True).last.click(); time.sleep(1)
        page.keyboard.press("Escape"); settle(page, 6)
    except Exception as e:
        print("HATA secim", str(e)[:200]); ipucu(["optionsList", "control"])
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "14-pano-filtreli", [
        (("css", '[data-test-subj^="optionsList-control-"]'), 7, "down"),
        (("text", "Ülke bazında istek ve yanıt süresi", True), 8, "right"),
    ])
    print("pano kaydedildi")


def lab18_harita(page):
    """LAB-18 Adim 2: Maps, cluster katmani. On kosul: veri_uret.py ve alarm-apache data view'i."""
    lab = "LAB-18"
    page.goto(BASE + "/app/maps/map", wait_until="domcontentloaded"); settle(page, 8)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); settle(page, 3)
    page.locator('[data-test-subj="addLayerButton"]').first.click(); time.sleep(3)
    shoot(page, lab, "01-maps-katman-turu", [
        (("testsubj", "clusters"), 1, "left"),
        (("testsubj", "documents"), 2, "left"),
    ])
    page.locator('[data-test-subj="clusters"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="mapGeoIndexPatternSelect"] [data-test-subj="comboBoxSearchInput"], [data-test-subj="mapGeoIndexPatternSelect"]').first.click(); time.sleep(1)
    page.keyboard.type("alarm", delay=30); time.sleep(1.5)
    page.get_by_role("option").first.click(); time.sleep(4)
    shoot(page, lab, "02-maps-veri", [
        (("testsubj", "mapGeoIndexPatternSelect"), 3, "left"),
        (("role", "button", "Add and close", True), 4, "up"),
    ])
    page.get_by_role("button", name="Add and close", exact=True).first.click(); settle(page, 8)
    page.mouse.move(700, 450); time.sleep(1)
    shoot(page, lab, "03-maps-kumeler", [
        (("testsubj", "mapLayerTOC"), 5, "down"),
        (("testsubj", "mapContainer"), None, None),
    ])
    page.locator('[data-test-subj="mapSaveButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Ziyaretçi haritası")
    try:
        page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("None")').first.click(); time.sleep(0.5)
    except Exception:
        pass
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 4)
    print("harita kaydedildi")


def lab18_kural(page):
    """LAB-18 Adim 4: kural formu. On kosul: alarm-5xx kurali (API ile kuruldu). Aktif alarm: lab18_aktif."""
    lab = "LAB-18"
    page.goto(BASE + "/app/management/insightsAndAlerting/triggersActions/edit/alarm-5xx", wait_until="domcontentloaded")
    settle(page, 8)
    marks = []
    for hedef, no, ok in ((("text", "Elasticsearch query", False), 1, "right"),
                          (("text", "alarm-apache", False), 2, "right"),
                          (("css", 'button:has-text("is above"), button:has-text("IS ABOVE")'), 3, "right"),
                          (("css", 'button:has-text("for the last"), button:has-text("FOR THE LAST")'), 3, "right")):
        try:
            box_of(page, hedef); marks.append((hedef, no, ok))
        except Exception as e:
            print("isaret yok:", hedef, str(e)[:80])
    shoot(page, lab, "04-kural-formu", marks, scroll_to=marks[0][0] if marks else None)
    try:
        shoot(page, lab, "04b-kural-aksiyon", [(("text", "alarm-gecmisi-yaz", False), 4, "right")],
              scroll_to=("text", "alarm-gecmisi-yaz", False))
    except Exception as e:
        print("HATA aksiyon", str(e)[:120])


def lab18_aktif(page):
    """LAB-18 Adim 5: ariza yazildiktan sonra kural sayfasinda ACIK alarm. Alarm acilana kadar (en cok ~3 dk) sayfa yenilenir."""
    lab = "LAB-18"
    for i in range(18):
        page.goto(BASE + "/app/management/insightsAndAlerting/triggersActions/rule/alarm-5xx", wait_until="domcontentloaded")
        settle(page, 6)
        kutu = page.get_by_text("Active now", exact=True).first.locator("xpath=..").inner_text().replace("\n", " ").strip()
        print("deneme", i + 1, "->", kutu)
        if kutu.startswith("1"):
            break
        time.sleep(10)
    shoot(page, lab, "05-kural-aktif", [(("text", "Active now", True), 1, "right")])


def lab18_rapor(page):
    """LAB-18 Adim 6: Discover CSV raporu ve Reporting listesi."""
    lab = "LAB-18"
    page.goto(BASE + "/app/discover", wait_until="domcontentloaded"); settle(page, 6)
    pick_dataview(page, 'Apache logları (alarm)'); settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); settle(page, 3)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('http.response.status_class : "5xx"'); page.keyboard.press("Enter"); settle(page, 5)
    page.locator('[data-test-subj="app-menu-overflow-button"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
    shoot(page, lab, "06-discover-export", [
        (("testsubj", "queryInput"), 1, "down"),
        (("testsubj", "exportMenuItem-CSV"), 2, "left"),
        (("testsubj", "exportMenuItem-scheduledReports"), 3, "left"),
    ])
    page.locator('[data-test-subj="exportMenuItem-CSV"]').first.click(); time.sleep(3)
    v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all()]
    print("  subj:", sorted(set(x for x in v if x and any(f in x.lower() for f in ("generate", "report", "csv", "export", "modal"))))[:30])
    for t in ("Generate CSV", "Export", "Generate export"):
        try:
            page.get_by_role("button", name=t, exact=True).last.click(timeout=2000); time.sleep(3); break
        except Exception:
            pass
    page.goto(BASE + "/app/management/insightsAndAlerting/reporting", wait_until="domcontentloaded"); settle(page, 8)
    for _ in range(10):
        if page.get_by_text("Done", exact=False).count() or page.get_by_text("Completed", exact=False).count():
            break
        time.sleep(3); page.reload(); settle(page, 4)
    shoot(page, lab, "07-reporting", [(("text", "Done", False), 4, "left")])


def lab12_upload(page):
    """LAB-12 Adim 7: Kibana'dan CSV yukleme. Dosya tarayicinin calistigi bilgisayardan secilir."""
    lab = "LAB-12"
    dosya = os.path.join(ROOT, "labs", "LAB-12-logstash-excel", "sample-data", "uygulama-loglari.csv")
    page.goto(BASE + "/app/home#/tutorial_directory/fileDataViz", wait_until="domcontentloaded"); settle(page, 6)
    page.locator('input[type="file"]').first.set_input_files(dosya); time.sleep(8)
    page.locator('[data-test-subj="dataVisualizerFileIndexNameInput"]').first.fill("excel-uygulama-loglari"); time.sleep(1)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "03-upload-onizleme", [
        (("testsubj", "dataVisualizerFileIndexNameInput"), 1, "right"),
        (("text", "uygulama-loglari.csv", True), 2, "right"),
        (("testsubj", "mlFileUploadFileStatusMappingsTab-0"), 3, "down"),
    ], scroll_to=("testsubj", "dataVisualizerFileIndexNameInput"))
    page.get_by_text("Advanced options", exact=True).first.click(); time.sleep(2)
    shoot(page, lab, "04-upload-import", [
        (("text", "Create data view", True), 4, "right"),
        (("text", "Customize index settings", False), 5, "right"),
        (("testsubj", "fileUploadImportButton"), 6, "right"),
    ], scroll_to=("testsubj", "fileUploadImportButton"))
    page.locator('[data-test-subj="fileUploadImportButton"]').first.click(); time.sleep(25)
    page.mouse.move(800, 60); time.sleep(1)
    shoot(page, lab, "05-upload-sonuc", [(("testsubj", "dataVisualizerFileResultsLinks"), 7, "up")],
          scroll_to=("testsubj", "dataVisualizerFileResultsLinks"))
    print("yuklendi")


def lab27(page, parca="hepsi"):
    """LAB-27: pano, harita, Mailpit, connector listesi, PDF ve Reporting.
    On kosul: Adim 1-5 calismis; Mailpit icin tunel: ssh -f -N -L 8025:127.0.0.1:8025 student@<ip>."""
    lab = "LAB-27"
    def zaman(preset="Last_1_hour"):
        page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
        page.locator(f'[data-test-subj="dateRangePickerPresetItem-{preset}"]').first.click(); settle(page, 4)
    # 1) pano
    if parca in ("hepsi", "pano"):
        page.goto(BASE + "/app/dashboards#/view/apache-web-operations", wait_until="domcontentloaded"); settle(page, 10)
        page.mouse.move(800, 60); time.sleep(2)
        v = [e.get_attribute("data-test-subj") for e in page.locator('[data-test-subj^="embeddablePanelHeading-"]').all()]
        print("  paneller:", v[:6])
        shoot(page, lab, "01-pano", [(("css", '[data-test-subj="dashboardPanel"]'), 1, None)])
        # 2) harita
        page.goto(BASE + "/app/maps/map", wait_until="domcontentloaded"); settle(page, 8)
        page.locator('[data-test-subj="addLayerButton"]').first.click(); time.sleep(3)
        page.locator('[data-test-subj="clusters"]').first.click(); time.sleep(3)
        page.locator('[data-test-subj="mapGeoIndexPatternSelect"]').first.click(); time.sleep(1)
        page.keyboard.type("Apache Web", delay=30); time.sleep(1.5)
        page.get_by_role("option").first.click(); time.sleep(4)
        page.get_by_role("button", name="Add and close", exact=True).first.click(); settle(page, 8)
        page.mouse.move(700, 450); time.sleep(1)
        shoot(page, lab, "02-harita", [(("testsubj", "mapLayerTOC"), 1, "down")])
        page.locator('[data-test-subj="mapSaveButton"]').first.click(); time.sleep(2)
        page.locator('[data-test-subj="savedObjectTitle"]').fill("Apache ziyaretçileri")
        try:
            page.locator('[data-test-subj="add-to-dashboard-options"] label:has-text("None")').first.click(); time.sleep(0.5)
        except Exception:
            pass
        page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 4)
    # 3) Mailpit
    if parca in ("hepsi", "mailpit"):
        try:
            page.goto("http://127.0.0.1:8025/", wait_until="domcontentloaded"); time.sleep(3)
            page.get_by_text("[ALARM]", exact=False).first.click(); time.sleep(3)
            shoot(page, lab, "03-mailpit", [(("text", "[ALARM]", False), 1, "down")])
        except Exception as e:
            print("HATA mailpit", str(e)[:150])
    # 4) connector listesi
    if parca in ("hepsi", "connector"):
        page.goto(BASE + "/app/management/insightsAndAlerting/triggersActionsConnectors/connectors", wait_until="domcontentloaded"); settle(page, 6)
        shoot(page, lab, "04-connectorlar", [
            (("text", "apache-mailpit", True), 1, "right"),
            (("text", "apache-eposta", True), 2, "right"),
            (("text", "apache-slack", True), 3, "right"),
        ])
    # 5) PDF
    if parca in ("hepsi", "pdf"):
        page.goto(BASE + "/app/dashboards#/view/apache-web-operations", wait_until="domcontentloaded"); settle(page, 10)
        page.mouse.move(800, 60); time.sleep(1)
        v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all()]
        print("  ust menu:", sorted(set(x for x in v if x and any(k in x.lower() for k in ("export", "share", "report")))))
        page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
        v = [e.get_attribute("data-test-subj") for e in page.locator("[data-test-subj]").all()]
        print("  export menu:", sorted(set(x for x in v if x and any(k in x.lower() for k in ("export", "pdf", "png", "report", "generate")))))
        try:
            page.locator('[data-test-subj="exportMenuItem-PDF"]').first.click(); time.sleep(3)
            shoot(page, lab, "05-pdf-olustur", [(("text", "Export dashboard as PDF", True), 1, "left"), (("testsubj", "generateReportButton"), 2, "up")])
            page.locator('[data-test-subj="generateReportButton"]').first.click(); time.sleep(5)
        except Exception as e:
            print("HATA pdf", str(e)[:150])
        page.goto(BASE + "/app/management/insightsAndAlerting/reporting", wait_until="domcontentloaded"); settle(page, 8)
        satir = 'tr:has-text("Apache Web Trafiği ve GeoIP"):has-text("Done")'
        for _ in range(24):
            if page.locator(satir).count():
                break
            time.sleep(5); page.reload(); settle(page, 4)
        print("  pdf satiri:", page.locator(satir).count())
        shoot(page, lab, "06-reporting", [(("css", satir), 3, "left")])


def lab18_pdf(page):
    """LAB-18 Adim 6 (PDF): Ziyaretci haritasi ile Alarm panosu, Export > PDF, Reporting. On kosul: Adim 2'nin haritasi."""
    lab = "LAB-18"
    page.goto(BASE + "/app/dashboards#/create?_g=(time:(from:now-7d,to:now))", wait_until="domcontentloaded"); settle(page, 6)
    page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="addToDashboardTab-library"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectFinderSearchInput"]').first.fill("Ziyaretçi"); page.keyboard.press("Enter"); time.sleep(3)
    shoot(page, lab, "08-pano-library", [
        (("testsubj", "dashboardAddTopNavButton"), 5, "down"),
        (("testsubj", "addToDashboardTab-library"), None, "down"),
    ])
    page.locator('[data-test-subj="dashboardAddPanel"]').first.get_by_role("button", name="Ziyaretçi haritası").first.click(); time.sleep(3)
    try: page.locator('[data-test-subj="euiFlyoutCloseButton"]').first.click(); time.sleep(2)
    except Exception: pass
    settle(page, 6)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Alarm panosu")
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 8)
    try: page.locator('[data-test-subj="dashboardViewOnlyMode"]').first.click(timeout=5000); settle(page, 4)
    except Exception: pass
    page.locator('[data-test-subj="exportTopNavButton"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="exportMenuItem-PDF"]').first.click(); time.sleep(3)
    shoot(page, lab, "09-pdf-export", [(("testsubj", "exportMenuItem-PDF"), 6, "left"), (("testsubj", "generateReportButton"), 7, "up")]) if page.locator('[data-test-subj="exportMenuItem-PDF"]').first.is_visible() else shoot(page, lab, "09-pdf-export", [(("testsubj", "generateReportButton"), 7, "up")])
    print("  generate:", page.locator('[data-test-subj="generateReportButton"]').first.inner_text())
    page.locator('[data-test-subj="generateReportButton"]').first.click(); time.sleep(5)
    page.goto(BASE + "/app/management/insightsAndAlerting/reporting", wait_until="domcontentloaded"); settle(page, 8)
    satir = 'tr:has-text("Alarm panosu") >> nth=0'   # en yeni rapor en ustte; eski kosulardan kalan "Done" satirlari yaniltmasin
    for _ in range(60):
        if page.locator(satir).count() and "Done" in page.locator(satir).inner_text():
            break
        time.sleep(5); page.reload(); settle(page, 4)
    print("  PDF_SATIRI:", page.locator(satir).inner_text().replace("\n", " | ")[:200])
    shoot(page, lab, "10-reporting-pdf", [(("css", satir), 8, "left")])


# Yeni numarali lab akislari; "eski_" ile baslayanlar yeniden yazilacak eski lablarin kaynagidir.

def lab07ek(page):
    """LAB-07 Adim 4 ek ornekler: Satis ozeti panosuna Lens ile uc panel (cizgi, metric, pasta)."""
    lab = "LAB-07"
    page.goto(BASE + "/app/dashboards#/list", wait_until="domcontentloaded"); settle(page, 5)
    page.get_by_text("Satış özeti", exact=True).first.click(); settle(page, 6)
    page.locator('[data-test-subj="dateRangePickerControlButton"], [data-test-subj="superDatePickerShowDatesButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"], [data-test-subj="superDatePickerCommonlyUsed_Last_7 days"]').first.click(); settle(page, 4)
    if not page.locator('[data-test-subj="dashboardAddTopNavButton"]').count():  # pano zaten duzenleme modunda olabilir
        page.locator('[data-test-subj="dashboardEditMode"]').first.click(timeout=15000); settle(page, 3)

    def yeni_panel():
        page.locator('[data-test-subj="dashboardAddTopNavButton"]').first.click(); time.sleep(2)
        page.locator('[data-test-subj="create-action-Visualization"]').first.click(); settle(page, 8)
        for txt in ("Don't show again", "Got it", "Dismiss"):
            try: page.get_by_text(txt).first.click(timeout=1200)
            except Exception: pass

    def tur(ad):
        page.locator('[data-test-subj="lnsChartSwitchPopover"]').first.click(); time.sleep(1.5)
        page.locator(f'[data-test-subj="lnsChartSwitchPopover_{ad}"]').first.click(); time.sleep(3)

    def boyut(panel, islem, field):
        page.locator(f'[data-test-subj="{panel}"] [data-test-subj="lns-empty-dimension"]').first.click(); time.sleep(2)
        page.locator(f'[data-test-subj="lns-indexPatternDimension-{islem}"]').first.click(); time.sleep(1.5)
        if field:
            cb = page.locator('[data-test-subj="indexPattern-dimension-field"] input').first
            cb.click(); cb.fill(field); time.sleep(1); page.keyboard.press("Enter"); time.sleep(3)
        page.locator('[data-test-subj="lns-indexPattern-dimensionContainerBack"]').first.click(); settle(page, 4)

    def kaydet(baslik, ad, isaretler):
        page.mouse.move(800, 60); time.sleep(1)
        shoot(page, lab, ad, isaretler + [(("testsubj", "lnsApp_saveButton"), len(isaretler) + 1, "down")])
        page.locator('[data-test-subj="lnsApp_saveButton"]').first.click(); time.sleep(2)
        page.locator('[data-test-subj="savedObjectTitle"]').fill(baslik)
        page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); settle(page, 8)

    # a) Gunluk ciro: cizgi grafik
    yeni_panel(); tur("line")
    boyut("lnsXY_xDimensionPanel", "date_histogram", "order_date")
    boyut("lnsXY_yDimensionPanel", "sum", "taxful_total_price")
    kaydet("Günlük ciro", "08-lens-gunluk-ciro", [
        (("testsubj", "lnsChartSwitchPopover"), 1, "down"),
        (("testsubj", "lnsXY_xDimensionPanel"), 2, "left"),
        (("testsubj", "lnsXY_yDimensionPanel"), 3, "left")])
    # b) Ortalama sepet: metric
    yeni_panel(); tur("lnsMetric")
    boyut("lnsMetric_primaryMetricDimensionPanel", "average", "taxful_total_price")
    kaydet("Ortalama sepet", "09-lens-ortalama-sepet", [
        (("testsubj", "lnsChartSwitchPopover"), 1, "down"),
        (("testsubj", "lnsMetric_primaryMetricDimensionPanel"), 2, "left")])
    # c) Cinsiyete gore siparis: pasta
    yeni_panel(); tur("pie")
    boyut("lnsPie_sliceByDimensionPanel", "terms", "customer_gender")
    boyut("lnsPie_sizeByDimensionPanel", "count", None)
    kaydet("Cinsiyete göre sipariş", "10-lens-cinsiyet-pasta", [
        (("testsubj", "lnsChartSwitchPopover"), 1, "down"),
        (("testsubj", "lnsPie_sliceByDimensionPanel"), 2, "left"),
        (("testsubj", "lnsPie_sizeByDimensionPanel"), 3, "left")])
    # Pano: dort panel, kaydet
    page.locator('[data-test-subj="dashboardQuickSaveMenuItem"]').first.click(); settle(page, 5)
    page.mouse.move(800, 60); time.sleep(1)
    n = page.locator('[data-test-subj="dashboardPanel"]').count()
    print("panel sayisi:", n)
    shoot(page, lab, "11-pano-dort-panel", [(("css", '[data-test-subj="dashboardPanel"]'), 1, "right")])

FLOWS = {"sunum": sunum, "lab01": lab01, "lab02": lab02, "lab04": lab04, "lab07": lab07, "lab07canli": lab07canli, "lab07runtime": lab07runtime, "lab07ek": lab07ek, "lab21": lab21,
         "lab14": lab14, "lab10": lab10, "lab12_upload": lab12_upload, "lab16": lab16, "lab16_2": lambda page: lab16(page, "2"), "lab16_pano": lab16_pano, "lab16_kaydet": lab16_kaydet, "lab24_izleme": lab24_izleme, "lab14_ingest_arayuz": lab14_ingest_arayuz, "lab14_default_pipeline": lab14_default_pipeline, "lab18_harita": lab18_harita, "lab27": lab27, "lab27_pano": lambda page: lab27(page, "pano"), "lab27_mailpit": lambda page: lab27(page, "mailpit"), "lab27_connector": lambda page: lab27(page, "connector"), "lab27_pdf": lambda page: lab27(page, "pdf"), "lab18_kural": lab18_kural, "lab18_aktif": lab18_aktif, "lab18_rapor": lab18_rapor, "lab18_pdf": lab18_pdf, "eski_lab04": eski_lab04, "eski_alarm": eski_alarm, "eski_fleet": eski_fleet,
         "eski_3node": eski_3node}

if __name__ == "__main__":
    names = sys.argv[1:] or list(FLOWS)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        page = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=SCALE)
        login(page)
        for n in names:
            FLOWS[n](page)
        b.close()
