#!/usr/bin/env bash
# Bir node'u Elasticsearch paketi icin hazirlar ve 9.5.5'i kurar (SERVISI BASLATMAZ).
# Uc node'da da ayni betik calisir; node-1'den: bash scripts/hazirla.sh | ssh <node> 'bash -s'
set -euo pipefail
sudo sysctl -q -w vm.max_map_count=262144
echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.d/99-elasticsearch.conf >/dev/null
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a   # paket kurarken soru sorulmasin
sudo -E apt-get update -qq
sudo -E apt-get upgrade -y -qq >/dev/null
sudo -E apt-get install -y -qq apt-transport-https gnupg curl jq >/dev/null
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor --yes -o /usr/share/keyrings/elasticsearch-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/9.x/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/elastic-9.x.list >/dev/null
sudo -E apt-get update -qq
sudo -E apt-get install -y -qq elasticsearch=9.5.5 >/tmp/adv10-apt.log 2>&1
sudo apt-mark hold elasticsearch >/dev/null
# heap: 8 GB'lik VM'de 2 GB (RAM'in yarisindan az; isletim sistemi dosya onbellegine yer kalsin)
printf -- '-Xms2g\n-Xmx2g\n' | sudo tee /etc/elasticsearch/jvm.options.d/heap.options >/dev/null
echo "$(hostname -s): $(dpkg-query -W -f='${Package} ${Version}' elasticsearch), servis: $(systemctl is-active elasticsearch || true)"
