(function () {
  const h = React.createElement;
  const { useEffect, useMemo, useState } = React;

  const DIMENSION_COLORS = {
    A: "#D55E00",
    I: "#0072B2",
    P: "#009E73",
    R: "#E69F00",
    S: "#CC79A7",
    X: "#56B4E9",
  };

  const SCOPE_COLORS = {
    ALL: "#334155",
    Studenti: "#2563EB",
    "Insegnanti in servizio": "#0F766E",
    "Insegnanti pre-service": "#B45309",
    Sconosciuto: "#6B7280",
  };

  const FALLBACK_COLOR = "#60748a";
  const CROSS_EDGE_COLOR = "#9ab0c8";

  function fmtPct(value) {
    return `${value.toFixed(1)}%`;
  }

  function clamp01(value) {
    return Math.max(0, Math.min(1, value));
  }

  function hexToRgb(hex) {
    if (!hex || typeof hex !== "string") return null;
    const clean = hex.trim().replace("#", "");
    if (clean.length !== 6 || /[^0-9a-f]/i.test(clean)) return null;
    return {
      r: parseInt(clean.slice(0, 2), 16),
      g: parseInt(clean.slice(2, 4), 16),
      b: parseInt(clean.slice(4, 6), 16),
    };
  }

  function blendHex(baseHex, mixHex, ratio) {
    const base = hexToRgb(baseHex);
    const mix = hexToRgb(mixHex);
    if (!base || !mix) return baseHex || mixHex || FALLBACK_COLOR;
    const t = clamp01(ratio);
    const r = Math.round(base.r + (mix.r - base.r) * t);
    const g = Math.round(base.g + (mix.g - base.g) * t);
    const b = Math.round(base.b + (mix.b - base.b) * t);
    return `#${[r, g, b]
      .map((n) => n.toString(16).padStart(2, "0"))
      .join("")}`;
  }

  function lightenColor(hex, amount) {
    return blendHex(hex, "#ffffff", amount);
  }

  function colorForCode(code) {
    if (!code || typeof code !== "string") return FALLBACK_COLOR;
    return DIMENSION_COLORS[code[0]] || FALLBACK_COLOR;
  }

  function colorForScope(scope) {
    if (!scope || typeof scope !== "string") return SCOPE_COLORS.ALL;
    return SCOPE_COLORS[scope] || SCOPE_COLORS.Sconosciuto;
  }

  function GraphView(props) {
    const { nodes, edges, minEdgeWeight, selectedNode, onSelectNode, scopeColor } = props;
    const width = 860;
    const height = 560;
    const cx = width / 2;
    const cy = height / 2;
    const radius = 190;

    const maxNode = Math.max(...nodes.map((n) => n.count), 1);
    const maxEdge = Math.max(...edges.map((e) => e.weight), 1);

    const laidOut = nodes.map((node, idx) => {
      const angle = (idx / Math.max(nodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
      const x = cx + radius * Math.cos(angle);
      const y = cy + radius * Math.sin(angle);
      const r = 20 + (node.count / maxNode) * 32;
      return { ...node, x, y, r };
    });
    const byId = Object.fromEntries(laidOut.map((n) => [n.id, n]));

    const visibleEdges = edges.filter((edge) => edge.weight >= minEdgeWeight);
    const topLabel = (text, maxChars) =>
      text.length > maxChars ? `${text.slice(0, maxChars - 1)}…` : text;

    return h(
      "div",
      { className: "graph-shell" },
      h(
        "svg",
        { width, height, viewBox: `0 0 ${width} ${height}`, role: "img" },
        h("defs", null,
          h("linearGradient", { id: "bgLine", x1: "0%", y1: "0%", x2: "100%", y2: "100%" },
            h("stop", { offset: "0%", stopColor: "#d6e4f5" }),
            h("stop", { offset: "100%", stopColor: "#bdd9cf" })
          )
        ),
        visibleEdges.map((edge) => {
          const left = byId[edge.source];
          const right = byId[edge.target];
          if (!left || !right) return null;
          const active =
            !selectedNode || selectedNode === edge.source || selectedNode === edge.target;
          return h("line", {
            key: `${edge.source}-${edge.target}`,
            x1: left.x,
            y1: left.y,
            x2: right.x,
            y2: right.y,
            stroke: "url(#bgLine)",
            strokeWidth: 1.4 + (edge.weight / maxEdge) * 9,
            strokeOpacity: active ? 0.85 : 0.18,
            strokeLinecap: "round",
          });
        }),
        laidOut.map((node) => {
          const active = !selectedNode || selectedNode === node.id;
          const dimensionColor = DIMENSION_COLORS[node.id] || FALLBACK_COLOR;
          return h(
            "g",
            {
              key: node.id,
              onClick: () => onSelectNode(selectedNode === node.id ? null : node.id),
              style: { cursor: "pointer" },
            },
            h("circle", {
              cx: node.x,
              cy: node.y,
              r: node.r + 3.2,
              fill: lightenColor(scopeColor, 0.9),
              fillOpacity: active ? 0.98 : 0.5,
              stroke: scopeColor,
              strokeOpacity: active ? 0.9 : 0.45,
              strokeWidth: active ? 2.4 : 1.6,
            }),
            h("circle", {
              cx: node.x,
              cy: node.y,
              r: node.r,
              fill: dimensionColor,
              fillOpacity: active ? 0.94 : 0.3,
              stroke: blendHex(dimensionColor, "#0f1f30", 0.25),
              strokeOpacity: 0.42,
              strokeWidth: 1.5,
            }),
            h("text", {
              x: node.x,
              y: node.y + 5,
              className: "node-label",
              textAnchor: "middle",
            }, node.id),
            h("text", {
              x: node.x + (node.x > cx ? node.r + 18 : -(node.r + 18)),
              y: node.y - 6,
              className: "node-sub",
              textAnchor: node.x > cx ? "start" : "end",
            }, topLabel(node.label, 28)),
            h("text", {
              x: node.x + (node.x > cx ? node.r + 18 : -(node.r + 18)),
              y: node.y + 12,
              className: "node-sub",
              textAnchor: node.x > cx ? "start" : "end",
            }, `${node.count} occorrenze`)
          );
        })
      )
    );
  }

  function SubcodeGraphView(props) {
    const { subcodes, relations, selectedSubcode, onSelectSubcode, scopeColor } = props;
    const width = 860;
    const height = 520;
    const cx = width / 2;
    const cy = height / 2;
    const ring = 165;
    const maxNode = Math.max(...subcodes.map((n) => n.count), 1);
    const maxEdge = Math.max(...relations.map((r) => r.weight), 1);
    const dimensions = ["A", "I", "P", "R", "S", "X"];
    const grouped = Object.fromEntries(
      dimensions.map((dim) => [dim, subcodes.filter((node) => node.id.startsWith(dim))])
    );
    const nodes = [];
    dimensions.forEach((dim, dimIndex) => {
      const group = grouped[dim] || [];
      if (!group.length) return;
      const sectorCenter =
        -Math.PI / 2 + (dimIndex / Math.max(dimensions.length, 1)) * Math.PI * 2;
      const sectorSpan = ((Math.PI * 2) / Math.max(dimensions.length, 1)) * 0.78;
      group.forEach((node, idx) => {
        const ratio = group.length === 1 ? 0.5 : idx / (group.length - 1);
        const angle = sectorCenter - sectorSpan / 2 + ratio * sectorSpan;
        const radialBand = ring + (idx % 2) * 32;
        nodes.push({
          ...node,
          x: cx + radialBand * Math.cos(angle),
          y: cy + radialBand * Math.sin(angle),
          r: 9 + (node.count / maxNode) * 14,
        });
      });
    });
    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));

    return h(
      "div",
      { className: "subgraph-shell" },
      h(
        "svg",
        { width, height, viewBox: `0 0 ${width} ${height}`, role: "img" },
        dimensions.map((dim, dimIndex) => {
          const group = grouped[dim] || [];
          if (!group.length) return null;
          const angle =
            -Math.PI / 2 + (dimIndex / Math.max(dimensions.length, 1)) * Math.PI * 2;
          const x = cx + (ring + 82) * Math.cos(angle);
          const y = cy + (ring + 82) * Math.sin(angle);
          return h(
            "text",
            {
              key: `cap-${dim}`,
              className: "sub-dim-caption",
              x,
              y,
              textAnchor: "middle",
            },
            dim
          );
        }),
        relations.map((edge) => {
          const left = byId[edge.source];
          const right = byId[edge.target];
          if (!left || !right) return null;
          const active =
            !selectedSubcode ||
            selectedSubcode === edge.source ||
            selectedSubcode === edge.target;
          const sameDimension = edge.source[0] === edge.target[0];
          return h("line", {
            key: `${edge.source}-${edge.target}`,
            x1: left.x,
            y1: left.y,
            x2: right.x,
            y2: right.y,
            stroke: sameDimension ? colorForCode(edge.source) : CROSS_EDGE_COLOR,
            strokeWidth: 1 + (edge.weight / maxEdge) * 7,
            strokeOpacity: active ? 0.68 : 0.08,
            strokeLinecap: "round",
          });
        }),
        nodes.map((node) => {
          const active = !selectedSubcode || selectedSubcode === node.id;
          const baseColor = colorForCode(node.id);
          const subnodeColor = lightenColor(baseColor, 0.2);
          return (
          h(
            "g",
            {
              key: node.id,
              style: { cursor: "pointer" },
              onClick: () =>
                onSelectSubcode(selectedSubcode === node.id ? null : node.id),
            },
            h("circle", {
              cx: node.x,
              cy: node.y,
              r: node.r + 2,
              fill: lightenColor(scopeColor, 0.9),
              fillOpacity: active ? 0.96 : 0.52,
              stroke: scopeColor,
              strokeOpacity: active ? 0.88 : 0.46,
              strokeWidth: active ? 1.8 : 1.2,
            }),
            h("circle", {
              cx: node.x,
              cy: node.y,
              r: node.r,
              fill: subnodeColor,
              fillOpacity: active ? 0.95 : 0.34,
              stroke: baseColor,
              strokeOpacity: 0.72,
              strokeWidth: 1.1,
            }),
            h(
              "text",
              {
                x: node.x,
                y: node.y + 4,
                className: "sub-node-code",
                textAnchor: "middle",
                style: { fill: "#0f1f30" },
              },
              node.id
            ),
            h(
              "text",
              {
                x: node.x + (node.x > cx ? node.r + 12 : -(node.r + 12)),
                y: node.y - 2,
                className: "sub-node-label",
                textAnchor: node.x > cx ? "start" : "end",
              },
              `${node.count}`
            ),
            h("title", null, `${node.id}: ${node.label}`)
          )
        );
      })
      )
    );
  }

  function App() {
    const [payload, setPayload] = useState(null);
    const [scope, setScope] = useState("ALL");
    const [minEdgeWeight, setMinEdgeWeight] = useState(1);
    const [selectedNode, setSelectedNode] = useState(null);
    const [subThemeDimension, setSubThemeDimension] = useState("ALL");
    const [subMinWeight, setSubMinWeight] = useState(3);
    const [maxSubNodes, setMaxSubNodes] = useState(80);
    const [selectedSubcode, setSelectedSubcode] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
      fetch("./praxis-graph-data.json")
        .then((res) => {
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }
          return res.json();
        })
        .then((data) => {
          setPayload(data);
          const keys = Object.keys(data.graphs || {});
          if (!keys.includes("ALL") && keys.length > 0) {
            setScope(keys[0]);
          }
        })
        .catch((err) => {
          setError(`Errore caricamento dati: ${err.message}`);
        });
    }, []);

    const scopes = useMemo(() => {
      if (!payload || !payload.graphs) return [];
      const keys = Object.keys(payload.graphs).filter((key) => {
        const graph = payload.graphs[key];
        return Array.isArray(graph?.nodes) && graph.nodes.length > 0;
      });
      return keys.sort((a, b) => {
        if (a === "ALL") return -1;
        if (b === "ALL") return 1;
        return a.localeCompare(b, "it");
      });
    }, [payload]);

    const graph = payload?.graphs?.[scope] || {
      nodes: [],
      edges: [],
      records_count: 0,
      items_count: 0,
      total_dimension_mentions: 0,
      top_dimensions: [],
      top_subcodes: [],
      dimension_to_subcodes: {},
      subcode_relations: [],
    };
    const scopeColor = colorForScope(scope);

    const maxEdgeWeight = Math.max(...graph.edges.map((e) => e.weight), 1);
    const edgesSorted = [...graph.edges].sort((a, b) => b.weight - a.weight).slice(0, 8);
    const selectedDetails = graph.nodes.find((n) => n.id === selectedNode) || null;
    const maxSubRelationWeight = Math.max(
      ...(graph.subcode_relations || []).map((r) => r.weight),
      1
    );
    const effectiveSubMinWeight = Math.min(subMinWeight, maxSubRelationWeight);
    const dimensionLabelMap = Object.fromEntries(
      graph.nodes.map((node) => [node.id, node.label])
    );
    const dimensionIds = graph.nodes.map((node) => node.id);
    const effectiveSubDimension =
      subThemeDimension === "AUTO"
        ? (selectedNode || dimensionIds[0] || null)
        : (subThemeDimension === "ALL" ? null : subThemeDimension);
    const subcodesPool = (
      effectiveSubDimension
        ? (graph.dimension_to_subcodes?.[effectiveSubDimension] || [])
        : (graph.subcodes || [])
    );
    const shownSubcodes = subcodesPool.slice(0, maxSubNodes);
    const maxSubcodeCount = Math.max(...shownSubcodes.map((row) => row.count), 1);
    const subgraphCodeSet = new Set(shownSubcodes.map((row) => row.id));
    const filteredSubRelations = (graph.subcode_relations || [])
      .filter((row) => {
        if (!subgraphCodeSet.has(row.source) || !subgraphCodeSet.has(row.target)) {
          return false;
        }
        if (row.weight < effectiveSubMinWeight) return false;
        if (!effectiveSubDimension) return true;
        return (
          row.source.startsWith(effectiveSubDimension) ||
          row.target.startsWith(effectiveSubDimension)
        );
      });
    const shownSubRelations = filteredSubRelations.slice(0, 20);

    const navLinks = h(
      "p",
      { className: "header-nav" },
      h(
        "a",
        { href: "../", className: "header-nav-link" },
        "Home Quartz"
      ),
      h("span", { className: "header-nav-sep" }, "|"),
      h("span", { className: "header-nav-current" }, "PRAXIS Graph"),
      h("span", { className: "header-nav-sep" }, "|"),
      h(
        "a",
        { href: "./wiki/", className: "header-nav-link" },
        "Wiki Graph"
      )
    );

    if (error) {
      return h(
        "div",
        { className: "page" },
        h("div", { className: "panel header" },
          h("h1", null, "PRAXIS Graph"),
          h("p", null, error),
          navLinks
        )
      );
    }

    if (!payload) {
      return h(
        "div",
        { className: "page" },
        h("div", { className: "panel header" },
          h("h1", null, "PRAXIS Graph"),
          h("p", null, "Caricamento in corso..."),
          navLinks
        )
      );
    }

    return h(
      "div",
      { className: "page" },
      h(
        "div",
        { className: "panel header" },
        h("h1", null, "PRAXIS Graph · Relazioni tra dimensioni"),
        h(
          "p",
          null,
          "Vista React affiancata a Quartz. Nodi = dimensioni, spessore archi = co-occorrenza nello stesso item."
        ),
        navLinks
      ),
      h(
        "div",
        { className: "row" },
        h(
          "div",
          { className: "panel" },
          h(
            "div",
            { className: "graph-with-controls vertical" },
            h(
              "div",
              { className: "graph-top-controls" },
              h(
                "div",
                { className: "controls-inline" },
                h(
                  "div",
                  { className: "sub-controls" },
                  h("label", { htmlFor: "scope" }, "Gruppo"),
                  h(
                    "select",
                    {
                      id: "scope",
                      value: scope,
                      onChange: (evt) => {
                        setScope(evt.target.value);
                        setSelectedNode(null);
                        setSubThemeDimension("ALL");
                        setSelectedSubcode(null);
                      },
                    },
                    scopes.map((name) =>
                      h("option", { key: name, value: name }, name === "ALL" ? "Tutti i gruppi" : name)
                    )
                  )
                ),
                h(
                  "div",
                  { className: "sub-controls" },
                  h("label", { htmlFor: "edge" }, `Soglia relazioni (>= ${minEdgeWeight})`),
                  h("input", {
                    id: "edge",
                    type: "range",
                    min: 1,
                    max: maxEdgeWeight,
                    step: 1,
                    value: minEdgeWeight,
                    onChange: (evt) => setMinEdgeWeight(Number(evt.target.value)),
                  })
                ),
                h(
                  "div",
                  {
                    className: "chip",
                    style: {
                      borderColor: scopeColor,
                      background: lightenColor(scopeColor, 0.9),
                      color: "#1f3347",
                    },
                  },
                  `${scope === "ALL" ? "Tutti i gruppi" : scope} · ${new Date(payload.meta.generated_at).toLocaleString("it-IT")}`
                )
              ),
              h(
                "div",
                { className: "kpi-grid" },
                h("div", { className: "kpi" }, h("div", { className: "n" }, graph.records_count), h("div", { className: "l" }, "Record")),
                h("div", { className: "kpi" }, h("div", { className: "n" }, graph.items_count), h("div", { className: "l" }, "Item con codici")),
                h("div", { className: "kpi" }, h("div", { className: "n" }, graph.total_dimension_mentions), h("div", { className: "l" }, "Menzioni dimensioni")),
                h("div", { className: "kpi" }, h("div", { className: "n" }, graph.edges.length), h("div", { className: "l" }, "Relazioni"))
              ),
              h(
                "div",
                { className: "legend", style: { gap: "6px" } },
                h(
                  "div",
                  { className: "legend-item", style: { fontWeight: 700, color: "#2b3b4c" } },
                  "Dimensioni PRAXIS"
                ),
                h("div", { className: "legend inline" },
                  graph.nodes.map((node) =>
                    h(
                      "div",
                      { className: "legend-item", key: `top-legend-${node.id}` },
                      h("span", {
                        className: "swatch",
                        style: { background: DIMENSION_COLORS[node.id] || FALLBACK_COLOR },
                      }),
                      h("span", null, `${node.id} · ${node.label}`)
                    )
                  )
                ),
                h(
                  "div",
                  { className: "legend-item", style: { fontWeight: 700, color: "#2b3b4c" } },
                  "Tipi soggetto"
                ),
                h("div", { className: "legend inline" },
                  Object.entries(SCOPE_COLORS).map(([name, color]) =>
                    h(
                      "div",
                      {
                        className: "legend-item",
                        key: `scope-legend-${name}`,
                        style: {
                          background: scope === name ? lightenColor(color, 0.86) : "#fff",
                          borderColor: scope === name ? color : "var(--border)",
                        },
                      },
                      h("span", {
                        className: "swatch",
                        style: { background: color },
                      }),
                      h("span", null, name === "ALL" ? "Tutti i gruppi" : name)
                    )
                  )
                )
              )
            ),
            h(
              "div",
              { className: "graph-main" },
              h(GraphView, {
                nodes: graph.nodes,
                edges: graph.edges,
                minEdgeWeight,
                selectedNode,
                onSelectNode: setSelectedNode,
                scopeColor,
              })
            )
          ),
          selectedDetails
            ? h(
                "div",
                { className: "help" },
                h("b", null, `Dettaglio ${selectedDetails.id} · ${selectedDetails.label}`),
                h(
                  "div",
                  { style: { marginTop: "6px" } },
                  selectedDetails.codes.map((entry) =>
                    h("div", { key: entry.code }, `${entry.code}: ${entry.description}`)
                  )
                )
              )
            : null,
          h(
            "h2",
            { style: { marginTop: "14px" } },
            effectiveSubDimension
              ? `Grafo sotto-temi ${effectiveSubDimension}`
              : "Grafo sotto-temi · tutte le dimensioni"
          ),
          h(
            "div",
            { className: "graph-with-controls vertical" },
            h(
              "div",
              { className: "graph-top-controls" },
              h(
                "div",
                { className: "controls-inline" },
                h(
                  "div",
                  { className: "sub-controls" },
                  h("label", { htmlFor: "sub-dimension" }, "Filtro sotto-temi"),
                  h(
                    "select",
                    {
                      id: "sub-dimension",
                      value: subThemeDimension,
                      onChange: (evt) => {
                        setSubThemeDimension(evt.target.value);
                        setSelectedSubcode(null);
                      },
                    },
                    h(
                      "option",
                      { value: "ALL" },
                      "Tutte le dimensioni insieme"
                    ),
                    h(
                      "option",
                      { value: "AUTO" },
                      "Automatico (usa il nodo selezionato)"
                    ),
                    dimensionIds.map((dim) =>
                      h(
                        "option",
                        { key: dim, value: dim },
                        `${dim} · ${dimensionLabelMap[dim] || dim}`
                      )
                    )
                  )
                ),
                h(
                  "div",
                  { className: "sub-controls" },
                  h(
                    "label",
                    { htmlFor: "sub-min-weight" },
                    `Peso minimo arco sotto-temi (>= ${effectiveSubMinWeight})`
                  ),
                  h("input", {
                    id: "sub-min-weight",
                    type: "range",
                    min: 1,
                    max: maxSubRelationWeight,
                    step: 1,
                    value: effectiveSubMinWeight,
                    onChange: (evt) => setSubMinWeight(Number(evt.target.value)),
                  })
                ),
                h(
                  "div",
                  { className: "sub-controls" },
                  h(
                    "label",
                    { htmlFor: "sub-max-nodes" },
                    `Numero nodi sotto-temi (fino a ${maxSubNodes})`
                  ),
                  h("input", {
                    id: "sub-max-nodes",
                    type: "range",
                    min: 8,
                    max: Math.max((graph.subcodes || []).length, 8),
                    step: 1,
                    value: Math.min(maxSubNodes, Math.max((graph.subcodes || []).length, 8)),
                    onChange: (evt) => setMaxSubNodes(Number(evt.target.value)),
                  })
                )
              )
            ),
            h(
              "div",
              { className: "graph-main" },
              shownSubcodes.length === 0
                ? h(
                    "div",
                    { className: "help" },
                    "Nessun sotto-tema disponibile per il grafo."
                  )
                : h(SubcodeGraphView, {
                    subcodes: shownSubcodes,
                    relations: filteredSubRelations,
                    selectedSubcode,
                    onSelectSubcode: setSelectedSubcode,
                    scopeColor,
                  })
            )
          ),
          h(
            "div",
            { className: "help" },
            `Nodi visibili: ${shownSubcodes.length} · Archi visibili: ${filteredSubRelations.length}`
          )
        ),
        h(
          "div",
          { className: "panel side" },
          h(
            "div",
            { className: "side-stack" },
            h(
              "section",
              { className: "side-section" },
              h("h2", null, "Dimensioni più presenti"),
              h(
                "div",
                { className: "rank" },
                graph.top_dimensions.map((row) =>
                  h(
                    "div",
                    { className: "rank-item", key: row.id },
                    h(
                      "div",
                      { className: "rank-head" },
                      h("span", { className: "rank-label" }, h("b", null, row.id), ` · ${row.label}`),
                      h("span", { className: "rank-value" }, `${row.count} · ${fmtPct(row.share)}`)
                    ),
                    h(
                      "div",
                      { className: "bar" },
                      h("span", {
                        style: {
                          width: `${row.share}%`,
                          background: DIMENSION_COLORS[row.id] || FALLBACK_COLOR,
                        },
                      })
                    )
                  )
                )
              )
            ),
            h(
              "section",
              { className: "side-section" },
              h("h2", null, "Sotto-temi"),
              h(
                "div",
                { className: "subcode-list" },
                shownSubcodes.length === 0
                  ? h(
                      "div",
                      { className: "help" },
                      "Nessun sotto-tema disponibile per il filtro scelto."
                    )
                  : shownSubcodes.map((row) =>
                      h(
                        "div",
                        { className: "subcode-item", key: row.id },
                        h(
                          "div",
                          { className: "subcode-head" },
                          h(
                            "span",
                            null,
                            h(
                              "span",
                              {
                                className: "code-badge",
                                style: { background: colorForCode(row.id) },
                              },
                              row.id
                            ),
                            ` · ${row.count}`
                          ),
                          h(
                            "span",
                            null,
                            fmtPct(
                              Number(
                                row.share_within_dimension ?? row.share ?? 0
                              )
                            )
                          )
                        ),
                        h(
                          "div",
                          { className: "bar" },
                          h("span", {
                            style: {
                              width: `${(row.count / maxSubcodeCount) * 100}%`,
                              background: colorForCode(row.id),
                            },
                          })
                        ),
                        h("div", { className: "subcode-label" }, row.label)
                      )
                    )
              )
            ),
            h(
              "section",
              { className: "side-section" },
              h("h2", null, "Relazioni tra dimensioni"),
              h(
                "div",
                { className: "rel-list" },
                edgesSorted.map((edge) =>
                  h(
                    "div",
                    { className: "rel-item", key: `${edge.source}-${edge.target}` },
                    h("span", null, `${edge.source} ↔ ${edge.target}`),
                    h("b", null, edge.weight)
                  )
                )
              )
            ),
            h(
              "section",
              { className: "side-section" },
              h("h2", null, "Relazioni tra sotto-temi"),
              h(
                "div",
                { className: "rel-list" },
                shownSubRelations.length === 0
                  ? h(
                      "div",
                      { className: "help" },
                      "Nessuna relazione tra sotto-temi con il filtro scelto."
                    )
                  : shownSubRelations.map((edge) =>
                      h(
                        "div",
                        { className: "rel-item", key: `${edge.source}-${edge.target}` },
                        h("span", null, `${edge.source} ↔ ${edge.target}`),
                        h("b", null, edge.weight)
                      )
                    )
              ),
              h(
                "div",
                { className: "help" },
                "Le etichette restano visibili. Clicca un nodo per filtrare i sotto-temi sulla dimensione selezionata."
              )
            )
          )
        )
      )
    );
  }

  ReactDOM.createRoot(document.getElementById("app")).render(h(App));
})();
