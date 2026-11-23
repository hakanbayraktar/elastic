#!/usr/bin/env python3
"""Excel (.xlsx) dosyasinin ilk sayfasini, Turkce Excel'in "CSV (noktali virgulle ayrilmis)"
ciktisindaki bicimde yazar: ayirici ';', ondalik virgul, binlik nokta, tarih gg.aa.yyyy.

Yalniz standart kutuphane kullanir (sunucuya paket kurmak gerekmez).
Kullanim: python3 scripts/xlsx_to_csv.py sample-data/satislar.xlsx > data/satislar.csv
Cikti UTF-8 ve LF satir sonudur.
"""
import datetime
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
TARIH_ID = set(range(14, 23))          # Excel'in yerlesik tarih bicimleri


def tr_sayi(v, ondalik):
    s = f'{v:,.{ondalik}f}'                                   # 1,234.50
    return s.replace(',', '_').replace('.', ',').replace('_', '.')   # 1.234,50


def bicim_tablosu(z):
    try:
        st = ET.fromstring(z.read('xl/styles.xml'))
    except KeyError:
        return [], {}
    ozel = {int(n.get('numFmtId')): n.get('formatCode') for n in st.iterfind('m:numFmts/m:numFmt', NS)}
    xf = [int(x.get('numFmtId', 0)) for x in st.iterfind('m:cellXfs/m:xf', NS)]
    return xf, ozel


def hucre(c, paylasilan, xf, ozel):
    t = c.get('t')
    if t == 'inlineStr':
        return ''.join(x.text or '' for x in c.iterfind('.//m:t', NS))
    v = c.find('m:v', NS)
    if v is None:
        return ''
    if t == 's':
        return paylasilan[int(v.text)]
    if t in ('str', 'b', 'e'):
        return v.text
    sayi = float(v.text)
    fid = xf[int(c.get('s', 0))] if xf else 0
    kod = ozel.get(fid, '')
    if fid in TARIH_ID or re.search(r'[dy]', kod.replace('"', '')):
        return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(sayi))).strftime('%d.%m.%Y')
    if fid == 4 or '#,##0.00' in kod:
        return tr_sayi(sayi, 2)
    if fid == 2 or kod == '0.00':
        return f'{sayi:.2f}'.replace('.', ',')
    return str(int(sayi)) if sayi.is_integer() else str(sayi).replace('.', ',')


def kolon_no(ref):
    n = 0
    for ch in re.match(r'[A-Z]+', ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def alan(s):
    return f'"{s.replace(chr(34), chr(34) * 2)}"' if any(x in s for x in ';"\n') else s


def main(yol):
    with zipfile.ZipFile(yol) as z:
        try:
            ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
            paylasilan = [''.join(t.text or '' for t in si.iterfind('.//m:t', NS)) for si in ss.iterfind('m:si', NS)]
        except KeyError:
            paylasilan = []
        xf, ozel = bicim_tablosu(z)
        sayfa = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    for row in sayfa.iterfind('m:sheetData/m:row', NS):
        hucreler = {kolon_no(c.get('r')): hucre(c, paylasilan, xf, ozel) for c in row.iterfind('m:c', NS)}
        if hucreler:
            sys.stdout.write(';'.join(alan(hucreler.get(i, '')) for i in range(max(hucreler) + 1)) + '\n')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('kullanim: xlsx_to_csv.py <dosya.xlsx>')
    main(sys.argv[1])
