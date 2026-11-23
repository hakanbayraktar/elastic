#!/usr/bin/env bash
# Kontrollu bir saldiri HIKAYESI uretir (gercek saldiri degil: yalnizca log satiri yazar).
# Satirlar labin data/attack-scenario.log dosyasina eklenir; Filebeat container'i bu dosyayi okur.
#
# Hikaye: tek bir IP once kullanici adi dener, sifre denemeleriyle brute force yapar, sonunda
# tutturur, yetki yukseltir ve arka kapi kullanici acar. Ayrica parolasi degismis bir yedekleme
# sunucusu 25 kez hatali giris dener (zararsiz ama alarm uretir: yanlis pozitif).
# IP'ler belgeleme araliklarindandir (203.0.113.0/24, 198.51.100.0/24).
#
# Kullanim: ./scripts/generate-attack-scenario.sh          # saldiri + yedekleme sunucusu
#           ./scripts/generate-attack-scenario.sh yedek    # yalniz yedekleme sunucusu (Adim 6)
set -euo pipefail
LOG="$(cd "$(dirname "$0")/.." && pwd)/data/attack-scenario.log"
ATTACKER_IP=203.0.113.77; VICTIM=devops; BACKUP_IP=198.51.100.20; H=$(hostname -s)
ts() { date -u -d "@$1" '+%Y-%m-%dT%H:%M:%S.%6N+00:00'; }
NOW=$(date -u +%s); START=$((NOW - 300)); PID=$((RANDOM % 50000 + 10000))

yedek() {
  for n in $(seq 1 25); do
    echo "$(ts $((START + 10 * n))) ${H} sshd[$((PID + 500 + n))]: Failed password for yedek from ${BACKUP_IP} port $((50000 + n)) ssh2"
  done
}
saldiri() {
  i=0
  for u in admin test oracle; do
    echo "$(ts $((START + i))) ${H} sshd[$((PID + i))]: Invalid user ${u} from ${ATTACKER_IP} port $((40000 + i)) ssh2"
    echo "$(ts $((START + i))) ${H} sshd[$((PID + i))]: Failed password for invalid user ${u} from ${ATTACKER_IP} port $((40000 + i)) ssh2"
    i=$((i + 3))
  done
  for n in $(seq 1 12); do
    echo "$(ts $((START + i))) ${H} sshd[$((PID + n))]: Failed password for ${VICTIM} from ${ATTACKER_IP} port $((41000 + n)) ssh2"
    i=$((i + 7))
  done
  echo "$(ts $((START + i))) ${H} sshd[$((PID + 99))]: Accepted password for ${VICTIM} from ${ATTACKER_IP} port 41999 ssh2"; i=$((i + 2))
  echo "$(ts $((START + i))) ${H} sshd[$((PID + 99))]: pam_unix(sshd:session): session opened for user ${VICTIM}(uid=1500) by ${VICTIM}(uid=0)"; i=$((i + 5))
  echo "$(ts $((START + i))) ${H} sudo:  ${VICTIM} : PWD=/home/${VICTIM} ; USER=root ; COMMAND=/bin/bash"; i=$((i + 4))
  echo "$(ts $((START + i))) ${H} useradd[$((PID + 120))]: new user: name=svc-backup, UID=1999, GID=1999, home=/home/svc-backup, shell=/bin/bash"; i=$((i + 3))
  echo "$(ts $((START + i))) ${H} sudo:  ${VICTIM} : PWD=/root ; USER=root ; COMMAND=/usr/bin/crontab -e"
}
if [ "${1:-}" = "yedek" ]; then
  yedek >> "${LOG}"; echo "[+] 25 satir yazildi: yedekleme sunucusu ${BACKUP_IP}"
else
  { saldiri; yedek; } >> "${LOG}"
  echo "[+] 48 satir yazildi -> data/attack-scenario.log"
  echo "    saldirgan ${ATTACKER_IP}: 18 basarisiz -> basarili giris -> sudo -> yeni kullanici"
  echo "    yedekleme sunucusu ${BACKUP_IP}: 25 basarisiz giris (zararsiz)"
fi
