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
LABELS_DIR = ROOT_DIR / "04-label" / "labels"
DEFAULT_HOST = "http://192.168.129.14:11434"
DEFAULT_MODEL = "qwen3.5:9b"

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
TEACHER_GROUPS = {"Insegnanti in servizio", "Insegnanti pre-service"}
GROUP_TO_COHORT = {
    "Insegnanti in servizio": "insegnanti_in_servizio",
    "Insegnanti pre-service": "insegnanti_pre_service",
    "Studenti": "studenti",
}

USAGE_CATEGORIES = [
    "efficienza_tempo",
    "personalizzazione",
    "individualizzazione",
    "supporto_comprensione",
    "produzione_materiali",
    "ricerca_informazioni",
    "feedback_valutazione",
    "creativita_coinvolgimento",
    "accessibilita_inclusione",
    "autonomia_organizzazione",
    "delega_cognitiva",
    "plagio_autorialita",
    "affidabilita_errori",
    "privacy_etica",
    "disuguaglianze",
    "riduzione_relazione",
    "standardizzazione",
    "dipendenza",
    "altro",
]

PERSONALIZATION_STRATEGIES = [
    "interessi_studenti",
    "scelte_percorsi",
    "potenzialita_talenti",
    "materiali_differenziati",
    "modalita_espressive",
    "attivita_elettive",
    "motivazione_coinvolgimento",
    "obiettivi_personali",
    "supporti_bes_dsa",
    "altro",
]

INDIVIDUALIZATION_STRATEGIES = [
    "recupero_prerequisiti",
    "livelli_difficolta",
    "scaffolding_guidato",
    "esercizi_differenziati",
    "semplificazione",
    "raggiungimento_competenze",
    "valutazione_formativa",
    "feedback_mirato",
    "supporti_bes_dsa",
    "altro",
]


@dataclass(frozen=True)
class AnalysisConfig:
    name: str
    logger_name: str
    schema_version: str
    default_output_dir: Path
    description: str
    no_item_status: str
    question_needles: tuple[str, ...]
    allowed_groups: set[str] | None
    system_prompt: str
    task_prompt: str
    output_example: str
    allowed_values_text: str
    aggregate_mode: str


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


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


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


def cohort_slug(group: str) -> str:
    if group in GROUP_TO_COHORT:
        return GROUP_TO_COHORT[group]
    slug = re.sub(r"[^a-z0-9]+", "_", group.lower()).strip("_")
    return slug or "sconosciuto"


def question_matches(question: str, needles: tuple[str, ...]) -> bool:
    normalized = normalize_for_match(question)
    return any(needle in normalized for needle in needles)


def parse_record(
    path: Path,
    config: AnalysisConfig,
    include_empty: bool = False,
) -> RawRecord | None:
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    title_match = re.search(r"^#\s+(.*)$", text, flags=re.MULTILINE)
    title = normalize_inline(title_match.group(1)) if title_match else path.stem
    group = normalize_inline(frontmatter.get("group", "Sconosciuto"))
    code = normalize_inline(frontmatter.get("record_code", path.stem))

    if config.allowed_groups is not None and group not in config.allowed_groups:
        return None

    items: list[QAItem] = []
    for match in ITEM_STRUCT_RE.finditer(text):
        idx = int(match.group("idx"))
        question = normalize_inline(match.group("q"))
        answer = normalize_answer(match.group("a"))
        if not question_matches(question, config.question_needles):
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


def parse_args(config: AnalysisConfig) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=config.description)
    parser.add_argument("--input-dir", type=Path, default=CORPUS_DIR)
    parser.add_argument("--output-dir", type=Path, default=config.default_output_dir)
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


