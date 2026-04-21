#!/usr/bin/env python3
"""Audit coerenza wiki ↔ labels + matching citazioni → item.

Read-only. Produce:
  labels/citation-mapping-report.json

Operazioni:
  1. Scansiona ogni wiki/*.md → estrae citazioni (source: [code](.../raw/STEM.md))
  2. Per ogni citazione:
     - determina wiki_dim da path pagina (wiki/POP/DIM/... o flat file)
     - estrae quote text (testo fra virgolette alte prima del link, se presente)
     - lookup labels/STEM.json → items[] con answer, codes
     - fuzzy match quote vs items[].answer → best item
  3. Produce report aggregato + per-citazione.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
WIKI_DIR = ROOT_DIR / "wiki"
LABELS_DIR = ROOT_DIR / "labels" / "ollama-gemma4"
REPORT_PATH = ROOT_DIR / "labels" / "citation-mapping-report.json"

CITATION_RE = re.compile(
    r"\(source:\s*\[(?P<code>[^\]]+)\]\((?P<path>\.{1,2}(?:/\.\.)*(?:/[^)]+)?/raw/(?P<stem>[^)#]+?)\.md)(?P<anchor>#[^)]*)?\)",
    re.IGNORECASE,
)

# Ultimo testo fra virgolette alte o basse prima della citazione
QUOTE_NEAR_RE = re.compile(r"[«\"]([^«»\"]{5,500})[»\"]\s*\([^)]*?source:", re.DOTALL)

DIM_FROM_PATH = {
    "practice-patterns": "P",
    "readiness-beliefs": "R",
    "adequacy-of-support": "A",
    "expectations": "X",
    "interpersonal-trust": "I",
    "skepticisms": "S",
}


def extract_wiki_dim(wiki_path: Path) -> str | None:
    """Determine PRAXIS dim from wiki file path.

    Esempi:
      wiki/insegnanti-attuali/readiness-beliefs/non-uso-consapevole.md -> R
      wiki/insegnanti-attuali/readiness-beliefs-insegnanti-attuali.md  -> R
      wiki/studenti/adequacy-of-support-studenti.md                    -> A
      wiki/studenti/non-classificati.md                                -> None
    """
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
    return re.sub(r"\s+", " ", text).strip().lower()


def best_item_match(quote: str, items: list[dict]) -> tuple[int | None, float]:
    """Trova item con answer più simile a quote. Ritorna (item_index, score)."""
    if not quote or not items:
        return None, 0.0
    qn = normalize(quote)
    best_idx = None
    best_score = 0.0
    for item in items:
        answer = item.get("answer", "")
        an = normalize(answer)
        if not an:
            continue
        # Score: ratio SequenceMatcher; boost se qn è substring di an
        score = difflib.SequenceMatcher(None, qn, an).ratio()
        if qn and qn in an:
            score = max(score, 0.9)
        if an and an in qn:
            score = max(score, 0.85)
        if score > best_score:
            best_score = score
            best_idx = item.get("index")
    return best_idx, round(best_score, 3)


def scan_wiki_citations() -> list[dict]:
    citations = []
    for md in sorted(WIKI_DIR.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        wiki_dim = extract_wiki_dim(md)
        # scorri linee per preservare contesto
        for m in CITATION_RE.finditer(text):
            stem = m.group("stem")
            anchor = m.group("anchor") or ""
            # cerca quote immediatamente prima
            start = max(0, m.start() - 600)
            snippet = text[start:m.start()]
            q_match = None
            for q in QUOTE_NEAR_RE.finditer(snippet + text[m.start():m.end()]):
                q_match = q
            quote = q_match.group(1).strip() if q_match else ""
            citations.append({
                "wiki_page": str(md.relative_to(ROOT_DIR)),
                "wiki_dim": wiki_dim,
                "raw_stem": stem,
                "raw_code": m.group("code"),
                "anchor_present": bool(anchor),
                "quoted_text": quote,
                "offset": m.start(),
            })
    return citations


def audit(citations: list[dict]) -> dict:
    total = len(citations)
    coherent = 0
    incoherent = []
    no_label = []
    matched_items = []
    unmatched_quotes = 0
    low_conf = 0

    # raw stems used
    stems_used = set(c["raw_stem"] for c in citations)

    for c in citations:
        stem = c["raw_stem"]
        label = load_label(stem)
        if label is None:
            no_label.append({
                "wiki_page": c["wiki_page"],
                "raw_stem": stem,
                "raw_code": c["raw_code"],
            })
            c["label_dims"] = None
            c["match_item"] = None
            c["match_score"] = None
            continue

        label_dims = label.get("record_dimensions", [])
        c["label_dims"] = label_dims

        wdim = c["wiki_dim"]
        if wdim is None:
            # pagina senza dim (es. non-classificati) — salto coerenza
            pass
        elif wdim in label_dims:
            coherent += 1
        else:
            incoherent.append({
                "wiki_page": c["wiki_page"],
                "raw_stem": stem,
                "wiki_dim": wdim,
                "label_dims": label_dims,
            })

        items = label.get("items", [])
        quote = c["quoted_text"]
        if quote:
            idx, score = best_item_match(quote, items)
            c["match_item"] = idx
            c["match_score"] = score
            if idx is None:
                unmatched_quotes += 1
            elif score < 0.6:
                low_conf += 1
            else:
                matched_items.append({
                    "wiki_page": c["wiki_page"],
                    "raw_stem": stem,
                    "item": idx,
                    "score": score,
                })
        else:
            c["match_item"] = None
            c["match_score"] = None

    # raw stems classificati ma mai citati
    all_label_stems = set(p.stem for p in LABELS_DIR.glob("*.json") if p.stem not in {"failures"})
    uncited = sorted(all_label_stems - stems_used)
    null_label = []
    for stem in sorted(all_label_stems):
        label = load_label(stem)
        if label and not label.get("record_dimensions"):
            null_label.append(stem)

    # dim dove pagina wiki cita
    wiki_dim_counter = Counter(c["wiki_dim"] for c in citations if c["wiki_dim"])

    return {
        "summary": {
            "citations_total": total,
            "distinct_raw_cited": len(stems_used),
            "coherent_dim_match": coherent,
            "incoherent_dim_mismatch": len(incoherent),
            "citations_without_label": len(no_label),
            "quotes_with_high_confidence_match": len([c for c in citations if c.get("match_score") and c["match_score"] >= 0.6]),
            "quotes_with_low_confidence_match": low_conf,
            "quotes_unmatched": unmatched_quotes,
            "citations_without_quote": len([c for c in citations if not c["quoted_text"]]),
            "raw_label_uncited": len(uncited),
            "raw_null_label": len(null_label),
            "wiki_dim_distribution": dict(wiki_dim_counter),
        },
        "incoherent_cases": incoherent[:50],
        "incoherent_total": len(incoherent),
        "citations_without_label": no_label[:20],
        "uncited_raw": uncited,
        "null_label_raw": null_label,
        "citations": citations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    print("Scanning wiki citations...", file=sys.stderr)
    citations = scan_wiki_citations()
    print(f"Trovate {len(citations)} citazioni", file=sys.stderr)

    print("Running audit...", file=sys.stderr)
    report = audit(citations)

    if args.summary_only:
        print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    else:
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report scritto: {args.output}", file=sys.stderr)
        print(json.dumps(report["summary"], indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
