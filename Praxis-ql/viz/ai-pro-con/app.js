(function () {
  const h = React.createElement;
  const { useEffect, useState } = React;
  const colors = { pro: "#0f766e", con: "#b91c1c", mixed: "#3b82f6", none: "#64748b" };
  const label = (x) => String(x || "").replaceAll("_", " ");
  const num = (x) => Number(x || 0).toLocaleString("it-IT");
  const pct = (x, t) => (!t ? "0,0%" : `${((x / t) * 100).toLocaleString("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`);

  function BarChart({ title, entries, color }) {
    const rows = Object.entries(entries || {}).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]);
    const width = 680, left = 210, chartW = 360, rowH = 30, height = rows.length * rowH + 46;
    const max = Math.max(...rows.map(([, v]) => v), 1);
    return h("svg", { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
      h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#5b6678", fontWeight: 700 } }, title),
      rows.map(([k, v], i) => {
        const y = 26 + i * rowH, w = (v / max) * chartW;
        return h("g", { key: k },
          h("text", { x: 0, y: y + 13, style: { fontSize: 12, fill: "#172033" } }, label(k)),
          h("rect", { x: left, y, width: w, height: 15, fill: color, rx: 4 }),
          h("text", { x: left + w + 8, y: y + 12, style: { fontSize: 11, fill: "#5b6678" } }, num(v)));
      }));
  }

  function StanceByCohort({ cohorts }) {
    const order = ["misto", "solo_pro", "solo_contro", "nessuno"];
    const palette = { misto: colors.mixed, solo_pro: colors.pro, solo_contro: colors.con, nessuno: colors.none };
    const width = 700, left = 170, chartW = 390, rowH = 48, height = cohorts.length * rowH + 50;
    return h("svg", { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
      h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#5b6678", fontWeight: 700 } }, "Stance per coorte"),
      cohorts.map((c, i) => {
        let x = left; const y = 30 + i * rowH;
        return h("g", { key: c.cohort },
          h("text", { x: 0, y: y + 14, style: { fontSize: 12, fill: "#172033" } }, c.label),
          order.map((s) => {
            const v = c.stance[s] || 0, w = (v / c.items_total) * chartW;
            const r = h("rect", { key: s, x, y, width: w, height: 18, fill: palette[s], rx: 4 });
            x += w; return r;
          }),
          h("text", { x: left + chartW + 10, y: y + 14, style: { fontSize: 11, fill: "#5b6678" } },
            order.map((s) => pct(c.stance[s] || 0, c.items_total)).join(" / ")));
      }));
  }

  function CohortTable({ cohorts }) {
    return h("div", { className: "table-wrap" }, h("table", { className: "table" },
      h("thead", null, h("tr", null, ["Coorte", "N", "Misto", "Solo pro", "Solo contro", "Nessuno", "Pro", "Contro"].map((x) => h("th", { key: x }, x)))),
      h("tbody", null, cohorts.map((c) => h("tr", { key: c.cohort },
        h("td", null, c.label), h("td", null, num(c.items_total)),
        h("td", null, `${num(c.stance.misto || 0)} (${pct(c.stance.misto || 0, c.items_total)})`),
        h("td", null, `${num(c.stance.solo_pro || 0)} (${pct(c.stance.solo_pro || 0, c.items_total)})`),
        h("td", null, `${num(c.stance.solo_contro || 0)} (${pct(c.stance.solo_contro || 0, c.items_total)})`),
        h("td", null, `${num(c.stance.nessuno || 0)} (${pct(c.stance.nessuno || 0, c.items_total)})`),
        h("td", null, num(c.pros_total)), h("td", null, num(c.cons_total)))))));
  }

  function Examples({ rows }) {
    return h("div", { className: "examples" }, rows.map((r, i) => h("article", { className: "example", key: `${r.source_name}-${i}` },
      h("span", { className: "badge" }, `${label(r.stance)} - ${r.cohort_label}`),
      h("div", { className: "answer" }, r.answer || "-"),
      h("div", { className: "meta" }, `Pro: ${label(r.pro_categories) || "-"} | Contro: ${label(r.con_categories) || "-"}`),
      h("div", { className: "meta" }, `${r.source_name} | conf: ${r.confidence}`),
      h("div", { className: "meta" }, r.reason))));
  }

  function App() {
    const [data, setData] = useState(null), [error, setError] = useState("");
    useEffect(() => { fetch("./ai-pro-con-data.json").then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }).then(setData).catch((e) => setError(String(e))); }, []);
    if (error) return h("main", { className: "page" }, h("section", { className: "panel" }, error));
    if (!data) return h("main", { className: "page" }, h("section", { className: "panel" }, "Caricamento..."));
    const t = data.totals;
    return h("main", { className: "page" },
      h("section", { className: "panel" }, h("h1", null, "Pro e contro dell'IA - Qwen 3.5 9B"), h("p", null, "Estrazione item-level dalle domande pro/contro su educazione e studio."), h("div", { className: "nav" }, h("a", { href: "../" }, "Grafo PRAXIS"), h("a", { href: "../prompt-complexity/" }, "Prompt complexity"))),
      h("section", { className: "panel" }, h("h2", null, "Sintesi"), h("div", { className: "kpi-grid" },
        h("div", { className: "kpi" }, h("div", { className: "n" }, num(t.items_total)), h("div", { className: "l" }, "Item")),
        h("div", { className: "kpi" }, h("div", { className: "n", style: { color: colors.mixed } }, `${pct(t.stance.misto || 0, t.items_total)}`), h("div", { className: "l" }, "Misto")),
        h("div", { className: "kpi" }, h("div", { className: "n", style: { color: colors.pro } }, num(t.pros_total)), h("div", { className: "l" }, "Pro estratti")),
        h("div", { className: "kpi" }, h("div", { className: "n", style: { color: colors.con } }, num(t.cons_total)), h("div", { className: "l" }, "Contro estratti")),
        h("div", { className: "kpi" }, h("div", { className: "n" }, num(data.failures)), h("div", { className: "l" }, "Failure script")),
        h("div", { className: "kpi" }, h("div", { className: "n" }, t.avg_confidence.toLocaleString("it-IT")), h("div", { className: "l" }, "Confidence media")))),
      h("section", { className: "row" }, h("div", { className: "panel" }, h(StanceByCohort, { cohorts: data.cohorts })), h("div", { className: "panel" }, h(BarChart, { title: "Categorie pro", entries: t.pro_categories, color: colors.pro }))),
      h("section", { className: "row" }, h("div", { className: "panel" }, h(BarChart, { title: "Categorie contro", entries: t.con_categories, color: colors.con })), h("div", { className: "panel" }, h("h2", null, "Dettaglio per coorte"), h(CohortTable, { cohorts: data.cohorts }))),
      h("section", { className: "panel" }, h("h2", null, "Esempi"), h(Examples, { rows: data.examples })));
  }
  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