def build_user_prompt(record: RawRecord, config: AnalysisConfig) -> str:
    answers = "\n\n".join(
        f"[{item.index}] DOMANDA: {item.question}\n[{item.index}] RISPOSTA: {item.answer}"
        for item in record.items
    )
    return f"""Record:
- file: {record.source_file.name}
- gruppo: {record.group}
- codice partecipante: {record.record_code}

{config.task_prompt}

Item da analizzare:
{answers}

Restituisci JSON con questa struttura:
{config.output_example}

Valori ammessi e vincoli:
{config.allowed_values_text}
- copri tutti gli index presenti;
- non ripetere domanda/risposta;
- reason deve essere breve e basata solo sulla risposta;
- evidence deve essere un breve estratto presente nella risposta;
- confidence deve essere compreso tra 0.0 e 1.0.
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
    system_prompt: str,
    user_prompt: str,
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
            "num_predict": 4096,
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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


def sanitize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    token = normalize_token(value)
    return token in {"true", "vero", "si", "yes", "1"}


def sanitize_text(value: Any, max_len: int = 240) -> str:
    text = normalize_inline(str(value or ""))
    if len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text


def sanitize_float(value: Any, default: float = 0.5) -> float:
    try:
        return clamp(float(value), 0.0, 1.0)
    except (TypeError, ValueError):
        return default


def sanitize_choice(value: Any, allowed: list[str], aliases: dict[str, str], default: str) -> str:
    token = normalize_token(value)
    allowed_set = set(allowed)
    if token in allowed_set:
        return token
    if token in aliases:
        return aliases[token]
    return default


def sanitize_list(raw: Any, allowed: list[str], aliases: dict[str, str] | None = None) -> list[str]:
    if not isinstance(raw, list):
        return []
    aliases = aliases or {}
    parsed: list[str] = []
    seen: set[str] = set()
    for value in raw:
        token = normalize_token(value)
        if token in aliases:
            token = aliases[token]
        if token not in allowed or token in seen:
            continue
        parsed.append(token)
        seen.add(token)
    return parsed


def sanitize_usage_entries(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        category = sanitize_choice(
            entry.get("category"),
            USAGE_CATEGORIES,
            {
                "time_saving": "efficienza_tempo",
                "efficienza": "efficienza_tempo",
                "personalization": "personalizzazione",
                "individualization": "individualizzazione",
                "comprensione": "supporto_comprensione",
                "materials": "produzione_materiali",
                "valutazione": "feedback_valutazione",
                "creativita": "creativita_coinvolgimento",
                "inclusione": "accessibilita_inclusione",
                "plagio": "plagio_autorialita",
                "errori": "affidabilita_errori",
                "privacy": "privacy_etica",
                "relazione": "riduzione_relazione",
                "other": "altro",
            },
            "altro",
        )
        entries.append(
            {
                "category": category,
                "evidence": sanitize_text(entry.get("evidence"), 220),
                "reason": sanitize_text(entry.get("reason"), 240),
            }
        )
    return entries


def validate_pro_con(record: RawRecord, payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_index = index_payload(payload)
    output: list[dict[str, Any]] = []
    for item in record.items:
        raw = by_index.get(item.index, {})
        pros = sanitize_usage_entries(raw.get("pros", []))
        cons = sanitize_usage_entries(raw.get("cons", []))
        stance = sanitize_choice(
            raw.get("stance"),
            ["solo_pro", "solo_contro", "misto", "nessuno"],
            {
                "only_pro": "solo_pro",
                "only_con": "solo_contro",
                "mixed": "misto",
                "none": "nessuno",
                "non_classificabile": "nessuno",
            },
            "misto" if pros and cons else "solo_pro" if pros else "solo_contro" if cons else "nessuno",
        )
        output.append(
            {
                "index": item.index,
                "question": item.question,
                "answer": item.answer,
                "stance": stance,
                "pros": pros,
                "cons": cons,
                "pro_count": len(pros),
                "con_count": len(cons),
                "confidence": sanitize_float(raw.get("confidence"), 0.0 if not raw else 0.5),
                "reason": sanitize_text(
                    raw.get("reason", "Nessuna classificazione valida restituita dal modello.")
                ),
            }
        )
    return output


def validate_teacher_practices(
    record: RawRecord,
    payload: dict[str, Any],
    allowed_strategies: list[str],
) -> list[dict[str, Any]]:
    by_index = index_payload(payload)
    output: list[dict[str, Any]] = []
    for item in record.items:
        raw = by_index.get(item.index, {})
        strategies = sanitize_list(
            raw.get("strategies", []),
            allowed_strategies,
            {"bes": "supporti_bes_dsa", "dsa": "supporti_bes_dsa", "other": "altro"},
        )
        output.append(
            {
                "index": item.index,
                "question": item.question,
                "answer": item.answer,
                "practice_present": sanitize_bool(raw.get("practice_present", bool(strategies))),
                "strategies": strategies,
                "target": sanitize_choice(
                    raw.get("target"),
                    ["singolo_studente", "gruppo_classe", "sottogruppo", "non_specificato"],
                    {
                        "individuale": "singolo_studente",
                        "classe": "gruppo_classe",
                        "gruppo": "sottogruppo",
                        "none": "non_specificato",
                    },
                    "non_specificato",
                ),
                "ai_role": sanitize_choice(
                    raw.get("ai_role"),
                    ["generazione_materiali", "suggerimento_strategie", "adattamento_contenuti", "feedback", "altro", "non_specificato"],
                    {
                        "materials": "generazione_materiali",
                        "strategy": "suggerimento_strategie",
                        "adaptation": "adattamento_contenuti",
                        "other": "altro",
                        "none": "non_specificato",
                    },
                    "non_specificato",
                ),
                "evidence": sanitize_text(raw.get("evidence"), 220),
                "confidence": sanitize_float(raw.get("confidence"), 0.0 if not raw else 0.5),
                "reason": sanitize_text(
                    raw.get("reason", "Nessuna classificazione valida restituita dal modello.")
                ),
            }
        )
    return output


def index_payload(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    by_index: dict[int, dict[str, Any]] = {}
    for raw_item in payload.get("items", []):
        if not isinstance(raw_item, dict):
            continue
        try:
            index = int(raw_item.get("index"))
        except (TypeError, ValueError):
            continue
        if index >= 1:
            by_index[index] = raw_item
    return by_index


def validate_model_output(
    record: RawRecord,
    payload: dict[str, Any],
    config: AnalysisConfig,
) -> list[dict[str, Any]]:
    if config.aggregate_mode == "pro_con":
        return validate_pro_con(record, payload)
    if config.aggregate_mode == "personalization":
        return validate_teacher_practices(record, payload, PERSONALIZATION_STRATEGIES)
    if config.aggregate_mode == "individualization":
        return validate_teacher_practices(record, payload, INDIVIDUALIZATION_STRATEGIES)
    raise ValueError(f"Modalita' aggregazione sconosciuta: {config.aggregate_mode}")


def build_result(
    record: RawRecord,
    items: list[dict[str, Any]],
    host: str,
    model: str,
    config: AnalysisConfig,
) -> dict[str, Any]:
    return {
        "schema_version": config.schema_version,
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
        "items": items,
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
    config: AnalysisConfig,
) -> dict[str, Any]:
    record = parse_record(path, config=config, include_empty=include_empty)
    if record is None:
        return {"status": config.no_item_status, "path": str(path), "result": None}

    destination = output_path_for(record, output_dir)
    if destination.exists() and not overwrite and not dry_run:
        existing = json.loads(destination.read_text(encoding="utf-8"))
        return {"status": "skipped", "path": str(path), "result": existing}

    prompt = build_user_prompt(record, config)
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
        system_prompt=config.system_prompt,
        user_prompt=prompt,
        timeout=timeout,
        thinking=thinking,
    )
    validated = validate_model_output(record, raw_payload, config)
    result = build_result(record, validated, host, model, config)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok", "path": str(path), "result": result}


def split_pipe(value: str) -> list[str]:
    if not value:
        return []
    return [part for part in value.split("|") if part]


def flatten_pro_con(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in ok_results(results):
        for item in result["items"]:
            base = base_row(result, item)
            base.update(
                {
                    "stance": item["stance"],
                    "pro_count": item["pro_count"],
                    "con_count": item["con_count"],
                    "pro_categories": "|".join(entry["category"] for entry in item["pros"]),
                    "con_categories": "|".join(entry["category"] for entry in item["cons"]),
                    "pros_json": json.dumps(item["pros"], ensure_ascii=False),
                    "cons_json": json.dumps(item["cons"], ensure_ascii=False),
                    "confidence": item["confidence"],
                    "reason": item["reason"],
                }
            )
            rows.append(base)
    return rows


def flatten_teacher_practices(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in ok_results(results):
        for item in result["items"]:
            base = base_row(result, item)
            base.update(
                {
                    "practice_present": item["practice_present"],
                    "strategies": "|".join(item["strategies"]),
                    "strategy_count": len(item["strategies"]),
                    "target": item["target"],
                    "ai_role": item["ai_role"],
                    "evidence": item["evidence"],
                    "confidence": item["confidence"],
                    "reason": item["reason"],
                }
            )
            rows.append(base)
    return rows


def base_row(result: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": result["source_name"],
        "record_code": result["record_code"],
        "group": result["group"],
        "cohort": result["cohort"],
        "item_index": item["index"],
        "question": item["question"],
        "answer": item["answer"],
    }


def ok_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item["result"]
        for item in results
        if item["status"] in {"ok", "skipped"} and item.get("result")
    ]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_aggregates(results: list[dict[str, Any]], output_dir: Path, config: AnalysisConfig) -> None:
    if config.aggregate_mode == "pro_con":
        rows = flatten_pro_con(results)
        basename = "all_pro_con"
    else:
        rows = flatten_teacher_practices(results)
        basename = f"all_{config.aggregate_mode}"

    if not rows:
        return

    write_csv(output_dir / f"{basename}.csv", rows)
    write_jsonl(output_dir / f"{basename}.jsonl", rows)

    cohort_dir = output_dir / "by_cohort"
    cohort_dir.mkdir(parents=True, exist_ok=True)
    rows_by_cohort: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_cohort[row["cohort"]].append(row)
    for cohort, cohort_rows in sorted(rows_by_cohort.items()):
        write_csv(cohort_dir / f"{cohort}.csv", cohort_rows)

    if config.aggregate_mode == "pro_con":
        write_pro_con_summaries(rows, output_dir)
    else:
        write_teacher_practice_summaries(rows, output_dir)


def write_pro_con_summaries(rows: list[dict[str, Any]], output_dir: Path) -> None:
    rows_by_cohort: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_cohort[row["cohort"]].append(row)

    with (output_dir / "summary_by_cohort.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cohort", "items_total", "solo_pro", "solo_contro", "misto", "nessuno", "pros_total", "cons_total", "avg_confidence"])
        for cohort, cohort_rows in sorted(rows_by_cohort.items()):
            stances = Counter(row["stance"] for row in cohort_rows)
            writer.writerow(
                [
                    cohort,
                    len(cohort_rows),
                    stances.get("solo_pro", 0),
                    stances.get("solo_contro", 0),
                    stances.get("misto", 0),
                    stances.get("nessuno", 0),
                    sum(int(row["pro_count"]) for row in cohort_rows),
                    sum(int(row["con_count"]) for row in cohort_rows),
                    round(sum(float(row["confidence"]) for row in cohort_rows) / len(cohort_rows), 6),
                ]
            )

    with (output_dir / "summary_categories.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cohort", "polarity", "category", "count", "item_share"])
        for cohort, cohort_rows in sorted(rows_by_cohort.items()):
            for polarity, field in [("pro", "pro_categories"), ("contro", "con_categories")]:
                counter: Counter[str] = Counter()
                for row in cohort_rows:
                    for category in split_pipe(row[field]):
                        counter[category] += 1
                for category, count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0])):
                    writer.writerow([cohort, polarity, category, count, round(count / len(cohort_rows), 6)])


def write_teacher_practice_summaries(rows: list[dict[str, Any]], output_dir: Path) -> None:
    rows_by_cohort: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_cohort[row["cohort"]].append(row)

    with (output_dir / "summary_by_cohort.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cohort", "items_total", "practice_present", "avg_confidence", "top_strategies", "top_targets", "top_ai_roles"])
        for cohort, cohort_rows in sorted(rows_by_cohort.items()):
            strategies: Counter[str] = Counter()
            targets = Counter(row["target"] for row in cohort_rows)
            roles = Counter(row["ai_role"] for row in cohort_rows)
            for row in cohort_rows:
                for strategy in split_pipe(row["strategies"]):
                    strategies[strategy] += 1
            writer.writerow(
                [
                    cohort,
                    len(cohort_rows),
                    sum(1 for row in cohort_rows if row["practice_present"]),
                    round(sum(float(row["confidence"]) for row in cohort_rows) / len(cohort_rows), 6),
                    "|".join(f"{key}:{value}" for key, value in strategies.most_common(5)),
                    "|".join(f"{key}:{value}" for key, value in targets.most_common(5)),
                    "|".join(f"{key}:{value}" for key, value in roles.most_common(5)),
                ]
            )

    with (output_dir / "summary_strategies.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cohort", "strategy", "count", "item_share"])
        for cohort, cohort_rows in sorted(rows_by_cohort.items()):
            counter: Counter[str] = Counter()
            for row in cohort_rows:
                for strategy in split_pipe(row["strategies"]):
                    counter[strategy] += 1
            for strategy, count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0])):
                writer.writerow([cohort, strategy, count, round(count / len(cohort_rows), 6)])


def main(config: AnalysisConfig) -> int:
    args = parse_args(config)
    configure_logging(args.log_level)
    logger = logging.getLogger(config.logger_name)

    files = sorted(args.input_dir.glob(args.glob))
    if args.limit:
        files = files[: args.limit]
    if not files:
        print("Nessun file trovato.", file=sys.stderr)
        return 1

    logger.info(
        "Avvio %s: files=%s model=%s host=%s workers=%s dry_run=%s output_dir=%s",
        config.name,
        len(files),
        args.model,
        args.host,
        args.workers,
        args.dry_run,
        args.output_dir,
    )

    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    if args.dry_run or args.workers == 1:
        for idx, path in enumerate(files, start=1):
            logger.info("[%s/%s] start %s", idx, len(files), path.name)
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
                    config=config,
                )
                results.append(result)
                logger.info("[%s/%s] %s %s", idx, len(files), result["status"], path.name)
            except Exception as exc:  # noqa: BLE001
                failures.append({"path": str(path), "error": str(exc)})
                logger.error("[%s/%s] failed %s: %s", idx, len(files), path.name, exc)
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
                    config,
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
                    logger.info("[%s/%s] %s %s", completed, len(files), result["status"], path.name)
                except Exception as exc:  # noqa: BLE001
                    failures.append({"path": str(path), "error": str(exc)})
                    logger.error("[%s/%s] failed %s: %s", completed, len(files), path.name, exc)

    if args.dry_run:
        sample = next((result for result in results if result["status"] == "dry_run"), {})
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_aggregates(results, args.output_dir, config)
        if failures:
            (args.output_dir / "failures.json").write_text(
                json.dumps(failures, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    elapsed = round(time.time() - started, 2)
    status_counts = Counter(item["status"] for item in results)
    logger.info(
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


def run(config: AnalysisConfig) -> None:
    try:
        raise SystemExit(main(config))
    except error.URLError as exc:
        print(f"Connessione Ollama fallita: {exc}", file=sys.stderr)
        raise SystemExit(2)
