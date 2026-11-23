#!/usr/bin/env bash
# LAB-08 temizligi: yalniz Adim 4 kutusunda olusturulan "ES|QL özeti" panosunu (basliga gore) siler.
# Ornek e-ticaret verisine ve ana cluster'a dokunmaz.
set -u
KB=http://127.0.0.1:5601; A='elastic:DevOps2026!'
title='ES|QL özeti'
for id in $(curl -s -u "$A" -G "$KB/api/saved_objects/_find" --data-urlencode "type=dashboard" --data-urlencode "search_fields=title" --data-urlencode "search=\"$title\"" | jq -r --arg t "$title" '.saved_objects[] | select(.attributes.title == $t) | .id'); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE -H 'kbn-xsrf: true' "$KB/api/saved_objects/dashboard/$id")
  echo "dashboard '$title' -> $code"
done
