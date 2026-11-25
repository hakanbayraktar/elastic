# LAB-18 Adim 7: alarm-5xx kurali; Adim 4'teki tanim + Slack ve e-posta aksiyonlari.
# Kullanim: jq -n --arg to "$ALARM_TO" -f scripts/kural.jq | ./scripts/kbn.sh POST /api/alerting/rule/alarm-5xx @-
{
  name: "Ödeme 5xx patlaması", rule_type_id: ".es-query", consumer: "stackAlerts", schedule: { interval: "1m" },
  params: { searchType: "esQuery", index: ["alarm-apache"], timeField: "@timestamp",
    esQuery: "{\"query\":{\"term\":{\"http.response.status_class\":\"5xx\"}}}",
    threshold: [10], thresholdComparator: ">", timeWindowSize: 5, timeWindowUnit: "m",
    size: 0, aggType: "count", groupBy: "all", excludeHitsFromPreviousRun: false },
  actions: [
    { id: "alarm-gecmisi-yaz", group: "query matched",
      params: { documents: [ { kural: "{{rule.name}}", adet: "{{context.value}}", kosul: "{{context.conditions}}", zaman: "{{context.date}}" } ] },
      frequency: { summary: false, notify_when: "onActionGroupChange", throttle: null } },
    { id: "alarm-slack", group: "query matched",
      params: { message: "[ALARM] {{rule.name}}: son 5 dakikada {{context.value}} adet 5xx ({{context.conditions}})" },
      frequency: { summary: false, notify_when: "onActionGroupChange", throttle: null } },
    { id: "alarm-eposta", group: "query matched",
      params: { to: [$to], subject: "[ALARM] {{rule.name}}: {{context.value}} adet 5xx",
        message: "Kural: {{rule.name}}\nÖlçülen: {{context.value}}\nKoşul: {{context.conditions}}\nZaman: {{context.date}}" },
      frequency: { summary: false, notify_when: "onActionGroupChange", throttle: null } }
  ]
}
