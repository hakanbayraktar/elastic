#!/usr/bin/env python3
"""README calistirici: bir lab README'sindeki kod bloklarini SIRAYLA calistirir ve
her blogu PASS / FAIL / ELLE / ATLA olarak raporlar.

Amac: "README'deki komutlarla test" kuralini mekaniklestirmek. Testi yapan kisi/ajan
raporu okuyup gercek ciktiyi README'deki beklenen blokla karsilastirir; bu arac
"gecti" kararini yalnizca cikis koduna gore verir, icerik eslesmesini insan yapar.

Kullanim (sunucuda, repo kokunden):
  python3 scripts/readme-runner/readme_runner.py labs/LAB-09A-.../README.md --list
  python3 scripts/readme-runner/readme_runner.py labs/LAB-09A-.../README.md            # hepsi
  python3 scripts/readme-runner/readme_runner.py labs/LAB-09A-.../README.md --from 7
  python3 scripts/readme-runner/readme_runner.py labs/LAB-09A-.../README.md --only 7,8

Blok turleri:
  bash/sh      -> kalici bir kabuk durumuyla calistirilir: onceki bloklarin `cd`'si ve
                  degisken atamalari (set -a ile) sonraki bloklara tasinir.
  http         -> Kibana Dev Tools istegi; LAB-01 omurgasina (ES_URL, varsayilan
                  http://localhost:9200) curl ile gonderilir; `kbn:/api/...` onekli istekler
                  Console'daki gibi Kibana'ya (KIBANA_URL, varsayilan http://localhost:5601)
                  kbn-xsrf basligiyla gider. LAB-09A/09B README'lerinde
                  http blogu yalnizca alinti oldugu icin calistirilmaz.
  diger (text, json, yaml, nginx, apache, ruby ...) -> calistirilmaz; bir onceki
                  komutun BEKLENEN ciktisi olarak rapora yazilir.

ELLE (elle yapilacak) sayilan bloklar: yer tutucu iceren (studentXX, <IP>, <...>),
sonsuz akan (`logs -f`, `tail -f`, `watch`), etkilesimli (`read -rsp`), nginx'i
degistiren (`sudo cp ... nginx`, `systemctl reload nginx`) bloklar ve "Config"
basligi altindaki alintilar. Bunlar raporda listelenir; calistirilmaz.

README isaretleri (blogun hemen ustundeki satir):
  <!-- runner:skip -->         blogu calistirma (alternatif yol, yikici adim vb.)
  <!-- runner:expect-fail -->  komutun sifir disi cikmasi beklenir (ornek: TLS reddi)
  <!-- runner:run -->          not kutusu (> ...) icindeki blogu yine de calistir

Ortam: calistiricinin ortam degiskenleri bloklara gecer. Etkilesimli parola blogu
(read -rsp) ELLE sayildigi icin RBAC_PASSWORD gibi degerleri kosudan once disarida
verin:  read -rsp 'parola: ' RBAC_PASSWORD; export RBAC_PASSWORD

Temizlik ve opsiyonel bolumler: README sirasinda "Temizlik" opsiyonel bolumlerden once
gelir. Ana akisi test etmek icin --list ile blok numaralarina bakip --only/--from ile
araliklari secin (ornek: ana akis, sonra opsiyonel bolumler, en son temizlik).

Rapor: $READMERUN_OUT (varsayilan ~/readme-runs) altina <lab>-<zaman>.md olarak yazilir.
Parola/anahtar gibi degerleri rapora yazmaz: 'encoded', 'api_key', 'password' iceren
satirlar maskelenir.
"""
import base64, datetime, json, os, re, subprocess, sys, tempfile, textwrap
from pathlib import Path
from urllib import request, error

FENCE = re.compile(r'^(?P<ind>[ >]*)```(?P<lang>[\w+-]*)\s*$')
# <p>, <b>, <br> gibi HTML etiketleri (html_strip ornekleri) yer tutucu sayilmaz.
HTML_TAGS = 'a|b|i|p|u|br|hr|em|li|ol|ul|h[1-6]|div|span|strong|script|style|body|html|head|title|table|tr|td|th|img|code|pre'
PLACEHOLDER = re.compile(r'studentXX|hostXX|<IP>|<(?!/?(?:' + HTML_TAGS + r')\b)[A-Za-z_][\w-]*>|\bXX\b')
ENDLESS = re.compile(r'logs\s+(?:[^\n|]*\s)?-f\b|\btail\s+(?:[^\n|]*\s)?-f\b|\bwatch\b|-f\s*$|journalctl\s+(?:[^\n|]*\s)?-f\b')
# Omurgayi (LAB-01 starter) durduran/silen komut: isaret unutulsa bile asla calistirilmaz.
BACKBONE_STOP = re.compile(r'LAB-01-kurulum-kontrol/starter[^\n]*compose[^\n]*\b(stop|down)\b')
INTERACTIVE = re.compile(r'read\s+-r?s?p|\bnano\b|\bvim?\b ')
NGINX_CHANGE = re.compile(r'(sudo\s+cp[^\n]*nginx|systemctl\s+reload\s+nginx|expose-external\.sh\s+(on|off))')
# _analyze yanitindaki "token" (metin parcasi) gizli bilgi degildir; yalniz access_token,
# refresh_token gibi anahtarlar maskelenir.
SECRET = re.compile(r'("?(encoded|api_key|password|secret|[a-z_]+_token)"?\s*[:=]\s*)("[^"]*"|\S+)', re.I)
RUNNABLE = {'bash', 'sh', 'shell', 'console'}
QUOTE_HEAD = re.compile(r'config|hangi satır|hangi satir', re.I)


