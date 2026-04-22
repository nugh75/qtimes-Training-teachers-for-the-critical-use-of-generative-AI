#!/usr/bin/env python3
"""Riscrive le citazioni wiki applicando il mapping finale.

Regole:
- confidence high/medium con item_index:
    (source: [code](.../02-corpus/X.md#item-N) · codes: R4, X2)
- confidence low/none:
    citazione record-level invariata (solo path, no anchor)
- dim_coherent == False:
    append ' · label: A1+I4' dopo la citazione

Applica replacement per offset decrescente per non spostare offset successivi.

Uso:
  python rewrite_wiki_citations.py --dry-run --page 01-wiki/X.md
  python rewrite_wiki_citations.py --dry-run
  python rewrite_wiki_citations.py --write
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
MAPPING_PATH = ROOT_DIR / "04-label" / "labels" / "citation-mapping-final.json"
WIKI_DIR = ROOT_DIR / "01-wiki"

# Match full citation at a given offset. Keep structure grouped so we can preserve parts.
CITATION_RE = re.compile(
    r"\(source:\s*\[(?P<code>[^\]]+)\]\((?P<path>\.{1,2}(?:/\.\.)*(?:/[^)]+)?/(?:raw|corpus)/(?P<stem>[^)#]+?)\.md)(?P<anchor>#[^)]*)?\)\)(?P<trail>(?:\s*·\s*(?:codes|label):\s*[^.)\n]+)*)",
    re.IGNORECASE,
)


def build_citation(c: dict, current_path: str, current_code: str) -> str:
    """Produce nuovo contenuto citazione."""
    # codici item (se resolvable)
    inline_codes = ""
    new_path = current_path
    if c["confidence"] in {"high", "medium"} and c["item_index"] is not None:
        anchor = f"#item-{c['item_index']}"
        # sostituisci o aggiungi anchor
        if "#" in new_path:
            new_path = new_path.split("#")[0]
        new_path = new_path + anchor
        codes = c.get("item_codes") or []
        if codes:
            inline_codes = f" · codes: {', '.join(codes)}"

    # tag label dim se incoerente
    label_tag = ""
    if c["dim_coherent"] is False:
        dims = [d for d in c["label_dims"] if d]
        if dims:
            label_tag = f" · label: {', '.join(dims)}"

    return f"(source: [{current_code}]({new_path}){inline_codes}){label_tag}"


def process_page(page_path: Path, citations: list[dict], dry_run: bool) -> tuple[int, str]:
    if not page_path.exists():
        return 0, ""
    text = page_path.read_text(encoding="utf-8")
    # Ordina per offset descrescente
    sorted_cits = sorted(citations, key=lambda c: c["offset"], reverse=True)
    changes = 0
    new_text = text
    for c in sorted_cits:
        # re-match at offset
        m = CITATION_RE.match(new_text, c["offset"])
        if not m:
            # potrebbe essere shiftato o già modificato
            continue
        current_path = m.group("path")
        current_code = m.group("code")
        replacement = build_citation(c, current_path, current_code)
        if replacement == m.group(0):
            continue
        new_text = new_text[:m.start()] + replacement + new_text[m.end():]
        changes += 1

    if dry_run:
        return changes, new_text
    if changes:
        page_path.write_text(new_text, encoding="utf-8")
    return changes, new_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", help="processa solo questa pagina (relative path)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--mapping", type=Path, default=MAPPING_PATH)
    args = parser.parse_args()

    if not args.dry_run and not args.write:
        parser.error("richiesto --dry-run o --write")

    data = json.loads(args.mapping.read_text(encoding="utf-8"))
    citations = data["citations"]

    # group by wiki_page
    by_page = defaultdict(list)
    for c in citations:
        by_page[c["wiki_page"]].append(c)

    pages = [args.page] if args.page else sorted(by_page.keys())
    total_changes = 0
    page_changes = 0
    for page_rel in pages:
        if page_rel not in by_page:
            print(f"[skip] {page_rel}: no citations", file=sys.stderr)
            continue
        page_path = ROOT_DIR / page_rel
        changes, new_text = process_page(page_path, by_page[page_rel], args.dry_run)
        if changes:
            page_changes += 1
            total_changes += changes
            status = "[dry]" if args.dry_run else "[written]"
            print(f"{status} {page_rel}: {changes} citations updated")
            if args.dry_run and args.page:
                print("--- NEW CONTENT PREVIEW (first 3000 chars) ---")
                print(new_text[:3000])
    print(f"\nTotal: {total_changes} citations across {page_changes} pages.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
