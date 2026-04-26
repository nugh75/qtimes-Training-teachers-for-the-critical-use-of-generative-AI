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
import unicodedata
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
DEFAULT_OUTPUT_DIR = (
    ROOT_DIR / "04-label" / "labels" / "ollama-qwen3-5-9b-prompt-complexity"
)
LOGGER = logging.getLogger("prompt_complexity_qwen_by_cohort")

FRONTMATTER_RE = re.compile(r"^---\n(?P<yaml>.*?)\n---\n", re.DOTALL)
ITEM_STRUCT_RE = re.compile(
    r"^## Item (?P<idx>\d+) \{#item-\d+\}\s*\n"
    r"(?:\s*\n)?"
    r"\*\*Q\*\*:\s*(?P<q>.*?)\s*\n"
    r"\*\*A\*\*:\s*(?P<a>.*?)\s*\n"
    r"\*\*Codes\*\*:",
    re.DOTALL | re.MULTILINE,
)

PROMPT_QUESTION_NEEDLES = (
    "esempi di prompt",
    "un prompt e un input",
    "un prompt e' un input",
)
PLACEHOLDER_VALUES = {"", "-", "_", "--", "---", "\u2014", "\u2013"}

GROUP_TO_COHORT = {
    "Insegnanti in servizio": "insegnanti_in_servizio",
    "Insegnanti pre-service": "insegnanti_pre_service",
    "Studenti": "studenti",
}

VALID_COMPLEXITY_LEVELS = {"assente", "base", "media", "alta"}
VALID_SPECIFICITY_LEVELS = {"assente", "bassa", "media", "alta"}
VALID_PROMPT_TYPES = {
    "non_prompt",
    "domanda_generica",
    "richiesta_operativa",
    "richiesta_didattica",
    "richiesta_creativa",
    "richiesta_valutativa",
    "meta_prompt",
    "altro",
}
STRATEGY_ORDER = [
    "riassunto",
    "spiegazione",
    "semplificazione",
    "traduzione",
    "esempio",
    "mappa_schema",
    "quiz_test",
    "lezione",
    "immagine_video",
    "attivita",
    "correzione",
    "ricerca",
    "scrittura",
    "pianificazione",
    "codice",
    "altro",
]
VALID_STRATEGIES = set(STRATEGY_ORDER)

COMPLEXITY_ALIASES = {
    "absent": "assente",
    "nessuna": "assente",
    "non_presente": "assente",
    "low": "base",
    "bassa": "base",
    "basic": "base",
    "medio": "media",
    "medium": "media",
    "alta": "alta",
    "high": "alta",
}
SPECIFICITY_ALIASES = {
    "absent": "assente",
    "nessuna": "assente",
    "low": "bassa",
    "base": "bassa",
    "basso": "bassa",
    "medio": "media",
    "medium": "media",
    "alta": "alta",
    "high": "alta",
}
PROMPT_TYPE_ALIASES = {
    "non prompt": "non_prompt",
    "nonprompt": "non_prompt",
    "generic_question": "domanda_generica",
    "domanda": "domanda_generica",
    "operational_request": "richiesta_operativa",
    "richiesta": "richiesta_operativa",
    "didactic_request": "richiesta_didattica",
    "educational_request": "richiesta_didattica",
    "creative_request": "richiesta_creativa",
    "evaluation_request": "richiesta_valutativa",
    "meta prompt": "meta_prompt",
    "metaprompt": "meta_prompt",
    "other": "altro",
}
STRATEGY_ALIASES = {
    "schema": "mappa_schema",
    "mappa": "mappa_schema",
    "mappe": "mappa_schema",
    "quiz": "quiz_test",
    "test": "quiz_test",
    "verifica": "quiz_test",
    "immagine": "immagine_video",
    "video": "immagine_video",
    "attivita_didattica": "attivita",
    "activity": "attivita",
    "correggere": "correzione",
    "correzioni": "correzione",
    "research": "ricerca",
    "writing": "scrittura",
    "planning": "pianificazione",
    "code": "codice",
    "other": "altro",
}

