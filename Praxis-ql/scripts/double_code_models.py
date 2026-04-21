#!/usr/bin/env python3
"""Double-coding con due modelli e report agreement item-level.

Workflow:
1) (opzionale) esegue labeling sugli stessi raw con due modelli;
2) confronta gli item tra i due output;
3) produce report JSON + CSV con accordo inter-rater.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from label_raw_with_ollama import (
    DEFAULT_HOST,
    RAW_DIR,
    default_output_dir_for_model,
    process_one,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_JSON = ROOT_DIR / "labels" / "double-coding-agreement.json"
DEFAULT_REPORT_CSV = ROOT_DIR / "labels" / "double-coding-item-agreement.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument(
        "--models",
        default="gemma4:31b,qwen3:32b",
        help="Due modelli separati da virgola.",
    )
    parser.add_argument("--glob", default="*.md")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--stems-file", type=Path)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument(
        "--heartbeat-seconds",
        type=int,
        default=30,
        help="Intervallo (s) per log di avanzamento quando non arrivano completamenti.",
    )
    parser.add_argument(
        "--log-queued",
        action="store_true",
        help="Logga ogni file messo in coda (verbose).",
    )
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--include-empty", action="store_true")
    parser.add_argument("--skip-labeling", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_REPORT_CSV)
    parser.add_argument(
        "--detailed-log",
        type=Path,
        help="Path file di log dettagliato del run (append).",
    )
    parser.add_argument("--max-disagreements", type=int, default=500)
    return parser.parse_args()


def parse_models(raw: str) -> list[str]:
    models = [m.strip() for m in raw.split(",") if m.strip()]
    unique: list[str] = []
    for model in models:
        if model not in unique:
            unique.append(model)
    if len(unique) != 2:
        raise ValueError("Servono esattamente 2 modelli (es: gemma4:31b,qwen3:32b).")
    return unique


def selected_files(input_dir: Path, glob: str, limit: int | None, stems_file: Path | None) -> list[Path]:
    files = sorted(input_dir.glob(glob))
    if stems_file:
        wanted = {
            line.strip()
            for line in stems_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        files = [path for path in files if path.stem in wanted]
    if limit:
        files = files[:limit]
    return files


def make_logger(log_path: Path | None):
    handle = None
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handle = log_path.open("a", encoding="utf-8")

    def _log(message: str) -> None:
        line = f"{datetime.now().isoformat(timespec='seconds')} {message}"
        print(line, file=sys.stderr)
        if handle:
            handle.write(line + "\n")
            handle.flush()

    return _log, handle


def timed_process_one(
    *,
    path: Path,
    output_dir: Path,
    host: str,
    model: str,
    timeout: int,
    overwrite: bool,
    include_empty: bool,
) -> tuple[dict[str, Any], float]:
    started = time.time()
    result = process_one(
        path=path,
        output_dir=output_dir,
        host=host,
        model=model,
        timeout=timeout,
        overwrite=overwrite,
        include_empty=include_empty,
        dry_run=False,
    )
    return result, round(time.time() - started, 2)


def run_labeling_for_model(
    model: str,
    files: list[Path],
    host: str,
    workers: int,
    heartbeat_seconds: int,
    log_queued: bool,
    timeout: int,
    overwrite: bool,
    include_empty: bool,
    log_fn,
) -> dict[str, Any]:
    output_dir = default_output_dir_for_model(model)
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    log_fn(
        f"[model-start] model={model} files={len(files)} workers={workers} output_dir={output_dir}"
    )
    if workers == 1:
        for path in files:
            try:
                log_fn(f"[start] model={model} file={path.name}")
                res, elapsed = timed_process_one(
                    path=path,
                    output_dir=output_dir,
                    host=host,
                    model=model,
                    timeout=timeout,
                    overwrite=overwrite,
                    include_empty=include_empty,
                )
                results.append(res)
                log_fn(
                    f"[done] model={model} file={path.name} status={res['status']} elapsed_s={elapsed}"
                )
            except Exception as exc:  # noqa: BLE001
                failures.append({"path": str(path), "error": str(exc)})
                log_fn(f"[error] model={model} file={path.name} error={exc}")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {
                executor.submit(
                    timed_process_one,
                    path=path,
                    output_dir=output_dir,
                    host=host,
                    model=model,
                    timeout=timeout,
                    overwrite=overwrite,
                    include_empty=include_empty,
                ): path
                for path in files
            }
            total = len(files)
            if log_queued:
                for path in files:
                    log_fn(f"[queued] model={model} file={path.name}")
            else:
                log_fn(f"[queued] model={model} files={total} detail=off")

            pending = set(future_map.keys())
            completed = 0
            wait_timeout = max(1, heartbeat_seconds)
            while pending:
                done, pending = concurrent.futures.wait(
                    pending,
                    timeout=wait_timeout,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                if not done:
                    log_fn(
                        f"[heartbeat] model={model} completed={completed}/{total} pending={len(pending)}"
                    )
                    continue

                for future in done:
                    path = future_map[future]
                    completed += 1
                    try:
                        result, elapsed = future.result()
                        results.append(result)
                        log_fn(
                            f"[done] model={model} file={path.name} status={result['status']} elapsed_s={elapsed} progress={completed}/{total}"
                        )
                    except Exception as exc:  # noqa: BLE001
                        failures.append({"path": str(path), "error": str(exc)})
                        log_fn(
                            f"[error] model={model} file={path.name} error={exc} progress={completed}/{total}"
                        )

    statuses = Counter(r["status"] for r in results)
    log_fn(
        f"[model-end] model={model} processed={len(results)} failures={len(failures)} statuses={dict(statuses)}"
    )
    return {
        "model": model,
        "output_dir": str(output_dir),
        "processed": len(results),
        "failures": failures,
        "statuses": dict(statuses),
    }


def load_labels(output_dir: Path, stems: list[str]) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for stem in stems:
        path = output_dir / f"{stem}.json"
        if not path.exists():
            continue
        loaded[stem] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def item_lookup(items: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for item in items:
        try:
            idx = int(item.get("index"))
        except Exception:  # noqa: BLE001
            continue
        out[idx] = item
    return out


def codeset(item: dict[str, Any] | None) -> set[str]:
    if not item:
        return set()
    return {str(code) for code in item.get("codes", [])}


def n1_count(label: dict[str, Any]) -> int:
    count = 0
    for item in label.get("items", []):
        for code in item.get("codes", []):
            if str(code).startswith("N1"):
                count += 1
    return count


def build_agreement_report(
    model_a: str,
    model_b: str,
    labels_a: dict[str, dict[str, Any]],
    labels_b: dict[str, dict[str, Any]],
    max_disagreements: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    stems_a = set(labels_a.keys())
    stems_b = set(labels_b.keys())
    common = sorted(stems_a & stems_b)
    missing_a = sorted(stems_b - stems_a)
    missing_b = sorted(stems_a - stems_b)

    rows: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    jaccards: list[float] = []
    exact_count = 0
    dim_exact_count = 0
    item_total = 0

    for stem in common:
        record_a = labels_a[stem]
        record_b = labels_b[stem]
        by_idx_a = item_lookup(record_a.get("items", []))
        by_idx_b = item_lookup(record_b.get("items", []))
        all_indices = sorted(set(by_idx_a.keys()) | set(by_idx_b.keys()))

        for idx in all_indices:
            item_a = by_idx_a.get(idx)
            item_b = by_idx_b.get(idx)
            set_a = codeset(item_a)
            set_b = codeset(item_b)
            dims_a = {code[0] for code in set_a if code}
            dims_b = {code[0] for code in set_b if code}
            score = round(jaccard(set_a, set_b), 4)
            exact = set_a == set_b
            dim_exact = dims_a == dims_b

            item_total += 1
            jaccards.append(score)
            if exact:
                exact_count += 1
            if dim_exact:
                dim_exact_count += 1

            row = {
                "raw_stem": stem,
                "item_index": idx,
                f"codes_{model_a}": sorted(set_a),
                f"codes_{model_b}": sorted(set_b),
                "exact_match": exact,
                "dimension_match": dim_exact,
                "jaccard": score,
                "question": (item_a or item_b or {}).get("question", ""),
                "answer": (item_a or item_b or {}).get("answer", ""),
            }
            rows.append(row)
            if not exact and len(disagreements) < max_disagreements:
                disagreements.append(row)

    summary = {
        "models": [model_a, model_b],
        "records_compared": len(common),
        f"records_missing_{model_a}": len(missing_a),
        f"records_missing_{model_b}": len(missing_b),
        "items_compared": item_total,
        "item_exact_set_agreement": round(exact_count / item_total, 4) if item_total else 0.0,
        "item_exact_dimension_agreement": round(dim_exact_count / item_total, 4) if item_total else 0.0,
        "item_mean_jaccard": round(mean(jaccards), 4) if jaccards else 0.0,
        f"n1_assignments_{model_a}": sum(n1_count(labels_a[stem]) for stem in common),
        f"n1_assignments_{model_b}": sum(n1_count(labels_b[stem]) for stem in common),
        "disagreements_captured": len(disagreements),
    }

    report = {
        "summary": summary,
        "missing_records": {
            model_a: missing_a,
            model_b: missing_b,
        },
        "disagreements": disagreements,
    }
    return report, rows


def write_item_csv(path: Path, rows: list[dict[str, Any]], model_a: str, model_b: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "raw_stem",
                "item_index",
                f"codes_{model_a}",
                f"codes_{model_b}",
                "exact_match",
                "dimension_match",
                "jaccard",
                "question",
                "answer",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["raw_stem"],
                    row["item_index"],
                    "|".join(row[f"codes_{model_a}"]),
                    "|".join(row[f"codes_{model_b}"]),
                    row["exact_match"],
                    row["dimension_match"],
                    row["jaccard"],
                    row["question"],
                    row["answer"],
                ]
            )


def main() -> int:
    args = parse_args()
    models = parse_models(args.models)
    files = selected_files(args.input_dir, args.glob, args.limit, args.stems_file)
    if not files:
        print("Nessun file raw selezionato.", file=sys.stderr)
        return 1
    log_fn, log_handle = make_logger(args.detailed_log)
    log_fn(
        f"[run-start] models={models} files={len(files)} host={args.host} timeout={args.timeout} overwrite={args.overwrite} workers={args.workers} heartbeat_s={args.heartbeat_seconds} log_queued={args.log_queued}"
    )

    stems = [path.stem for path in files]
    run_reports: list[dict[str, Any]] = []
    if not args.skip_labeling:
        for model in models:
            log_fn(f"[run] model={model} files={len(files)}")
            run_report = run_labeling_for_model(
                model=model,
                files=files,
                host=args.host,
                workers=args.workers,
                heartbeat_seconds=args.heartbeat_seconds,
                log_queued=args.log_queued,
                timeout=args.timeout,
                overwrite=args.overwrite,
                include_empty=args.include_empty,
                log_fn=log_fn,
            )
            run_reports.append(run_report)
            if run_report["failures"]:
                log_fn(f"[warn] model={model} failures={len(run_report['failures'])}")

    out_a = default_output_dir_for_model(models[0])
    out_b = default_output_dir_for_model(models[1])
    labels_a = load_labels(out_a, stems)
    labels_b = load_labels(out_b, stems)

    report, rows = build_agreement_report(
        model_a=models[0],
        model_b=models[1],
        labels_a=labels_a,
        labels_b=labels_b,
        max_disagreements=args.max_disagreements,
    )
    report["run_reports"] = run_reports
    report["input"] = {
        "files_selected": len(files),
        "glob": args.glob,
        "input_dir": str(args.input_dir),
        "stems_file": str(args.stems_file) if args.stems_file else None,
        "workers": args.workers,
        "heartbeat_seconds": args.heartbeat_seconds,
        "log_queued": args.log_queued,
        "detailed_log": str(args.detailed_log) if args.detailed_log else None,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_item_csv(args.csv_out, rows, models[0], models[1])
    log_fn(
        f"[run-end] summary={json.dumps(report['summary'], ensure_ascii=False)} json={args.json_out} csv={args.csv_out}"
    )
    if log_handle:
        log_handle.close()

    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    print(f"JSON: {args.json_out}", file=sys.stderr)
    print(f"CSV: {args.csv_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
