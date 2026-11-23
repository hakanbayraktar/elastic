"""LAB-11 isaretli Kibana ekran goruntuleri: Fleet ajan listesi ve politikayi canli degistirme.

Kullanim (yerelde, sunucuya SSH tuneli acikken; LAB-11 Adim 1-2 calismis olmali):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab15.py
Parcalar (README sirasiyla, aradaki README komutlari runner ile):
    python3 shots_lab15.py 1      Adim 2 ajan listesi + Adim 5 (Period 10s -> 30s, Save and deploy) GERCEKTEN yapilir
    python3 shots_lab15.py nginx  Adim 6: Add integrations > Nginx (ECS) > nginx-lab > Lab Linux sunucu GERCEKTEN eklenir
    python3 shots_lab15.py pano   Adim 7: Lens CPU grafigi ve "Sunucu CPU (Fleet)" panosu GERCEKTEN kaydedilir
Cikti: assets/screenshots/LAB-11/<ad>.png
"""
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-11"
PERIOD = 'xpath=(//*[normalize-space(text())="System process metrics"]/following::input)[1]'


def lab11(page):
    # Adim 2: ajan listesi
    page.goto(k.BASE + "/app/fleet/agents", wait_until="domcontentloaded"); k.settle(page, 6)
    k.shoot(page, LAB, "01-fleet-agents", [(("css", 'tr:has-text("linux-agent-01")'), 1, "down")])

    # Adim 5: politika -> system-lab -> Change defaults -> Period -> Save -> Save and deploy
    page.goto(k.BASE + "/app/fleet/policies/fleet-linux-policy", wait_until="domcontentloaded"); k.settle(page, 6)
    k.shoot(page, LAB, "02-policy-system", [(("text", "system-lab", True), 1, "left")])
    page.get_by_text("system-lab", exact=True).first.click(); k.settle(page, 6)
    metrics = page.locator("div").filter(has=page.get_by_text("Collect metrics from System instances", exact=True)) \
                  .filter(has=page.get_by_text("Change defaults")).last
    metrics.get_by_text("Change defaults").click(); time.sleep(2)
    k.shoot(page, LAB, "03-change-defaults-hostfs", [
        (("css", 'xpath=(//*[normalize-space(text())="Collect metrics from System instances"]/following::*[normalize-space(text())="Change defaults"])[1]'), 2, "left"),
        (("css", 'xpath=(//*[normalize-space(text())="Proc Filesystem Directory"]/following::input)[1]'), None, "left"),
    ], scroll_to=("text", "Collect metrics from System instances", True))
    inp = page.locator(PERIOD)
    print("period once:", inp.input_value())
    inp.fill("30s"); time.sleep(1)
    inp.evaluate("e => e.scrollIntoView({block: 'center'})"); time.sleep(1)   # alt cubugun arkasinda kalmasin
    k.shoot(page, LAB, "04-process-period-save", [
        (("css", PERIOD), 3, "left"),
        (("role", "button", "Save integration"), 4, "up"),
    ], scroll_to=("css", PERIOD))
    page.get_by_role("button", name="Save integration").click(); time.sleep(3)
    k.shoot(page, LAB, "05-save-and-deploy", [(("role", "button", "Save and deploy changes"), 5, "down")])
    page.get_by_role("button", name="Save and deploy changes").click(); k.settle(page, 5)
    print("kaydedildi")


def lab11_nginx(page):
    page.goto(k.BASE + "/app/integrations/browse", wait_until="domcontentloaded"); k.settle(page, 6)
    sb = page.locator('[data-test-subj="epmList.searchBar"]').first
    (sb.locator("input").first if sb.locator("input").count() else sb).fill("nginx"); time.sleep(4)
    k.shoot(page, LAB, "06-integrations-nginx", [
        (("testsubj", "epmList.searchBar"), 1, "down"),
        (("testsubj", "integration-card:epr:nginx"), 2, "left"),
    ])
    page.locator('[data-test-subj="integration-card:epr:nginx"]').first.click(); k.settle(page, 6)
    page.locator('[data-test-subj="addIntegrationPolicyButton"]').first.click(); k.settle(page, 8)
    page.locator('[data-test-subj="packagePolicyNameInput"]').fill("nginx-lab")
    metrik = page.locator('[data-test-subj="PackagePolicy.InputStreamConfig.Switch"]').nth(1)
    metrik.click(); time.sleep(1)
    print("anahtarlar:", [s.get_attribute("aria-checked") for s in page.locator('[data-test-subj="PackagePolicy.InputStreamConfig.Switch"]').all()])
    k.shoot(page, LAB, "07-nginx-ayar", [
        (("testsubj", "packagePolicyNameInput"), 4, "left"),
        (("css", 'xpath=(//*[@data-test-subj="PackagePolicy.InputStreamConfig.Switch"])[2]'), 5, "left"),
    ], scroll_to=("testsubj", "packagePolicyNameInput"))
    page.locator('[data-test-subj="existingHostsTab"]').click(); time.sleep(3)
    page.locator('[data-test-subj="agentPolicyMultiSelect"] [data-test-subj="comboBoxSearchInput"]').first.click(); time.sleep(2)
    page.get_by_role("option", name="Lab Linux sunucu").first.click(); time.sleep(2)
    page.keyboard.press("Escape"); time.sleep(1)
    k.shoot(page, LAB, "08-nginx-politika", [
        (("testsubj", "existingHostsTab"), 6, "up"),
        (("testsubj", "agentPolicyMultiSelect"), 7, "left"),
        (("testsubj", "createPackagePolicySaveButton"), 8, "up"),
    ], scroll_to=("testsubj", "agentPolicyMultiSelect"))
    page.locator('[data-test-subj="createPackagePolicySaveButton"]').click(); time.sleep(4)
    page.locator('[data-test-subj="confirmModalConfirmButton"]').click(); k.settle(page, 6)
    print("nginx-lab eklendi")


