#!/usr/bin/env python3
"""Estrae campione stratificato di incoerenze wiki↔label per review.

Input: labels/citation-mapping-report.json
Output:
  - labels/incoherent-review-sample.json
  - labels/incoherent-review-sample.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT_DIR / "labels" / "citation-mapping-report.json"
DEFAULT_LABELS = ROOT_DIR / "labels" / "ollama-gemma4"
DEFAULT_JSON_OUT = ROOT_DIR / "labels" / "incoherent-review-sample.json"
DEFAULT_CSV_OUT = ROOT_DIR / "labels" / "incoherent-review-sample.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--labels-dir", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV_OUT)
    return parser.parse_args()


def population_from_stem(stem: str) -> str:
    if stem.startswith("insegnanti_attuali_"):
        return "insegnanti-attuali"
    if stem.startswith("insegnanti_futuri_"):
        return "insegnanti-futuri"
    if stem.startswith("studenti_"):
        return "studenti"
    return "altro"


def load_incoherent_cases(report: dict[str, Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    citations = report.get("citations")
    if isinstance(citations, list):
        for c in citations:
            wiki_dim = c.get("wiki_dim")
            label_dims = c.get("label_dims")
            if not wiki_dim or not isinstance(label_dims, list):
                continue
            if wiki_dim in label_dims:
                continue
            cases.append(
                {
                    "wiki_page": c.get("wiki_page"),
                    "raw_stem": c.get("raw_stem"),
                    "wiki_dim": wiki_dim,
                    "label_dims": label_dims,
                    "quoted_text": c.get("quoted_text", ""),
                    "match_item": c.get("match_item"),
                    "match_score": c.get("match_score"),
                    "offset": c.get("offset"),
                }
            )
        return cases

    # fallback su incoherent_cases (tipicamente troncato ai primi 50)
    for c in report.get("incoherent_cases", []):
        cases.append(
            {
                "wiki_page": c.get("wiki_page"),
                "raw_stem": c.get("raw_stem"),
                "wiki_dim": c.get("wiki_dim"),
                "label_dims": c.get("label_dims", []),
                "quoted_text": "",
                "match_item": None,
                "match_score": None,
                "offset": None,
            }
        )
    return cases


def dedupe_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, int | None]] = set()
    unique: list[dict[str, Any]] = []
    for case in cases:
        key = (
            str(case.get("wiki_page")),
            str(case.get("raw_stem")),
            str(case.get("wiki_dim")),
            case.get("offset"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def allocate_proportionally(strata_counts: dict[str, int], sample_size: int) -> dict[str, int]:
    strata = sorted(strata_counts.keys())
    if not strata:
        return {}

    allocation = {s: 0 for s in strata}
    total = sum(strata_counts.values())
    if sample_size <= 0:
        return allocation

    # Se possibile garantisci almeno 1 caso per strato.
    guaranteed = min(sample_size, len(strata))
    for stratum in strata[:guaranteed]:
        allocation[stratum] = 1

    remaining = sample_size - guaranteed
    if remaining <= 0:
        return allocation

    residual_capacity = {s: max(strata_counts[s] - allocation[s], 0) for s in strata}
    capacity_total = sum(residual_capacity.values())
    if capacity_total <= 0:
        return allocation

    raw_quota = {
        s: (residual_capacity[s] / capacity_total) * remaining for s in strata
    }
    floors = {s: int(raw_quota[s]) for s in strata}
    for s in strata:
        allocation[s] += floors[s]

    assigned = sum(floors.values())
    leftover = remaining - assigned
    ranked = sorted(
        strata,
        key=lambda s: (raw_quota[s] - floors[s], residual_capacity[s]),
        reverse=True,
    )
    i = 0
    while leftover > 0 and ranked:
        s = ranked[i % len(ranked)]
        if allocation[s] < strata_counts[s]:
            allocation[s] += 1
            leftover -= 1
        i += 1
        if i > 10000:  # guard rail
            break
    return allocation


def load_label_item(labels_dir: Path, stem: str, match_item: int | None) -> tuple[str, str, list[str]]:
    path = labels_dir / f"{stem}.json"
    if not path.exists() or match_item is None:
        return "", "", []
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("items", []):
        try:
            idx = int(item.get("index"))
        except Exception:  # noqa: BLE001
            continue
        if idx == match_item:
            return (
                str(item.get("question", "")),
                str(item.get("answer", "")),
                [str(c) for c in item.get("codes", [])],
            )
    return "", "", []


def suggest_authority(wiki_dim: str, item_codes: list[str], match_score: float | None) -> str:
    if item_codes:
        if any(code.startswith(wiki_dim) for code in item_codes):
            return "wiki"
        if match_score is not None and match_score >= 0.7:
            return "label"
    if match_score is not None and match_score < 0.5:
        return "unclear"
    return "unclear"


def build_sample(
    cases: list[dict[str, Any]],
    labels_dir: Path,
    sample_size: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        pop = population_from_stem(str(case["raw_stem"]))
        stratum = f"{case['wiki_dim']}|{pop}"
        case["population"] = pop
        case["stratum"] = stratum
        by_stratum[stratum].append(case)

    strata_counts = {k: len(v) for k, v in by_stratum.items()}
    allocation = allocate_proportionally(strata_counts, sample_size)
    rng = random.Random(seed)

    sampled: list[dict[str, Any]] = []
    for stratum, qty in allocation.items():
        if qty <= 0:
            continue
        pool = by_stratum[stratum]
        qty = min(qty, len(pool))
        sampled.extend(rng.sample(pool, qty))

    sampled = sorted(sampled, key=lambda c: (c["stratum"], c.get("wiki_page", ""), c.get("raw_stem", "")))

    enriched: list[dict[str, Any]] = []
    for idx, case in enumerate(sampled, start=1):
        question, answer, item_codes = load_label_item(
            labels_dir=labels_dir,
            stem=str(case["raw_stem"]),
            match_item=case.get("match_item"),
        )
        auto = suggest_authority(
            wiki_dim=str(case["wiki_dim"]),
            item_codes=item_codes,
            match_score=case.get("match_score"),
        )
        enriched.append(
            {
                "id": idx,
                "raw_stem": case["raw_stem"],
                "population": case["population"],
                "wiki_page": case["wiki_page"],
                "wiki_dim": case["wiki_dim"],
                "label_dims": case["label_dims"],
                "quoted_text": case.get("quoted_text", ""),
                "match_item": case.get("match_item"),
                "match_score": case.get("match_score"),
                "item_codes": item_codes,
                "item_question": question,
                "item_answer": answer,
                "auto_suggestion": auto,  # wiki | label | unclear
                "final_decision": "",  # compilare in review
                "review_note": "",
            }
        )

    summary = {
        "total_incoherent_cases": len(cases),
        "sample_size_requested": sample_size,
        "sample_size_built": len(enriched),
        "seed": seed,
        "strata_distribution_full": dict(sorted(strata_counts.items())),
        "strata_distribution_sample": dict(sorted(Counter(e["population"] + "|" + e["wiki_dim"] for e in enriched).items())),
        "allocation": dict(sorted(allocation.items())),
    }
    return enriched, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "raw_stem",
                "population",
                "wiki_page",
                "wiki_dim",
                "label_dims",
                "match_item",
                "match_score",
                "item_codes",
                "auto_suggestion",
                "final_decision",
                "review_note",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["id"],
                    row["raw_stem"],
                    row["population"],
                    row["wiki_page"],
                    row["wiki_dim"],
                    "|".join(row["label_dims"]),
                    row["match_item"],
                    row["match_score"],
                    "|".join(row["item_codes"]),
                    row["auto_suggestion"],
                    row["final_decision"],
                    row["review_note"],
                ]
            )


def main() -> int:
    args = parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    incoherent = dedupe_cases(load_incoherent_cases(report))
    sample, summary = build_sample(
        cases=incoherent,
        labels_dir=args.labels_dir,
        sample_size=args.sample_size,
        seed=args.seed,
    )

    payload = {"summary": summary, "sample": sample}
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(args.csv_out, sample)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"JSON: {args.json_out}")
    print(f"CSV: {args.csv_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
