(function () {
  const CONFIG = {
    title: "Individualizzazione dell'insegnamento con IA - Qwen 3.5 9B",
    dataFile: "./teaching-individualization-data.json",
    peerHref: "../teaching-personalization/",
    peerLabel: "Personalizzazione",
    accent: "#0f766e",
  };
  renderTeacherPracticeDashboard(CONFIG);

  function renderTeacherPracticeDashboard(config) {
    const h = React.createElement;
    const { useEffect, useState } = React;
    const label = (x) => String(x || "").replaceAll("_", " ");
    const num = (x) => Number(x || 0).toLocaleString("it-IT");
    const pct = (x, t) => (!t ? "0,0%" : `${((x / t) * 100).toLocaleString("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`);

    function BarChart({ title, entries, color }) {
      const rows = Object.entries(entries || {}).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]);
      const width = 680, left = 220, chartW = 350, rowH = 30, height = rows.length * rowH + 46;
      const max = Math.max(...rows.map(([, v]) => v), 1);
      return h("svg", { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
        h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#5b6678", fontWeight: 700 } }, title),
        rows.map(([k, v], i) => {
          const y = 26 + i * rowH, w = (v / max) * chartW;
          return h("g", { key: k }, h("text", { x: 0, y: y + 13, style: { fontSize: 12, fill: "#172033" } }, label(k)),
            h("rect", { x: left, y, width: w, height: 15, fill: color, rx: 4 }),
            h("text", { x: left + w + 8, y: y + 12, style: { fontSize: 11, fill: "#5b6678" } }, num(v)));
        }));
    }

    function PresenceByCohort({ cohorts }) {
      const width = 680, left = 180, chartW = 380, rowH = 48, height = cohorts.length * rowH + 50;
      return h("svg", { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
        h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#5b6678", fontWeight: 700 } }, "Pratica rilevata per coorte"),
        cohorts.map((c, i) => {
          const y = 30 + i * rowH, yesW = (c.practice_present / c.items_total) * chartW;
          return h("g", { key: c.cohort }, h("text", { x: 0, y: y + 14, style: { fontSize: 12, fill: "#172033" } }, c.label),
            h("rect", { x: left, y, width: yesW, height: 18, fill: "#0f766e", rx: 4 }),
            h("rect", { x: left + yesW, y, width: chartW - yesW, height: 18, fill: "#64748b", rx: 4 }),
            h("text", { x: left + chartW + 10, y: y + 14, style: { fontSize: 11, fill: "#5b6678" } }, `${pct(c.practice_present, c.items_total)} rilevata`));
        }));
    }

    function CohortTable({ cohorts }) {
      return h("div", { className: "table-wrap" }, h("table", { className: "table" },
        h("thead", null, h("tr", null, ["Coorte", "N", "Presente", "Assente", "Confidence", "Tutte le strategie"].map((x) => h("th", { key: x }, x)))),
        h("tbody", null, cohorts.map((c) => h("tr", { key: c.cohort },
          h("td", null, c.label), h("td", null, num(c.items_total)),
          h("td", null, `${num(c.practice_present)} (${pct(c.practice_present, c.items_total)})`),
          h("td", null, num(c.practice_absent)),
          h("td", null, c.avg_confidence.toLocaleString("it-IT")),
          h("td", null, Object.entries(c.strategies).map(([k, v]) => `${label(k)}:${v}`).join(" | ") || "-"))))));
    }

    function Examples({ rows }) {
      return h("div", { className: "examples" }, rows.map((r, i) => h("article", { className: "example", key: `${r.source_name}-${i}` },
        h("span", { className: "badge" }, `${r.practice_present === "True" ? "presente" : "assente"} - ${r.cohort_label}`),
        h("div", { className: "answer" }, r.answer || "-"),
        h("div", { className: "meta" }, `Strategie: ${label(r.strategies) || "-"} | target: ${label(r.target)} | ruolo IA: ${label(r.ai_role)}`),
        h("div", { className: "meta" }, `${r.source_name} | conf: ${r.confidence}`),
        h("div", { className: "meta" }, r.reason))));
    }

    function App() {
      const [data, setData] = useState(null), [error, setError] = useState("");
      useEffect(() => { fetch(config.dataFile).then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }).then(setData).catch((e) => setError(String(e))); }, []);
      if (error) return h("main", { className: "page" }, h("section", { className: "panel" }, error));
      if (!data) return h("main", { className: "page" }, h("section", { className: "panel" }, "Caricamento..."));
      const t = data.totals;
      return h("main", { className: "page" },
        h("section", { className: "panel" }, h("h1", null, config.title), h("p", null, "Analisi item-level sulle sole risposte degli insegnanti."), h("div", { className: "nav" }, h("a", { href: "../" }, "Grafo PRAXIS"), h("a", { href: config.peerHref }, config.peerLabel), h("a", { href: "../ai-pro-con/" }, "Pro e contro"))),
        h("section", { className: "panel" }, h("h2", null, "Sintesi"), h("div", { className: "kpi-grid" },
          h("div", { className: "kpi" }, h("div", { className: "n" }, num(t.items_total)), h("div", { className: "l" }, "Item")),
          h("div", { className: "kpi" }, h("div", { className: "n", style: { color: "#0f766e" } }, `${pct(t.practice_present, t.items_total)}`), h("div", { className: "l" }, "Pratica rilevata")),
          h("div", { className: "kpi" }, h("div", { className: "n" }, num(t.practice_absent)), h("div", { className: "l" }, "Assente/generica")),
          h("div", { className: "kpi" }, h("div", { className: "n" }, t.avg_confidence.toLocaleString("it-IT")), h("div", { className: "l" }, "Confidence media")))),
        h("section", { className: "row" }, h("div", { className: "panel" }, h(PresenceByCohort, { cohorts: data.cohorts })), h("div", { className: "panel" }, h(BarChart, { title: "Strategie", entries: t.strategies, color: config.accent }))),
        h("section", { className: "row" }, h("div", { className: "panel" }, h(BarChart, { title: "Target", entries: t.targets, color: "#0f766e" })), h("div", { className: "panel" }, h(BarChart, { title: "Ruolo IA", entries: t.ai_roles, color: "#334155" }))),
        h("section", { className: "panel" }, h("h2", null, "Dettaglio per coorte"), h(CohortTable, { cohorts: data.cohorts })),
        h("section", { className: "panel" }, h("h2", null, "Esempi"), h(Examples, { rows: data.examples })));
    }
    ReactDOM.createRoot(document.getElementById("root")).render(h(App));
  }
})();
