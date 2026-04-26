(function () {
  const h = React.createElement;
  const { useEffect, useMemo, useRef, useState } = React;

  const GROUP_COLORS = {
    "insegnanti-attuali": "#e76f51",
    "insegnanti-futuri": "#43aa8b",
    "studenti": "#3d8bfd",
    "_root": "#8aa0b8",
  };

  const PRAXIS_COLORS = {
    "expectations": "#f4a261",
    "skepticisms": "#b56576",
    "interpersonal-trust": "#6c5ce7",
    "practice-patterns": "#2a9d8f",
    "adequacy-of-support": "#ef476f",
    "readiness-beliefs": "#06d6a0",
    "_index": "#c7cfd8",
  };

  const FALLBACK_PALETTE = [
    "#e76f51", "#2a9d8f", "#577590", "#f4a261",
    "#43aa8b", "#6c5ce7", "#b56576", "#3d8bfd",
    "#ef476f", "#06d6a0",
  ];

  function colorFor(key, registry) {
    if (registry[key]) return registry[key];
    let hash = 0;
    for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) | 0;
    return FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length];
  }

  function trimmedEdge(a, b, extraStart, extraEnd) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    const ux = dx / dist;
    const uy = dy / dist;
    const start = (a.r || 0) + extraStart;
    const end = (b.r || 0) + extraEnd;
    return {
      x1: a.x + ux * start,
      y1: a.y + uy * start,
      x2: b.x - ux * end,
      y2: b.y - uy * end,
    };
  }

  function buildLayout(nodes, edges, width, height) {
    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
    const degree = {};
    nodes.forEach((n) => {
      degree[n.id] = 0;
    });
    edges.forEach((e) => {
      degree[e.source] = (degree[e.source] || 0) + 1;
      degree[e.target] = (degree[e.target] || 0) + 1;
    });

    const positions = {};
    const radius = Math.min(width, height) * 0.36;
    nodes.forEach((node, idx) => {
      const angle = (idx / Math.max(nodes.length, 1)) * Math.PI * 2;
      positions[node.id] = {
        x: width / 2 + radius * Math.cos(angle),
        y: height / 2 + radius * Math.sin(angle),
      };
    });

    const iterations = 260;
    const area = width * height;
    const k = Math.sqrt(area / Math.max(nodes.length, 1)) * 0.55;
    let temp = width * 0.09;

    for (let iter = 0; iter < iterations; iter++) {
      const disp = {};
      nodes.forEach((n) => {
        disp[n.id] = { x: 0, y: 0 };
      });

      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const pa = positions[a.id];
          const pb = positions[b.id];
          let dx = pa.x - pb.x;
          let dy = pa.y - pb.y;
          let dist = Math.sqrt(dx * dx + dy * dy) + 0.01;
          const force = (k * k) / dist;
          dx /= dist;
          dy /= dist;
          disp[a.id].x += dx * force;
          disp[a.id].y += dy * force;
          disp[b.id].x -= dx * force;
          disp[b.id].y -= dy * force;
        }
      }

      edges.forEach((edge) => {
        const source = edge.source;
        const target = edge.target;
        const ps = positions[source];
        const pt = positions[target];
        if (!ps || !pt) return;
        let dx = ps.x - pt.x;
        let dy = ps.y - pt.y;
        let dist = Math.sqrt(dx * dx + dy * dy) + 0.01;
        const force = (dist * dist) / k;
        dx /= dist;
        dy /= dist;
        disp[source].x -= dx * force;
        disp[source].y -= dy * force;
        disp[target].x += dx * force;
        disp[target].y += dy * force;
      });

      nodes.forEach((node) => {
        const d = disp[node.id];
        let dx = d.x;
        let dy = d.y;
        const dist = Math.sqrt(dx * dx + dy * dy) + 0.01;
        dx = (dx / dist) * Math.min(dist, temp);
        dy = (dy / dist) * Math.min(dist, temp);
        positions[node.id].x = Math.max(40, Math.min(width - 40, positions[node.id].x + dx));
        positions[node.id].y = Math.max(40, Math.min(height - 40, positions[node.id].y + dy));
      });

      temp *= 0.985;
    }

    return nodes.map((node) => ({
      ...node,
      x: positions[node.id].x,
      y: positions[node.id].y,
      r: 5 + Math.min(22, Math.sqrt((degree[node.id] || 1) + 1) * 2.2),
    }));
  }

  function App() {
    const [data, setData] = useState(null);
    const [error, setError] = useState("");
    const [section, setSection] = useState("ALL");
    const [query, setQuery] = useState("");
    const [selectedNode, setSelectedNode] = useState(null);
    const [hoveredNode, setHoveredNode] = useState(null);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [dragging, setDragging] = useState(false);
    const dragRef = useRef(null);

    const width = 1320;
    const height = 720;

    const navLinks = h(
      "p",
      { className: "header-nav" },
      h(
        "a",
        { href: "../../", className: "header-nav-link" },
        "Home Quartz"
      ),
      h("span", { className: "header-nav-sep" }, "|"),
      h(
        "a",
        { href: "../", className: "header-nav-link" },
        "PRAXIS Graph"
      ),
      h("span", { className: "header-nav-sep" }, "|"),
      h("span", { className: "header-nav-current" }, "Wiki Graph")
    );

    useEffect(() => {
      fetch("./wiki-graph-data.json")
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.json();
        })
        .then((payload) => setData(payload))
        .catch((err) => setError(`Errore caricamento: ${err.message}`));
    }, []);

    const sections = useMemo(() => {
      if (!data) return [];
      return Object.keys(data.sections || {}).sort((a, b) => a.localeCompare(b, "it"));
    }, [data]);
    const groups = useMemo(() => {
      if (!data) return [];
      return Object.keys(data.groups || {}).sort((a, b) => a.localeCompare(b, "it"));
    }, [data]);
    const praxisElements = useMemo(() => {
      if (!data) return [];
      return Object.keys(data.praxis_elements || {}).sort((a, b) => a.localeCompare(b, "it"));
    }, [data]);

    const normalizedQuery = query.trim().toLowerCase();

    const filtered = useMemo(() => {
      if (!data) return { nodes: [], edges: [] };
      const baseNodes = data.nodes || [];
      const nodes = baseNodes.filter((node) => {
        const okSection = section === "ALL" || node.section === section;
        if (!okSection) return false;
        if (!normalizedQuery) return true;
        return (
          node.title.toLowerCase().includes(normalizedQuery) ||
          node.id.toLowerCase().includes(normalizedQuery) ||
          node.path.toLowerCase().includes(normalizedQuery)
        );
      });
      const nodeSet = new Set(nodes.map((n) => n.id));
      const edges = (data.edges || []).filter(
        (edge) => nodeSet.has(edge.source) && nodeSet.has(edge.target)
      );
      return { nodes, edges };
    }, [data, section, normalizedQuery]);

    const laidOut = useMemo(
      () => buildLayout(filtered.nodes, filtered.edges, width, height),
      [filtered.nodes, filtered.edges]
    );
    const byId = useMemo(
      () => Object.fromEntries(laidOut.map((n) => [n.id, n])),
      [laidOut]
    );
    const edgeMax = Math.max(...filtered.edges.map((e) => e.weight), 1);

    const nodeLinkedToSelected = useMemo(() => {
      if (!selectedNode) return new Set();
      const set = new Set([selectedNode]);
      filtered.edges.forEach((edge) => {
        if (edge.source === selectedNode) set.add(edge.target);
        if (edge.target === selectedNode) set.add(edge.source);
      });
      return set;
    }, [filtered.edges, selectedNode]);

    function resetView() {
      setZoom(1);
      setPan({ x: 0, y: 0 });
    }

    function zoomStep(delta) {
      setZoom((z) => Math.max(0.35, Math.min(3.2, z + delta)));
    }

    function onWheel(evt) {
      evt.preventDefault();
      const delta = evt.deltaY < 0 ? 0.12 : -0.12;
      zoomStep(delta);
    }

    function onPointerDown(evt) {
      dragRef.current = { x: evt.clientX, y: evt.clientY, panX: pan.x, panY: pan.y };
      setDragging(true);
    }
    function onPointerMove(evt) {
      if (!dragRef.current) return;
      const dx = evt.clientX - dragRef.current.x;
      const dy = evt.clientY - dragRef.current.y;
      setPan({ x: dragRef.current.panX + dx, y: dragRef.current.panY + dy });
    }
    function onPointerUp() {
      dragRef.current = null;
      setDragging(false);
    }

    if (error) {
      return h("div", { className: "page" }, h("div", { className: "panel head" }, h("h1", null, "Wiki Graph"), h("p", null, error), navLinks));
    }
    if (!data) {
      return h("div", { className: "page" }, h("div", { className: "panel head" }, h("h1", null, "Wiki Graph"), h("p", null, "Caricamento dati..."), navLinks));
    }

    return h(
      "div",
      { className: "page" },
      h(
        "div",
        { className: "panel head" },
        h("h1", null, "Grafo Wiki"),
        h(
          "p",
          null,
          "Solo pagine in 01-wiki/ e solo link markdown. Un nodo per pagina."
        ),
        navLinks
      ),
      h(
        "div",
        { className: "panel" },
        h(
          "div",
          { className: "controls" },
          h("div", null,
            h("label", { htmlFor: "wiki-search" }, "Cerca pagina"),
            h("input", {
              id: "wiki-search",
              type: "text",
              value: query,
              placeholder: "Titolo, path, slug...",
              onChange: (evt) => setQuery(evt.target.value),
            })
          ),
          h("div", null,
            h("label", { htmlFor: "wiki-section" }, "Sezione"),
            h(
              "select",
              {
                id: "wiki-section",
                value: section,
                onChange: (evt) => {
                  setSection(evt.target.value);
                  setSelectedNode(null);
                },
              },
              h("option", { value: "ALL" }, "Tutte"),
              sections.map((s) =>
                h("option", { key: s, value: s }, `${s} (${data.sections[s]})`)
              )
            )
          ),
          h("div", { className: "meta-chip" }, `Nodi: ${laidOut.length} · Archi: ${filtered.edges.length}`),
          h(
            "div",
            { className: "btns" },
            h("button", { type: "button", onClick: () => zoomStep(-0.16), title: "Zoom out" }, "−"),
            h("button", { type: "button", onClick: () => zoomStep(0.16), title: "Zoom in" }, "+"),
            h("button", { type: "button", onClick: resetView, title: "Reset view" }, "Reset")
          )
        ),
        h(
          "div",
          { className: "legend" },
          h("strong", { style: { fontSize: "0.82rem", color: "#4b5b6f", marginRight: 6 } }, "Gruppo (bordo):"),
          groups.map((g) =>
            h(
              "div",
              { key: `g-${g}`, className: "legend-item" },
              h("span", { className: "sw", style: { background: "#fff", border: `3px solid ${colorFor(g, GROUP_COLORS)}` } }),
              h("span", null, `${g} · ${data.groups[g]}`)
            )
          )
        ),
        h(
          "div",
          { className: "legend", style: { marginTop: 6 } },
          h("strong", { style: { fontSize: "0.82rem", color: "#4b5b6f", marginRight: 6 } }, "Praxis (riempimento):"),
          praxisElements.map((p) =>
            h(
              "div",
              { key: `p-${p}`, className: "legend-item" },
              h("span", { className: "sw", style: { background: colorFor(p, PRAXIS_COLORS) } }),
              h("span", null, `${p} · ${data.praxis_elements[p]}`)
            )
          )
        ),
        h(
          "div",
          { className: "graph-box" },
          h(
            "svg",
            {
              className: dragging ? "dragging" : "",
              role: "img",
              viewBox: `0 0 ${width} ${height}`,
              onWheel,
              onPointerDown,
              onPointerMove,
              onPointerUp,
              onPointerLeave: onPointerUp,
            },
            h(
              "defs",
              null,
              h(
                "marker",
                {
                  id: "edge-arrow",
                  viewBox: "0 0 10 10",
                  refX: 9,
                  refY: 5,
                  markerWidth: 7,
                  markerHeight: 7,
                  orient: "auto-start-reverse",
                },
                h("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#7389a3", fillOpacity: 0.72 })
              )
            ),
            h(
              "g",
              {
                transform: `translate(${pan.x},${pan.y}) scale(${zoom})`,
              },
              filtered.edges.map((edge) => {
                const a = byId[edge.source];
                const b = byId[edge.target];
                if (!a || !b) return null;
                const active =
                  !selectedNode ||
                  edge.source === selectedNode ||
                  edge.target === selectedNode;
                const line = trimmedEdge(a, b, 4, 8);
                return h("line", {
                  key: `${edge.source}-${edge.target}`,
                  className: "edge",
                  ...line,
                  strokeWidth: 0.9 + (edge.weight / edgeMax) * 3.5,
                  strokeOpacity: active ? 0.42 : 0.07,
                  markerEnd: active ? "url(#edge-arrow)" : undefined,
                });
              }),
              laidOut.map((node) => {
                const active =
                  !selectedNode || selectedNode === node.id || nodeLinkedToSelected.has(node.id);
                const showLabel = hoveredNode === node.id || selectedNode === node.id;
                return h(
                  "g",
                  {
                    key: node.id,
                    style: { cursor: "pointer" },
                    onClick: () => setSelectedNode(selectedNode === node.id ? null : node.id),
                    onPointerEnter: () => setHoveredNode(node.id),
                    onPointerLeave: () => setHoveredNode((cur) => (cur === node.id ? null : cur)),
                  },
                  h("circle", {
                    className: "node",
                    cx: node.x,
                    cy: node.y,
                    r: node.r,
                    fill: colorFor(node.praxis || "_index", PRAXIS_COLORS),
                    fillOpacity: active ? 0.9 : 0.2,
                    stroke: colorFor(node.group || "_root", GROUP_COLORS),
                    strokeWidth: 2.5,
                  }),
                  showLabel
                    ? h(
                        "text",
                        {
                          className: "node-label",
                          x: node.x + node.r + 6,
                          y: node.y - 2,
                          textAnchor: "start",
                        },
                        node.title
                      )
                    : null,
                  h("title", null, `${node.title}\n${node.path}\ngruppo: ${node.group} · praxis: ${node.praxis}`)
                );
              })
            )
          )
        ),
        h(
          "div",
          { className: "note" },
          "Interazione: rotella = zoom, trascina = pan, Reset = centra. Etichette visibili solo al passaggio del mouse o su nodo selezionato."
        )
      )
    );
  }

  ReactDOM.createRoot(document.getElementById("app")).render(h(App));
})();
