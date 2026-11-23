#!/usr/bin/env bash
# LAB-09 temizligi: yalniz bu labin model-* index'lerini (alias'lar index'le birlikte gider) siler.
# Ana cluster'a ve diger lablara dokunmaz.
set -u
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200
for idx in model-siparisler-v1 model-siparisler-v2 model-urun-ozellik model-musteri-siparis model-musteriler model-satislar; do
  echo "index $idx -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/$idx")"
done