SYSTEM_PROMPT = """Sei un analista qualitativo di prompt literacy in ambito educativo.
Analizza esclusivamente il testo della risposta (campo A): e' l'esempio di prompt dichiarato dal partecipante.

Regole:
1. Valuta la complessita' del prompt, non la qualita' della risposta del modello.
2. Non usare conoscenze esterne e non inferire pratiche non presenti nel testo.
3. complexity_level deve essere: assente, base, media, alta.
4. specificity_level deve essere: assente, bassa, media, alta.
5. prompt_type deve essere uno tra quelli ammessi nel prompt utente.
6. strategies e' una lista di strategie ammesse, anche vuota.
7. I campi has_* sono booleani basati solo su evidenza testuale esplicita.
8. confidence deve essere compreso tra 0.0 e 1.0.
9. reason deve essere breve (max 25 parole).
10. Restituisci solo JSON valido.
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
class PromptMetrics:
    char_count: int
    word_count: int
    sentence_count: int
    question_mark_count: int
    request_count: int
    has_multiple_requests: bool
    is_empty_or_placeholder: bool


@dataclass
class PromptComplexityItem:
    index: int
    question: str
    answer: str
    metrics: PromptMetrics
    complexity_level: str
    specificity_level: str
    prompt_type: str
    strategies: list[str]
    has_role: bool
    has_context: bool
    has_constraints: bool
    has_output_format: bool
    has_audience: bool
    has_evaluation_criteria: bool
    has_iterative_instruction: bool
    confidence: float
    reason: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisi complessita' dei prompt PRAXIS con Qwen, separata per coorte."
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


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_for_match(text: str) -> str:
    text = strip_accents(text).lower()
    text = text.replace("e'", "e").replace("e`", "e")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return normalize_inline(text)


def normalize_token(value: Any) -> str:
    token = normalize_for_match(str(value))
    token = token.replace("-", "_").replace(" ", "_")
    token = re.sub(r"[^a-z0-9_]+", "", token)
    return token


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


def is_prompt_example_question(question: str) -> bool:
    normalized = normalize_for_match(question)
    return any(needle in normalized for needle in PROMPT_QUESTION_NEEDLES)


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
        if not is_prompt_example_question(question):
            continue
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


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text, flags=re.UNICODE))


def count_sentences(text: str) -> int:
    parts = [part for part in re.split(r"[.!?\n;]+", text) if part.strip()]
    return len(parts)


def count_requests(text: str) -> int:
    normalized = normalize_for_match(text)
    request_markers = [
        "puoi",
        "fammi",
        "fai",
        "crea",
        "scrivi",
        "spiega",
        "riassumi",
        "traduci",
        "correggi",
        "genera",
        "dammi",
        "fornisci",
        "prepara",
        "elenca",
        "suggerisci",
        "aiutami",
    ]
    count = sum(1 for marker in request_markers if re.search(rf"\b{marker}\b", normalized))
    structural_separators = len(re.findall(r"(?:^|\n)\s*(?:[-*]|\d+[.)])\s+", text))
    strong_separators = len(re.findall(r"[;\n]", text))
    if not normalized:
        return 0
    return max(1, count, min(structural_separators + strong_separators + 1, 6))


def build_metrics(answer: str) -> PromptMetrics:
    stripped = answer.strip()
    request_count = count_requests(stripped)
    return PromptMetrics(
        char_count=len(stripped),
        word_count=count_words(stripped),
        sentence_count=count_sentences(stripped),
        question_mark_count=stripped.count("?"),
        request_count=request_count,
        has_multiple_requests=request_count > 1,
        is_empty_or_placeholder=is_empty_answer(stripped),
    )


def build_user_prompt(record: RawRecord) -> str:
    answers = "\n\n".join(
        f"[{item.index}] RISPOSTA: {item.answer}" for item in record.items
    )
    allowed_types = ", ".join(sorted(VALID_PROMPT_TYPES))
    allowed_strategies = ", ".join(STRATEGY_ORDER)

    return f"""Record:
- file: {record.source_file.name}
- gruppo: {record.group}
- codice partecipante: {record.record_code}

Risposte alla domanda sugli esempi di prompt:
{answers}

Classifica ogni RISPOSTA secondo questa rubrica:
- assente: risposta vuota, non so, oppure non fornisce un esempio di prompt.
- base: richiesta breve con un solo obiettivo, senza contesto o vincoli.
- media: richiesta con obiettivo chiaro e almeno un elemento tra contesto, destinatario, vincolo o formato.
- alta: richiesta articolata con piu' elementi espliciti tra contesto, destinatario, vincoli, formato, criteri o sequenza.

