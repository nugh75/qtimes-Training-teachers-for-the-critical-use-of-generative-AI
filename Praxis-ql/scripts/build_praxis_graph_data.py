#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from label_raw_with_ollama import CODEBOOK


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT_DIR / "labels" / "ollama-gemma4"
DEFAULT_OUTPUT_FILE = ROOT_DIR / "viz" / "praxis-graph-data.json"

DIMENSION_LABELS: dict[str, str] = {
    "A": "Adeguatezza del supporto",
    "I": "Fiducia interpersonale",
    "P": "Practice patterns",
    "R": "Readiness beliefs",
    "S": "Skepticisms",
    "X": "Expectations",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggrega i file label JSON in un dataset per il grafo relazionale "
            "delle dimensioni PRAXIS."
        )
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    return parser.parse_args()


def load_records(input_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("*.json")):
        if path.name in {"failures.json"}:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            records.append(payload)
    return records


def normalize_dimension(code: Any) -> str | None:
    if not isinstance(code, str) or len(code) < 2:
        return None
    dim = code[0].upper()
    if dim in DIMENSION_LABELS:
        return dim
    return None


def normalize_code(code: Any) -> str | None:
    if not isinstance(code, str):
        return None
    cleaned = code.strip().upper()
    if cleaned in CODEBOOK:
        return cleaned
    return None


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    node_counts: dict[str, Counter[str]] = defaultdict(Counter)
    edge_counts: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    subcode_counts: dict[str, Counter[str]] = defaultdict(Counter)
    subcode_edges: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    dimension_subcode_counts: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    items_count = Counter[str]()
    records_count = Counter[str]()

    for record in records:
        group = str(record.get("group", "Sconosciuto")).strip() or "Sconosciuto"
        scopes = ("ALL", group)
        for scope in scopes:
            records_count[scope] += 1

        for item in record.get("items", []):
            if not isinstance(item, dict):
                continue
            valid_codes = sorted(
                {
                    code
                    for raw in item.get("codes", [])
                    for code in [normalize_code(raw)]
                    if code
                }
            )
            dims = sorted(
                {
                    dim
                    for code in valid_codes
                    for dim in [normalize_dimension(code)]
                    if dim
                }
            )
            if not valid_codes or not dims:
                continue
            for scope in scopes:
                items_count[scope] += 1
                for dim in dims:
                    node_counts[scope][dim] += 1
                for code in valid_codes:
                    subcode_counts[scope][code] += 1
                    dimension_subcode_counts[scope][code[0]][code] += 1
                for left, right in combinations(dims, 2):
                    edge_counts[scope][(left, right)] += 1
                for left, right in combinations(valid_codes, 2):
                    subcode_edges[scope][(left, right)] += 1

    codebook_by_dimension: dict[str, list[dict[str, str]]] = defaultdict(list)
    for code, description in sorted(CODEBOOK.items()):
        dim = code[0].upper()
        if dim in DIMENSION_LABELS:
            codebook_by_dimension[dim].append(
                {"code": code, "description": description}
            )

    graphs: dict[str, Any] = {}
    all_scopes = sorted(set(node_counts.keys()) | set(records_count.keys()))
    for scope in all_scopes:
        counter = node_counts.get(scope, Counter())
        edge_counter = edge_counts.get(scope, Counter())
        sub_counter = subcode_counts.get(scope, Counter())
        sub_edge_counter = subcode_edges.get(scope, Counter())
        dim_sub_counter = dimension_subcode_counts.get(scope, {})

        nodes = [
            {
                "id": dim,
                "label": DIMENSION_LABELS[dim],
                "count": count,
                "codes": codebook_by_dimension.get(dim, []),
            }
            for dim, count in sorted(counter.items(), key=lambda x: (-x[1], x[0]))
        ]
        edges = [
            {
                "source": source,
                "target": target,
                "weight": weight,
            }
            for (source, target), weight in sorted(
                edge_counter.items(), key=lambda x: (-x[1], x[0][0], x[0][1])
            )
        ]
        total_mentions = sum(node["count"] for node in nodes) or 1
        top_dimensions = [
            {
                "id": node["id"],
                "label": node["label"],
                "count": node["count"],
                "share": round((node["count"] / total_mentions) * 100, 2),
            }
            for node in nodes
        ]
        total_sub_mentions = sum(sub_counter.values()) or 1
        subcodes = [
            {
                "id": code,
                "dimension": code[0],
                "label": CODEBOOK.get(code, ""),
                "count": count,
                "share": round((count / total_sub_mentions) * 100, 2),
            }
            for code, count in sorted(sub_counter.items(), key=lambda x: (-x[1], x[0]))
        ]
        top_subcodes = subcodes[:20]
        dimension_to_subcodes: dict[str, list[dict[str, Any]]] = {}
        for dim in sorted(DIMENSION_LABELS):
            local_counter = dim_sub_counter.get(dim, Counter())
            total_dim_mentions = sum(local_counter.values()) or 1
            dimension_to_subcodes[dim] = [
                {
                    "id": code,
                    "dimension": dim,
                    "label": CODEBOOK.get(code, ""),
                    "count": count,
                    "share_within_dimension": round(
                        (count / total_dim_mentions) * 100, 2
                    ),
                }
                for code, count in sorted(
                    local_counter.items(), key=lambda x: (-x[1], x[0])
                )
            ]
        subcode_relations = [
            {
                "source": source,
                "target": target,
                "weight": weight,
            }
            for (source, target), weight in sorted(
                sub_edge_counter.items(), key=lambda x: (-x[1], x[0][0], x[0][1])
            )
        ]

        graphs[scope] = {
            "nodes": nodes,
            "edges": edges,
            "records_count": records_count.get(scope, 0),
            "items_count": items_count.get(scope, 0),
            "total_dimension_mentions": total_mentions,
            "top_dimensions": top_dimensions,
            "subcodes": subcodes,
            "top_subcodes": top_subcodes,
            "total_subcode_mentions": total_sub_mentions,
            "dimension_to_subcodes": dimension_to_subcodes,
            "subcode_relations": subcode_relations,
        }

    return {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "records_total": len(records),
            "dimensions": DIMENSION_LABELS,
        },
        "graphs": graphs,
    }


def main() -> int:
    args = parse_args()
    records = load_records(args.input_dir)
    payload = aggregate(records)

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "records": payload["meta"]["records_total"],
                "scopes": sorted(payload["graphs"].keys()),
                "output_file": str(args.output_file),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
