#!/usr/bin/env python3
"""Costruisce mapping finale citazione wiki → item corpus.

Output: 04-label/labels/citation-mapping-final.json

Struttura:
{
  "citations": [
    {
      "wiki_page": "01-wiki/.../page.md",
      "offset": 1234,
      "line": 18,
      "raw_stem": "insegnanti_attuali_X",
      "raw_code": "X",
      "wiki_dim": "R",
      "label_dims": ["A", "R"],
      "quoted_text": "...",
      "item_index": 2 | null,
      "item_answer": "...",
      "item_codes": ["R4"],
      "match_score": 0.95,
      "match_strategy": "exact_substring" | "fuzzy" | "none",
      "confidence": "high" | "medium" | "low" | "none",
      "dim_coherent": true
    }
  ],
  "summary": {...}
}
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
WIKI_DIR = ROOT_DIR / "01-wiki"
LABELS_DIR = ROOT_DIR / "04-label" / "labels" / "ollama-gemma4"
OUTPUT_PATH = ROOT_DIR / "04-label" / "labels" / "citation-mapping-final.json"

CITATION_RE = re.compile(
    r"\(source:\s*\[(?P<code>[^\]]+)\]\((?P<path>\.{1,2}(?:/\.\.)*(?:/[^)]+)?/(?:raw|corpus)/(?P<stem>[^)#]+?)\.md)(?P<anchor>#[^)]*)?\)",
    re.IGNORECASE,
)

# Cattura quote immediately preceding citation (within 500 chars).
# Supporta «», "", "".
QUOTE_PRECEDING_RE = re.compile(
    r"[«\"\"]([^«»\"\"]{3,600})[»\"\"]\s*(?:\([^)]*?source:|\(source:)",
)

DIM_FROM_PATH = {
    "practice-patterns": "P",
    "readiness-beliefs": "R",
    "adequacy-of-support": "A",
    "expectations": "X",
    "interpersonal-trust": "I",
    "skepticisms": "S",
}


def extract_wiki_dim(wiki_path: Path) -> str | None:
    parts = wiki_path.relative_to(WIKI_DIR).parts
    for part in parts:
        stem = part.replace(".md", "")
        for dim_slug, dim_letter in DIM_FROM_PATH.items():
            if dim_slug in stem:
                return dim_letter
    return None


def load_label(stem: str) -> dict | None:
    path = LABELS_DIR / f"{stem}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    # strip markdown emphasis markers that commonly wrap quotes
    text = re.sub(r"[*_`]", "", text)
    # normalize curly quotes to straight
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    # collapse whitespace + lower
    return re.sub(r"\s+", " ", text).strip().lower()


def line_of_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_quote_before(text: str, citation_start: int) -> str:
    """Cerca ultima quote fra virgolette nei 600 char precedenti la citation."""
    start = max(0, citation_start - 600)
    window = text[start:citation_start + 200]
    matches = list(QUOTE_PRECEDING_RE.finditer(window))
    if not matches:
        return ""
    # prendi l'ultima
    return matches[-1].group(1).strip()


def score_item(quote: str, answer: str) -> tuple[float, str]:
    """Return (score, strategy)."""
    qn = normalize(quote)
    an = normalize(answer)
    if not qn or not an:
        return 0.0, "none"
    if qn == an:
        return 1.0, "exact"
    if qn in an:
        # quote è substring di answer → alto
        coverage = len(qn) / max(len(an), 1)
        return 0.85 + 0.1 * min(coverage, 1.0), "quote_in_answer"
    if an in qn:
        # answer è substring di quote (quote più lunga con contesto)
        coverage = len(an) / max(len(qn), 1)
        return 0.80 + 0.1 * min(coverage, 1.0), "answer_in_quote"
    # fuzzy ratio
    ratio = difflib.SequenceMatcher(None, qn, an).ratio()
    return ratio, "fuzzy"


def best_item_match(quote: str, items: list[dict]) -> tuple[int | None, float, str, dict | None]:
    if not quote or not items:
        return None, 0.0, "none", None
    best_idx = None
    best_score = 0.0
    best_strategy = "none"
    best_item = None
    for item in items:
        answer = item.get("answer", "")
        score, strategy = score_item(quote, answer)
        if score > best_score:
            best_score = score
            best_idx = item.get("index")
            best_strategy = strategy
            best_item = item
    return best_idx, round(best_score, 3), best_strategy, best_item


def confidence_level(score: float) -> str:
    if score >= 0.9:
        return "high"
    if score >= 0.7:
        return "medium"
    if score >= 0.5:
        return "low"
    return "none"


def build_mapping() -> dict:
    all_citations = []
    label_cache: dict[str, dict | None] = {}

    for md in sorted(WIKI_DIR.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        wiki_dim = extract_wiki_dim(md)
        rel = str(md.relative_to(ROOT_DIR))
        for m in CITATION_RE.finditer(text):
            stem = m.group("stem")
            anchor_present = bool(m.group("anchor"))
            offset = m.start()
            line = line_of_offset(text, offset)
            quote = find_quote_before(text, offset)

            if stem not in label_cache:
                label_cache[stem] = load_label(stem)
            label = label_cache[stem]

            label_dims = label.get("record_dimensions", []) if label else []
            items = label.get("items", []) if label else []

            # match
            idx, score, strategy, item_obj = best_item_match(quote, items)
            conf = confidence_level(score) if quote else "none"

            # coerenza dim (ignora N che è catch-all)
            praxis_dims = [d for d in label_dims if d != "N"]
            dim_coherent = None
            if wiki_dim and praxis_dims:
                dim_coherent = wiki_dim in label_dims
            elif wiki_dim and not praxis_dims and label_dims == ["N"]:
                dim_coherent = False  # citato in pagina dim X ma record è solo N
            elif wiki_dim is None:
                dim_coherent = None  # pagina senza dim (es. non-classificati)

            all_citations.append({
                "wiki_page": rel,
                "offset": offset,
                "line": line,
                "raw_stem": stem,
                "raw_code": m.group("code"),
                "wiki_dim": wiki_dim,
                "label_dims": label_dims,
                "quoted_text": quote,
                "item_index": idx if conf in {"high", "medium"} else None,
                "item_answer": (item_obj.get("answer") if item_obj and conf in {"high", "medium"} else None),
                "item_codes": (item_obj.get("codes") if item_obj and conf in {"high", "medium"} else None),
                "match_score": score,
                "match_strategy": strategy,
                "confidence": conf,
                "dim_coherent": dim_coherent,
                "anchor_already_present": anchor_present,
            })

    # summary
    total = len(all_citations)
    conf_counter = Counter(c["confidence"] for c in all_citations)
    strategy_counter = Counter(c["match_strategy"] for c in all_citations)
    coherent_counter = Counter(c["dim_coherent"] for c in all_citations)
    with_item = sum(1 for c in all_citations if c["item_index"] is not None)

    summary = {
        "citations_total": total,
        "by_confidence": dict(conf_counter),
        "by_strategy": dict(strategy_counter),
        "by_dim_coherent": {str(k): v for k, v in coherent_counter.items()},
        "resolvable_to_item": with_item,
        "record_level_only": total - with_item,
    }
    return {"summary": summary, "citations": all_citations}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    print("Building citation mapping...", file=sys.stderr)
    report = build_mapping()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {args.output}", file=sys.stderr)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
