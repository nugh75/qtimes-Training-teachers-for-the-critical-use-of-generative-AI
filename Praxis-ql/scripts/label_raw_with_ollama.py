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
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "raw"
OUTPUT_DIR = ROOT_DIR / "labels" / "ollama-gemma4"
DEFAULT_HOST = "http://192.168.129.14:11434"
DEFAULT_MODEL = "gemma4:e4b"
LOGGER = logging.getLogger("label_raw_with_ollama")


CODEBOOK: dict[str, str] = {
    "P1": "Produzione di materiali didattici o di studio: verifiche, quiz, riassunti, mappe, esercizi, spiegazioni, materiali di supporto.",
    "P2": "Individualizzazione e personalizzazione: adattamento di spiegazioni, testi, attivita' o percorsi al singolo studente o gruppo.",
    "P3": "Inclusione e accessibilita': CAA, supporti multimodali, traduzioni per NAI, accesso a contenuti per studenti fragili.",
    "P4": "Supporto allo studio, simulazione, tutoraggio: autovalutazione, interrogazioni simulate, chiarimenti, allenamento.",
    "P5": "Strategie operative di produzione: riassunti, schemi, mappe, spiegazioni, traduzioni, riscritture, esempi, visualizzazioni.",
    "P6": "Ecosistema di strumenti: strumenti e piattaforme usati, singoli o in combinazione.",
    "P7": "Prompting visibile: presenza di prompt riportati o descritti come pratica concreta.",
    "R1": "Competenza pratica percepita: saper usare o non saper usare strumenti e prompt.",
    "R2": "Competenza teorica o epistemologica: comprensione o non comprensione di limiti, funzionamento e verifica dell'IA.",
    "R3": "Gap tra uso personale e uso didattico: uso privato piu' sicuro dell'uso pedagogico.",
    "R4": "Competenza di prompting: capacita' di formulare prompt efficaci.",
    "R5": "Non-uso per impreparazione o rifiuto competente: non uso motivato da insicurezza, scelta epistemica o resistenza consapevole.",
    "A1": "Assenza di formazione formale: mancano corsi, accompagnamento o inserimento curricolare.",
    "A2": "Supporto insufficiente o diseguale: supporto sporadico, tardivo o inadeguato.",
    "A3": "Vincoli infrastrutturali ed economici: dispositivi, connessione, licenze, paywall, accesso diseguale.",
    "A4": "Uso compensativo dell'IA: l'IA colma lacune del sistema formativo o didattico.",
    "X1": "Efficienza e risparmio di tempo.",
    "X2": "Semplificazione e comprensione: chiarificazione, comprensione piu' rapida, focalizzazione dei concetti.",
    "X3": "Personalizzazione e attenzione al singolo.",
    "X4": "Inclusione e accesso.",
    "X5": "Autonomia, organizzazione e supporto al percorso.",
    "X6": "Coinvolgimento, arricchimento e innovazione.",
    "X7": "Cambiamento condizionato: beneficio subordinato a controllo umano e uso critico.",
    "I1": "Fiducia tecnica condizionata: utile ma da verificare e controllare.",
    "I2": "Sfiducia tecnica: errori, allucinazioni, traduzioni scorrette, versioni sbagliate.",
    "I3": "Fiducia o sfiducia negli utenti: uso etico e responsabile da parte di studenti o docenti.",
    "I4": "Fiducia relazionale e pedagogica: insostituibilita' di relazione, empatia, giudizio umano.",
    "I5": "Privacy e affidamento dei dati.",
    "S1": "Delega cognitiva eccessiva: pigrizia, dipendenza, non fare piu' nulla da soli.",
    "S2": "Ghostwriting e plagio: testi, temi, tesi, elaborati o compiti spacciati come propri.",
    "S3": "Appiattimento, omologazione, perdita di creativita'.",
    "S4": "Erosione del pensiero critico.",
    "S5": "Informazioni false, imprecisione, affidabilita' debole.",
    "S6": "Sostituzione del docente o della relazione educativa.",
    "S7": "Ambiti off-limits: relazioni umane, scrittura soggettiva, valutazione, lingue classiche, matematica, medicina, diagnosi, counseling.",
    "N1": "Risposta non classificabile: troppo breve, generica, vuota, tautologica o fuori tema per attribuzione di codici PRAXIS.",
}


