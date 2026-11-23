"""README sadeleştirmesinde komutların bozulmadığını denetler.

Eski sürüm (git HEAD) ile çalışma kopyasındaki README'nin kod bloklarını sırasıyla karşılaştırır.
Çalıştırılan ya da alıntılanan bloklar (bash, http, json, yaml ...) birebir aynı ve aynı sırada olmalıdır;
`text` çıktı blokları ve diyagramlar yalnızca raporlanır. Bir blok kaldırıldıysa ya da eklendiyse raporlanır.
Kullanım (repo kökünden): python3 scripts/readme_komut_denetimi.py labs/LAB-02-*/README.md [...]
Çıkış kodu: 0 = hepsi aynı, 1 = fark var.
"""
import re, subprocess, sys

# Yalnızca okunan bloklar (çıktı, klasör ağacı, diyagram): kaldırılması raporlanır ama hata sayılmaz
BILGI = {'text', 'yok', 'mermaid', 'plaintext'}
BLOCK = re.compile(r'^([ \t]*)```([\w+-]*)[^\n]*\n(.*?)^\1```', re.S | re.M)


def blocks(text):
    out = []
    for m in BLOCK.finditer(text):
        lang = m.group(2).lower() or 'yok'
        body = '\n'.join(l[len(m.group(1)):] if l.startswith(m.group(1)) else l for l in m.group(3).rstrip().split('\n'))
        out.append((lang, body.strip()))
    return out


def main(paths):
    bad = 0
    for p in paths:
        try:
            old = subprocess.run(['git', 'show', 'HEAD:' + p], capture_output=True, text=True, check=True).stdout
        except subprocess.CalledProcessError:
            print('YENİ DOSYA (denetim yok):', p); continue
        new = open(p, encoding='utf-8').read()
        a = [x for x in blocks(old) if x[0] not in BILGI]
        b = [x for x in blocks(new) if x[0] not in BILGI]
        ta = [x[1] for x in blocks(old) if x[0] in BILGI]
        tb = [x[1] for x in blocks(new) if x[0] in BILGI]
        for x in ta:
            if x not in tb:
                print('  bilgi: çıktı/şema bloğu kaldırıldı (%s): %s' % (p, x[:90].replace('\n', ' ⏎ ')))
        if [x[1] for x in a] == [x[1] for x in b]:
            print('AYNI  %-70s %d blok' % (p, len(a)))
            continue
        bad += 1
        print('FARK  %s  eski %d blok, yeni %d blok' % (p, len(a), len(b)))
        i = 0
        while i < max(len(a), len(b)):
            x = a[i][1] if i < len(a) else None
            y = b[i][1] if i < len(b) else None
            if x != y:
                print('  ilk fark %d. blokta' % (i + 1))
                print('  ESKİ:', (x or '-')[:200].replace('\n', ' ⏎ '))
                print('  YENİ:', (y or '-')[:200].replace('\n', ' ⏎ '))
                break
            i += 1
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