def blocks(md_text):
    """(no, lang, code, heading, line) listesi. > ile alintilanmis bloklar da okunur."""
    out, lines, i, heading = [], md_text.splitlines(), 0, ''
    while i < len(lines):
        line = lines[i]
        if re.match(r'^#{1,6} ', line):
            heading = line.lstrip('#').strip()
        m = FENCE.match(line)
        if m:
            ind, lang, start = m['ind'], m['lang'].lower(), i
            body = []
            i += 1
            while i < len(lines) and not FENCE.match(lines[i]):
                l = lines[i]
                body.append(l[len(ind):] if l.startswith(ind) else l.lstrip(' >'))
                i += 1
            prev = lines[start - 1].strip().lstrip('> ').strip() if start > 0 else ''
            prev2 = lines[start - 2].strip().lstrip('> ').strip() if start > 1 else ''
            marker = ' '.join(x for x in (prev, prev2) if x.startswith('<!-- runner:'))
            quoted = '>' in ind
            out.append([len(out) + 1, lang or 'text', '\n'.join(body), heading, start + 1, marker, quoted])
        i += 1
    return out


def classify(lang, code, heading, lab, marker='', quoted=False):
    if lang not in RUNNABLE and lang != 'http':
        return 'CIKTI', 'beklenen cikti / alinti'
    if 'runner:skip' in marker:
        return 'ATLA', 'README isareti: runner:skip'
    if quoted and 'runner:run' not in marker:
        return 'ATLA', 'not/uyari kutusu icinde (alternatif veya bilgi)'
    if QUOTE_HEAD.search(heading):
        return 'ATLA', 'Config basligi altinda alinti'
    if lang == 'http' and ('LAB-09A' in lab or 'LAB-09B' in lab):
        return 'ATLA', 'LAB-09 http bloklari alintidir (istekler run-http.sh ile calisir)'
    if BACKBONE_STOP.search(code):
        return 'ATLA', 'omurgayi durdurur (LAB-01 compose stop/down)'
    if PLACEHOLDER.search(code):
        return 'ELLE', 'yer tutucu iceriyor: ' + PLACEHOLDER.search(code)[0]
    if lang != 'http' and ENDLESS.search(code):
        return 'ELLE', 'sonsuz akan komut'
    if INTERACTIVE.search(code):
        return 'ELLE', 'etkilesimli giris istiyor'
    if NGINX_CHANGE.search(code):
        return 'ELLE', 'host nginx degistiriyor'
    if lang == 'http' and not re.search(r'(?m)^(GET|POST|PUT|DELETE|HEAD) ', code):
        return 'ATLA', 'http parcasi (istek satiri yok)'
    return 'CALISTIR', ''


def mask(text):
    return SECRET.sub(lambda m: m.group(1) + '"***"', text)


