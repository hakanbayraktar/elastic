#!/usr/bin/env bash
# LAB-04 temizligi: yalniz bu labin kayitli Discover aramasini ("Kadin 100 dolar ustu siparisler") ve
# Adim 5 kutusundaki "Kadin siparisleri" panosunu siler.
# Ornek e-ticaret verisi sonraki lablarda kullanildigi icin silinmez. Ana cluster'a dokunmaz.
set -u
A='elastic:DevOps2026!'; KB=http://127.0.0.1:5601
P=0
for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=dashboard&search_fields=title&search=Kad%C4%B1n&per_page=100" | jq -r '.saved_objects[] | select(.attributes.title == "Kadın siparişleri") | .id'); do
  curl -s -o /dev/null -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/saved_objects/dashboard/$id"; P=$((P + 1))
done
echo "pano (Kadın siparişleri) -> $P"
N=0
for id in $(curl -s -u "$A" "$KB/api/saved_objects/_find?type=search&search_fields=title&search=Kad%C4%B1n&per_page=100" | jq -r '.saved_objects[] | select(.attributes.title == "Kadın 100 dolar üstü siparişler") | .id'); do
  curl -s -o /dev/null -u "$A" -H 'kbn-xsrf: true' -X DELETE "$KB/api/saved_objects/search/$id"; N=$((N + 1))
done
echo "kayitli arama (Kadın 100 dolar üstü siparişler) -> $N"
