#!/usr/bin/env python3
"""Elastic Security (SIEM) tespit kurallarini kurar.

Bes kural; ilk dordu saldiri zincirinin dort halkasini, besincisi dosya degisikligini yakalar:
  1. Threshold -> ayni kaynaktan yogun basarisiz deneme (brute force)
  2. EQL sequence -> basarisiz denemelerin ARDINDAN gelen basarili giris (ihlal)
  3. Query -> saldiri sonrasi kalicilik: yeni kullanici hesabi
  4. Query -> tehdit istihbarati (IOC) eslesmesi
  5. Query -> izlenen yapilandirma dosyasi degisti (Auditbeat FIM)

Uretilen alarmlar Kibana > Security > Alerts ekraninda ve
.alerts-security.alerts-* index'inde goruntulenir.
"""
import base64
import json
import os
import ssl
import sys
import time
from urllib import error, request

BASE = os.environ.get("KIBANA_URL", "http://127.0.0.1:5601").rstrip("/")
USER = os.environ.get("ES_USER", "elastic")
PWD = os.environ.get("ELASTIC_PASSWORD", "DevOps2026!")
HEADERS = {
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
    "Authorization": "Basic " + base64.b64encode(f"{USER}:{PWD}".encode()).decode(),
}
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

INDEX = ["siem-auth-*"]


def mitre(tactic_id, tactic_name, technique_id, technique_name):
    return [{
        "framework": "MITRE ATT&CK",
        "tactic": {"id": tactic_id, "name": tactic_name,
                   "reference": f"https://attack.mitre.org/tactics/{tactic_id}/"},
        "technique": [{"id": technique_id, "name": technique_name,
                       "reference": f"https://attack.mitre.org/techniques/{technique_id}/"}],
    }]


