"""LAB-11 isaretli Kibana ekran goruntuleri, README sirasiyla ve GERCEKTEN yapilir.

    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 TOKEN_DOSYA=<gizli dosya> python3 scripts/screenshots/shots_lab11.py fleet
        Adim 1: output, Fleet Server (Quick Start), Lab Linux sunucu politikasi, System integration'i (hostfs),
        enrollment token. Iki token TOKEN_DOSYA'ya .env bicimiyle yazilir (README Adim 2'de elle yapilan is);
        ekrana basilmaz, goruntulerde maskelenir.
    ... ajanlar          Adim 3 sonrasi: Fleet > Agents listesi
    ... period           Adim 5: Period 10s -> 30s, Save and deploy
    ... nginx hazir      Adim 6 ve kutusu: Nginx integration'i, hazir pano
    ... pano             Adim 7: Lens CPU grafigi, "Sunucu CPU (Fleet)" panosu
Cikti: assets/screenshots/LAB-11/<ad>.png; isaretsiz kopyalar sunum/_build/ekran/LAB-11.
"""
import os
import re
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-11"
POLITIKA = "Lab Linux sunucu"
HATA = []
SUNUM = os.environ.get("SUNUM_EKRAN", "/Users/hakan/elk/elk-workspace/sunum/_build/ekran/LAB-11")
TOKEN_DOSYA = os.environ.get("TOKEN_DOSYA", "")
MASKE = "AAEAAWVsYXN0aWMv•••••••• (gizlendi)"


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


def menu(page, ad, goruntu=None):
    page.goto(k.BASE + "/app/home", wait_until="domcontentloaded"); k.settle(page, 4)
    page.locator('[data-test-subj="toggleNavButton"]').first.click(); time.sleep(2)
    page.locator(nav(ad)).first.scroll_into_view_if_needed(); time.sleep(0.5)
    if goruntu:
        shot(page, goruntu, [(("testsubj", "toggleNavButton"), 1, "right"), (("css", nav(ad)), 2, "right")])
    page.locator(nav(ad)).first.click(); k.settle(page, 6)


def isaretle(loc, ad):
    loc.evaluate(f"e => e.setAttribute('data-isaret', '{ad}')")
    return ("css", f'[data-isaret="{ad}"]')


def satir_isaretle(kod, bas, ad):
    """Kod blogunda `bas` ile baslayan satirin ustune seffaf bir kutu koyar. Satirin span'i onceki satirin
    sonundaki \\n ile basladigi icin kendi kutusu yarim satir yukari kayar; Range yalniz satirin metnini olcer.
    Kutu draw()'in 6 px payi kadar iceriden baslar: komsu satirlar 20 px aralikli, cizgi onlarin ustune binmesin."""
    kod.evaluate("""(e, a) => {
      const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let n, r = null;
      while ((n = w.nextNode())) {
        const i = r ? 0 : n.nodeValue.indexOf(a[0]);
        if (i < 0) continue;
        if (!r) { r = document.createRange(); r.setStart(n, i); }
        const j = n.nodeValue.indexOf('\\n', i);
        if (j >= 0) { r.setEnd(n, j); break; }
        r.setEnd(n, n.nodeValue.length);
      }
      const b = r.getBoundingClientRect(), d = document.createElement('div');
      d.setAttribute('data-isaret', a[1]);
      Object.assign(d.style, {position: 'fixed', left: (b.left - 4) + 'px', top: (b.top + 6) + 'px', width: (b.width + 8) + 'px',
                              height: Math.max(b.height - 12, 2) + 'px', pointerEvents: 'none', zIndex: 99999});
      document.body.appendChild(d); }""", [bas, ad])
    return ("css", f'[data-isaret="{ad}"]')


def onayla(page):
    try:
        page.locator('[data-test-subj="confirmModalConfirmButton"]').first.click(timeout=5000); k.settle(page, 4)
    except Exception:
        pass


