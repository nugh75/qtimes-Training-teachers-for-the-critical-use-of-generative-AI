#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "raw"
WIKI_DIR = ROOT_DIR / "wiki"
LABELS_DIR = ROOT_DIR / "labels" / "ollama-gemma4"
OUTPUT_DIR = ROOT_DIR / "labels" / "ollama-gemma4-wiki-links"
DEFAULT_HOST = "http://192.168.129.14:11434"
DEFAULT_MODEL = "gemma4:e4b"
LOGGER = logging.getLogger("link_raw_to_wiki")


POPULATION_MAP = {
    "Insegnanti in servizio": "insegnanti-attuali",
    "Insegnanti pre-service": "insegnanti-futuri",
    "Studenti": "studenti",
}

DIM_NAMES = {
    "P": "Practice patterns",
    "R": "Readiness beliefs",
    "A": "Adequacy of support",
    "X": "eXpectations",
    "I": "Interpersonal & Institutional trust",
    "S": "Skepticisms",
}


SYSTEM_PROMPT = """Sei un codificatore qualitativo esperto del framework PRAXIS.
Devi collegare un record raw alle pagine wiki tematiche gia' esistenti per la sua popolazione.

Regole:
1. Usa solo gli slug di pagina forniti nel catalogo.
2. Un record puo' essere collegato a zero, una o piu' pagine per ciascuna dimensione rilevante.
3. Non inventare pagine.
4. Preferisci poche pagine molto pertinenti a molte pagine marginali.
5. La reason deve citare brevemente il contenuto del record che giustifica il link (max 25 parole).
6. Restituisci JSON valido e nient'altro.
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
    code: str
    items: list[QAItem]


@dataclass
class WikiPage:
    slug: str
    title: str
    dimension: str
    population: str
    summary: str
    is_index: bool = False


@dataclass
class LabelData:
    dimensions: list[str] = field(default_factory=list)
    subcodes: list[str] = field(default_factory=list)
    record_note: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collega i file raw PRAXIS alle pagine wiki tematiche via LLM Ollama."
    )
    parser.add_argument("--input-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--wiki-dir", type=Path, default=WIKI_DIR)
    parser.add_argument("--labels-dir", type=Path, default=LABELS_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--glob", default="*.md")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-index-pages",
        action="store_true",
        help="Esclude dal catalogo le pagine di sintesi di dimensione.",
    )
    parser.add_argument(
        "--require-labels",
        action="store_true",
        help="Salta i record privi di file label JSON.",
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


def parse_raw_markdown(path: Path) -> RawRecord:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.*)$", text, flags=re.MULTILINE)
    group_match = re.search(r"\*\*Gruppo di origine:\*\*\s*(.*)", text)
    item_pattern = re.compile(r"- \*\*(.*?)\*\*: ?(.*?)(?=\n- \*\*|\Z)", re.DOTALL)

    title = normalize_inline(title_match.group(1)) if title_match else path.stem
    group = normalize_inline(group_match.group(1)) if group_match else "Sconosciuto"

    items: list[QAItem] = []
    code = ""
    index = 1
    for match in item_pattern.finditer(text):
        question = normalize_inline(match.group(1))
        answer = re.sub(r"\n{3,}", "\n\n", match.group(2).strip())
        if question.lower() == "codice":
            code = normalize_inline(answer)
            continue
        if answer in {"", "-", "."}:
            continue
        items.append(QAItem(index=index, question=question, answer=answer))
        index += 1

    return RawRecord(
        source_file=path,
        title=title,
        group=group,
        code=code or path.stem,
        items=items,
    )


DIM_LETTER_RE = re.compile(r"\*\*Dimensione\*\*\s*:\s*.*?\(([PRAXIS])\)", re.IGNORECASE)
DIM_LETTER_HEAD_RE = re.compile(r"^#\s+([PRAXIS])\s*[—\-]", re.MULTILINE)
SUMMARY_RE = re.compile(r"\*\*Summary\*\*\s*:\s*(.+?)(?:\n\n|\Z)", re.DOTALL)


def parse_wiki_page(path: Path, wiki_root: Path) -> WikiPage | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    rel = path.relative_to(wiki_root)
    parts = rel.parts
    if not parts:
        return None
    population = parts[0]
    if population not in POPULATION_MAP.values():
        return None

    title_match = re.search(r"^#\s+(.*)$", text, flags=re.MULTILINE)
    title = normalize_inline(title_match.group(1)) if title_match else path.stem

    dim_match = DIM_LETTER_RE.search(text)
    if dim_match:
        dimension = dim_match.group(1).upper()
    else:
        head_match = DIM_LETTER_HEAD_RE.search(text)
        dimension = head_match.group(1).upper() if head_match else ""

    if not dimension:
        return None

    summary_match = SUMMARY_RE.search(text)
    summary = normalize_inline(summary_match.group(1)) if summary_match else ""
    if len(summary) > 400:
        summary = summary[:400].rsplit(" ", 1)[0] + "…"

    is_index = path.stem.startswith(f"{dimension.lower()}-") or "index-" in path.stem or path.stem.startswith(dimension.lower())
    # heuristic: pages whose filename matches dimension-slug-pop are indices
    is_index = bool(
        re.match(
            r"^(practice-patterns|readiness-beliefs|adequacy-of-support|expectations|interpersonal-trust|skepticisms)",
            path.stem,
        )
    ) and "-" in path.stem and path.stem.count("-") >= 2

    slug = str(Path("wiki") / rel).replace("\\", "/")

    return WikiPage(
        slug=slug,
        title=title,
        dimension=dimension,
        population=population,
        summary=summary,
        is_index=is_index,
    )


def build_wiki_catalog(wiki_root: Path, skip_index: bool) -> dict[str, dict[str, list[WikiPage]]]:
    catalog: dict[str, dict[str, list[WikiPage]]] = {
        pop: {d: [] for d in DIM_NAMES}
        for pop in POPULATION_MAP.values()
    }
    for md_path in wiki_root.rglob("*.md"):
        page = parse_wiki_page(md_path, wiki_root)
        if page is None:
            continue
        if skip_index and page.is_index:
            continue
        catalog[page.population][page.dimension].append(page)
    for pop in catalog:
        for dim in catalog[pop]:
            catalog[pop][dim].sort(key=lambda p: (not p.is_index, p.title.lower()))
    return catalog


def load_label(labels_dir: Path, stem: str) -> LabelData | None:
    path = labels_dir / f"{stem}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return LabelData(
        dimensions=list(data.get("record_dimensions", [])),
        subcodes=list(data.get("record_subcodes", [])),
        record_note=str(data.get("record_note", "")),
    )


def population_for(record: RawRecord) -> str | None:
    return POPULATION_MAP.get(record.group)


def build_user_prompt(
    record: RawRecord,
    population: str,
    dimensions: list[str],
    catalog: dict[str, dict[str, list[WikiPage]]],
    label: LabelData | None,
) -> tuple[str, dict[str, WikiPage]]:
    slug_index: dict[str, WikiPage] = {}
    blocks: list[str] = []
    for dim in dimensions:
        pages = catalog.get(population, {}).get(dim, [])
        if not pages:
            continue
        lines = [f"### Dimensione {dim} — {DIM_NAMES[dim]}"]
        for page in pages:
            slug_index[page.slug] = page
            summary = f" — {page.summary}" if page.summary else ""
            flag = " (indice)" if page.is_index else ""
            lines.append(f"- `{page.slug}`{flag}: **{page.title}**{summary}")
        blocks.append("\n".join(lines))

    catalog_text = "\n\n".join(blocks) if blocks else "(nessuna pagina disponibile)"

    qas = "\n\n".join(
        f"[{item.index}] DOMANDA: {item.question}\nRISPOSTA: {item.answer}"
        for item in record.items
    )

    label_hint = ""
    if label is not None:
        label_hint = (
            f"\nEtichette pre-assegnate: dimensioni={label.dimensions}, "
            f"subcodici={label.subcodes}\n"
            f"Nota sintetica record: {label.record_note}\n"
        )

    return (
        f"""Popolazione: {population}
