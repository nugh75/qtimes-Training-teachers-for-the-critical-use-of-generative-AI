#!/usr/bin/env python3
from __future__ import annotations

"""Normalizza legenda e codici PRAXIS nei record corpus item-based.

Uso:
    python expand_praxis_codes_in_markdown.py --write
"""

import argparse
import re
from pathlib import Path

from label_raw_with_ollama import CODEBOOK, ROOT_DIR


DEFAULT_INPUT_DIR = ROOT_DIR / "02-corpus"
SKIP_FILES: set[str] = set()
CODES_RE = re.compile(r"^\*\*Codes\*\*: (.*)$")
CODE_RE = re.compile(r"\b[APRSXIN]\d\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalizza i codici PRAXIS nei markdown item-based di 02-corpus/."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--glob", default="*.md")
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def unique_codes(text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in CODE_RE.findall(text):
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered


def format_codes_extended(codes: list[str]) -> str:
    if not codes:
        return "—"
    return "; ".join(f"{code} — {CODEBOOK.get(code, 'Codice non definito')}" for code in codes)


def remove_existing_legend(text: str) -> str:
    return re.sub(
        r"\n## Legenda codici del record\n.*?(?=\n## Item \d+ \{#item-\d+\}\n)",
        "\n",
        text,
        flags=re.DOTALL,
    )


def insert_legend(text: str, codes: list[str]) -> str:
    if not codes:
        return text
    legend_lines = ["## Legenda codici del record", ""]
    legend_lines.extend(f"- **{code}**: {CODEBOOK.get(code, 'Codice non definito')}" for code in codes)
    legend_lines.append("")
    legend_block = "\n".join(legend_lines)
    return re.sub(
        r"\n## Item \d+ \{#item-\d+\}\n",
        lambda match: f"\n{legend_block}\n{match.group(0).lstrip()}",
        text,
        count=1,
    )


def expand_markdown(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    record_codes = unique_codes(text)

    i = 0
    while i < len(lines):
        line = lines[i]
        codes_match = CODES_RE.match(line)

        if codes_match:
            codes = unique_codes(codes_match.group(1))
            out.append(f"**Codes**: {format_codes_extended(codes)}")
            i += 1
            continue

        out.append(line)
        i += 1

    expanded = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    expanded = remove_existing_legend(expanded)

    expanded = insert_legend(expanded, record_codes)
    return expanded


def process_file(path: Path, write: bool) -> tuple[bool, bool]:
    original = path.read_text(encoding="utf-8")
    updated = expand_markdown(original)
    changed = updated != original
    if changed and write:
        path.write_text(updated, encoding="utf-8")
    return changed, changed and write


def main() -> int:
    args = parse_args()
    files = sorted(args.input_dir.glob(args.glob))
    files = [path for path in files if path.name not in SKIP_FILES]

    changed = 0
    written = 0
    for path in files:
        file_changed, file_written = process_file(path, write=args.write)
        if file_changed:
            changed += 1
        if file_written:
            written += 1

    action = "scritte" if args.write else "da aggiornare"
    print(f"File {action}: {written if args.write else changed} / {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
