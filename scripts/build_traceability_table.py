#!/usr/bin/env python3
"""Build markdown traceability table: dati -> corpus -> wiki -> article section."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
DEFAULT_CITATION_MAP = ROOT_DIR / "04-label" / "labels" / "citation-mapping-final.json"
DEFAULT_BUILD_MANIFEST = ROOT_DIR / "04-label" / "labels" / "corpus-build-manifest.json"
DEFAULT_OUTPUT = ROOT_DIR / "05-documentazione" / "tracciabilita-e2e.md"

ARTICLE_SECTION_BY_DIM = {
    "P": "4.1 Practice patterns (P)",
    "R": "4.2 Readiness beliefs (R)",
    "A": "4.3 Adequacy of support (A)",
    "X": "4.4 eXpectations (X)",
    "I": "4.5 Interpersonal & Institutional trust (I)",
    "S": "4.6 Skepticisms (S)",
    "N": "4.x Non-classificati / controllo coerenza",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--citation-map", type=Path, default=DEFAULT_CITATION_MAP)
    parser.add_argument("--build-manifest", type=Path, default=DEFAULT_BUILD_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def md_escape(value: str) -> str:
    return value.replace("|", "\\|")


def resolve_article_section(dim: str) -> str:
    if not dim:
        return "TBD"
    return ARTICLE_SECTION_BY_DIM.get(dim.upper(), f"TBD ({dim})")


def build_rows(citation_map: dict, build_manifest: dict) -> tuple[list[str], dict[str, int]]:
    records = build_manifest.get("records", [])
    stem_to_source: dict[str, tuple[str, int]] = {}
    for rec in records:
        output_file = str(rec.get("output_file", ""))
        stem = output_file[:-3] if output_file.endswith(".md") else output_file
        source_file = str(rec.get("source_file", ""))
        source_row = int(rec.get("source_row", 0) or 0)
        if stem:
            stem_to_source[stem] = (source_file, source_row)

    citations = citation_map.get("citations", [])
    lines: list[str] = []
    stats = {"total": 0, "mapped": 0, "needs_source": 0, "review": 0}

    for idx, citation in enumerate(citations, start=1):
        stats["total"] += 1

        raw_stem = str(citation.get("raw_stem", "")).strip()
        item_index = citation.get("item_index")
        item_index_str = str(item_index) if item_index is not None else "?"
        item_codes = citation.get("item_codes") or []
        if isinstance(item_codes, list):
            item_codes_str = ", ".join(str(code) for code in item_codes) if item_codes else "N/A"
        else:
            item_codes_str = str(item_codes)

        wiki_page = str(citation.get("wiki_page", "")).strip()
        wiki_line = citation.get("line")
        wiki_ref = f"{wiki_page}:{wiki_line}" if wiki_page and wiki_line else (wiki_page or "N/A")

        wiki_dim = str(citation.get("wiki_dim", "")).strip().upper()
        article_section = resolve_article_section(wiki_dim)

        source_info = stem_to_source.get(raw_stem)
        if source_info:
            source_file, source_row = source_info
            dato_ref = f"dati/{source_file}#row{source_row}"
        else:
            dato_ref = "N/A"

        corpus_ref = f"02-corpus/{raw_stem}.md#item-{item_index_str}" if raw_stem else "N/A"

        dim_coherent = bool(citation.get("dim_coherent", False))
        if not source_info:
            status = "needs-source"
            stats["needs_source"] += 1
        elif item_index is None:
            status = "review"
            stats["review"] += 1
        elif not dim_coherent:
            status = "review"
            stats["review"] += 1
        else:
            status = "mapped"
            stats["mapped"] += 1

        trace_id = f"T{idx:04d}"
        line = (
            f"| {trace_id} | {md_escape(dato_ref)} | {md_escape(corpus_ref)} | "
            f"{md_escape(item_codes_str)} | {md_escape(wiki_ref)} | "
            f"{md_escape(article_section)} | — | {status} |"
        )
        lines.append(line)

    return lines, stats


def main() -> int:
    args = parse_args()
    citation_map = load_json(args.citation_map)
    build_manifest = load_json(args.build_manifest)

    rows, stats = build_rows(citation_map, build_manifest)

    content: list[str] = []
    content.append("# Tabella Tracciabilita End-to-End")
    content.append("")
    content.append("**Versione**: 1.0")
    content.append("**Fonte mapping**: 04-label/labels/citation-mapping-final.json")
    content.append("**Fonte dati->corpus**: 04-label/labels/corpus-build-manifest.json")
    content.append("")
    content.append("## Sintesi")
    content.append("")
    content.append(f"- Totale evidenze mappate: {stats['total']}")
    content.append(f"- Stato `mapped`: {stats['mapped']}")
    content.append(f"- Stato `review`: {stats['review']}")
    content.append(f"- Stato `needs-source`: {stats['needs_source']}")
    content.append("")
    content.append("## Tabella")
    content.append("")
    content.append(
        "| Trace ID | Dato sorgente | Record/item corpus | Codice finale | Pagina wiki | Sezione articolo | Decision log | Stato |"
    )
    content.append("|---|---|---|---|---|---|---|---|")
    content.extend(rows)
    content.append("")

    args.output.write_text("\n".join(content), encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"rows={stats['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
