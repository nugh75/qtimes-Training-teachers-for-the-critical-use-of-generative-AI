#!/usr/bin/env python3
"""Re-label via Ollama per record corpus con classificazione nulla o fallita.

Riusa infrastruttura di label_raw_with_ollama.py ma:
  - parsa 02-corpus/ in nuovo formato item-based (post Fase 0);
  - cerca label esistente; se null_dim o missing → re-label;
  - scrive/sovrascrive 04-label/labels/ollama-gemma4/STEM.json.

Target di default:
  - record corpus con label JSON che ha record_dimensions == []
  - record corpus con stem in failures.json

Uso:
  python relabel_null_items.py --dry-run    # mostra cosa farebbe
  python relabel_null_items.py --execute    # esegui chiamate ollama
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from label_raw_with_ollama import (
    CODEBOOK,
    ROOT_DIR,
    SYSTEM_PROMPT,
    build_user_prompt,
    ollama_chat,
    validate_model_output,
)
from label_raw_with_ollama import QAItem, RawRecord

RAW_DIR = ROOT_DIR / "02-corpus"
LABELS_DIR = ROOT_DIR / "04-label" / "labels" / "ollama-gemma4"
FAILURES_PATH = LABELS_DIR / "failures.json"
DEFAULT_HOST = "http://192.168.129.14:11434"
DEFAULT_MODEL = "gemma4:e4b"

ITEM_RE = re.compile(
    r"^## Item (?P<idx>\d+) \{#item-\d+\}\s*\n"
    r"(?:\s*\n)?"
    r"\*\*Q\*\*:\s*(?P<q>.*?)\s*\n"
    r"\*\*A\*\*:\s*(?P<a>.*?)\s*\n"
    r"\*\*Codes\*\*:",
    re.DOTALL | re.MULTILINE,
)

FRONTMATTER_RE = re.compile(r"^---\n(?P<yaml>.*?)\n---\n", re.DOTALL)


def parse_new_raw(path: Path) -> RawRecord:
    """Parse 02-corpus/STEM.md in formato item-based."""
    text = path.read_text(encoding="utf-8")

    code = ""
    group = "Sconosciuto"
    fm = FRONTMATTER_RE.search(text)
    if fm:
        for line in fm.group("yaml").splitlines():
            if line.startswith("record_code:"):
                code = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("group:"):
                group = line.split(":", 1)[1].strip()

    items: list[QAItem] = []
    for m in ITEM_RE.finditer(text):
        idx = int(m.group("idx"))
        q = m.group("q").strip()
        a = m.group("a").strip()
        if a in {"", "-", '"-"'}:
            continue
        items.append(QAItem(index=idx, question=q, answer=a))

    return RawRecord(
        source_file=path,
        title=path.stem,
        group=group,
        code=code or path.stem,
        items=items,
    )


def find_null_stems() -> list[str]:
    stems: set[str] = set()
    # 1) null record_dimensions
    for jp in LABELS_DIR.glob("*.json"):
        if jp.stem in {"failures"}:
            continue
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not data.get("record_dimensions"):
            stems.add(jp.stem)
    # 2) failures
    if FAILURES_PATH.exists():
        failures = json.loads(FAILURES_PATH.read_text(encoding="utf-8"))
        for f in failures:
            p = Path(f.get("path", ""))
            if p.name.endswith(".md"):
                stems.add(p.stem)
    return sorted(stems)


def build_label_json(record: RawRecord, model_out: dict, model: str, host: str) -> dict:
    code_counts: dict[str, int] = {}
    for item in model_out["items"]:
        for c in item["codes"]:
            code_counts[c] = code_counts.get(c, 0) + 1
    return {
        "source_file": str(record.source_file),
        "source_name": record.source_file.name,
        "title": f"Risposta {record.code}",
        "group": record.group,
        "record_code": record.code,
        "host": host,
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_dimensions": model_out["record_dimensions"],
        "record_subcodes": model_out["record_subcodes"],
        "record_note": model_out["record_note"],
        "code_counts": code_counts,
        "items": model_out["items"],
    }


def process(stem: str, host: str, model: str, timeout: int, dry_run: bool) -> dict | None:
    raw_path = RAW_DIR / f"{stem}.md"
    if not raw_path.exists():
        print(f"[skip] record corpus mancante: {stem}", file=sys.stderr)
        return None
    record = parse_new_raw(raw_path)
    if not record.items:
        print(f"[skip] no items: {stem}", file=sys.stderr)
        return None
    prompt = build_user_prompt(record)
    if dry_run:
        print(f"[dry] {stem} — {len(record.items)} items, prompt {len(prompt)} chars")
        return None
    print(f"[call] {stem} ({len(record.items)} items)...", file=sys.stderr)
    try:
        raw_output = ollama_chat(host, model, prompt, timeout)
    except Exception as exc:
        print(f"[error] {stem}: {exc}", file=sys.stderr)
        return None
    validated = validate_model_output(record, raw_output)
    result = build_label_json(record, validated, model, host)
    out = LABELS_DIR / f"{stem}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[written] {out.name} — dims={result['record_dimensions']} codes={result['record_subcodes']}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stem", help="re-label solo questo stem")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.error("richiesto --dry-run o --execute")

    if args.stem:
        stems = [args.stem]
    else:
        stems = find_null_stems()
        print(f"Trovati {len(stems)} stems da re-label:", file=sys.stderr)
        for s in stems:
            print(f"  {s}", file=sys.stderr)

    successes = 0
    for stem in stems:
        res = process(stem, args.host, args.model, args.timeout, args.dry_run)
        if res is not None:
            successes += 1

    print(f"\nDone. {successes}/{len(stems)} relabeled.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