SYSTEM_PROMPT = """Sei un codificatore qualitativo esperto del framework PRAXIS.
Devi leggere un singolo record in formato domanda-risposta e assegnare soltanto i subcodici validi del codebook fornito.

Regole:
1. Usa solo i codici ammessi.
2. Un item puo' ricevere zero, uno o piu' codici.
3. Non inventare codici nuovi.
4. Se una risposta e' solo '-' o e' vuota o non informativa, assegna il codice N1 (risposta non classificabile).
5. Preferisci pochi codici pertinenti a molti codici rumorosi.
6. Considera soprattutto il contenuto espresso nella risposta, non la sola formulazione della domanda.
7. Restituisci JSON valido e nient'altro.
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Etichetta i file raw PRAXIS usando un modello Ollama remoto."
    )
    parser.add_argument("--input-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--glob", default="*.md")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Livello log mostrato a terminale.",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Non filtra le risposte vuote o con solo '-'.",
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


def parse_raw_markdown(path: Path, include_empty: bool = False) -> RawRecord:
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
        answer = normalize_answer(match.group(2))
        if question.lower() == "codice":
            code = normalize_inline(answer)
            continue
        if not include_empty and answer in {"", "-"}:
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


def build_user_prompt(record: RawRecord) -> str:
    codes = "\n".join(f"- {code}: {desc}" for code, desc in CODEBOOK.items())
    qas = "\n\n".join(
        f"[{item.index}] DOMANDA: {item.question}\nRISPOSTA: {item.answer}"
        for item in record.items
    )

    return f"""Codebook disponibile:
{codes}

Record:
- file: {record.source_file.name}
- gruppo: {record.group}
- codice partecipante: {record.code}

Item da etichettare:
{qas}

Restituisci un JSON con questa struttura:
{{
  "items": [
    {{
      "index": 1,
      "codes": ["P2", "X3"],
      "reason": "breve motivazione aderente al testo"
    }}
  ],
  "record_note": "breve nota opzionale sul profilo generale del record"
}}

Vincoli:
- l'array "items" deve coprire tutti gli indici presenti nel record;
- "codes" puo' essere vuoto;
- non ripetere il testo delle domande o delle risposte;
- usa solo i codici ammessi;
- la reason deve essere breve e fattuale.
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


def ollama_chat(host: str, model: str, prompt: str, timeout: int) -> dict[str, Any]:
    url = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
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


def validate_model_output(record: RawRecord, payload: dict[str, Any]) -> dict[str, Any]:
    by_index: dict[int, dict[str, Any]] = {}
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError):
            continue
        if index < 1 or index > len(record.items):
            continue
        seen: list[str] = []
        for code in item.get("codes", []):
            if code in CODEBOOK and code not in seen:
                seen.append(code)
        by_index[index] = {
            "index": index,
            "codes": seen,
            "reason": normalize_inline(str(item.get("reason", ""))),
        }

    normalized_items: list[dict[str, Any]] = []
    for source_item in record.items:
        normalized = by_index.get(
            source_item.index,
            {"index": source_item.index, "codes": [], "reason": ""},
        )
        normalized_items.append(
            {
                "index": source_item.index,
                "question": source_item.question,
                "answer": source_item.answer,
                "codes": normalized["codes"],
                "reason": normalized["reason"],
            }
        )

    record_subcodes = sorted(
        {code for item in normalized_items for code in item["codes"]}
    )
    record_dimensions = sorted({code[0] for code in record_subcodes})

    return {
        "record_note": normalize_inline(str(payload.get("record_note", ""))),
        "record_subcodes": record_subcodes,
        "record_dimensions": record_dimensions,
        "items": normalized_items,
    }


