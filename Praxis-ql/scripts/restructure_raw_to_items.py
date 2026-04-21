#!/usr/bin/env python3
"""Ristruttura raw/*.md in formato item-based con anchor.

Legge:
  - labels/ollama-gemma4/STEM.json (sorgente di verità: items, codes, Q+A)
  - raw/STEM.md (solo per preservare Q+A esatti se mancano in JSON)

Produce:
  - raw/STEM.md con frontmatter YAML + sezioni "## Item N {#item-N}"

Uso:
  # dry-run su singolo file (stampa output, non scrive)
  python restructure_raw_to_items.py --stem insegnanti_attuali_060580 --dry-run

  # esegui su tutti
  python restructure_raw_to_items.py --all --write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from label_raw_with_ollama import CODEBOOK, ROOT_DIR

RAW_DIR = ROOT_DIR / "raw"
LABELS_DIR = ROOT_DIR / "labels" / "ollama-gemma4"


def load_label(stem: str) -> dict:
    path = LABELS_DIR / f"{stem}.json"
    if not path.exists():
        raise FileNotFoundError(f"Label JSON mancante: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(values) + "]"


def yaml_str(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def format_codes_inline(codes: list[str]) -> str:
    if not codes:
        return "—"
    parts = []
    for code in codes:
        desc = CODEBOOK.get(code, "Codice non definito")
        parts.append(f"{code} — {desc}")
    return "; ".join(parts)


def build_markdown(label: dict) -> str:
    code = label.get("record_code", "")
    group = label.get("group", "Sconosciuto")
    dims = label.get("record_dimensions", [])
    subcodes = label.get("record_subcodes", [])
    model = label.get("model", "")
    generated_at = label.get("generated_at", "")
    label_source = label.get("source_name", "")
    note = label.get("record_note", "")
    items = label.get("items", [])

    lines = ["---"]
    lines.append(f"record_code: {yaml_str(code)}")
    lines.append(f"group: {group}")
    lines.append(f"dimensions: {yaml_list(dims)}")
    lines.append(f"subcodes: {yaml_list(subcodes)}")
    if model:
        lines.append(f"model: {model}")
    if generated_at:
        lines.append(f"generated_at: {yaml_str(generated_at)}")
    if label_source:
        lines.append(f"label_source: labels/ollama-gemma4/{label_source.replace('.md', '.json')}")
    if note:
        lines.append(f"note: {yaml_str(note)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Risposta {code}")
    lines.append("")

    for item in items:
        idx = item.get("index", 0)
        q = item.get("question", "").strip()
        a = item.get("answer", "").strip()
        codes = item.get("codes", [])
        reason = item.get("reason", "").strip()

        lines.append(f"## Item {idx} {{#item-{idx}}}")
        lines.append("")
        lines.append(f"**Q**: {q}")
        lines.append(f"**A**: {a}")
        lines.append(f"**Codes**: {format_codes_inline(codes)}")
        if reason:
            lines.append(f"**Reason**: {reason}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def process(stem: str, *, write: bool, dry_run: bool) -> str:
    label = load_label(stem)
    content = build_markdown(label)
    target = RAW_DIR / f"{stem}.md"

    if dry_run:
        print(f"--- DRY RUN: {target} ---")
        print(content)
        print(f"--- END ({len(content)} chars) ---")
        return content

    if write:
        target.write_text(content, encoding="utf-8")
        print(f"[written] {target}")
    return content


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stem", help="processa un singolo raw (es. insegnanti_attuali_060580)")
    parser.add_argument("--all", action="store_true", help="processa tutti i raw con JSON corrispondente")
    parser.add_argument("--dry-run", action="store_true", help="stampa output, non scrivere")
    parser.add_argument("--write", action="store_true", help="sovrascrivi raw/STEM.md")
    args = parser.parse_args()

    if not args.stem and not args.all:
        parser.error("richiesto --stem o --all")
    if not args.dry_run and not args.write:
        parser.error("richiesto --dry-run o --write")

    if args.stem:
        process(args.stem, write=args.write, dry_run=args.dry_run)
        return 0

    skip = {"failures", "metodologia"}
    stems = sorted(p.stem for p in LABELS_DIR.glob("*.json") if p.stem not in skip)
    print(f"trovati {len(stems)} stems", file=sys.stderr)
    for stem in stems:
        try:
            process(stem, write=args.write, dry_run=args.dry_run)
        except Exception as exc:
            print(f"[error] {stem}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
