(function () {
  const h = React.createElement;
  const { useEffect, useMemo, useState } = React;

  const COLORS = {
    positive: "#1f7a48",
    neutral: "#4b5f76",
    negative: "#b63a3a",
    emotion: "#8b5cf6",
  };

  function pct(v, total) {
    if (!total) return "0.0%";
    return `${((v / total) * 100).toFixed(1)}%`;
  }

  function num(v) {
    return Number(v).toLocaleString("it-IT");
  }

  function dec6(v) {
    return Number(v).toLocaleString("it-IT", {
      minimumFractionDigits: 6,
      maximumFractionDigits: 6,
    });
  }

  function parseTopEmotions(text) {
    if (!text) return [];
    return String(text)
      .split("|")
      .map((chunk) => chunk.trim())
      .filter(Boolean)
      .map((chunk) => {
        const [label, count] = chunk.split(":");
        return { label: (label || "").trim(), count: Number(count) || 0 };
      })
      .filter((item) => item.label);
  }

  function scoreColor(value) {
    if (value > 0.02) return COLORS.positive;
    if (value < -0.02) return COLORS.negative;
    return COLORS.neutral;
  }

  function StackedBars({ cohorts }) {
    const width = 560;
    const rowH = 42;
    const pad = 18;
    const left = 160;
    const chartW = width - left - pad;
    const height = cohorts.length * rowH + 56;

    return h(
      "svg",
      { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
      h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#4d6673", fontWeight: 700 } }, "Distribuzione sentiment per coorte"),
      cohorts.map((c, i) => {
        const y = 30 + i * rowH;
        const total = c.items_total;
        const wPos = (c.positive / total) * chartW;
        const wNeu = (c.neutral / total) * chartW;
        const wNeg = chartW - wPos - wNeu;

        return h(
          "g",
          { key: c.cohort },
          h("text", { x: 0, y: y + 14, style: { fontSize: 12, fill: "#18323f" } }, c.label),
          h("rect", { x: left, y, width: wPos, height: 16, fill: COLORS.positive, rx: 4 }),
          h("rect", { x: left + wPos, y, width: wNeu, height: 16, fill: COLORS.neutral }),
          h("rect", { x: left + wPos + wNeu, y, width: wNeg, height: 16, fill: COLORS.negative, rx: 4 }),
          h("text", { x: left + chartW + 8, y: y + 13, style: { fontSize: 11, fill: "#4d6673" } }, `${pct(c.positive, total)} / ${pct(c.neutral, total)} / ${pct(c.negative, total)}`)
        );
      })
    );
  }

  function EmotionTotalsBars({ emotionTotals }) {
    const entries = Object.entries(emotionTotals || {}).sort((a, b) => b[1] - a[1]);
    const width = 640;
    const rowH = 30;
    const pad = 16;
    const left = 190;
    const chartW = width - left - pad;
    const height = entries.length * rowH + 44;
    const max = Math.max(...entries.map((item) => item[1]), 1);

    return h(
      "svg",
      { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
      h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#4d6673", fontWeight: 700 } }, "Frequenza emozioni (totale corpus)"),
      entries.map(([label, value], i) => {
        const y = 24 + i * rowH;
        const bar = (value / max) * chartW;
        return h(
          "g",
          { key: label },
          h("text", { x: 0, y: y + 13, style: { fontSize: 12, fill: "#18323f" } }, label),
          h("rect", { x: left, y, width: bar, height: 14, fill: COLORS.emotion, rx: 4 }),
          h("text", { x: left + bar + 8, y: y + 12, style: { fontSize: 11, fill: "#4d6673" } }, num(value))
        );
      })
    );
  }

  function EmotionTopByCohort({ cohorts }) {
    return h(
      "div",
      { className: "emotion-cards" },
      cohorts.map((cohort) =>
        h(
          "article",
          { className: "emotion-card", key: cohort.cohort },
          h("h3", null, cohort.label),
          h("p", null, `Emozioni totali: ${num(cohort.emotions_total)} | Avg per item: ${dec6(cohort.avg_emotions_per_item)}`),
          h(
            "ul",
            { className: "emotion-list" },
            parseTopEmotions(cohort.top_emotions).map((emotion) =>
              h(
                "li",
                { key: `${cohort.cohort}-${emotion.label}` },
                `${emotion.label}: ${num(emotion.count)}`
              )
            )
          )
        )
      )
    );
  }

  function ScoreConfidenceChart({ cohorts }) {
    const width = 560;
    const height = 220;
    const left = 56;
    const right = 20;
    const top = 24;
    const bottom = 34;
    const innerW = width - left - right;
    const innerH = height - top - bottom;

    const n = cohorts.length;
    const step = innerW / Math.max(n - 1, 1);

    function x(i) { return left + i * step; }
    function yScore(v) {
      const min = -0.2;
      const max = 0.2;
      const t = Math.max(0, Math.min(1, (v - min) / (max - min)));
      return top + (1 - t) * innerH;
    }
    function yConf(v) {
      const min = 0.82;
      const max = 0.92;
      const t = Math.max(0, Math.min(1, (v - min) / (max - min)));
      return top + (1 - t) * innerH;
    }

    const scorePath = cohorts
      .map((c, i) => `${i === 0 ? "M" : "L"}${x(i)} ${yScore(c.avg_score)}`)
      .join(" ");
    const confPath = cohorts
      .map((c, i) => `${i === 0 ? "M" : "L"}${x(i)} ${yConf(c.avg_confidence)}`)
      .join(" ");

    return h(
      "svg",
      { width: "100%", viewBox: `0 0 ${width} ${height}`, role: "img" },
      h("text", { x: 0, y: 14, style: { fontSize: 12, fill: "#4d6673", fontWeight: 700 } }, "Avg score e confidence per coorte"),
      [0.82, 0.85, 0.88, 0.91].map((t) =>
        h("line", {
          key: `grid-${t}`,
          x1: left,
          y1: yConf(t),
          x2: width - right,
          y2: yConf(t),
          stroke: "#e0e9e7",
          strokeWidth: 1,
        })
      ),
      h("path", { d: scorePath, fill: "none", stroke: "#0f766e", strokeWidth: 3 }),
      h("path", { d: confPath, fill: "none", stroke: "#334155", strokeWidth: 3, strokeDasharray: "6 4" }),
      cohorts.map((c, i) =>
        h(
          "g",
          { key: c.cohort },
          h("circle", { cx: x(i), cy: yScore(c.avg_score), r: 4, fill: "#0f766e" }),
          h("circle", { cx: x(i), cy: yConf(c.avg_confidence), r: 4, fill: "#334155" }),
          h("text", { x: x(i), y: height - 8, textAnchor: "middle", style: { fontSize: 11, fill: "#4d6673" } }, c.label)
        )
      )
    );
  }

  function App() {
    const [data, setData] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
      fetch("./sentiment-data.json")
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.json();
        })
        .then((payload) => setData(payload))
        .catch((err) => setError(String(err)));
    }, []);

    const totals = data?.totals;
    const cohorts = data?.cohorts || [];
    const emotionTotals = data?.emotion_totals || {};

    const bestScore = useMemo(() => {
      if (!cohorts.length) return null;
      return [...cohorts].sort((a, b) => b.avg_score - a.avg_score)[0];
    }, [cohorts]);

    const topEmotion = useMemo(() => {
      const entries = Object.entries(emotionTotals).sort((a, b) => b[1] - a[1]);
      return entries.length ? { label: entries[0][0], count: entries[0][1] } : null;
    }, [emotionTotals]);

    if (error) {
      return h("div", { className: "page" }, h("div", { className: "panel" }, `Errore caricamento dati: ${error}`));
    }
    if (!data) {
      return h("div", { className: "page" }, h("div", { className: "panel" }, "Caricamento dashboard..."));
    }

    return h(
      "div",
      { className: "page" },
      h(
        "section",
        { className: "panel" },
        h("h1", null, "Sentiment + Emozioni Dashboard PRAXIS - Qwen 3.5 9B"),
        h("p", null, "Sintesi visiva item-level su sentiment ed emozioni per le tre coorti (solo campo risposta A, modalita no-thinking)."),
        h(
          "div",
          { className: "nav" },
          h("a", { href: "../" }, "Apri grafo PRAXIS"),
          h("a", { href: "../../01-wiki/20-labels/sentiment-qwen3-5-9b.md" }, "Vai alla scheda wiki risultati")
        )
      ),
      h(
        "section",
        { className: "panel" },
        h("h2", null, "Totale corpus analizzato"),
        h(
          "div",
          { className: "kpi-grid" },
          h("div", { className: "kpi" }, h("div", { className: "n" }, num(totals.items_total)), h("div", { className: "l" }, "Item totali")),
          h("div", { className: "kpi pos" }, h("div", { className: "n" }, num(totals.positive)), h("div", { className: "l" }, "Positive")),
          h("div", { className: "kpi neu" }, h("div", { className: "n" }, num(totals.neutral)), h("div", { className: "l" }, "Neutral")),
          h("div", { className: "kpi neg" }, h("div", { className: "n" }, num(totals.negative)), h("div", { className: "l" }, "Negative")),
          h("div", { className: "kpi" }, h("div", { className: "n" }, num(totals.emotions_total)), h("div", { className: "l" }, "Emozioni totali")),
          h("div", { className: "kpi" }, h("div", { className: "n", style: { color: scoreColor(totals.avg_score_weighted) } }, dec6(totals.avg_score_weighted)), h("div", { className: "l" }, "Avg score pesata")),
          h("div", { className: "kpi" }, h("div", { className: "n" }, dec6(totals.avg_confidence_weighted)), h("div", { className: "l" }, "Avg confidence pesata")),
          h("div", { className: "kpi" }, h("div", { className: "n" }, dec6(totals.avg_emotions_per_item)), h("div", { className: "l" }, "Avg emozioni/item"))
        ),
        h(
          "div",
          { className: "legend" },
          h("span", null, h("span", { className: "dot", style: { background: COLORS.positive } }), "Positive"),
          h("span", null, h("span", { className: "dot", style: { background: COLORS.neutral } }), "Neutral"),
          h("span", null, h("span", { className: "dot", style: { background: COLORS.negative } }), "Negative"),
          h("span", null, h("span", { className: "dot", style: { background: COLORS.emotion } }), "Emozioni")
        )
      ),
      h(
        "section",
        { className: "row" },
        h("div", { className: "panel" }, h(StackedBars, { cohorts })),
        h("div", { className: "panel" }, h(ScoreConfidenceChart, { cohorts }))
      ),
      h(
        "section",
        { className: "row" },
        h("div", { className: "panel" }, h(EmotionTotalsBars, { emotionTotals })),
        h(
          "div",
          { className: "panel" },
          h("h2", null, "Top emozioni per coorte"),
          h(EmotionTopByCohort, { cohorts })
        )
      ),
      h(
        "section",
        { className: "panel" },
        h("h2", null, "Dettaglio numerico per coorte"),
        h(
          "div",
          { className: "table-wrap" },
        h(
          "table",
          { className: "table" },
          h("thead", null,
            h("tr", null,
              h("th", null, "Coorte"),
              h("th", null, "Item"),
              h("th", null, "Positive"),
              h("th", null, "Neutral"),
              h("th", null, "Negative"),
              h("th", null, "Emozioni totali"),
              h("th", null, "Avg emozioni/item"),
              h("th", null, "Avg score"),
              h("th", null, "Avg confidence"),
              h("th", null, "Top emozioni")
            )
          ),
          h("tbody", null,
            cohorts.map((c) =>
              h("tr", { key: c.cohort },
                h("td", null, c.label),
                h("td", null, num(c.items_total)),
                h("td", null, `${num(c.positive)} (${pct(c.positive, c.items_total)})`),
                h("td", null, `${num(c.neutral)} (${pct(c.neutral, c.items_total)})`),
                h("td", null, `${num(c.negative)} (${pct(c.negative, c.items_total)})`),
                h("td", null, num(c.emotions_total)),
                h("td", null, dec6(c.avg_emotions_per_item)),
                h("td", { style: { color: scoreColor(c.avg_score), fontWeight: 700 } }, dec6(c.avg_score)),
                h("td", null, dec6(c.avg_confidence)),
                h(
                  "td",
                  null,
                  parseTopEmotions(c.top_emotions)
                    .map((emotion) => `${emotion.label}: ${num(emotion.count)}`)
                    .join(", ")
                )
              )
            )
          )
        )
        )
      ),
      h(
        "section",
        { className: "panel note" },
        h("h2", null, "Spiegazione rapida"),
        h("p", null, "La classificazione e item-per-item e usa solo il testo della risposta (campo A). Domande e metadati sono esclusi dal prompt."),
        h("p", null, `La coorte con avg score piu alto e ${bestScore ? bestScore.label : "n/d"}. L'emozione piu frequente nel corpus e ${topEmotion ? `${topEmotion.label} (${num(topEmotion.count)})` : "n/d"}.`),
        h("p", null, "Per audit completo consultare i CSV/JSONL in 04-label/labels/ollama-qwen3-5-9b-sentiment-emotions.")
      )
    );
  }

  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
