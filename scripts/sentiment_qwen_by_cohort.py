#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
CORPUS_DIR = ROOT_DIR / "02-corpus"
DEFAULT_HOST = "http://192.168.129.14:11434"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "04-label" / "labels" / "ollama-qwen3-5-9b-sentiment"
LOGGER = logging.getLogger("sentiment_qwen_by_cohort")

FRONTMATTER_RE = re.compile(r"^---\n(?P<yaml>.*?)\n---\n", re.DOTALL)
ITEM_STRUCT_RE = re.compile(
    r"^## Item (?P<idx>\d+) \{#item-\d+\}\s*\n"
    r"(?:\s*\n)?"
    r"\*\*Q\*\*:\s*(?P<q>.*?)\s*\n"
    r"\*\*A\*\*:\s*(?P<a>.*?)\s*\n"
    r"\*\*Codes\*\*:",
    re.DOTALL | re.MULTILINE,
)

PLACEHOLDER_VALUES = {"", "-", "_", "--", "---", "\u2014", "\u2013"}
VALID_SENTIMENTS = {"positive", "neutral", "negative"}

GROUP_TO_COHORT = {
    "Insegnanti in servizio": "insegnanti_in_servizio",
    "Insegnanti pre-service": "insegnanti_pre_service",
    "Studenti": "studenti",
}

SYSTEM_PROMPT = """Sei un analista di sentiment in ambito educativo.
Analizza esclusivamente il testo della risposta (campo A), in italiano.

Regole:
1. Usa solo sentiment: positive, neutral, negative.
2. score deve essere compreso tra -1.0 e 1.0.
3. confidence deve essere compreso tra 0.0 e 1.0.
4. reason deve essere breve (max 20 parole) e basata solo sul testo.
5. Ignora domande, codici, reason, cited in e qualsiasi commento/metadato.
5. Restituisci solo JSON valido.
"""


@dataclass
class QAItem:
    index: int
    question: str
    answer: str


@dataclass
class RawRecord:
    source_file: Path
    title: str
    group: str
    record_code: str
    items: list[QAItem]