# ------------------------------------------------------------------ Adim 1: Fleet'i hazirlayin
def fleet(page):
    menu(page, "Fleet", "01a-menu-fleet")
    # 1) Output: ajanlar veriyi nereye yazacak
    page.locator('[data-test-subj="fleet-settings-tab"]').first.click(); k.settle(page, 5)
    shot(page, "01b-settings-output", [(("testsubj", "fleet-settings-tab"), 1, "down"), (("testsubj", "editOutputBtn"), 2, "left")],
         scroll_to=("testsubj", "editOutputBtn"))
    page.locator('[data-test-subj="editOutputBtn"]').first.click(); time.sleep(3)
    hosts = page.locator('.euiFlyout .euiFormRow:has(label:text-is("Hosts")) input').first
    hosts.fill("http://elasticsearch-lab00:9200"); time.sleep(1)
    shot(page, "01c-output-hosts", [(isaretle(hosts, "hosts"), 1, "left"), (("testsubj", "saveApplySettingsBtn"), 2, "up")])
    page.locator('[data-test-subj="saveApplySettingsBtn"]').first.click(); time.sleep(3)
    if page.locator('[data-test-subj="confirmModalConfirmButton"]').count():
        shot(page, "01d-output-onay", [(("testsubj", "confirmModalConfirmButton"), 1, "down")])
    onayla(page)
    print("output:", page.locator('[data-test-subj="settingsOutputsTable"]').first.inner_text().replace("\n", " ")[:120])

    # 2) Fleet Server: Quick Start politikayi ve service token'i uretir
    page.locator('[data-test-subj="fleet-agents-tab"]').first.click(); k.settle(page, 6)
    shot(page, "01e-add-fleet-server", [(("testsubj", "fleet-agents-tab"), 1, "down"),
                                        (("testsubj", "fleetServerLanding.addFleetServerButton"), 2, "down")])
    page.locator('[data-test-subj="fleetServerLanding.addFleetServerButton"]').first.click(); time.sleep(4)
    page.get_by_placeholder("Specify name").fill("Lab Fleet Server")
    page.get_by_placeholder("Specify host URL").fill("https://fleet-server:8220"); time.sleep(1)
    shot(page, "01f-quick-start", [(("text", "Quick Start", True), 1, "down"), (isaretle(page.get_by_placeholder("Specify name"), "fsad"), 2, "left"),
                                   (isaretle(page.get_by_placeholder("Specify host URL"), "fsurl"), 3, "left"),
                                   (("role", "button", "Generate Fleet Server policy"), 4, "right")])
    page.get_by_role("button", name="Generate Fleet Server policy").click()
    page.get_by_text("Fleet Server policy created.").first.wait_for(timeout=120000); time.sleep(3)
    kod = page.locator(".euiFlyout .euiCodeBlock").filter(has_text="--fleet-server-service-token=").first
    servis = re.search(r"--fleet-server-service-token=(\S+)", kod.inner_text()).group(1)
    politika_id = re.search(r"--fleet-server-policy=(\S+)", kod.inner_text()).group(1)
    print("Fleet Server politika id:", politika_id, "| service token alindi:", servis.startswith("AAEAA"))
    # Goruntude token gorunmesin: metin dugumlerinde maskele
    kod.evaluate("""(e, a) => { const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
        let n; while ((n = w.nextNode())) { if (n.nodeValue.includes(a[0])) n.nodeValue = n.nodeValue.replace(a[0], a[1]); } }""", [servis, MASKE])
    kod.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    isaret = [(satir_isaretle(kod, "--fleet-server-service-token=", "token"), 1, "left"),
              (satir_isaretle(kod, "--fleet-server-policy=", "polid"), 2, "right")]
    shot(page, "01g-service-token", isaret)
    if TOKEN_DOSYA:
        fd = os.open(TOKEN_DOSYA, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(f"FLEET_SERVER_SERVICE_TOKEN={servis}\n")
    page.locator('.euiFlyout [data-test-subj="euiFlyoutCloseButton"]').first.click(); time.sleep(2)
    fs_izleme(page)
    politika(page)


def fs_izleme(page):
    # Quick Start'in politikasinda ajan izleme acik gelir: ilk dakikalarda Fleet Server degraded gorunur
    page.goto(k.BASE + "/app/fleet/policies", wait_until="domcontentloaded"); k.settle(page, 5)
    link = '[data-test-subj="agentPolicyNameLink"]:text-is("Fleet Server Policy")'
    shot(page, "01g2-fs-policy", [(("testsubj", "fleet-agent-policies-tab"), 1, "down"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)
    shot(page, "01g3-fs-settings", [(("testsubj", "agentPolicySettingsTab"), 1, "down")])
    page.locator('[data-test-subj="agentPolicySettingsTab"]').first.click(); k.settle(page, 5)
    for cb in ("collectLogsCheckbox", "collectMetricsCheckbox"):
        c = page.locator(f'[data-test-subj="{cb}"]').first
        c.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(0.5)   # alt cubugun arkasinda kalmasin
        if c.is_checked():
            c.click(); time.sleep(0.5)
    print("izleme isaretleri:", [page.locator(f'[data-test-subj="{cb}"]').first.is_checked() for cb in ("collectLogsCheckbox", "collectMetricsCheckbox")])
    page.locator('[data-test-subj="collectLogsCheckbox"]').first.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    kaydet = page.get_by_role("button", name="Save changes").first
    shot(page, "01g4-fs-monitoring", [(("testsubj", "collectLogsCheckbox"), 1, "left"), (("testsubj", "collectMetricsCheckbox"), 2, "left"),
                                      (isaretle(kaydet, "fskaydet"), 3, "up")], scroll_to=("testsubj", "collectMetricsCheckbox"))
    kaydet.click(); time.sleep(3)
    onayla(page)
    print("Fleet Server Policy izleme kapatildi")


def politika(page):
    # 3) Linux politikasi
    page.goto(k.BASE + "/app/fleet/policies", wait_until="domcontentloaded"); k.settle(page, 5)
    shot(page, "01h-create-policy", [(("testsubj", "fleet-agent-policies-tab"), 1, "down"), (("testsubj", "createAgentPolicyButton"), 2, "left")])
    page.locator('[data-test-subj="createAgentPolicyButton"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="createAgentPolicyNameField"]').fill(POLITIKA); time.sleep(1)
    shot(page, "01i-policy-ad", [(("testsubj", "createAgentPolicyNameField"), 1, "left"),
                                 (("testsubj", "agentPolicyFormSystemMonitoringCheckbox"), 2, "left"),
                                 (("text", "Advanced options", True), 3, "left")])
    page.get_by_text("Advanced options", exact=True).first.click(); time.sleep(2)
    ns = page.locator('[data-test-subj="defaultNamespaceInput"]').first
    ns.scroll_into_view_if_needed()
    temizle = ns.locator('[data-test-subj="comboBoxClearButton"]')
    if temizle.count():
        temizle.first.click(); time.sleep(0.5)
    ns.locator("input").first.click(); page.keyboard.type("fleetlab"); page.keyboard.press("Enter"); time.sleep(1)
    shot(page, "01j-namespace", [(("testsubj", "defaultNamespaceInput"), 1, "left")], scroll_to=("testsubj", "defaultNamespaceInput"))
    for cb in ("collectLogsCheckbox", "collectMetricsCheckbox"):
        c = page.locator(f'[data-test-subj="{cb}"]').first
        c.scroll_into_view_if_needed()
        if c.is_checked():
            c.click(force=True); time.sleep(0.5)
    shot(page, "01k-monitoring", [(("testsubj", "collectLogsCheckbox"), 1, "left"), (("testsubj", "collectMetricsCheckbox"), 2, "left"),
                                  (("testsubj", "createAgentPolicyFlyoutBtn"), 3, "up")], scroll_to=("testsubj", "collectLogsCheckbox"))
    page.locator('[data-test-subj="createAgentPolicyFlyoutBtn"]').first.click(); k.settle(page, 8)
    print("politika olusturuldu:", page.url.replace(k.BASE, "")[:90])

    sistem_ayar(page)


def sistem_ayar(page):
    # 4) System integration'i: ad ve hostfs
    page.goto(k.BASE + "/app/fleet/policies", wait_until="domcontentloaded"); k.settle(page, 5)
    link = f'[data-test-subj="agentPolicyNameLink"]:text-is("{POLITIKA}")'
    shot(page, "01l-policy-ac", [(("css", link), 1, "right")])
    page.locator(link).first.click(); k.settle(page, 6)
    sistem = page.locator('[data-test-subj="PackagePoliciesTableName"]').filter(has_text=re.compile(r"^system-")).first
    print("system integration:", sistem.inner_text())
    shot(page, "01l2-policy-system", [(isaretle(sistem, "sys"), 1, "right")])
    sistem.click(); k.settle(page, 8)
    ad = page.locator('[data-test-subj="packagePolicyNameInput"]').first
    ad.fill("system-lab"); time.sleep(0.5)
    shot(page, "01m-integration-ad", [(("testsubj", "packagePolicyNameInput"), 1, "left")], scroll_to=("testsubj", "packagePolicyNameInput"))
    metrics = page.locator("div").filter(has=page.get_by_text("Collect metrics from System instances", exact=True)) \
                  .filter(has=page.get_by_text("Change defaults")).last
    cd = metrics.get_by_text("Change defaults").first
    shot(page, "01n-change-defaults", [(isaretle(cd, "cd"), 1, "left")], scroll_to=("text", "Collect metrics from System instances", True))
    cd.click(); time.sleep(2)
    proc = page.locator('xpath=(//*[normalize-space(text())="Proc Filesystem Directory"]/following::input)[1]').first
    proc.fill("/hostfs"); time.sleep(0.5)
    proc.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "01o-hostfs", [(isaretle(proc, "proc"), 1, "left"), (("role", "button", "Save integration"), 2, "up")], scroll_to=isaretle(proc, "proc"))
    page.get_by_role("button", name="Save integration").click(); time.sleep(3)
    if page.locator('[data-test-subj="confirmModalConfirmButton"]').count():
        shot(page, "01p-save-deploy", [(("testsubj", "confirmModalConfirmButton"), 1, "down")])
    onayla(page)
    print("integration kaydedildi:", page.url.replace(k.BASE, "")[:90])

    token(page)


def token(page):
    # 5) Enrollment token
    page.goto(k.BASE + "/app/fleet/agents", wait_until="domcontentloaded"); k.settle(page, 5)
    page.locator('[data-test-subj="fleet-enrollment-tokens-tab"]').first.click(); k.settle(page, 5)
    sat = page.locator('[data-test-subj="enrollmentTokenListTable"] tbody tr').filter(has_text=POLITIKA).first
    shot(page, "01q-enrollment-token", [(("testsubj", "fleet-enrollment-tokens-tab"), 1, "down"),
                                        (isaretle(sat.locator('[data-test-subj="showHideTokenButton"]').first, "goz"), 2, "down"),
                                        (isaretle(sat.locator('[data-test-subj="copyTokenButton"]').first, "kopya"), 3, "right")])
    sat.locator('[data-test-subj="showHideTokenButton"]').first.click(); time.sleep(1)
    kayit = sat.locator('[data-test-subj="apiKeyField"]').first.inner_text().strip()
    print("enrollment token alindi:", len(kayit) > 40)
    sat.locator('[data-test-subj="showHideTokenButton"]').first.click(); time.sleep(0.5)
    if TOKEN_DOSYA:
        with open(TOKEN_DOSYA, "a") as f:
            f.write(f"FLEET_ENROLLMENT_TOKEN={kayit}\n")
        print("token dosyasi yazildi")


def politika_ac(page, goruntu=None):
    menu(page, "Fleet")
    page.locator('[data-test-subj="fleet-agent-policies-tab"]').first.click(); k.settle(page, 5)
    link = f'[data-test-subj="agentPolicyNameLink"]:text-is("{POLITIKA}")'
    if goruntu:
        shot(page, goruntu, [(("testsubj", "fleet-agent-policies-tab"), 1, "down"), (("css", link), 2, "right")])
    page.locator(link).first.click(); k.settle(page, 6)


# ------------------------------------------------------------------ Adim 3: ajan listesi
def ajanlar(page):
    menu(page, "Fleet")
    page.locator('[data-test-subj="fleet-agents-tab"]').first.click(); k.settle(page, 8)
    print("ajanlar:", page.locator("tbody").first.inner_text().replace("\n", " ")[:200])
    shot(page, "03a-fleet-agents", [(("css", 'tbody a:text-is("linux-agent-01")'), 1, "ic"), (("css", 'tbody a:text-is("fleet-server")'), 2, "ic")])


# ------------------------------------------------------------------ Adim 5: Period 10s -> 30s
PERIOD = 'xpath=(//*[normalize-space(text())="System process metrics"]/following::input)[1]'


def period(page):
    politika_ac(page, "05a-politika-ac")
    sistem = page.locator('[data-test-subj="PackagePoliciesTableName"]').filter(has_text="system-lab").first
    shot(page, "05b-system-lab", [(isaretle(sistem, "sys5"), 1, "right")])
    sistem.click(); k.settle(page, 8)
    metrics = page.locator("div").filter(has=page.get_by_text("Collect metrics from System instances", exact=True)) \
                  .filter(has=page.get_by_text("Change defaults")).last
    cd = metrics.get_by_text("Change defaults").first
    cd.click(); time.sleep(2)
    inp = page.locator(PERIOD).first
    print("period once:", inp.input_value())
    inp.fill("30s"); time.sleep(1)
    inp.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)
    shot(page, "05c-period", [(isaretle(inp, "period"), 1, "left"), (("role", "button", "Save integration"), 2, "up")],
         scroll_to=("css", '[data-isaret="period"]'))
    page.get_by_role("button", name="Save integration").click(); time.sleep(3)
    shot(page, "05d-save-deploy", [(("testsubj", "confirmModalConfirmButton"), 1, "down")])
    onayla(page)
    print("kaydedildi")


# ------------------------------------------------------------------ Adim 6: Nginx integration'i
def nginx(page):
    menu(page, "Integrations", "06a-menu-integrations")
    sb = page.locator('[data-test-subj="epmList.searchBar"]').first
    (sb.locator("input").first if sb.locator("input").count() else sb).fill("nginx"); time.sleep(4)
    shot(page, "06b-nginx-ara", [(("testsubj", "epmList.searchBar"), 1, "down"), (("testsubj", "integration-card:epr:nginx"), 2, "left")])
    page.locator('[data-test-subj="integration-card:epr:nginx"]').first.click(); k.settle(page, 6)
    shot(page, "06c-add-nginx", [(("testsubj", "addIntegrationPolicyButton"), 1, "left")])
    page.locator('[data-test-subj="addIntegrationPolicyButton"]').first.click(); k.settle(page, 8)
    page.locator('[data-test-subj="packagePolicyNameInput"]').fill("nginx-lab")
    metrik = page.locator('[data-test-subj="PackagePolicy.InputStreamConfig.Switch"]').nth(1)
    metrik.click(); time.sleep(1)
    print("anahtarlar:", [x.get_attribute("aria-checked") for x in page.locator('[data-test-subj="PackagePolicy.InputStreamConfig.Switch"]').all()])
    shot(page, "06d-nginx-ayar", [(("testsubj", "packagePolicyNameInput"), 1, "left"),
                                  (("css", 'xpath=(//*[@data-test-subj="PackagePolicy.InputStreamConfig.Switch"])[2]'), 2, "left")],
         scroll_to=("testsubj", "packagePolicyNameInput"))
    page.locator('[data-test-subj="existingHostsTab"]').click(); time.sleep(3)
    # Kibana uygun politika sayisina gore coklu (agentPolicyMultiSelect) ya da tekli (agentPolicySelect) kutu cizer
    coklu = page.locator('[data-test-subj="agentPolicyMultiSelect"]').count() > 0
    secici = "agentPolicyMultiSelect" if coklu else "agentPolicySelect"
    if coklu:
        page.locator('[data-test-subj="agentPolicyMultiSelect"] [data-test-subj="comboBoxSearchInput"]').first.click(); time.sleep(2)
    else:
        page.locator('[data-test-subj="agentPolicySelect"]').first.click(); time.sleep(2)
    page.get_by_role("option", name=POLITIKA).first.click(); time.sleep(2)
    if coklu:
        page.keyboard.press("Escape"); time.sleep(1)
    print("politika kutusu:", secici)
    shot(page, "06e-nginx-politika", [(("testsubj", "existingHostsTab"), 1, "up"), (("testsubj", secici), 2, "left"),
                                      (("testsubj", "createPackagePolicySaveButton"), 3, "up")], scroll_to=("testsubj", secici))
    page.locator('[data-test-subj="createPackagePolicySaveButton"]').click(); time.sleep(4)
    shot(page, "06f-nginx-onay", [(("testsubj", "confirmModalConfirmButton"), 1, "down")])
    onayla(page)
    print("nginx-lab eklendi:", page.url.replace(k.BASE, "")[:80])


def hazir(page):
    menu(page, "Integrations")
    page.get_by_role("tab", name="Installed integrations").first.click(); k.settle(page, 5)
    kart = '[data-test-subj="installedIntegrationsTable.integrationNameColumn.nginx"]'
    shot(page, "06g-installed", [(("role", "tab", "Installed integrations"), 1, "down"), (("css", kart), 2, "left")])
    page.locator(kart).first.click(); k.settle(page, 6)
    page.locator('[data-test-subj="tab-assets"]').first.click(); k.settle(page, 6)
    pano = '[data-test-subj="fleetAssetsAccordion.content.dashboard.[Logs Nginx] Overview"]'
    shot(page, "06h-nginx-assets", [(("testsubj", "tab-assets"), 1, "down"), (("css", pano), 2, "left")])
    page.locator(pano + " a").first.click()
    page.wait_for_url("**/app/dashboards#/view/**", timeout=60000, wait_until="commit"); k.settle(page, 8)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    shot(page, "06i-son-7-gun", [(("testsubj", "dateRangePickerInput"), 1, "down"), (("testsubj", "dateRangePickerPresetItem-Last_7_days"), 2, "left")],
         scroll_to=("testsubj", "dateRangePickerPresetItem-Last_7_days"))
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_7_days"]').first.click(); k.settle(page, 10)
    page.mouse.move(800, 60); time.sleep(1)
    print("panel:", page.locator('[data-test-subj="dashboardPanel"]').count(), "hata:", page.locator('[data-test-subj="embeddableError"]').count())
    shot(page, "06j-nginx-hazir-pano", [])


# ------------------------------------------------------------------ Adim 7: Lens CPU panosu
def pano(page):
    menu(page, "Dashboards", "07a-menu-dashboards")
    shot(page, "07b-create-dashboard", [(("testsubj", "dashboardListingCreateButton"), 1, "left")])
    page.locator('[data-test-subj="dashboardListingCreateButton"]').first.click(); k.settle(page, 6)
    shot(page, "07c-create-visualization", [(("testsubj", "create-action-Visualization"), 1, "down")])
    page.locator('[data-test-subj="create-action-Visualization"]').first.click(); k.settle(page, 8)
    for txt in ("Don't show again", "Got it", "Dismiss"):
        try: page.get_by_text(txt).first.click(timeout=1200)
        except Exception: pass
    page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
    page.keyboard.type("metrics-*"); time.sleep(2)
    shot(page, "07d-data-view", [(("testsubj", "lns-dataView-switch-link"), 1, "down"), (("role", "option", "metrics-*"), 2, "right")])
    page.get_by_role("option", name="metrics-*").first.click(); k.settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_15_minutes"]').first.click(); k.settle(page, 3)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.fill('data_stream.dataset : "system.cpu" and data_stream.namespace : "fleetlab"'); q.press("Enter"); k.settle(page, 4)
    f = "system.cpu.total.norm.pct"
    page.locator('[data-test-subj="lnsIndexPatternFieldSearch"]').fill("total.norm"); time.sleep(2)
    page.locator(f'[data-test-subj="lnsFieldListPanelField-{f}"]').first.hover(); time.sleep(0.5)
    shot(page, "07e-sorgu-alan", [(("testsubj", "queryInput"), 1, "down"), (("testsubj", "lnsIndexPatternFieldSearch"), 2, "right"),
                                  (("testsubj", f"fieldToggle-{f}"), 3, "right")])
    page.locator(f'[data-test-subj="fieldToggle-{f}"]').first.click(); k.settle(page, 5)
    med = page.get_by_text("Median of system.cpu.total.norm.pct").last
    shot(page, "07f-median", [(isaretle(med, "med"), 1, "left")])
    med.click(); time.sleep(2)
    page.locator('[data-test-subj="lns-indexPatternDimension-average"]').first.click(); k.settle(page, 3)
    page.locator('[data-test-subj="name-input"]').first.fill("Sunucu CPU (%)"); time.sleep(2)
    shot(page, "07g-average", [(("testsubj", "lns-indexPatternDimension-average"), 1, "left"), (("testsubj", "name-input"), 2, "up"),
                               (("testsubj", "lns-indexPattern-dimensionContainerClose"), 3, "left")], scroll_to=("testsubj", "name-input"))
    page.locator('[data-test-subj="lns-indexPattern-dimensionContainerClose"]').first.click(); time.sleep(2)
    shot(page, "07h-save-return", [(("testsubj", "lnsApp_saveAndReturnButton"), 1, "down")])
    page.locator('[data-test-subj="lnsApp_saveAndReturnButton"]').first.click(); k.settle(page, 8)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Sunucu CPU (Fleet)")
    st = page.locator('[data-test-subj="storeTimeWithDashboard"]').first
    if st.get_attribute("aria-checked") != "true":
        st.click(); time.sleep(1)
    shot(page, "07i-pano-kaydet", [(("testsubj", "savedObjectTitle"), 1, "left"), (("testsubj", "storeTimeWithDashboard"), 2, "left"),
                                   (("testsubj", "confirmSaveSavedObjectButton"), 3, "up")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 8)
    try:
        page.locator('[data-test-subj="dashboardViewOnlyMode"]').first.click(timeout=5000); k.settle(page, 4)
    except Exception:
        pass
    page.mouse.move(1500, 800); time.sleep(1)
    shot(page, "07j-pano-cpu", [])
    print("pano kaydedildi")


if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        for parca in sys.argv[1:]:
            {"fleet": fleet, "fsizleme": fs_izleme, "politika": politika, "sistem": sistem_ayar, "token": token, "ajanlar": ajanlar, "period": period,
             "nginx": nginx, "hazir": hazir, "pano": pano}[parca](page)
        br.close()
    print("HATALI GORUNTU:", HATA if HATA else "yok")
    sys.exit(1 if HATA else 0)
