#!/usr/bin/env python3
"""Propaga N1 deterministico a item con codes=[].

Per ogni labels/*.json:
  - se un item ha codes == [], imposta codes = ["N1"] e reason fallback se vuoto
  - ricalcola record_subcodes, record_dimensions, code_counts
  - preserva record_note originale

Idempotente. Safe re-run.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
LABELS_DIR = ROOT_DIR / "labels" / "ollama-gemma4"
SKIP = {"failures", "metodologia"}


def propagate(path: Path) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for item in data.get("items", []):
        codes = item.get("codes", [])
        if not codes:
            item["codes"] = ["N1"]
            if not item.get("reason"):
                item["reason"] = "Risposta non classificabile: troppo breve, generica o fuori tema."
            changed = True
    if not changed:
        return False
    # recompute aggregates
    all_codes = [c for item in data["items"] for c in item["codes"]]
    subcodes = sorted(set(all_codes))
    dims = sorted({c[0] for c in subcodes})
    data["record_subcodes"] = subcodes
    data["record_dimensions"] = dims
    data["code_counts"] = dict(Counter(all_codes))
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def main() -> int:
    updated = 0
    total = 0
    for p in sorted(LABELS_DIR.glob("*.json")):
        if p.stem in SKIP:
            continue
        total += 1
        if propagate(p):
            updated += 1
    print(f"Total: {total}, updated: {updated}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
