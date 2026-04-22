#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
DEFAULT_INPUT_DIR = ROOT_DIR / "04-label" / "labels" / "ollama-gemma4"
DEFAULT_OUTPUT_FILE = DEFAULT_INPUT_DIR / "viewer.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una vista HTML dei file JSON prodotti da label_raw_with_ollama.py."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--summary-file", type=Path)
    parser.add_argument("--failures-file", type=Path)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--title", default="PRAXIS Label Viewer")
    return parser.parse_args()


def _ensure_record_defaults(record: dict[str, Any]) -> dict[str, Any]:
    record.setdefault("source_name", "")
    record.setdefault("group", "Sconosciuto")
    record.setdefault("record_code", "")
    record.setdefault("model", "")
    record.setdefault("generated_at", "")
    record.setdefault("record_dimensions", [])
    record.setdefault("record_subcodes", [])
    record.setdefault("record_note", "")
    record.setdefault("code_counts", {})
    record.setdefault("items", [])
    return record


def load_records(input_dir: Path, summary_file: Path | None) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []

    chosen_summary = summary_file or (input_dir / "summary.jsonl")
    if chosen_summary.exists():
        for line_no, line in enumerate(chosen_summary.read_text(encoding="utf-8").splitlines(), start=1):
            content = line.strip()
            if not content:
                continue
            try:
                records.append(_ensure_record_defaults(json.loads(content)))
            except json.JSONDecodeError as exc:
                errors.append(
                    f"summary.jsonl line {line_no}: {exc.msg} (line {exc.lineno}, col {exc.colno})"
                )
        return records, errors

    for path in sorted(input_dir.glob("*.json")):
        if path.name in {"failures.json"}:
            continue
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and "items" in parsed:
                records.append(_ensure_record_defaults(parsed))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: {exc.msg} (line {exc.lineno}, col {exc.colno})")

    return records, errors


