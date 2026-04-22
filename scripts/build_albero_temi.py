#!/usr/bin/env python3
"""Rigenera 01-wiki/00-indice/albero-temi.md dallo stato filesystem di 01-wiki/.

Estrae titolo H1 da ogni .md; se manca, usa stem.
Produce albero ASCII deterministico ordinato per path.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "Praxis-ql"
WIKI = ROOT / "01-wiki"
TARGET = WIKI / "00-indice" / "albero-temi.md"

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def title_of(md: Path) -> str:
    try:
        text = md.read_text(encoding="utf-8")
    except Exception:
        return md.stem
    m = H1_RE.search(text)
    return m.group(1).strip() if m else md.stem


def build_tree(root: Path, indent: str = "") -> list[str]:
    lines: list[str] = []
    entries = sorted(
        (p for p in root.iterdir() if not p.name.startswith(".")),
        key=lambda p: (not p.is_dir(), p.name.lower()),
    )
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        branch = indent + connector
        if entry.is_dir():
            lines.append(f"{branch}{entry.name}/")
            sub_indent = indent + ("    " if is_last else "│   ")
            lines.extend(build_tree(entry, sub_indent))
        elif entry.suffix == ".md":
            title = title_of(entry)
            lines.append(f"{branch}{entry.name} — {title}")
    return lines


def main() -> None:
    lines: list[str] = ["# Albero dei temi — LLM Wiki", "", "```", "01-wiki/"]
    lines.extend(build_tree(WIKI))
    lines.append("```")
    lines.append("")
    lines.append("_Generato automaticamente da scripts/build_albero_temi.py_")
    TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Written: {TARGET}")


if __name__ == "__main__":
    main()
