# Apache 5xx kurali: Mailpit + gercek e-posta (Resend) + Slack aksiyonlariyla. Kullanim:
#   jq -n --arg to "$ALARM_TO" -f scripts/kural.jq | curl ... -X POST .../api/alerting/rule/apache-5xx -d @-
{
  name: "Apache 5xx artışı", rule_type_id: ".es-query", consumer: "stackAlerts", schedule: { interval: "1m" },
  params: { searchType: "esQuery", index: ["apache-web-*"], timeField: "@timestamp",
    esQuery: "{\"query\":{\"bool\":{\"filter\":[{\"term\":{\"event.dataset\":\"apache.access\"}},{\"range\":{\"http.response.status_code\":{\"gte\":500}}}]}}}",
    threshold: [40], thresholdComparator: ">", timeWindowSize: 2, timeWindowUnit: "m",
    size: 0, aggType: "count", groupBy: "all", excludeHitsFromPreviousRun: false },
  actions: [
    { id: "apache-mailpit", group: "query matched",
      params: { to: ["operasyon@lab.local"], subject: "[ALARM] {{rule.name}}: {{context.value}} adet 5xx",
                message: "{{context.conditions}}\nOlculen: {{context.value}}\nZaman: {{context.date}}" },
      frequency: { summary: false, notify_when: "onActionGroupChange", throttle: null } },
    { id: "apache-eposta", group: "query matched",
      params: { to: [$to], subject: "[ALARM] {{rule.name}}: {{context.value}} adet 5xx",
                message: "{{context.conditions}}\nOlculen: {{context.value}}\nZaman: {{context.date}}" },
      frequency: { summary: false, notify_when: "onActionGroupChange", throttle: null } },
    { id: "apache-slack", group: "query matched",
      params: { message: ":rotating_light: *{{rule.name}}*: {{context.value}} adet 5xx (son 2 dk). {{context.date}}" },
      frequency: { summary: false, notify_when: "onActionGroupChange", throttle: null } }
  ]
}
