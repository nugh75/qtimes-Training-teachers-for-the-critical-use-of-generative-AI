#!/usr/bin/env python3
"""Aggiunge backlink item -> wiki nei raw a partire dal mapping finale.

Legge:
  - labels/citation-mapping-final.json
  - raw/STEM.md in formato item-based

Produce:
  - per ogni "## Item N {#item-N}" una sezione finale "**Cited in:**"
  - link wiki deduplicati per item

Regole:
  - usa solo citazioni con confidence high/medium e item_index valorizzato;
  - le citazioni record-level restano escluse;
  - il rendering e' idempotente: una riesecuzione sostituisce la sezione esistente.

Uso:
  python add_item_backlinks.py --stem insegnanti_attuali_060580 --dry-run
  python add_item_backlinks.py --all --dry-run
  python add_item_backlinks.py --all --write
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "raw"
MAPPING_PATH = ROOT_DIR / "labels" / "citation-mapping-final.json"

ITEM_HEADING_RE = re.compile(r"^## Item (?P<idx>\d+) \{#item-\d+\}\s*$", re.MULTILINE)
BACKLINK_MARKER = "\n**Cited in:**"


def load_mapping(path: Path) -> dict[str, dict[int, list[str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    grouped: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))

    for citation in data.get("citations", []):
        confidence = citation.get("confidence")
        item_index = citation.get("item_index")
        wiki_page = citation.get("wiki_page")
        stem = citation.get("raw_stem")
        if confidence not in {"high", "medium"}:
            continue
        if item_index is None or not wiki_page or not stem:
            continue
        grouped[str(stem)][int(item_index)].add(str(wiki_page))

    result: dict[str, dict[int, list[str]]] = {}
    for stem, by_item in grouped.items():
        result[stem] = {
            item_index: sorted(paths)
            for item_index, paths in sorted(by_item.items())
        }
    return result


def build_backlinks_lines(raw_path: Path, wiki_pages: list[str]) -> list[str]:
    if not wiki_pages:
        return ["**Cited in:** —"]

    lines = ["**Cited in:**"]
    for wiki_page in wiki_pages:
        target = os.path.relpath(ROOT_DIR / wiki_page, start=raw_path.parent).replace("\\", "/")
        lines.append(f"- [{wiki_page}]({target})")
    return lines


def update_item_block(block: str, raw_path: Path, wiki_pages: list[str]) -> str:
    if BACKLINK_MARKER in block:
        block = block.split(BACKLINK_MARKER, 1)[0].rstrip()
    else:
        block = block.rstrip()

    backlink_lines = build_backlinks_lines(raw_path, wiki_pages)
    return block + "\n\n" + "\n".join(backlink_lines) + "\n\n"


def update_raw(raw_path: Path, item_backlinks: dict[int, list[str]]) -> tuple[str, int, int]:
    original = raw_path.read_text(encoding="utf-8")
    matches = list(ITEM_HEADING_RE.finditer(original))
    if not matches:
        raise ValueError(f"Nessun item trovato in {raw_path}")

    chunks: list[str] = []
    cursor = 0
    linked_items = 0
    total_items = 0

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(original)
        if index == 0:
            chunks.append(original[cursor:start])

        item_index = int(match.group("idx"))
        total_items += 1
        wiki_pages = item_backlinks.get(item_index, [])
        if wiki_pages:
            linked_items += 1
        chunks.append(update_item_block(original[start:end], raw_path, wiki_pages))
        cursor = end

    updated = "".join(chunks).rstrip() + "\n"
    return updated, total_items, linked_items


def process_file(stem: str, backlinks: dict[str, dict[int, list[str]]], *, write: bool, dry_run: bool) -> tuple[int, int, bool]:
    raw_path = RAW_DIR / f"{stem}.md"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw markdown mancante: {raw_path}")

    updated, total_items, linked_items = update_raw(raw_path, backlinks.get(stem, {}))
    original = raw_path.read_text(encoding="utf-8")
    changed = updated != original

    if dry_run and changed:
        print(f"[dry-run] {raw_path}: items={total_items}, linked_items={linked_items}")
    elif dry_run:
        print(f"[dry-run] {raw_path}: no changes")

    if write and changed:
        raw_path.write_text(updated, encoding="utf-8")
        print(f"[written] {raw_path}: items={total_items}, linked_items={linked_items}")

    return total_items, linked_items, changed


def stems_from_raw() -> list[str]:
    return sorted(path.stem for path in RAW_DIR.glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stem", help="processa un singolo raw (es. insegnanti_attuali_060580)")
    parser.add_argument("--all", action="store_true", help="processa tutti i raw")
    parser.add_argument("--mapping", type=Path, default=MAPPING_PATH)
    parser.add_argument("--dry-run", action="store_true", help="analizza senza scrivere")
    parser.add_argument("--write", action="store_true", help="scrive i backlink nei raw")
    args = parser.parse_args()

    if not args.stem and not args.all:
        parser.error("richiesto --stem o --all")
    if not args.dry_run and not args.write:
        parser.error("richiesto --dry-run o --write")

    backlinks = load_mapping(args.mapping)
    stems = [args.stem] if args.stem else stems_from_raw()

    files_changed = 0
    items_total = 0
    linked_items_total = 0

    for stem in stems:
        try:
            item_count, linked_count, changed = process_file(
                stem,
                backlinks,
                write=args.write,
                dry_run=args.dry_run,
            )
        except Exception as exc:
            print(f"[error] {stem}: {exc}", file=sys.stderr)
            continue

        items_total += item_count
        linked_items_total += linked_count
        if changed:
            files_changed += 1

    mode = "dry-run" if args.dry_run else "write"
    print(
        json.dumps(
            {
                "mode": mode,
                "files": len(stems),
                "files_changed": files_changed,
                "items_total": items_total,
                "linked_items_total": linked_items_total,
                "mapping_path": str(args.mapping),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())