Restituisci JSON con questa struttura:
{{
  "items": [
    {{
      "index": 3,
      "complexity_level": "base",
      "specificity_level": "bassa",
      "prompt_type": "richiesta_operativa",
      "strategies": ["riassunto"],
      "has_role": false,
      "has_context": false,
      "has_constraints": false,
      "has_output_format": false,
      "has_audience": false,
      "has_evaluation_criteria": false,
      "has_iterative_instruction": false,
      "confidence": 0.8,
      "reason": "Richiesta breve e chiara, senza contesto o vincoli."
    }}
  ]
}}

Vincoli:
- copri tutti gli index presenti;
- non ripetere domanda/risposta;
- usa solo complexity_level: assente | base | media | alta;
- usa solo specificity_level: assente | bassa | media | alta;
- usa solo prompt_type: {allowed_types};
- usa solo strategies: {allowed_strategies};
- se non ci sono strategie esplicite usa strategies: [];
- reason deve citare solo elementi presenti nella risposta.
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
            "num_predict": 3072,
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


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def sanitize_complexity(value: Any, metrics: PromptMetrics) -> str:
    token = normalize_token(value)
    if token in VALID_COMPLEXITY_LEVELS:
        return token
    if token in COMPLEXITY_ALIASES:
        return COMPLEXITY_ALIASES[token]
    if metrics.is_empty_or_placeholder:
        return "assente"
    if metrics.word_count >= 35 or metrics.request_count >= 4:
        return "alta"
    if metrics.word_count >= 14 or metrics.request_count >= 2:
        return "media"
    return "base"


def sanitize_specificity(value: Any, complexity_level: str) -> str:
    token = normalize_token(value)
    if token in VALID_SPECIFICITY_LEVELS:
        return token
    if token in SPECIFICITY_ALIASES:
        return SPECIFICITY_ALIASES[token]
    if complexity_level == "assente":
        return "assente"
    if complexity_level == "alta":
        return "alta"
    if complexity_level == "media":
        return "media"
    return "bassa"


def sanitize_prompt_type(value: Any, complexity_level: str) -> str:
    token = normalize_token(value)
    if token in VALID_PROMPT_TYPES:
        return token
    if token in PROMPT_TYPE_ALIASES:
        return PROMPT_TYPE_ALIASES[token]
    if complexity_level == "assente":
        return "non_prompt"
    return "altro"


def sanitize_strategy(value: Any) -> str:
    token = normalize_token(value)
    if token in VALID_STRATEGIES:
        return token
    return STRATEGY_ALIASES.get(token, "")


