#!/usr/bin/env python3
"""sample-data/satislar.xlsx dosyasini uretir (yalniz gelistirme icin; lab adimlarinda calistirilmaz).

Yalniz standart kutuphane kullanir. Hucre bicimleri Turkce Excel'deki gibidir:
Tarih "gg.aa.yyyy", Birim Fiyat ve Tutar "#.##0,00" (binlik nokta, ondalik virgul).
Veri sentetiktir ve deterministiktir.
"""
import datetime
import os
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'sample-data', 'satislar.xlsx')

BASLIK = ['Fatura No', 'Tarih', 'Müşteri', 'İl', 'Ürün', 'Adet', 'Birim Fiyat', 'Tutar']
URUNLER = [('Dizüstü Bilgisayar', 28499.90), ('Kablosuz Kulaklık', 1299.50), ('Akıllı Saat', 2199.00),
           ('Çelik Termos', 349.00), ('Ofis Sandalyesi', 4750.00), ('Bluetooth Hoparlör', 899.90)]
ILLER = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Eskişehir', 'Muğla']
MUSTERILER = ['Ağaoğlu Yapı', 'Şimşek Lojistik', 'Öztürk Gıda', 'Çınar Eğitim', 'Güneş Enerji', 'Yıldız Tekstil']


def satirlar():
    bas = datetime.date(2026, 1, 9)
    for i in range(24):
        urun, fiyat = URUNLER[(i * 5) % len(URUNLER)]
        adet = (i * 7) % 9 + 1
        yield [f'F-2026-{1001 + i}', bas + datetime.timedelta(days=i * 13), MUSTERILER[(i * 3) % 6],
               ILLER[(i * 5) % 6], urun, adet, fiyat, round(adet * fiyat, 2)]


def kolon(n):
    return 'ABCDEFGH'[n]


def serial(d):
    return (d - datetime.date(1899, 12, 30)).days


def sheet_xml(rows):
    out = []
    for r, row in enumerate(rows, 1):
        cells = []
        for c, v in enumerate(row):
            ref = f'{kolon(c)}{r}'
            if isinstance(v, str):
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(v)}</t></is></c>')
            elif isinstance(v, datetime.date):
                cells.append(f'<c r="{ref}" s="1"><v>{serial(v)}</v></c>')
            elif isinstance(v, float):
                cells.append(f'<c r="{ref}" s="2"><v>{v}</v></c>')
            else:
                cells.append(f'<c r="{ref}"><v>{v}</v></c>')
        out.append(f'<row r="{r}">{"".join(cells)}</row>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(out)}</sheetData></worksheet>')


PARTS = {
    '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>',
    '_rels/.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>',
    'xl/workbook.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Satışlar" sheetId="1" r:id="rId1"/></sheets></workbook>',
    'xl/_rels/workbook.xml.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>',
    'xl/styles.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="dd\\.mm\\.yyyy"/></numFmts>'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="3"><xf numFmtId="0"/><xf numFmtId="164" applyNumberFormat="1"/>'
        '<xf numFmtId="4" applyNumberFormat="1"/></cellXfs>'
        '</styleSheet>',
}

if __name__ == '__main__':
    rows = [BASLIK] + list(satirlar())
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in PARTS.items():
            z.writestr(name, data)
        z.writestr('xl/worksheets/sheet1.xml', sheet_xml(rows))
    print(os.path.relpath(OUT), len(rows) - 1, 'satir')
