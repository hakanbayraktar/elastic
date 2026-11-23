#!/usr/bin/env bash
# ADV-10 temizligi: uc node'da Elasticsearch paketi, verisi, ayarlari ve sertifikalari silinir.
# Yalniz bu lab icin acilmis VM'lerde calistirin; ~/adv10.env ve SSH anahtari kalir.
set -uo pipefail
cd "$(dirname "$0")"
. scripts/ortam.sh
TEMIZLE='sudo systemctl stop elasticsearch 2>/dev/null; sudo apt-mark unhold elasticsearch >/dev/null 2>&1;
  sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y -qq elasticsearch >/dev/null 2>&1;
  sudo rm -rf /var/lib/elasticsearch /etc/elasticsearch /var/log/elasticsearch;
  echo "$(hostname -s): $(dpkg-query -W -f="\${Status}" elasticsearch 2>/dev/null || echo paket yok)"'
n1 "$TEMIZLE"; n2 "$TEMIZLE"; n3 "$TEMIZLE"