def sanitize_strategies(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    parsed: list[str] = []
    seen: set[str] = set()
    for value in raw:
        strategy = sanitize_strategy(value)
        if not strategy or strategy in seen:
            continue
        parsed.append(strategy)
        seen.add(strategy)
    return parsed


def sanitize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    token = normalize_token(value)
    return token in {"true", "vero", "si", "yes", "1"}


def sanitize_reason(value: Any) -> str:
    reason = normalize_inline(str(value))
    if len(reason) > 240:
        return reason[:237].rstrip() + "..."
    return reason


def validate_model_output(
    record: RawRecord,
    payload: dict[str, Any],
) -> list[PromptComplexityItem]:
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
        by_index[index] = raw_item

    validated: list[PromptComplexityItem] = []
    for item in record.items:
        metrics = build_metrics(item.answer)
        raw = by_index.get(item.index, {})
        complexity_level = sanitize_complexity(raw.get("complexity_level"), metrics)
        specificity_level = sanitize_specificity(
            raw.get("specificity_level"),
            complexity_level,
        )
        prompt_type = sanitize_prompt_type(raw.get("prompt_type"), complexity_level)
        strategies = sanitize_strategies(raw.get("strategies", []))
        try:
            confidence = float(raw.get("confidence", 0.0 if not raw else 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        reason = sanitize_reason(
            raw.get("reason", "Nessuna classificazione valida restituita dal modello.")
        )

        validated.append(
            PromptComplexityItem(
                index=item.index,
                question=item.question,
                answer=item.answer,
                metrics=metrics,
                complexity_level=complexity_level,
                specificity_level=specificity_level,
                prompt_type=prompt_type,
                strategies=strategies,
                has_role=sanitize_bool(raw.get("has_role", False)),
                has_context=sanitize_bool(raw.get("has_context", False)),
                has_constraints=sanitize_bool(raw.get("has_constraints", False)),
                has_output_format=sanitize_bool(raw.get("has_output_format", False)),
                has_audience=sanitize_bool(raw.get("has_audience", False)),
                has_evaluation_criteria=sanitize_bool(
                    raw.get("has_evaluation_criteria", False)
                ),
                has_iterative_instruction=sanitize_bool(
                    raw.get("has_iterative_instruction", False)
                ),
                confidence=clamp(confidence, 0.0, 1.0),
                reason=reason,
            )
        )
    return validated


def item_to_dict(item: PromptComplexityItem) -> dict[str, Any]:
    return {
        "index": item.index,
        "question": item.question,
        "answer": item.answer,
        "metrics": {
            "char_count": item.metrics.char_count,
            "word_count": item.metrics.word_count,
            "sentence_count": item.metrics.sentence_count,
            "question_mark_count": item.metrics.question_mark_count,
            "request_count": item.metrics.request_count,
            "has_multiple_requests": item.metrics.has_multiple_requests,
            "is_empty_or_placeholder": item.metrics.is_empty_or_placeholder,
        },
        "complexity_level": item.complexity_level,
        "specificity_level": item.specificity_level,
        "prompt_type": item.prompt_type,
        "strategies": item.strategies,
        "has_role": item.has_role,
        "has_context": item.has_context,
        "has_constraints": item.has_constraints,
        "has_output_format": item.has_output_format,
        "has_audience": item.has_audience,
        "has_evaluation_criteria": item.has_evaluation_criteria,
        "has_iterative_instruction": item.has_iterative_instruction,
        "confidence": item.confidence,
        "reason": item.reason,
    }


def build_result(
    record: RawRecord,
    items: list[PromptComplexityItem],
    host: str,
    model: str,
) -> dict[str, Any]:
    complexity_counts = Counter(item.complexity_level for item in items)
    specificity_counts = Counter(item.specificity_level for item in items)
    prompt_type_counts = Counter(item.prompt_type for item in items)
    strategy_counts = Counter(strategy for item in items for strategy in item.strategies)
    avg_words = sum(item.metrics.word_count for item in items) / len(items) if items else 0.0
    avg_confidence = sum(item.confidence for item in items) / len(items) if items else 0.0

    return {
        "schema_version": "prompt_complexity.v1",
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
        "complexity_counts": dict(sorted(complexity_counts.items())),
        "specificity_counts": dict(sorted(specificity_counts.items())),
        "prompt_type_counts": dict(sorted(prompt_type_counts.items())),
        "strategy_counts": dict(sorted(strategy_counts.items())),
        "avg_word_count": round(avg_words, 6),
        "avg_confidence": round(avg_confidence, 6),
        "items": [item_to_dict(item) for item in items],
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
        return {"status": "no_prompt_item", "path": str(path), "result": None}

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
    validated = validate_model_output(record=record, payload=raw_payload)
    result = build_result(record=record, items=validated, host=host, model=model)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok", "path": str(path), "result": result}


def split_pipe(value: str) -> list[str]:
    if not value:
        return []
    return [part for part in value.split("|") if part]


def flatten_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ok_results = [
        item["result"]
        for item in results
        if item["status"] in {"ok", "skipped"} and item.get("result")
    ]
    flat_rows: list[dict[str, Any]] = []
    for result in ok_results:
        for item in result["items"]:
            metrics = item["metrics"]
            strategies = item.get("strategies", [])
            row = {
                "source_name": result["source_name"],
                "record_code": result["record_code"],
                "group": result["group"],
                "cohort": result["cohort"],
                "item_index": item["index"],
                "question": item["question"],
                "answer": item["answer"],
                "char_count": metrics["char_count"],
                "word_count": metrics["word_count"],
                "sentence_count": metrics["sentence_count"],
                "question_mark_count": metrics["question_mark_count"],
                "request_count": metrics["request_count"],
                "has_multiple_requests": metrics["has_multiple_requests"],
                "is_empty_or_placeholder": metrics["is_empty_or_placeholder"],
                "complexity_level": item["complexity_level"],
                "specificity_level": item["specificity_level"],
                "prompt_type": item["prompt_type"],
                "strategies": "|".join(strategies),
                "strategy_count": len(strategies),
                "has_role": item["has_role"],
                "has_context": item["has_context"],
                "has_constraints": item["has_constraints"],
                "has_output_format": item["has_output_format"],
                "has_audience": item["has_audience"],
                "has_evaluation_criteria": item["has_evaluation_criteria"],
                "has_iterative_instruction": item["has_iterative_instruction"],
                "confidence": item["confidence"],
                "reason": item["reason"],
            }
            flat_rows.append(row)
    return flat_rows


def write_aggregates(results: list[dict[str, Any]], output_dir: Path) -> None:
    flat_rows = flatten_results(results)
    if not flat_rows:
        return

    jsonl_path = output_dir / "all_prompt_complexity.jsonl"
    all_items_csv = output_dir / "all_prompt_complexity.csv"
    cohort_dir = output_dir / "by_cohort"
    summary_csv = output_dir / "summary_by_cohort.csv"
    summary_strategy_csv = output_dir / "summary_by_strategy.csv"
    summary_type_csv = output_dir / "summary_by_prompt_type.csv"
    cohort_dir.mkdir(parents=True, exist_ok=True)

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
        "char_count",
        "word_count",
        "sentence_count",
        "question_mark_count",
        "request_count",
        "has_multiple_requests",
        "is_empty_or_placeholder",
        "complexity_level",
        "specificity_level",
        "prompt_type",
        "strategies",
        "strategy_count",
        "has_role",
        "has_context",
        "has_constraints",
        "has_output_format",
        "has_audience",
        "has_evaluation_criteria",
        "has_iterative_instruction",
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
                "assente",
                "base",
                "media",
                "alta",
                "avg_word_count",
                "avg_request_count",
                "avg_confidence",
                "with_role",
                "with_context",
                "with_constraints",
                "with_output_format",
                "with_audience",
                "with_evaluation_criteria",
                "with_iterative_instruction",
                "top_strategies",
            ]
        )
        for cohort, rows in sorted(rows_by_cohort.items()):
            complexity = Counter(row["complexity_level"] for row in rows)
            strategy_counter: Counter[str] = Counter()
            for row in rows:
                for strategy in split_pipe(row["strategies"]):
                    strategy_counter[strategy] += 1

            top_strategies = "|".join(
                f"{strategy}:{count}"
                for strategy, count in strategy_counter.most_common(5)
            )
            writer.writerow(
                [
                    cohort,
                    len(rows),
                    complexity.get("assente", 0),
                    complexity.get("base", 0),
                    complexity.get("media", 0),
                    complexity.get("alta", 0),
                    round(sum(int(row["word_count"]) for row in rows) / len(rows), 6),
                    round(sum(int(row["request_count"]) for row in rows) / len(rows), 6),
                    round(sum(float(row["confidence"]) for row in rows) / len(rows), 6),
                    sum(1 for row in rows if row["has_role"]),
                    sum(1 for row in rows if row["has_context"]),
                    sum(1 for row in rows if row["has_constraints"]),
                    sum(1 for row in rows if row["has_output_format"]),
                    sum(1 for row in rows if row["has_audience"]),
                    sum(1 for row in rows if row["has_evaluation_criteria"]),
                    sum(1 for row in rows if row["has_iterative_instruction"]),
                    top_strategies,
                ]
            )

    with summary_strategy_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cohort", "strategy", "count", "item_share"])
        for cohort, rows in sorted(rows_by_cohort.items()):
            counter: Counter[str] = Counter()
            for row in rows:
                for strategy in split_pipe(row["strategies"]):
                    counter[strategy] += 1
            for strategy, count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0])):
                writer.writerow([cohort, strategy, count, round(count / len(rows), 6)])

    with summary_type_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cohort", "prompt_type", "count", "item_share"])
        for cohort, rows in sorted(rows_by_cohort.items()):
            counter = Counter(row["prompt_type"] for row in rows)
            for prompt_type, count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0])):
                writer.writerow([cohort, prompt_type, count, round(count / len(rows), 6)])


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
        (
            "Avvio prompt-complexity: files=%s model=%s host=%s workers=%s "
            "dry_run=%s thinking=%s output_dir=%s"
        ),
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
        sample = next((result for result in results if result["status"] == "dry_run"), {})
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
