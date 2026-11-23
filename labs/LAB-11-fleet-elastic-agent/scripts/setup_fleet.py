#!/usr/bin/env python3
"""LAB-11 Adim 1: Fleet'i hazirlar ve iki ajanin ihtiyac duydugu token'lari .env.fleet dosyasina yazar.

Yaptiklari (hepsi Kibana Fleet API ve Elasticsearch API ile):
  1. Fleet Server icin bir service token uretir (elastic/fleet-server hesabi).
  2. Fleet'in varsayilan output'unu ana cluster'a, Fleet Server adresini https://fleet-server:8220 yapar.
  3. fleet_server ve system paketlerini kurar.
  4. Iki agent policy acar (namespace fleetlab): fleet-server-policy ve fleet-linux-policy.
     Linux politikasina System integration'i system.hostfs=/hostfs ile eklenir.
  5. fleet-linux-policy icin enrollment token'i alir.
Token degerleri ekrana basilmaz.
"""
import base64
import json
import os
import urllib.error
import urllib.request

ES = os.environ.get("ES_URL", "http://127.0.0.1:9200")
KB = os.environ.get("KIBANA_URL", "http://127.0.0.1:5601")
AUTH = "Basic " + base64.b64encode(b"elastic:DevOps2026!").decode()
NS = "fleetlab"
TOKEN = "fleet-lab-token"


def api(base, path, method="GET", body=None):
    req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", AUTH)
    req.add_header("Content-Type", "application/json")
    req.add_header("kbn-xsrf", "true")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def surum(paket):
    return api(KB, f"/api/fleet/epm/packages/{paket}")[1]["item"]["latestVersion"]


api(ES, f"/_security/service/elastic/fleet-server/credential/token/{TOKEN}", "DELETE")
servis_token = api(ES, f"/_security/service/elastic/fleet-server/credential/token/{TOKEN}", "POST")[1]["token"]["value"]
print("service token          : uretildi (elastic/fleet-server/" + TOKEN + ")")

api(KB, "/api/fleet/setup", "POST")
api(KB, "/api/fleet/outputs/fleet-default-output", "PUT",
    {"name": "default", "type": "elasticsearch", "hosts": ["http://elasticsearch-lab00:9200"], "is_default": True})
print("output                 : http://elasticsearch-lab00:9200")
hosts = api(KB, "/api/fleet/fleet_server_hosts")[1].get("items", [])
if not any("https://fleet-server:8220" in h.get("host_urls", []) for h in hosts):
    api(KB, "/api/fleet/fleet_server_hosts", "POST",
        {"name": "Lab Fleet Server", "host_urls": ["https://fleet-server:8220"], "is_default": True})
print("fleet server adresi    : https://fleet-server:8220")

for paket in ("fleet_server", "system"):
    api(KB, f"/api/fleet/epm/packages/{paket}/{surum(paket)}", "POST")
print("paketler               : fleet_server, system")

for pid, ad in (("fleet-server-policy", "Lab Fleet Server"), ("fleet-linux-policy", "Lab Linux sunucu")):
    api(KB, "/api/fleet/agent_policies", "POST", {"id": pid, "name": ad, "namespace": NS, "monitoring_enabled": []})
api(KB, "/api/fleet/package_policies", "POST", {
    "name": "fleet_server-lab", "policy_id": "fleet-server-policy", "namespace": NS,
    "package": {"name": "fleet_server", "version": surum("fleet_server")}})
# system.hostfs: ajan konteynerde calisir; sunucunun /proc'u /hostfs/proc'a baglanir (docker-compose.yml).
api(KB, "/api/fleet/package_policies", "POST", {
    "name": "system-lab", "policy_id": "fleet-linux-policy", "namespace": NS,
    "package": {"name": "system", "version": surum("system")},
    "inputs": {"system-system/metrics": {"vars": {"system.hostfs": "/hostfs"}}}})
print("politikalar            : fleet-server-policy, fleet-linux-policy (namespace " + NS + ")")

anahtarlar = api(KB, "/api/fleet/enrollment_api_keys?perPage=100")[1].get("items", [])
kayit = next((k["api_key"] for k in anahtarlar if k.get("policy_id") == "fleet-linux-policy" and k.get("active")), None)
print("enrollment token       : " + ("alindi" if kayit else "YOK"))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env.fleet"), "w") as f:
    f.write(f"FLEET_SERVER_SERVICE_TOKEN={servis_token}\nFLEET_ENROLLMENT_TOKEN={kayit}\n")
print(".env.fleet             : yazildi")
