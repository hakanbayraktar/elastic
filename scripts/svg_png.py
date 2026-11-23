"""assets/infographics/*.svg -> aynı adlı .png (README'lerde gömülen kopya).

GitLab, SVG dosyasını tarayıcıda açmaz, indirir; README'deki görsele tıklayınca büyüyebilmesi için
README'ler PNG kopyasını gösterir. Kaynak her zaman SVG'dir: SVG'yi düzenledikten sonra bu betiği çalıştırın.
Gerekli: python3 -m pip install playwright ; yerel Google Chrome.
Kullanım (repo kökünden): python3 scripts/svg_png.py [dosya.svg ...]
"""
import glob, os, re, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 1.5   # 1600 px genişlikteki SVG -> 2400 px PNG: büyütünce yazı net kalır


def main(files):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome', headless=True)
        for f in files:
            ET.parse(f)
            head = open(f, encoding='utf-8').read(600)
            w = float(re.search(r'width="([\d.]+)"', head).group(1))
            h = float(re.search(r'height="([\d.]+)"', head).group(1))
            pg = b.new_page(viewport={'width': int(w), 'height': int(h)}, device_scale_factor=SCALE)
            pg.goto('file://' + os.path.abspath(f))
            out = f[:-4] + '.png'
            pg.screenshot(path=out)
            pg.close()
            print(os.path.relpath(out, ROOT))
        b.close()


if __name__ == '__main__':
    main(sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'assets', 'infographics', '*.svg'))))