@dataclass
class SentimentItem:
    index: int
    question: str
    answer: str
    sentiment: str
    score: float
    confidence: float
    reason: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sentiment analysis PRAXIS con Qwen, con output separati per coorte."
    )
    parser.add_argument("--input-dir", type=Path, default=CORPUS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--glob", default="*.md")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--include-empty", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Abilita reasoning/thinking del modello (default: disabilitato).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def configure_logging(level_name: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def normalize_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_answer(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    parsed: dict[str, str] = {}
    for line in match.group("yaml").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip('"').strip("'")
    return parsed


def is_empty_answer(answer: str) -> bool:
    value = answer.strip().strip('"').strip("'")
    return value in PLACEHOLDER_VALUES


def parse_record(path: Path, include_empty: bool = False) -> RawRecord | None:
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    title_match = re.search(r"^#\s+(.*)$", text, flags=re.MULTILINE)
    title = normalize_inline(title_match.group(1)) if title_match else path.stem
    group = normalize_inline(frontmatter.get("group", "Sconosciuto"))
    code = normalize_inline(frontmatter.get("record_code", path.stem))

    items: list[QAItem] = []
    for match in ITEM_STRUCT_RE.finditer(text):
        idx = int(match.group("idx"))
        question = normalize_inline(match.group("q"))
        answer = normalize_answer(match.group("a"))
        if not include_empty and is_empty_answer(answer):
            continue
        items.append(QAItem(index=idx, question=question, answer=answer))

    if not items:
        return None

    return RawRecord(
        source_file=path,
        title=title,
        group=group,
        record_code=code,
        items=items,
    )


def cohort_slug(group: str) -> str:
    if group in GROUP_TO_COHORT:
        return GROUP_TO_COHORT[group]
    slug = re.sub(r"[^a-z0-9]+", "_", group.lower()).strip("_")
    return slug or "sconosciuto"


def build_user_prompt(record: RawRecord) -> str:
    answers = "\n\n".join(
        f"[{item.index}] RISPOSTA: {item.answer}" for item in record.items
    )

    return f"""Record:
- file: {record.source_file.name}
- gruppo: {record.group}
- codice partecipante: {record.record_code}

Risposte da classificare (usa solo il contenuto dopo "RISPOSTA"):
{answers}

Restituisci JSON con questa struttura:
{{
  "items": [
    {{
      "index": 1,
      "sentiment": "neutral",
      "score": 0.0,
      "confidence": 0.75,
      "reason": "breve motivazione"
    }}
  ]
}}

Vincoli:
- copri tutti gli index presenti;
- non ripetere domanda/risposta;
- usa solo sentiment: positive | neutral | negative.
"""


def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json(text: str) -> dict[str, Any]:
    cleaned = strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])


def ollama_chat(
    host: str,
    model: str,
    prompt: str,
    timeout: int,
    thinking: bool,
) -> dict[str, Any]:
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "think": thinking,
        "options": {
            "temperature": 0.1,
            "num_predict": 2048,
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    content = raw["message"]["content"]
    return extract_json(content)


def sanitize_sentiment(value: Any, score: float) -> str:
    token = normalize_inline(str(value)).lower()
    if token in VALID_SENTIMENTS:
        return token
    if score > 0.2:
        return "positive"
    if score < -0.2:
        return "negative"
    return "neutral"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def validate_model_output(record: RawRecord, payload: dict[str, Any]) -> list[SentimentItem]:
    by_index: dict[int, dict[str, Any]] = {}
    for raw_item in payload.get("items", []):
        if not isinstance(raw_item, dict):
            continue
        try:
            index = int(raw_item.get("index"))
        except (TypeError, ValueError):
            continue
        if index < 1:
            continue

        try:
            score = float(raw_item.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        try:
            confidence = float(raw_item.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        score = clamp(score, -1.0, 1.0)
        confidence = clamp(confidence, 0.0, 1.0)
        sentiment = sanitize_sentiment(raw_item.get("sentiment"), score)
        reason = normalize_inline(str(raw_item.get("reason", "")))

        by_index[index] = {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "reason": reason,
        }

    validated: list[SentimentItem] = []
    for item in record.items:
        normalized = by_index.get(
            item.index,
            {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "reason": "Nessuna classificazione valida restituita dal modello.",
            },
        )
        validated.append(
            SentimentItem(
                index=item.index,
                question=item.question,
                answer=item.answer,
                sentiment=normalized["sentiment"],
                score=normalized["score"],
                confidence=normalized["confidence"],
                reason=normalized["reason"],
            )
        )

    return validated


def build_result(record: RawRecord, items: list[SentimentItem], host: str, model: str) -> dict[str, Any]:
    sentiment_counts = Counter(item.sentiment for item in items)
    avg_score = sum(item.score for item in items) / len(items) if items else 0.0
    avg_confidence = sum(item.confidence for item in items) / len(items) if items else 0.0

    return {
        "source_file": str(record.source_file),
        "source_name": record.source_file.name,
        "title": record.title,
        "group": record.group,
        "cohort": cohort_slug(record.group),
        "record_code": record.record_code,
        "host": host,
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(items),
        "sentiment_counts": dict(sorted(sentiment_counts.items())),
        "avg_score": round(avg_score, 6),
        "avg_confidence": round(avg_confidence, 6),
        "items": [
            {
                "index": item.index,
                "question": item.question,
                "answer": item.answer,
                "sentiment": item.sentiment,
                "score": item.score,
                "confidence": item.confidence,
                "reason": item.reason,
            }
            for item in items
        ],
    }


def output_path_for(record: RawRecord, output_dir: Path) -> Path:
    return output_dir / f"{record.source_file.stem}.json"


def process_one(
    path: Path,
    output_dir: Path,
    host: str,
    model: str,
    timeout: int,
    overwrite: bool,
    include_empty: bool,
    dry_run: bool,
    thinking: bool,
) -> dict[str, Any]:
    record = parse_record(path, include_empty=include_empty)
    if record is None:
        return {"status": "empty", "path": str(path), "result": None}

    destination = output_path_for(record, output_dir)
    if destination.exists() and not overwrite and not dry_run:
        existing = json.loads(destination.read_text(encoding="utf-8"))
        return {"status": "skipped", "path": str(path), "result": existing}

    prompt = build_user_prompt(record)
    if dry_run:
        return {
            "status": "dry_run",
            "path": str(path),
            "record": {
                "source_name": record.source_file.name,
                "group": record.group,
                "record_code": record.record_code,
                "items": [item.__dict__ for item in record.items],
            },
            "prompt": prompt,
        }

    raw_payload = ollama_chat(
        host=host,
        model=model,
        prompt=prompt,
        timeout=timeout,
        thinking=thinking,
    )
    validated = validate_model_output(record, raw_payload)
    result = build_result(record, validated, host=host, model=model)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok", "path": str(path), "result": result}


def write_aggregates(results: list[dict[str, Any]], output_dir: Path) -> None:
    ok_results = [
        item["result"]
        for item in results
        if item["status"] in {"ok", "skipped"} and item.get("result")
    ]
    if not ok_results:
        return

    jsonl_path = output_dir / "all_items_sentiment.jsonl"
    all_items_csv = output_dir / "all_items_sentiment.csv"
    cohort_dir = output_dir / "by_cohort"
    summary_csv = output_dir / "summary_by_cohort.csv"

    cohort_dir.mkdir(parents=True, exist_ok=True)

    flat_rows: list[dict[str, Any]] = []
    for result in ok_results:
        for item in result["items"]:
            flat_rows.append(
                {
                    "source_name": result["source_name"],
                    "record_code": result["record_code"],
                    "group": result["group"],
                    "cohort": result["cohort"],
                    "item_index": item["index"],
                    "question": item["question"],
                    "answer": item["answer"],
                    "sentiment": item["sentiment"],
                    "score": item["score"],
                    "confidence": item["confidence"],
                    "reason": item["reason"],
                }
            )

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in flat_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    fields = [
        "source_name",
        "record_code",
        "group",
        "cohort",
        "item_index",
        "question",
        "answer",
        "sentiment",
        "score",
        "confidence",
        "reason",
    ]

    with all_items_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flat_rows)

    rows_by_cohort: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in flat_rows:
        rows_by_cohort[row["cohort"]].append(row)

    for cohort, rows in sorted(rows_by_cohort.items()):
        cohort_csv = cohort_dir / f"{cohort}.csv"
        with cohort_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    with summary_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "cohort",
                "items_total",
                "positive",
                "neutral",
                "negative",
                "avg_score",
                "avg_confidence",
            ]
        )

        for cohort, rows in sorted(rows_by_cohort.items()):
            sentiments = Counter(row["sentiment"] for row in rows)
            avg_score = sum(float(row["score"]) for row in rows) / len(rows)
            avg_conf = sum(float(row["confidence"]) for row in rows) / len(rows)
            writer.writerow(
                [
                    cohort,
                    len(rows),
                    sentiments.get("positive", 0),
                    sentiments.get("neutral", 0),
                    sentiments.get("negative", 0),
                    round(avg_score, 6),
                    round(avg_conf, 6),
                ]
            )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    files = sorted(args.input_dir.glob(args.glob))
    if args.limit:
        files = files[: args.limit]
    if not files:
        print("Nessun file trovato.", file=sys.stderr)
        return 1

    LOGGER.info(
        "Avvio sentiment: files=%s model=%s host=%s workers=%s dry_run=%s thinking=%s output_dir=%s",
        len(files),
        args.model,
        args.host,
        args.workers,
        args.dry_run,
        args.thinking,
        args.output_dir,
    )

    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    if args.dry_run or args.workers == 1:
        for idx, path in enumerate(files, start=1):
            LOGGER.info("[%s/%s] start %s", idx, len(files), path.name)
            try:
                result = process_one(
                    path=path,
                    output_dir=args.output_dir,
                    host=args.host,
                    model=args.model,
                    timeout=args.timeout,
                    overwrite=args.overwrite,
                    include_empty=args.include_empty,
                    dry_run=args.dry_run,
                    thinking=args.thinking,
                )
                results.append(result)
                LOGGER.info("[%s/%s] %s %s", idx, len(files), result["status"], path.name)
            except Exception as exc:  # noqa: BLE001
                failures.append({"path": str(path), "error": str(exc)})
                LOGGER.error("[%s/%s] failed %s: %s", idx, len(files), path.name, exc)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_map = {
                executor.submit(
                    process_one,
                    path,
                    args.output_dir,
                    args.host,
                    args.model,
                    args.timeout,
                    args.overwrite,
                    args.include_empty,
                    args.dry_run,
                    args.thinking,
                ): path
                for path in files
            }
            completed = 0
            for future in concurrent.futures.as_completed(future_map):
                path = future_map[future]
                completed += 1
                try:
                    result = future.result()
                    results.append(result)
                    LOGGER.info("[%s/%s] %s %s", completed, len(files), result["status"], path.name)
                except Exception as exc:  # noqa: BLE001
                    failures.append({"path": str(path), "error": str(exc)})
                    LOGGER.error("[%s/%s] failed %s: %s", completed, len(files), path.name, exc)

    if args.dry_run:
        sample = results[0] if results else {}
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_aggregates(results, args.output_dir)
        if failures:
            (args.output_dir / "failures.json").write_text(
                json.dumps(failures, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    elapsed = round(time.time() - started, 2)
    status_counts = Counter(item["status"] for item in results)
    LOGGER.info(
        "Completato: processed=%s failures=%s statuses=%s elapsed=%ss",
        len(results),
        len(failures),
        dict(status_counts),
        elapsed,
    )
    print(
        json.dumps(
            {
                "processed": len(results),
                "failures": len(failures),
                "statuses": dict(status_counts),
                "output_dir": str(args.output_dir),
                "elapsed_seconds": elapsed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0 if not failures else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except error.URLError as exc:
        print(f"Connessione Ollama fallita: {exc}", file=sys.stderr)
        raise SystemExit(2)
