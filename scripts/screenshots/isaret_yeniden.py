"""Isaretli bir goruntuyu, ayni anda alinmis isaretsiz kopyasindan (sunum/_build/ekran) yeniden cizer.
Akisi tekrar calistirmak sunucuda nesne kaydi/silme gerektirdiginde kullanilir. Kutular CSS px (1600 genislik).
    python3 scripts/screenshots/isaret_yeniden.py
"""
import os
import shutil

import kibana_shots as k

ROOT = k.ROOT
SUNUM = "/Users/hakan/elk/elk-workspace/sunum/_build/ekran"

IS = {
    # (lab, ad): [((x, y, w, h), no, ok)]
    ("LAB-16", "05f-dort-panel"): [((11, 154, 783, 30), 1, "ic"), ((808, 154, 783, 30), 2, "ic"),
                                   ((11, 574, 783, 30), 3, "ic"), ((808, 574, 783, 30), 4, "ic")],
    ("LAB-11", "03a-fleet-agents"): [((186, 412, 104, 20), 1, "right"), ((186, 474, 82, 20), 2, "right")],
    ("LAB-11", "07g-average"): [((1218, 344, 176, 28), 1, "left"), ((1340, 792, 242, 30), 2, "up"), ((1218, 852, 60, 32), 3, "left")],
    ("LAB-14", "06b-pano-ara"): [((202, 210, 748, 38), 1, "left"), ((241, 314, 264, 16), 2, "left")],
    ("LAB-13", "07g-pano"): [((8, 154, 788, 410), 1, "ic")],
    ("LAB-17", "07c-eksik-panel"): [((8, 308, 788, 380), 1, None)],
    ("LAB-18", "02g-harita"): [((1268, 190, 318, 332), 1, "left"), ((610, 370, 360, 90), 2, "down")],
}


def ciz(lab, ad, isaretler):
    kaynak = os.path.join(SUNUM, lab, ad + ".png")
    hedef = os.path.join(ROOT, "assets", "screenshots", lab, ad + ".png")
    shutil.copyfile(kaynak, hedef)
    eski = k.SCALE
    k.SCALE = 1   # isaretsiz kopya zaten 1600 px'e indirilmis
    try:
        k.draw(hedef, [({"x": x, "y": y, "width": w, "height": h}, no, ok) for (x, y, w, h), no, ok in isaretler])
    finally:
        k.SCALE = eski
    print("ok", hedef)


if __name__ == "__main__":
    for (lab, ad), isaretler in IS.items():
        ciz(lab, ad, isaretler)