def load_failures(path: Path | None, input_dir: Path) -> list[dict[str, Any]]:
    chosen = path or (input_dir / "failures.json")
    if not chosen.exists():
        return []
    try:
        payload = json.loads(chosen.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            normalized.append(
                {
                    "path": str(item.get("path", "")),
                    "error": str(item.get("error", "")),
                }
            )
    return normalized


def build_meta(records: list[dict[str, Any]], parse_errors: list[str], failures: list[dict[str, Any]]) -> dict[str, Any]:
    groups = Counter(record.get("group", "Sconosciuto") for record in records)
    models = Counter(record.get("model", "") for record in records if record.get("model"))
    dims = Counter(dim for record in records for dim in record.get("record_dimensions", []))
    subcodes = Counter(code for record in records for code in record.get("record_subcodes", []))

    return {
        "records_total": len(records),
        "groups": dict(groups),
        "models": dict(models),
        "dimensions": dict(dims),
        "subcodes": dict(subcodes),
        "parse_errors": parse_errors,
        "failures_total": len(failures),
    }


def json_for_script(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def render_html(title: str, records: list[dict[str, Any]], failures: list[dict[str, Any]], meta: dict[str, Any]) -> str:
    payload_json = json_for_script(
        {
            "title": title,
            "records": records,
            "failures": failures,
            "meta": meta,
        }
    )
    template = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__PAGE_TITLE__</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --panel: #ffffff;
      --ink: #172433;
      --muted: #516178;
      --accent: #0f6d5f;
      --border: #d8e0ea;
      --chip: #e8f4f2;
      --warn-bg: #fff6ea;
      --warn-ink: #8a4b00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--ink);
      background: linear-gradient(135deg, #f4f7fb 0%, #edf4ff 45%, #f6faf6 100%);
    }}
    .wrap {{
      max-width: 1500px;
      margin: 0 auto;
      padding: 22px;
      display: grid;
      gap: 16px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: 0 8px 22px rgba(24, 36, 51, 0.06);
      padding: 16px;
    }}
    h1 {{
      margin: 0;
      font-size: 1.35rem;
      letter-spacing: 0.2px;
    }}
    .subtitle {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 0.94rem;
    }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }}
    .chip {{
      background: var(--chip);
      color: var(--accent);
      border: 1px solid #cae8e2;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 0.83rem;
      font-weight: 600;
    }}
    .controls {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 10px;
    }}
    .controls input, .controls select, .controls button {{
      width: 100%;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 10px;
      font-size: 0.9rem;
      color: var(--ink);
      background: #fff;
    }}
    .controls button {{
      background: #f1f6ff;
      cursor: pointer;
      font-weight: 600;
    }}
    .controls button:hover {{
      background: #e5eefb;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 16px;
    }}
    .table-wrap {{
      max-height: 70vh;
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 12px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    thead th {{
      position: sticky;
      top: 0;
      z-index: 1;
      background: #f9fbff;
      border-bottom: 1px solid var(--border);
      text-align: left;
      padding: 9px;
    }}
    tbody td {{
      border-top: 1px solid var(--border);
      padding: 8px 9px;
      vertical-align: top;
    }}
    tbody tr {{
      cursor: pointer;
    }}
    tbody tr:hover {{
      background: #f3f8ff;
    }}
    tbody tr.active {{
      background: #eaf4ff;
      outline: 1px solid #b4d2f2;
    }}
    .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.84rem;
    }}
    .muted {{
      color: var(--muted);
    }}
    .list {{
      display: grid;
      gap: 10px;
      max-height: 70vh;
      overflow: auto;
    }}
    .item-box {{
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px;
      background: #fcfdff;
    }}
    .item-head {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-weight: 600;
      margin-bottom: 6px;
    }}
    .codes {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .code {{
      background: #eef2ff;
      color: #3344a1;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 0.78rem;
      font-weight: 700;
    }}
    .pager {{
      margin-top: 10px;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .warn {{
      margin-top: 8px;
      background: var(--warn-bg);
      color: var(--warn-ink);
      border: 1px solid #ffd9a9;
      border-radius: 10px;
      padding: 8px 10px;
      font-size: 0.85rem;
    }}
    @media (max-width: 1120px) {{
      .controls {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="panel">
      <h1 id="title"></h1>
      <div class="subtitle" id="subtitle"></div>
      <div class="stats" id="stats"></div>
      <div id="warnings"></div>
    </section>

    <section class="panel controls">
      <input id="search" type="search" placeholder="Cerca in file, note, codici..." />
      <select id="groupFilter"></select>
      <select id="modelFilter"></select>
      <select id="dimFilter"></select>
      <select id="subcodeFilter"></select>
      <button id="resetBtn" type="button">Reset filtri</button>
    </section>

    <section class="grid">
      <section class="panel">
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Gruppo</th>
                <th>Record</th>
                <th>Dim</th>
                <th>Subcodici</th>
              </tr>
            </thead>
            <tbody id="rows"></tbody>
          </table>
        </div>
        <div class="pager">
          <button id="prevBtn" type="button">Prev</button>
          <button id="nextBtn" type="button">Next</button>
          <span class="muted" id="pageInfo"></span>
        </div>
      </section>

      <section class="panel">
        <div id="recordHeader" class="muted">Seleziona un record dalla tabella a sinistra.</div>
        <div id="recordMeta" style="margin-top: 10px;"></div>
        <div id="itemList" class="list" style="margin-top: 12px;"></div>
      </section>
    </section>
  </div>

  <script id="payload" type="application/json">__PAYLOAD_JSON__</script>
  <script>
    const payload = JSON.parse(document.getElementById("payload").textContent);
    const records = payload.records || [];
    const failures = payload.failures || [];
    const meta = payload.meta || {{}};

    const state = {{
      search: "",
      group: "ALL",
      model: "ALL",
      dim: "ALL",
      subcode: "ALL",
      page: 1,
      perPage: 50,
      selectedSource: "",
    }};

    function esc(value) {{
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    function uniqueSorted(values) {{
      return [...new Set(values)].filter(Boolean).sort((a, b) => a.localeCompare(b));
    }}

    function setSelectOptions(selectEl, label, values) {{
      const options = [`<option value="ALL">${{esc(label)}} (tutti)</option>`];
      values.forEach((value) => {{
        options.push(`<option value="${{esc(value)}}">${{esc(value)}}</option>`);
      }});
      selectEl.innerHTML = options.join("");
    }}

    function renderTop() {{
      document.getElementById("title").textContent = payload.title || "Label Viewer";
      document.getElementById("subtitle").textContent =
        `Record caricati: ${{meta.records_total || 0}} | Fallimenti: ${{meta.failures_total || 0}}`;

      const statsEl = document.getElementById("stats");
      const chips = [];
      const byGroup = Object.entries(meta.groups || {{}}).sort((a, b) => b[1] - a[1]).slice(0, 6);
      const bySub = Object.entries(meta.subcodes || {{}}).sort((a, b) => b[1] - a[1]).slice(0, 8);
      byGroup.forEach(([group, count]) => chips.push(`<span class="chip">${{esc(group)}}: ${{count}}</span>`));
      bySub.forEach(([code, count]) => chips.push(`<span class="chip">${{esc(code)}}: ${{count}}</span>`));
      statsEl.innerHTML = chips.join("");

      const warnings = [];
      (meta.parse_errors || []).forEach((err) => warnings.push(`<div class="warn">Errore parsing: ${{esc(err)}}</div>`));
      failures.slice(0, 5).forEach((entry) => {{
        warnings.push(`<div class="warn">Failure: ${{esc(entry.path)}} | ${{esc(entry.error)}}</div>`);
      }});
      if (failures.length > 5) {{
        warnings.push(`<div class="warn">Altri ${{failures.length - 5}} failures presenti in failures.json</div>`);
      }}
      document.getElementById("warnings").innerHTML = warnings.join("");
    }}

    function setupFilters() {{
      setSelectOptions(
        document.getElementById("groupFilter"),
        "Gruppo",
        uniqueSorted(records.map((r) => r.group))
      );
      setSelectOptions(
        document.getElementById("modelFilter"),
        "Modello",
        uniqueSorted(records.map((r) => r.model))
      );
      setSelectOptions(
        document.getElementById("dimFilter"),
        "Dimensione",
        uniqueSorted(records.flatMap((r) => r.record_dimensions || []))
      );
      setSelectOptions(
        document.getElementById("subcodeFilter"),
        "Subcodice",
        uniqueSorted(records.flatMap((r) => r.record_subcodes || []))
      );
    }}

    function matches(record) {{
      if (state.group !== "ALL" && record.group !== state.group) return false;
      if (state.model !== "ALL" && record.model !== state.model) return false;
      if (state.dim !== "ALL" && !(record.record_dimensions || []).includes(state.dim)) return false;
      if (state.subcode !== "ALL" && !(record.record_subcodes || []).includes(state.subcode)) return false;
      if (!state.search) return true;

      const hay = [
        record.source_name,
        record.group,
        record.record_code,
        record.record_note,
        ...(record.record_subcodes || []),
        ...(record.record_dimensions || []),
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(state.search);
    }}

    function filteredRecords() {{
      return records.filter(matches);
    }}

    function showRecord(record) {{
      state.selectedSource = record.source_name || "";
      const header = document.getElementById("recordHeader");
      const metaBox = document.getElementById("recordMeta");
      const list = document.getElementById("itemList");

      header.innerHTML = `<strong>${{esc(record.source_name)}}</strong> <span class="muted">| ${{esc(record.group)}} | ${{esc(record.model)}}</span>`;

      const subcodes = (record.record_subcodes || []).map((c) => `<span class="code">${{esc(c)}}</span>`).join("");
      metaBox.innerHTML = `
        <div class="mono">record_code: ${{esc(record.record_code)}} | generated_at: ${{esc(record.generated_at)}}</div>
        <div style="margin-top:8px;"><strong>Record note:</strong> ${{esc(record.record_note || "-")}}</div>
        <div style="margin-top:8px;"><strong>Subcodici record:</strong> ${{subcodes || '<span class="muted">nessuno</span>'}}</div>
      `;

      const cards = (record.items || []).map((item) => {{
        const codes = (item.codes || []).map((code) => `<span class="code">${{esc(code)}}</span>`).join("");
        return `
          <article class="item-box">
            <div class="item-head">
              <span>Item #${{esc(item.index)}}</span>
              <span class="codes">${{codes || '<span class="muted">no-codes</span>'}}</span>
            </div>
            <div><strong>Q:</strong> ${{esc(item.question || "")}}</div>
            <div style="margin-top:6px;"><strong>A:</strong> ${{esc(item.answer || "")}}</div>
            <div style="margin-top:6px;" class="muted"><strong>Reason:</strong> ${{esc(item.reason || "")}}</div>
          </article>
        `;
      }});
      list.innerHTML = cards.join("");
    }}

    function renderRows() {{
      const filtered = filteredRecords();
      const totalPages = Math.max(1, Math.ceil(filtered.length / state.perPage));
      if (state.page > totalPages) state.page = totalPages;
      const from = (state.page - 1) * state.perPage;
      const pageRows = filtered.slice(from, from + state.perPage);
      const rowsEl = document.getElementById("rows");

      rowsEl.innerHTML = pageRows
        .map((record) => {{
          const active = record.source_name === state.selectedSource ? "active" : "";
          return `
            <tr data-source="${{esc(record.source_name)}}" class="${{active}}">
              <td class="mono">${{esc(record.source_name)}}</td>
              <td>${{esc(record.group)}}</td>
              <td class="mono">${{esc(record.record_code)}}</td>
              <td>${{esc((record.record_dimensions || []).join(", "))}}</td>
              <td>${{esc((record.record_subcodes || []).join(", "))}}</td>
            </tr>
          `;
        })
        .join("");

      document.getElementById("pageInfo").textContent =
        `Pagina ${{state.page}} / ${{totalPages}} | records filtrati: ${{filtered.length}}`;

      rowsEl.querySelectorAll("tr").forEach((row) => {{
        row.addEventListener("click", () => {{
          const src = row.getAttribute("data-source");
          const found = filtered.find((r) => r.source_name === src);
          if (found) {{
            showRecord(found);
            renderRows();
          }}
        }});
      }});

      if (!state.selectedSource && filtered.length > 0) {{
        showRecord(filtered[0]);
        renderRows();
      }}
    }}

    function attachEvents() {{
      document.getElementById("search").addEventListener("input", (event) => {{
        state.search = event.target.value.trim().toLowerCase();
        state.page = 1;
        renderRows();
      }});
      document.getElementById("groupFilter").addEventListener("change", (event) => {{
        state.group = event.target.value;
        state.page = 1;
        renderRows();
      }});
      document.getElementById("modelFilter").addEventListener("change", (event) => {{
        state.model = event.target.value;
        state.page = 1;
        renderRows();
      }});
      document.getElementById("dimFilter").addEventListener("change", (event) => {{
        state.dim = event.target.value;
        state.page = 1;
        renderRows();
      }});
      document.getElementById("subcodeFilter").addEventListener("change", (event) => {{
        state.subcode = event.target.value;
        state.page = 1;
        renderRows();
      }});
      document.getElementById("resetBtn").addEventListener("click", () => {{
        state.search = "";
        state.group = "ALL";
        state.model = "ALL";
        state.dim = "ALL";
        state.subcode = "ALL";
        state.page = 1;
        state.selectedSource = "";
        document.getElementById("search").value = "";
        document.getElementById("groupFilter").value = "ALL";
        document.getElementById("modelFilter").value = "ALL";
        document.getElementById("dimFilter").value = "ALL";
        document.getElementById("subcodeFilter").value = "ALL";
        renderRows();
      }});
      document.getElementById("prevBtn").addEventListener("click", () => {{
        state.page = Math.max(1, state.page - 1);
        renderRows();
      }});
      document.getElementById("nextBtn").addEventListener("click", () => {{
        state.page = state.page + 1;
        renderRows();
      }});
    }}

    renderTop();
    setupFilters();
    attachEvents();
    renderRows();
  </script>
</body>
</html>
"""
    template = template.replace("{{", "{").replace("}}", "}")
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return template.replace("__PAGE_TITLE__", safe_title).replace("__PAYLOAD_JSON__", payload_json)


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir

    if not input_dir.exists():
        print(f"Cartella non trovata: {input_dir}")
        return 1

    records, parse_errors = load_records(input_dir=input_dir, summary_file=args.summary_file)
    failures = load_failures(path=args.failures_file, input_dir=input_dir)
    meta = build_meta(records=records, parse_errors=parse_errors, failures=failures)

    html = render_html(title=args.title, records=records, failures=failures, meta=meta)
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(html, encoding="utf-8")

    print(
        json.dumps(
            {
                "records_loaded": len(records),
                "parse_errors": len(parse_errors),
                "failures_loaded": len(failures),
                "output_file": str(args.output_file),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
