#!/usr/bin/env bash
# LAB-18 temizligi: alarm-5xx kurali (arayuzde kurulduysa adla), alarm-gecmisi-yaz, alarm-slack, alarm-eposta connector'lari, alarm-apache ve alarm-gecmisi index'leri,
# alarm-apache sablonu, data view'i ve ona bagli harita / kayitli arama. Ana cluster ve diger lablar etkilenmez.
set -u
A='elastic:DevOps2026!'; ES=http://127.0.0.1:9200; KB=http://127.0.0.1:5601
k() { curl -s -o /dev/null -w '%{http_code}' -u "$A" -H 'kbn-xsrf: true' "$@"; }
echo "kural alarm-5xx -> $(k -X DELETE "$KB/api/alerting/rule/alarm-5xx")"
# Adim 4 kutusu: kural arayuzde kurulduysa id'si rastgeledir; adla bulunur
for id in $(curl -s -u "$A" "$KB/api/alerting/rules/_find?per_page=100&search_fields=name&search=%22%C3%96deme%205xx%20patlamas%C4%B1%22" \
  | jq -r '.data[] | select(.name == "Ödeme 5xx patlaması" and .id != "alarm-5xx") | .id'); do
  echo "kural $id -> $(k -X DELETE "$KB/api/alerting/rule/$id")"
done
echo "connector alarm-gecmisi-yaz -> $(k -X DELETE "$KB/api/actions/connector/alarm-gecmisi-yaz")"
# Slack ve e-posta kutusu: connector'lar arayuzde kurulur (id rastgele); adla bulunur, yoksa satir basilmaz
for id in $(curl -s -u "$A" "$KB/api/actions/connectors" | jq -r '.[] | select(.name == "alarm-slack" or .name == "alarm-eposta") | .id'); do
  echo "connector $id -> $(k -X DELETE "$KB/api/actions/connector/$id")"
done
N=0
for t in map search lens dashboard; do
  for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=$t&per_page=1000&has_reference=%7B%22type%22%3A%22index-pattern%22%2C%22id%22%3A%22alarm-apache%22%7D" | jq -r '.saved_objects[].id'); do
    k -X DELETE "$KB/api/saved_objects/$t/$id?force=true" >/dev/null; N=$((N + 1))
  done
done
for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=dashboard&search_fields=title&search=Alarm&per_page=100" | jq -r '.saved_objects[] | select(.attributes.title == "Alarm panosu") | .id'); do
  k -X DELETE "$KB/api/saved_objects/dashboard/$id" >/dev/null; N=$((N + 1))
done
echo "Kibana nesneleri -> $N silindi"
echo "data view alarm-apache -> $(k -X DELETE "$KB/api/data_views/data_view/alarm-apache")"
echo "index'ler -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/alarm-apache,alarm-gecmisi?ignore_unavailable=true")"
for t in alarm-apache alarm-gecmisi; do
  echo "sablon $t -> $(curl -s -o /dev/null -w '%{http_code}' -u "$A" -X DELETE "$ES/_index_template/$t")"
done
