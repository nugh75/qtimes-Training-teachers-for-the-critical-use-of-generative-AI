#!/usr/bin/env python3
"""Propaga e raffina N1 su item senza codice o con legacy N1.

Per ogni 04-label/labels/*.json:
  - se un item ha codes == [], assegna N1a/N1b/N1c in modo deterministico;
  - se un item ha legacy N1, lo converte in N1a/N1b/N1c;
  - ricalcola record_subcodes, record_dimensions, code_counts.

Idempotente. Safe re-run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
DEFAULT_LABELS_DIR = ROOT_DIR / "04-label" / "labels" / "ollama-gemma4"
SKIP = {"failures", "metodologia"}

SHORT_MARKERS = {
    "",
    "-",
    "_",
    "—",
    "no",
    "si",
    "sì",
    "nessuno",
    "nessuna",
    "niente",
    "nulla",
    "non so",
    "non saprei",
    "boh",
}

OUT_OF_TOPIC_MARKERS = (
    "non posso rispondere",
    "non so rispondere",
    "non insegno",
    "non ho esperienza",
    "non la utilizzo per questo scopo",
    "non la utilizzo",
    "nessuna esperienza",
)

TAUTOLOGY_MARKERS = (
    "è un",
    "e un",
    "si intende",
    "significa",
    "input per",
    "in pratica",
)

N1_REASON = {
    "N1a": "Risposta troppo breve o non informativa.",
    "N1b": "Risposta fuori tema rispetto alla domanda.",
    "N1c": "Risposta tautologica o meta-definizione.",
}

STOPWORDS = {
    "della",
    "delle",
    "degli",
    "dello",
    "dell",
    "nella",
    "nelle",
    "nello",
    "dellia",
    "questa",
    "questo",
    "quello",
    "quella",
    "perche",
    "perché",
    "dove",
    "come",
    "quali",
    "quale",
}


def normalize(text: str) -> str:
    lowered = text.lower().strip().strip('"').strip("'")
    return re.sub(r"\s+", " ", lowered)


def keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-zàèéìòùA-ZÀÈÉÌÒÙ]{3,}", text.lower())
    return {t for t in tokens if len(t) >= 5 and t not in STOPWORDS}


def classify_n1(question: str, answer: str, reason: str) -> str:
    q = normalize(question)
    a = normalize(answer)
    r = normalize(reason)
    words = [w for w in re.split(r"\W+", a) if w]

    if a in SHORT_MARKERS or len(words) <= 3:
        return "N1a"
    if any(marker in r for marker in ("troppo breve", "non informativa", "vuota", "generica")):
        return "N1a"
    if "fuori tema" in r:
        return "N1b"
    if any(marker in a for marker in OUT_OF_TOPIC_MARKERS):
        return "N1b"

    qk = keywords(q)
    ak = keywords(a)
    overlap = len(qk & ak)
    if "tautolog" in r:
        return "N1c"
    if any(marker in a for marker in TAUTOLOGY_MARKERS) and overlap >= 1:
        return "N1c"

    return "N1b"


def refine_item_codes(item: dict) -> tuple[list[str], bool]:
    changed = False
    codes = [str(c) for c in item.get("codes", [])]
    question = str(item.get("question", ""))
    answer = str(item.get("answer", ""))
    reason = str(item.get("reason", ""))

    if not codes:
        return [classify_n1(question, answer, reason)], True

    normalized: list[str] = []
    for code in codes:
        if code == "N1":
            normalized.append(classify_n1(question, answer, reason))
            changed = True
        else:
            normalized.append(code)

    deduped: list[str] = []
    for code in normalized:
        if code not in deduped:
            deduped.append(code)

    if deduped != codes:
        changed = True
    return deduped, changed


def propagate(path: Path, dry_run: bool = False) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for item in data.get("items", []):
        refined_codes, item_changed = refine_item_codes(item)
        if item_changed:
            item["codes"] = refined_codes
            changed = True
        if not item.get("reason"):
            n1_codes = [c for c in item.get("codes", []) if c in N1_REASON]
            if n1_codes:
                item["reason"] = N1_REASON[n1_codes[0]]
                changed = True

    if not changed:
        return False

    all_codes = [c for item in data.get("items", []) for c in item.get("codes", [])]
    subcodes = sorted(set(all_codes))
    dims = sorted({c[0] for c in subcodes})
    data["record_subcodes"] = subcodes
    data["record_dimensions"] = dims
    data["code_counts"] = dict(Counter(all_codes))

    if not dry_run:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS_DIR)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    labels_dir: Path = args.labels_dir
    if not labels_dir.exists():
        print(f"Directory non trovata: {labels_dir}", file=sys.stderr)
        return 1

    updated = 0
    total = 0
    for p in sorted(labels_dir.glob("*.json")):
        if p.stem in SKIP:
            continue
        total += 1
        if propagate(p, dry_run=args.dry_run):
            updated += 1

    mode = "dry-run" if args.dry_run else "write"
    print(f"Mode: {mode} | Total: {total}, updated: {updated}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
