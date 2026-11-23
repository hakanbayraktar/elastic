#!/usr/bin/env bash
# ADV-10 ortak tanimlar. ~/adv10.env uc node'un ic IP'sini tasir (Adim 0'da yazilir).
# n1/n2/n3: komutu o node'da calistirir (node-1 yereldir, digerleri SSH ile).
set -a; . "$HOME/adv10.env"; set +a
: "${NODE1:?~/adv10.env icinde NODE1 yok}" "${NODE2:?NODE2 yok}" "${NODE3:?NODE3 yok}"
SSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"
CA="$HOME/http_ca.crt"   # Adim 2de node-1in HTTP CA sertifikasindan kopyalanir
n1() { bash -c "$1"; }
n2() { $SSH "$NODE2" "$1"; }
n3() { $SSH "$NODE3" "$1"; }
# es: node-1 uzerinden HTTPS istegi (paketin urettigi CA ile dogrulanir)
es() { curl -s --cacert "$CA" -u "elastic:${ES_PW:-DevOps2026!}" "$@"; }