def build_result(
    record: RawRecord,
    model_output: dict[str, Any],
    host: str,
    model: str,
) -> dict[str, Any]:
    code_counts = Counter(
        code for item in model_output["items"] for code in item["codes"]
    )
    return {
        "source_file": str(record.source_file),
        "source_name": record.source_file.name,
        "title": record.title,
        "group": record.group,
        "record_code": record.code,
        "host": host,
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_dimensions": model_output["record_dimensions"],
        "record_subcodes": model_output["record_subcodes"],
        "record_note": model_output["record_note"],
        "code_counts": dict(sorted(code_counts.items())),
        "items": model_output["items"],
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
) -> dict[str, Any]:
    record = parse_raw_markdown(path, include_empty=include_empty)
    destination = output_path_for(record, output_dir)
    if destination.exists() and not overwrite and not dry_run:
        existing = json.loads(destination.read_text(encoding="utf-8"))
        return {"status": "skipped", "path": str(path), "result": existing}

    prompt = build_user_prompt(record)
    if dry_run:
        return {
            "status": "dry_run",
            "path": str(path),
            "prompt": prompt,
            "record": {
                "title": record.title,
                "group": record.group,
                "record_code": record.code,
                "items": [item.__dict__ for item in record.items],
            },
        }

    raw_payload = ollama_chat(host=host, model=model, prompt=prompt, timeout=timeout)
    validated = validate_model_output(record, raw_payload)
    result = build_result(record, validated, host=host, model=model)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"status": "ok", "path": str(path), "result": result}


def write_summaries(results: list[dict[str, Any]], output_dir: Path) -> None:
    ok_results = [item["result"] for item in results if item["status"] in {"ok", "skipped"}]
    if not ok_results:
        return

    jsonl_path = output_dir / "summary.jsonl"
    csv_path = output_dir / "summary.csv"

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for result in ok_results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "source_name",
                "group",
                "record_code",
                "record_dimensions",
                "record_subcodes",
                "record_note",
            ]
        )
        for result in ok_results:
            writer.writerow(
                [
                    result["source_name"],
                    result["group"],
                    result["record_code"],
                    "|".join(result["record_dimensions"]),
                    "|".join(result["record_subcodes"]),
                    result["record_note"],
                ]
            )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)
    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir

    files = sorted(input_dir.glob(args.glob))
    if args.limit:
        files = files[: args.limit]
    if not files:
        print("Nessun file trovato.", file=sys.stderr)
        return 1

    total = len(files)
    LOGGER.info(
        "Avvio labeling: files=%s model=%s host=%s workers=%s dry_run=%s",
        total,
        args.model,
        args.host,
        args.workers,
        args.dry_run,
    )

    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    if args.dry_run or args.workers == 1:
        for index, path in enumerate(files, start=1):
            LOGGER.info("[%s/%s] start %s", index, total, path.name)
            try:
                result = process_one(
                    path=path,
                    output_dir=output_dir,
                    host=args.host,
                    model=args.model,
                    timeout=args.timeout,
                    overwrite=args.overwrite,
                    include_empty=args.include_empty,
                    dry_run=args.dry_run,
                )
                results.append(result)
                status = result["status"]
                subcodes = (
                    len(result.get("result", {}).get("record_subcodes", []))
                    if status in {"ok", "skipped"}
                    else 0
                )
                LOGGER.info(
                    "[%s/%s] %s %s subcodes=%s",
                    index,
                    total,
                    status,
                    path.name,
                    subcodes,
                )
            except Exception as exc:  # noqa: BLE001
                failures.append({"path": str(path), "error": str(exc)})
                LOGGER.error("[%s/%s] failed %s: %s", index, total, path.name, exc)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_map = {
                executor.submit(
                    process_one,
                    path,
                    output_dir,
                    args.host,
                    args.model,
                    args.timeout,
                    args.overwrite,
                    args.include_empty,
                    args.dry_run,
                ): path
                for path in files
            }
            for path in files:
                LOGGER.info("[queued] %s", path.name)
            completed = 0
            for future in concurrent.futures.as_completed(future_map):
                path = future_map[future]
                completed += 1
                try:
                    result = future.result()
                    results.append(result)
                    status = result["status"]
                    subcodes = (
                        len(result.get("result", {}).get("record_subcodes", []))
                        if status in {"ok", "skipped"}
                        else 0
                    )
                    LOGGER.info(
                        "[%s/%s] %s %s subcodes=%s",
                        completed,
                        total,
                        status,
                        path.name,
                        subcodes,
                    )
                except Exception as exc:  # noqa: BLE001
                    failures.append({"path": str(path), "error": str(exc)})
                    LOGGER.error(
                        "[%s/%s] failed %s: %s",
                        completed,
                        total,
                        path.name,
                        exc,
                    )

    if args.dry_run:
        sample = results[0] if results else {}
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        write_summaries(results, output_dir)
        if failures:
            (output_dir / "failures.json").write_text(
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
                "output_dir": str(output_dir),
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