def lab11_pano(page):
    page.goto(k.BASE + "/app/dashboards#/create?_g=(time:(from:now-15m,to:now))", wait_until="domcontentloaded"); k.settle(page, 6)
    page.locator('[data-test-subj="create-action-Visualization"]').first.click(); k.settle(page, 8)
    for txt in ("Don't show again", "Got it", "Dismiss"):
        try: page.get_by_text(txt).first.click(timeout=1200)
        except Exception: pass
    page.locator('[data-test-subj="lns-dataView-switch-link"]').first.click(); time.sleep(2)
    page.keyboard.type("metrics-*"); time.sleep(2)
    page.get_by_role("option", name="metrics-*").first.click(); k.settle(page, 5)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.fill('data_stream.dataset : "system.cpu" and data_stream.namespace : "fleetlab"'); q.press("Enter"); k.settle(page, 4)
    f = "system.cpu.total.norm.pct"
    page.locator('[data-test-subj="lnsIndexPatternFieldSearch"]').fill("total.norm"); time.sleep(2)
    page.locator(f'[data-test-subj="lnsFieldListPanelField-{f}"]').first.hover(); time.sleep(0.5)
    page.locator(f'[data-test-subj="fieldToggle-{f}"]').first.click(); k.settle(page, 5)
    k.shoot(page, LAB, "09-lens-cpu", [
        (("testsubj", "lns-dataView-switch-link"), 1, "down"),
        (("testsubj", "queryInput"), 2, "down"),
    ])
    page.get_by_text("Median of system.cpu.total.norm.pct").last.click(); time.sleep(2)
    page.locator('[data-test-subj="lns-indexPatternDimension-average"]').first.click(); k.settle(page, 3)
    page.locator('[data-test-subj="name-input"]').first.fill("Sunucu CPU (%)"); time.sleep(2)
    k.shoot(page, LAB, "10-lens-average", [
        (("testsubj", "lns-indexPatternDimension-average"), 3, "left"),
        (("testsubj", "name-input"), 4, "left"),
    ], scroll_to=("testsubj", "name-input"))
    page.locator('[data-test-subj="lns-indexPattern-dimensionContainerClose"]').first.click(); time.sleep(2)
    page.locator('[data-test-subj="lnsApp_saveAndReturnButton"]').first.click(); k.settle(page, 8)
    page.locator('[data-test-subj="dashboardInteractiveSaveMenuItem"]').first.click(); time.sleep(3)
    page.locator('[data-test-subj="savedObjectTitle"]').fill("Sunucu CPU (Fleet)")
    st = page.locator('[data-test-subj="storeTimeWithDashboard"]').first
    if st.get_attribute("aria-checked") != "true":
        st.click(); time.sleep(1)
    k.shoot(page, LAB, "11-pano-kaydet", [(("testsubj", "storeTimeWithDashboard"), 5, "left")])
    page.locator('[data-test-subj="confirmSaveSavedObjectButton"]').first.click(); k.settle(page, 8)
    page.mouse.move(1500, 800); time.sleep(1)
    k.shoot(page, LAB, "12-pano-cpu", [])
    print("pano kaydedildi")


if __name__ == "__main__":
    import sys
    parca = sys.argv[1] if len(sys.argv) > 1 else "1"
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        {"1": lab11, "nginx": lab11_nginx, "pano": lab11_pano}[parca](page)
        br.close()