Record:
- file: {record.source_file.name}
- gruppo: {record.group}
- codice partecipante: {record.code}
{label_hint}
Catalogo pagine wiki disponibili per le dimensioni pertinenti:
{catalog_text}

Item del record:
{qas}

Restituisci un JSON con questa struttura:
{{
  "record_pages": [
    {{"slug": "wiki/...", "dimension": "P", "reason": "..."}}
  ],
  "items": [
    {{
      "index": 1,
      "pages": [
        {{"slug": "wiki/...", "dimension": "X", "reason": "..."}}
      ]
    }}
  ]
}}

Vincoli:
- gli slug devono esistere nel catalogo;
- un item puo' avere 0 pagine;
- non ripetere il testo del record, solo brevi reason;
- non inventare slug o dimensioni.
""",
        slug_index,
    )


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


def ollama_chat(host: str, model: str, prompt: str, timeout: int) -> dict[str, Any]:
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    return extract_json(raw["message"]["content"])


def validate_output(
    record: RawRecord,
    payload: dict[str, Any],
    slug_index: dict[str, WikiPage],
) -> dict[str, Any]:
    def clean_page_entry(entry: Any) -> dict[str, Any] | None:
        if not isinstance(entry, dict):
            return None
        slug = str(entry.get("slug", "")).strip()
        page = slug_index.get(slug)
        if page is None:
            return None
        dimension = str(entry.get("dimension", page.dimension)).upper().strip() or page.dimension
        if dimension not in DIM_NAMES:
            dimension = page.dimension
        return {
            "slug": slug,
            "title": page.title,
            "dimension": dimension,
            "is_index": page.is_index,
            "reason": normalize_inline(str(entry.get("reason", ""))),
        }

    record_pages: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    for raw_entry in payload.get("record_pages", []) or []:
        clean = clean_page_entry(raw_entry)
        if clean and clean["slug"] not in seen_slugs:
            seen_slugs.add(clean["slug"])
            record_pages.append(clean)

    by_index: dict[int, list[dict[str, Any]]] = {}
    for item in payload.get("items", []) or []:
        if not isinstance(item, dict):
            continue
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError):
            continue
        if index < 1 or index > len(record.items):
            continue
        cleaned: list[dict[str, Any]] = []
        seen: set[str] = set()
        for page_entry in item.get("pages", []) or []:
            clean = clean_page_entry(page_entry)
            if clean and clean["slug"] not in seen:
                seen.add(clean["slug"])
                cleaned.append(clean)
        by_index[index] = cleaned

    normalized_items: list[dict[str, Any]] = []
    for src in record.items:
        normalized_items.append(
            {
                "index": src.index,
                "question": src.question,
                "answer": src.answer,
                "pages": by_index.get(src.index, []),
            }
        )

    # union item pages into record_pages if LLM omitted them
    for item in normalized_items:
        for page in item["pages"]:
            if page["slug"] not in seen_slugs:
                seen_slugs.add(page["slug"])
                record_pages.append(
                    {
                        "slug": page["slug"],
                        "title": page["title"],
                        "dimension": page["dimension"],
                        "is_index": page["is_index"],
                        "reason": "",
                    }
                )

    return {"record_pages": record_pages, "items": normalized_items}


def build_result(
    record: RawRecord,
    population: str,
    dimensions: list[str],
    validated: dict[str, Any],
    label: LabelData | None,
    host: str,
    model: str,
) -> dict[str, Any]:
    slug_counts = Counter(
        page["slug"] for item in validated["items"] for page in item["pages"]
    )
    dim_counts = Counter(page["dimension"] for page in validated["record_pages"])
    return {
        "source_file": str(record.source_file),
        "source_name": record.source_file.name,
        "title": record.title,
        "group": record.group,
        "record_code": record.code,
        "population": population,
        "dimensions_considered": dimensions,
        "label_dimensions": label.dimensions if label else [],
        "label_subcodes": label.subcodes if label else [],
        "host": host,
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_pages": validated["record_pages"],
        "page_counts": dict(sorted(slug_counts.items())),
        "dimension_counts": dict(sorted(dim_counts.items())),
        "items": validated["items"],
    }


def process_one(
    path: Path,
    catalog: dict[str, dict[str, list[WikiPage]]],
    labels_dir: Path,
    output_dir: Path,
    host: str,
    model: str,
    timeout: int,
    overwrite: bool,
    require_labels: bool,
    dry_run: bool,
) -> dict[str, Any]:
    record = parse_raw_markdown(path)
    population = population_for(record)
    if population is None:
        return {"status": "skipped_group", "path": str(path)}

    label = load_label(labels_dir, path.stem)
    if require_labels and label is None:
        return {"status": "missing_label", "path": str(path)}

    dimensions = sorted(set(label.dimensions)) if label and label.dimensions else list(DIM_NAMES)

    destination = output_dir / f"{path.stem}.json"
    if destination.exists() and not overwrite and not dry_run:
        existing = json.loads(destination.read_text(encoding="utf-8"))
        return {"status": "skipped", "path": str(path), "result": existing}

    prompt, slug_index = build_user_prompt(
        record=record,
        population=population,
        dimensions=dimensions,
        catalog=catalog,
        label=label,
    )

    if dry_run:
        return {
            "status": "dry_run",
            "path": str(path),
            "population": population,
            "dimensions": dimensions,
            "catalog_size": len(slug_index),
            "prompt": prompt,
        }

    if not slug_index:
        return {"status": "no_pages", "path": str(path), "population": population}

    raw_payload = ollama_chat(host=host, model=model, prompt=prompt, timeout=timeout)
    validated = validate_output(record, raw_payload, slug_index)
    result = build_result(
        record=record,
        population=population,
        dimensions=dimensions,
        validated=validated,
        label=label,
        host=host,
        model=model,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"status": "ok", "path": str(path), "result": result}


def write_summary(results: list[dict[str, Any]], output_dir: Path) -> None:
    ok = [r["result"] for r in results if r["status"] in {"ok", "skipped"}]
    if not ok:
        return
    jsonl = output_dir / "summary.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for item in ok:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    page_to_records: dict[str, list[str]] = {}
    for item in ok:
        for page in item.get("record_pages", []):
            page_to_records.setdefault(page["slug"], []).append(item["record_code"])
    backlinks = output_dir / "backlinks.json"
    backlinks.write_text(
        json.dumps(
            {slug: sorted(set(codes)) for slug, codes in sorted(page_to_records.items())},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    catalog = build_wiki_catalog(args.wiki_dir, args.skip_index_pages)
    pages_total = sum(len(pages) for pops in catalog.values() for pages in pops.values())
    LOGGER.info("Catalogo wiki: %s pagine totali", pages_total)

    files = sorted(args.input_dir.glob(args.glob))
    if args.limit:
        files = files[: args.limit]
    if not files:
        print("Nessun file raw trovato.", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    total = len(files)
    LOGGER.info(
        "Avvio linking: files=%s model=%s host=%s workers=%s dry_run=%s",
        total, args.model, args.host, args.workers, args.dry_run,
    )

    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    def run_one(path: Path) -> dict[str, Any]:
        return process_one(
            path=path,
            catalog=catalog,
            labels_dir=args.labels_dir,
            output_dir=args.output_dir,
            host=args.host,
            model=args.model,
            timeout=args.timeout,
            overwrite=args.overwrite,
            require_labels=args.require_labels,
            dry_run=args.dry_run,
        )

    if args.dry_run or args.workers == 1:
        for index, path in enumerate(files, start=1):
            LOGGER.info("[%s/%s] start %s", index, total, path.name)
            try:
                result = run_one(path)
                results.append(result)
                LOGGER.info("[%s/%s] %s %s", index, total, result["status"], path.name)
            except Exception as exc:  # noqa: BLE001
                failures.append({"path": str(path), "error": str(exc)})
                LOGGER.error("[%s/%s] failed %s: %s", index, total, path.name, exc)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_map = {executor.submit(run_one, path): path for path in files}
            completed = 0
            for future in concurrent.futures.as_completed(future_map):
                path = future_map[future]
                completed += 1
                try:
                    result = future.result()
                    results.append(result)
                    LOGGER.info(
                        "[%s/%s] %s %s", completed, total, result["status"], path.name
                    )
                except Exception as exc:  # noqa: BLE001
                    failures.append({"path": str(path), "error": str(exc)})
                    LOGGER.error(
                        "[%s/%s] failed %s: %s", completed, total, path.name, exc
                    )

    if not args.dry_run:
        write_summary(results, args.output_dir)
        if failures:
            (args.output_dir / "failures.json").write_text(
                json.dumps(failures, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    elapsed = round(time.time() - started, 2)
    status_counts = Counter(item["status"] for item in results)
    LOGGER.info(
        "Completato: processed=%s failures=%s statuses=%s elapsed=%ss",
        len(results), len(failures), dict(status_counts), elapsed,
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
