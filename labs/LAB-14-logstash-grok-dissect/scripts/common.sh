# LAB-14 ortak degiskenler: tum betikler ayni adresleri ve kimlik bilgisini kullanir.
ES_URL="${ES_URL:-http://localhost:9200}"
KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
ES_USER="${ES_USER:-elastic}"
ELASTIC_PASSWORD="${ELASTIC_PASSWORD:-DevOps2026!}"
LOGSTASH_HOST="${LOGSTASH_HOST:-127.0.0.1}"
LOGSTASH_TCP_PORT="${LOGSTASH_TCP_PORT:-5000}"
LOGSTASH_API="${LOGSTASH_API:-http://127.0.0.1:9600}"
LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

es() { curl -s -u "${ES_USER}:${ELASTIC_PASSWORD}" "$@"; }
