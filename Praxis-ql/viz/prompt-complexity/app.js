(function () {
  const h = React.createElement;
  const { useEffect, useState } = React;

  const COLORS = {
    assente: "#64748b",
    base: "#3b82f6",
    media: "#f59e0b",
    alta: "#b91c1c",
    accent: "#0f766e",
    slate: "#334155",
  };
  const complexityOrder = ["assente", "base", "media", "alta"];

  function num(v) {
    return Number(v || 0).toLocaleString("it-IT");
  }

  function pct(v, total) {
    if (!total) return "0,0%";
    return `${((Number(v) / total) * 100).toLocaleString("it-IT", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })}%`;
  }

  function label(text) {
    return String(text || "").replaceAll("_", " ");
  }

  function StackedComplexity({ cohorts }) {
    const width = 680;
    const rowH = 48;
    const left = 170;
    const chartW = 420;
    const height = cohorts.length * rowH + 52;
    return h(
      "svg",
      { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
      h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#5a6678", fontWeight: 700 } }, "Complessita per coorte"),
      cohorts.map((cohort, i) => {
        const y = 30 + i * rowH;
        let x = left;
        return h(
          "g",
          { key: cohort.cohort },
          h("text", { x: 0, y: y + 14, style: { fontSize: 12, fill: "#172033" } }, cohort.label),
          complexityOrder.map((level) => {
            const value = cohort.complexity[level] || 0;
            const w = (value / cohort.items_total) * chartW;
            const node = h("rect", { key: level, x, y, width: w, height: 18, fill: COLORS[level], rx: 4 });
            x += w;
            return node;
          }),
          h("text", { x: left + chartW + 10, y: y + 14, style: { fontSize: 11, fill: "#5a6678" } },
            complexityOrder.map((level) => pct(cohort.complexity[level] || 0, cohort.items_total)).join(" / "))
        );
      })
    );
  }

  function BarChart({ title, entries, color = COLORS.accent }) {
    const data = Object.entries(entries || {})
      .filter(([, value]) => value > 0)
      .sort((a, b) => b[1] - a[1]);
    const width = 680;
    const rowH = 30;
    const left = 190;
    const chartW = 390;
    const height = Math.max(data.length, 1) * rowH + 46;
    const max = Math.max(...data.map(([, value]) => value), 1);
    return h(
      "svg",
      { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
      h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#5a6678", fontWeight: 700 } }, title),
      data.map(([key, value], i) => {
        const y = 26 + i * rowH;
        const w = (value / max) * chartW;
        return h(
          "g",
          { key },
          h("text", { x: 0, y: y + 13, style: { fontSize: 12, fill: "#172033" } }, label(key)),
          h("rect", { x: left, y, width: w, height: 15, fill: color, rx: 4 }),
          h("text", { x: left + w + 8, y: y + 12, style: { fontSize: 11, fill: "#5a6678" } }, num(value))
        );
      })
    );
  }

  function FeatureTable({ data }) {
    const features = Object.keys(data.feature_labels || {});
    return h(
      "div",
      { className: "table-wrap" },
      h(
        "table",
        { className: "table" },
        h(
          "thead",
          null,
          h(
            "tr",
            null,
            h("th", null, "Parametro"),
            h("th", null, "Totale"),
            data.cohorts.map((cohort) => h("th", { key: cohort.cohort }, cohort.label))
          )
        ),
        h(
          "tbody",
          null,
          features.map((field) =>
            h(
              "tr",
              { key: field },
              h("td", null, data.feature_labels[field]),
              h("td", null, `${num(data.totals.features[field])} (${pct(data.totals.features[field], data.totals.items_total)})`),
              data.cohorts.map((cohort) =>
                h("td", { key: `${cohort.cohort}-${field}` }, `${num(cohort.features[field])} (${pct(cohort.features[field], cohort.items_total)})`)
              )
            )
          )
        )
      )
    );
  }

  function CohortTable({ cohorts }) {
    return h(
      "div",
      { className: "table-wrap" },
      h(
        "table",
        { className: "table" },
        h(
          "thead",
          null,
          h("tr", null, ["Coorte", "N", "Assente", "Base", "Media", "Alta", "Parole medie", "Confidence"].map((x) => h("th", { key: x }, x)))
        ),
        h(
          "tbody",
          null,
          cohorts.map((c) =>
            h(
              "tr",
              { key: c.cohort },
              h("td", null, c.label),
              h("td", null, num(c.items_total)),
              ...complexityOrder.map((level) => h("td", { key: level }, `${num(c.complexity[level] || 0)} (${pct(c.complexity[level] || 0, c.items_total)})`)),
              h("td", null, c.avg_word_count.toLocaleString("it-IT")),
              h("td", null, c.avg_confidence.toLocaleString("it-IT"))
            )
          )
        )
      )
    );
  }

  function Examples({ examples }) {
    return h(
      "div",
      { className: "examples" },
      examples.map((ex, i) =>
        h(
          "article",
          { className: "example", key: `${ex.source_name}-${i}` },
          h("span", { className: "badge" }, `${ex.level} - ${ex.cohort_label}`),
          h("div", { className: "answer" }, ex.answer || "-"),
          h("div", { className: "meta" }, `${ex.source_name} | ${label(ex.prompt_type)} | parole: ${num(ex.word_count)} | conf: ${ex.confidence}`),
          h("div", { className: "meta" }, ex.reason)
        )
      )
    );
  }

  function App() {
    const [data, setData] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
      fetch("./prompt-complexity-data.json")
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.json();
        })
        .then((payload) => setData(payload))
        .catch((err) => setError(String(err)));
    }, []);

    if (error) return h("div", { className: "page" }, h("section", { className: "panel" }, `Errore caricamento dati: ${error}`));
    if (!data) return h("div", { className: "page" }, h("section", { className: "panel" }, "Caricamento dashboard..."));

    const totals = data.totals;
    return h(
      "main",
      { className: "page" },
      h(
        "section",
        { className: "panel" },
        h("h1", null, "Prompt Complexity Dashboard PRAXIS - Qwen 3.5 9B"),
        h("p", null, "Analisi della sola domanda sugli esempi di prompt. Le metriche sono descrittive e item-level."),
        h("div", { className: "nav" }, h("a", { href: "../" }, "Grafo PRAXIS"), h("a", { href: "../sentiment/" }, "Sentiment dashboard"))
      ),
      h(
        "section",
        { className: "panel" },
        h("h2", null, "Sintesi"),
        h(
          "div",
          { className: "kpi-grid" },
          h("div", { className: "kpi" }, h("div", { className: "n" }, num(totals.items_total)), h("div", { className: "l" }, "Item analizzati")),
          h("div", { className: "kpi" }, h("div", { className: "n", style: { color: COLORS.base } }, `${pct(totals.complexity.base, totals.items_total)}`), h("div", { className: "l" }, "Prompt base")),
          h("div", { className: "kpi" }, h("div", { className: "n", style: { color: COLORS.media } }, `${pct(totals.complexity.media, totals.items_total)}`), h("div", { className: "l" }, "Prompt medi")),
          h("div", { className: "kpi" }, h("div", { className: "n", style: { color: COLORS.high } }, `${pct(totals.complexity.alta, totals.items_total)}`), h("div", { className: "l" }, "Prompt alti")),
          h("div", { className: "kpi" }, h("div", { className: "n" }, totals.avg_word_count.toLocaleString("it-IT")), h("div", { className: "l" }, "Parole medie")),
          h("div", { className: "kpi" }, h("div", { className: "n" }, num(Object.keys(totals.strategies || {}).length)), h("div", { className: "l" }, "Strategie rilevate"))
        )
      ),
      h(
        "section",
        { className: "row" },
        h("div", { className: "panel" }, h(StackedComplexity, { cohorts: data.cohorts }), h("div", { className: "legend" }, complexityOrder.map((level) => h("span", { key: level }, h("span", { className: "dot", style: { background: COLORS[level] } }), level)))),
        h("div", { className: "panel" }, h(BarChart, { title: "Tipi di prompt", entries: totals.prompt_type, color: COLORS.slate }))
      ),
      h(
        "section",
        { className: "row" },
        h("div", { className: "panel" }, h(BarChart, { title: "Strategie dichiarate", entries: totals.strategies, color: COLORS.accent })),
        h("div", { className: "panel" }, h(BarChart, { title: "Specificita", entries: totals.specificity, color: "#7c3aed" }))
      ),
      h("section", { className: "panel" }, h("h2", null, "Parametri presenti nei prompt"), h(FeatureTable, { data })),
      h("section", { className: "panel" }, h("h2", null, "Dettaglio per coorte"), h(CohortTable, { cohorts: data.cohorts })),
      h("section", { className: "panel" }, h("h2", null, "Esempi classificati"), h(Examples, { examples: data.examples }))
    );
  }

  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
