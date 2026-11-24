#!/usr/bin/env python3
"""README bash bloklarinda etkilesimli bash'in gecmis genisletmesine (!) takilacak yerleri bulur.
Etkilesimli kabukta (set -o histexpand) cift tirnak ya da tirnaksiz baglamdaki `!x` "event not found" verir;
tek tirnak icinde guvenlidir. README runner etkilesimsiz kostugu icin bunu yakalamaz.
    python3 scripts/histexpand_denetimi.py labs/*/README.md labs/advanced/*/README.md
"""
import re
import sys

BLOK = re.compile(r"```bash\n(.*?)```", re.S)


def riskli(satir):
    """Kacissiz $( ... ) yeni bir tirnak baglami acar (bash'in gecmis genisletmesi de boyle izler)."""
    tek = cift = False
    yigin = []
    i = 0
    while i < len(satir):
        c = satir[i]
        if c == "\\" and not tek:
            i += 2; continue
        if c == "$" and not tek and satir[i + 1:i + 2] == "(":
            yigin.append((tek, cift)); tek = cift = False; i += 2; continue
        if c == ")" and not tek and not cift and yigin:
            tek, cift = yigin.pop(); i += 1; continue
        if c == "'" and not cift:
            tek = not tek
        elif c == '"' and not tek:
            cift = not cift
        elif c == "!" and not tek:
            sonraki = satir[i + 1] if i + 1 < len(satir) else " "
            if sonraki not in ' \t\n="(' and not (cift and sonraki == '"'):
                return i
        i += 1
    return -1


toplam = 0
for yol in sys.argv[1:]:
    metin = open(yol, encoding="utf-8").read()
    for m in BLOK.finditer(metin):
        bas = metin[:m.start()].count("\n") + 2
        bitis = None
        for j, satir in enumerate(m.group(1).split("\n")):
            if bitis is not None:            # heredoc govdesi gecmis genisletmesine girmez (bash -i ile denendi)
                if satir.strip() == bitis:
                    bitis = None
                continue
            h = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", satir)
            if h:
                bitis = h.group(1)
            k = riskli(satir)
            if k >= 0:
                toplam += 1
                print(f"{yol}:{bas + j}: ...{satir[max(0, k - 50):k + 20]}...")
print(f"[SONUC] riskli satir: {toplam}")