def run_bash(code, state_dir, cwd0, timeout):
    env_file, cwd_file = state_dir / 'env.sh', state_dir / 'cwd'
    cwd = cwd_file.read_text().strip() if cwd_file.exists() else cwd0
    script = textwrap.dedent(f'''\
        set -a
        [ -f "{env_file}" ] && . "{env_file}" >/dev/null 2>&1
        cd "{cwd}" || exit 97
        set -o pipefail
        __rc=0
        {{
        {code}
        }} || __rc=$?
        pwd > "{cwd_file}"
        export -p > "{env_file}"
        exit $__rc
        ''')
    try:
        p = subprocess.run(['bash', '-c', script], capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired as e:
        return 124, ((e.stdout or b'').decode(errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or '')) + f'\n[ZAMAN ASIMI {timeout}s]'


def run_http(code, timeout):
    base = os.environ.get('ES_URL', 'http://localhost:9200')
    kbase = os.environ.get('KIBANA_URL', 'http://localhost:5601')
    auth = 'Basic ' + base64.b64encode((os.environ.get('ES_USER', 'elastic') + ':' +
                                        os.environ.get('ES_PASS', 'DevOps2026!')).encode()).decode()
    reqs = list(re.finditer(r'(?m)^(GET|POST|PUT|DELETE|HEAD) (\S+)\s*$', code))
    out, worst = [], 0
    for i, m in enumerate(reqs):
        end = reqs[i + 1].start() if i + 1 < len(reqs) else len(code)
        body = '\n'.join(l for l in code[m.end():end].splitlines() if l.strip() and not l.lstrip().startswith('#'))
        # Kibana Console'un """...""" (uc tirnak) metni JSON string'e cevrilir (ES|QL sorgulari boyle yazilir).
        body = re.sub(r'"""(.*?)"""', lambda q: json.dumps(textwrap.dedent(q.group(1)).strip()), body, flags=re.S)
        bulk = '_bulk' in m[2]
        data = ((body.rstrip() + '\n') if bulk else body).encode() if body else None
        path = m[2]
        headers = {'Authorization': auth,
                   'Content-Type': 'application/x-ndjson' if bulk else 'application/json'}
        url = base + '/' + path.lstrip('/')
        if path.startswith('kbn:'):
            # Kibana Dev Tools: "kbn:" oneki istegi Kibana API'sine yonlendirir.
            url = kbase + '/' + path[4:].lstrip('/')
            headers['kbn-xsrf'] = 'true'
        req = request.Request(url, data=data, method=m[1], headers=headers)
        try:
            r = request.urlopen(req, timeout=timeout)
        except error.HTTPError as e:
            r = e
        except OSError as e:
            out.append(f'{m[1]} {m[2]} -> BAGLANTI HATASI {e}'); worst = 1; continue
        with r:
            raw = r.read().decode(errors='replace')
        out.append(f'{m[1]} {m[2]} -> HTTP {r.status}\n{raw[:3000]}')
        if r.status >= 400:
            worst = 1
    return worst, '\n'.join(out)


def main():
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); sys.exit(0)
    readme = Path(a.pop(0)).resolve()
    mode, sel, timeout = 'run', {}, int(os.environ.get('READMERUN_TIMEOUT', '900'))
    while a:
        o = a.pop(0)
        if o == '--list': mode = 'list'
        elif o == '--from': sel['from'] = int(a.pop(0))
        elif o == '--only': sel['only'] = {int(x) for x in a.pop(0).split(',')}
        elif o == '--until': sel['until'] = int(a.pop(0))
        elif o == '--timeout': timeout = int(a.pop(0))
        else: sys.exit('bilinmeyen secenek: ' + o)
    lab = readme.parent.name
    bl = blocks(readme.read_text(encoding='utf-8'))
    for b in bl:
        b += list(classify(b[1], b[2], b[3], lab, b[5], b[6]))
    if mode == 'list':
        for no, lang, code, head, line, marker, quoted, kind, why in bl:
            first = code.strip().splitlines()[0][:70] if code.strip() else ''
            print(f'{no:3d} L{line:<5d} {kind:8s} {lang:6s} {first}' + (f'   [{why}]' if why and kind != 'CIKTI' else ''))
        return
    out_dir = Path(os.environ.get('READMERUN_OUT', str(Path.home() / 'readme-runs')))
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    report = out_dir / f'{lab}-{stamp}.md'
    state = Path(tempfile.mkdtemp(prefix='readme-runner-'))
    counts = {'PASS': 0, 'FAIL': 0, 'ELLE': 0, 'ATLA': 0}
    lines = [f'# README kosusu: {lab}', '', f'- Dosya: `{readme}`', f'- Zaman: {stamp}', '']
    last_result = None
    for idx, (no, lang, code, head, line, marker, quoted, kind, why) in enumerate(bl):
        # --from ve --until birlikte verilebilir (aralik); --only digerleriyle kesisir.
        chosen = (no >= sel.get('from', 0) and no <= sel.get('until', 10**9)
                  and ('only' not in sel or no in sel['only']))
        if kind == 'CIKTI':
            if last_result is not None:
                lines += ['', f'Beklenen (README blok {no}, satir {line}):', '```' + lang, code, '```']
            continue
        last_result = None
        if not chosen:
            continue
        lines += ['', f'## Blok {no} (satir {line}) — {head}', '', '```' + lang, mask(code), '```']
        if kind in ('ELLE', 'ATLA'):
            counts[kind] += 1
            lines.append(f'**{kind}** — {why}')
            print(f'[{kind:4s}] blok {no:3d} L{line}: {why}', flush=True)
            continue
        if lang == 'http':
            rc, out = run_http(code, timeout)
        else:
            rc, out = run_bash(code, state, str(readme.parent), timeout)
        if 'runner:expect-fail' in marker:
            verdict = 'PASS' if rc != 0 else 'FAIL'
        else:
            verdict = 'PASS' if rc == 0 else 'FAIL'
        counts[verdict] += 1
        lines += [f'**{verdict}** (cikis kodu {rc})', '', 'Gercek cikti:', '```text', mask(out.rstrip())[-6000:], '```']
        last_result = verdict
        print(f'[{verdict}] blok {no:3d} L{line}: rc={rc}', flush=True)
    lines += ['', '## Ozet', '', ' | '.join(f'{k}: {v}' for k, v in counts.items()),
              '', 'Not: PASS yalnizca cikis kodu 0 demektir. Gercek ciktiyi "Beklenen" blogu ile karsilastirin;',
              'README\'deki <!-- OLC: --> isaretli yerlere gercek ciktiyi yazin.']
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\n[SONUC] ' + ' '.join(f'{k}={v}' for k, v in counts.items()) + f'\n[RAPOR] {report}')
    sys.exit(1 if counts['FAIL'] else 0)


if __name__ == '__main__':
    main()
