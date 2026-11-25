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
            tip = tail = None   # None: numara kutunun icinde solda; "ic": icinde sagda (basligi kapatmaz)
        if tip:
            d.line((tail, tip), fill=RED, width=7)
            import math
            ang = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
            h = 26
            p1 = (tip[0] - h * math.cos(ang - 0.45), tip[1] - h * math.sin(ang - 0.45))
            p2 = (tip[0] - h * math.cos(ang + 0.45), tip[1] - h * math.sin(ang + 0.45))
            d.polygon([tip, p1, p2], fill=RED)
            nx, ny = tail
        elif arrow == "ic":
            nx, ny = x1 - 36, cy
        else:
            nx, ny = x0 + 36, y0 + 36   # oksuz isaret: numara kutunun icinde, sol ust kosede
        if no is None:
            continue
        r = 24
        # numara goruntunun disina tasmasin (kenara degen kutularda yarim kalmasin)
        nx = min(max(nx, r + 6), im.width - r - 6)
        ny = min(max(ny, r + 6), im.height - r - 6)
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

FLOWS = {"sunum": sunum, "lab01": lab01, "lab02": lab02, "lab04": lab04, "lab07": lab07, "lab07canli": lab07canli, "lab07runtime": lab07runtime, "lab07ek": lab07ek,
         "lab10": lab10, "lab12_upload": lab12_upload, "lab27": lab27, "lab27_mailpit": lambda page: lab27(page, "mailpit"), "lab27_connector": lambda page: lab27(page, "connector"), "eski_lab04": eski_lab04, "eski_alarm": eski_alarm, "eski_fleet": eski_fleet,
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