RULES = [
    {
        "rule_id": "siem-lab-ssh-brute-force",
        "name": "SSH Brute Force: ayni kaynaktan yogun basarisiz deneme",
        "description": ("On dakikalik pencerede ayni kaynak IP'den 10 ya da daha fazla basarisiz "
                        "kimlik dogrulama. Tek bir hatali parola normaldir; yogunluk saldiridir."),
        "type": "threshold",
        "language": "kuery",
        "query": 'event.outcome : "failure"',
        "threshold": {"field": ["source.ip"], "value": 10},
        "severity": "high",
        "risk_score": 73,
        "interval": "1m",
        "from": "now-10m",
        "threat": mitre("TA0006", "Credential Access", "T1110", "Brute Force"),
        "note": ("### Triyaj\n1. Kaynak IP'nin gecmisine bak: yalnizca basarisiz mi, "
                 "arada basarili var mi?\n2. Hedeflenen kullanici sayisi 1 ise parola "
                 "deneme, cok ise kullanici tarama (spraying).\n3. Basarili giris varsa "
                 "olayi ihlal olarak yukselt."),
    },
    {
        "rule_id": "siem-lab-successful-login-after-bruteforce",
        "name": "Ihlal: basarisiz denemelerin ardindan basarili SSH girisi",
        "description": ("Ayni kaynak IP'den art arda bes basarisiz denemeden sonra basarili "
                        "giris. Tek basina her iki olay da sessizdir; SIREYI yakalamak icin "
                        "EQL sequence gerekir."),
        "type": "eql",
        "language": "eql",
        "query": ('sequence by source.ip with maxspan=15m\n'
                  '  [ any where event.outcome == "failure" ] with runs=5\n'
                  '  [ any where event.action == "ssh_login_success" ]'),
        "severity": "critical",
        "risk_score": 88,
        "interval": "1m",
        "from": "now-20m",
        "threat": mitre("TA0001", "Initial Access", "T1078", "Valid Accounts"),
        "note": ("### Triyaj\n1. Giris yapilan hesabi ve kaynak IP'yi tespit et.\n"
                 "2. Giristen SONRAKI olaylari incele: sudo, yeni kullanici, crontab.\n"
                 "3. Hesabin parolasini sifirla, oturumlari sonlandir."),
    },
    {
        "rule_id": "siem-lab-new-user-created",
        "name": "Kalicilik: yeni kullanici hesabi olusturuldu",
        "description": ("Sunucuda yeni bir yerel kullanici hesabi acildi. Planli degilse "
                        "saldirganin kalicilik (persistence) adimidir."),
        "type": "query",
        "language": "kuery",
        "query": 'event.action : "user_created"',
        "severity": "high",
        "risk_score": 70,
        "interval": "1m",
        "from": "now-10m",
        "threat": mitre("TA0003", "Persistence", "T1136", "Create Account"),
        "note": "### Triyaj\n1. Hesabi kim acti (sudo kaydi)?\n2. Degisiklik talebi var mi?",
    },
    {
        "rule_id": "siem-lab-threat-intel-match",
        "name": "Tehdit istihbarati eslesmesi: bilinen kotu IP",
        "description": ("Olaydaki kaynak IP, siem-threat-intel listesindeki bir gosterge ile "
                        "eslesti. Zenginlestirme asamasinda isaretlenir, burada alarma donusur."),
        "type": "query",
        "language": "kuery",
        "query": 'threat.indicator.matched.field : "source.ip"',
        "severity": "medium",
        "risk_score": 55,
        "interval": "1m",
        "from": "now-10m",
        "threat": mitre("TA0043", "Reconnaissance", "T1595", "Active Scanning"),
        "note": "### Triyaj\n1. Gostergenin guven seviyesine bak (threat.indicator.confidence).\n"
                "2. Dusuk guvende tek basina aksiyon alma; baska sinyallerle birlestir.",
    },
    {
        "rule_id": "siem-lab-config-changed",
        "name": "Kritik yapilandirma dosyasi degisti",
        "description": "Izlenen SSH yapilandirmasi degistirildi (Auditbeat dosya butunlugu).",
        "type": "query",
        "language": "kuery",
        "index": ["siem-fim-*"],
        "query": 'event.module : "file_integrity" and event.action : "updated" and file.path : "/izlenen/sshd_config"',
        "severity": "high",
        "risk_score": 73,
        "interval": "1m",
        "from": "now-10m",
        "threat": mitre("TA0003", "Persistence", "T1098", "Account Manipulation"),
    },
]


def api(method, path, body=None, allow=()):
    payload = json.dumps(body).encode() if body is not None else None
    req = request.Request(BASE + path, data=payload, headers=HEADERS, method=method)
    try:
        with request.urlopen(req, context=CONTEXT, timeout=60) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        if exc.code not in allow:
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}: "
                               f"{exc.read().decode('utf-8', 'replace')}") from None
        return exc.code, {}


def main():
    print(f"Kibana bekleniyor ({BASE}) ...", flush=True)
    for _ in range(30):
        try:
            api("GET", "/api/status")
            break
        except (OSError, RuntimeError):
            time.sleep(2)
    else:
        raise SystemExit("Kibana'ya erisilemedi.")

    # Alarm index'ini (.alerts-security.alerts-default) hazirla
    api("POST", "/api/detection_engine/index", allow=(409, 400))

    for rule in RULES:
        body = {
            "enabled": True,
            "index": rule.pop("index", INDEX),
            "max_signals": 100,
            "tags": ["siem-lab"],
            "author": ["Elastic Lab"],
            "license": "Lab",
            **rule,
        }
        api("DELETE", f"/api/detection_engine/rules?rule_id={rule['rule_id']}", allow=(404,))
        _, created = api("POST", "/api/detection_engine/rules", body)
        print(f"[+] Kural kuruldu: {created.get('name')}  "
              f"[{created.get('type')}] severity={created.get('severity')} "
              f"risk={created.get('risk_score')}")

    print(f"\n[+] {len(RULES)} tespit kurali etkin.")
    print(f"    Alarmlar: {BASE}/app/security/alerts")
    print(f"    Kurallar: {BASE}/app/security/rules")


if __name__ == "__main__":
    main()
