"""LAB-12 isaretli Kibana ekran goruntuleri (data view + Discover).

Kullanim (yerelde, sunucuya SSH tuneli acikken; LAB-12 Adim 1-4 calismis olmali):
    ssh -f -N -L 25601:127.0.0.1:5601 student@<sunucu>
    KB_BASE=http://127.0.0.1:25601 python3 scripts/screenshots/shots_lab08.py
Cikti: assets/screenshots/LAB-12/<ad>.png
"""
import sys
import time

import kibana_shots as k
from playwright.sync_api import sync_playwright

LAB = "LAB-12"


def lab12(page):
    # Adim 6a: zaman alanli data view
    page.goto(k.BASE + "/app/management/kibana/dataViews", wait_until="domcontentloaded"); k.settle(page, 4)
    btn = page.locator('[data-test-subj="createDataViewButton"]:visible')
    if not btn.count():
        btn = page.locator('[data-test-subj="noDataViewsPromptCreateDataView"]:visible')
    btn.first.click(); time.sleep(3)
    page.locator('[data-test-subj="createIndexPatternNameInput"]').fill("excel-satislar")
    page.locator('[data-test-subj="createIndexPatternTitleInput"]').fill("excel-satislar"); time.sleep(3)
    page.locator('[data-test-subj="timestampField"] [data-test-subj="comboBoxSearchInput"]').click(); time.sleep(1)
    page.get_by_role("option", name="@timestamp", exact=True).first.click(); time.sleep(1)
    k.shoot(page, LAB, "01-dataview-excel", [
        (("testsubj", "createIndexPatternNameInput"), 1, "left"),
        (("testsubj", "createIndexPatternTitleInput"), 2, "left"),
        (("testsubj", "timestampField"), 3, "left"),
        (("testsubj", "saveIndexPatternButton"), 4, "up"),
    ])
    page.locator('[data-test-subj="saveIndexPatternButton"]').first.click(); time.sleep(4)

    # Adim 6b: Discover, Last 1 year, KQL il : "Istanbul"
    page.goto(k.BASE + "/app/discover", wait_until="domcontentloaded"); k.settle(page, 6)
    k.pick_dataview(page, 'excel-satislar'); k.settle(page, 5)
    page.locator('[data-test-subj="dateRangePickerControlButton"]').first.click(); time.sleep(1.5)
    page.locator('[data-test-subj="dateRangePickerPresetItem-Last_1_year"]').first.click(); k.settle(page, 6)
    q = page.locator('[data-test-subj="queryInput"]').first
    q.click(); q.fill('il : "İstanbul"'); page.keyboard.press("Enter"); k.settle(page, 6)
    k.shoot(page, LAB, "02-discover-excel", [
        (("testsubj", "dateRangePickerControlButton"), 1, "down"),
        (("testsubj", "queryInput"), 2, "down"),
        (("testsubj", "discoverQueryHits"), 3, "down"),
    ])
    print("hits:", page.locator('[data-test-subj="discoverQueryHits"]').first.inner_text())


if __name__ == "__main__":
    with sync_playwright() as pw:
        pw.selectors.set_test_id_attribute("data-test-subj")
        br = pw.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=k.SCALE)
        k.login(page)
        lab12(page)
        br.close()
    sys.exit(0)
