#!/usr/bin/env python3
"""Import a BibTeX file into a Zotero group library via the Web API.

Reads ZOTERO_API_KEY, ZOTERO_LIBRARY_TYPE=group, ZOTERO_GROUP_ID from environment.
Pins the BibTeX citation key into the Zotero `extra` field so Better BibTeX (on
the client) can preserve `Davis1989PerceivedU`-style keys.

Usage:
  set -a; source .env; set +a
  .venv/bin/python scripts/import_bib_to_zotero.py [--bib path] [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BIB = Path("/home/nugh75/-qtimes/docs/bibliografia/reference.bib")
ZOTERO_API = "https://api.zotero.org"
BATCH_SIZE = 50

BIBTEX_TO_ZOTERO_TYPE = {
    "article": "journalArticle",
    "book": "book",
    "booklet": "book",
    "inbook": "bookSection",
    "incollection": "bookSection",
    "inproceedings": "conferencePaper",
    "conference": "conferencePaper",
    "manual": "report",
    "mastersthesis": "thesis",
    "phdthesis": "thesis",
    "misc": "document",
    "online": "webpage",
    "techreport": "report",
    "report": "report",
    "unpublished": "manuscript",
    "proceedings": "book",
    "thesis": "thesis",
    "software": "computerProgram",
    "dataset": "dataset",
    "webpage": "webpage",
}


def clean_value(value: str) -> str:
    value = value.strip().strip(",")
    value = re.sub(r"\s+", " ", value)
    for old, new in {r"\&": "&", r"\%": "%", r"\_": "_", "{": "", "}": ""}.items():
        value = value.replace(old, new)
    return value.strip()


def split_bib_entries(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(text):
        at = text.find("@", i)
        if at == -1:
            break
        match = re.match(r"@([A-Za-z]+)\s*\{", text[at:])
        if not match:
            i = at + 1
            continue
        entry_type = match.group(1)
        body_start = at + match.end()
        depth = 1
        j = body_start
        while j < len(text) and depth:
            char = text[j]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            j += 1
        if depth != 0:
            raise ValueError(f"Unclosed BibTeX entry near byte {at}")
        body = text[body_start : j - 1]
        entries.append((entry_type.lower(), body))
        i = j
    return entries


def read_balanced_value(body: str, start: int) -> tuple[str, int]:
    i = start
    while i < len(body) and body[i].isspace():
        i += 1
    if i >= len(body):
        return "", i
    if body[i] == "{":
        depth = 1
        j = i + 1
        while j < len(body) and depth:
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
            j += 1
        return body[i + 1 : j - 1], j
    if body[i] == '"':
        j = i + 1
        while j < len(body) and body[j] != '"':
            j += 1
        return body[i + 1 : j], min(j + 1, len(body))
    j = i
    while j < len(body) and body[j] != ",":
        j += 1
    return body[i:j], j


def parse_entry(entry_type: str, body: str) -> dict[str, Any] | None:
    key_end = body.find(",")
    if key_end == -1:
        return None
    key = body[:key_end].strip()
    fields_text = body[key_end + 1 :]
    fields: dict[str, str] = {}
    i = 0
    while i < len(fields_text):
        while i < len(fields_text) and (fields_text[i].isspace() or fields_text[i] == ","):
            i += 1
        if i >= len(fields_text):
            break
        name_match = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*=", fields_text[i:])
        if not name_match:
            next_comma = fields_text.find(",", i)
            if next_comma == -1:
                break
            i = next_comma + 1
            continue
        name = name_match.group(1).lower()
        i += name_match.end()
        value, i = read_balanced_value(fields_text, i)
        fields[name] = clean_value(value)
        while i < len(fields_text) and fields_text[i] != ",":
            i += 1
    return {"type": entry_type, "key": key, "fields": fields}


def parse_authors(author_field: str) -> list[dict[str, str]]:
    creators: list[dict[str, str]] = []
    if not author_field:
        return creators
    for raw in re.split(r"\s+and\s+", author_field):
        raw = raw.strip()
        if not raw:
            continue
        if raw.lower() in ("others", "et al"):
            continue
        if "," in raw:
            last, first = [part.strip() for part in raw.split(",", 1)]
        else:
            tokens = raw.split()
            last = tokens[-1] if tokens else raw
            first = " ".join(tokens[:-1])
        creators.append({"creatorType": "author", "firstName": first, "lastName": last})
    return creators


def normalize_doi(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value


def to_zotero_item(entry: dict[str, Any]) -> dict[str, Any]:
    f = entry["fields"]
    item_type = BIBTEX_TO_ZOTERO_TYPE.get(entry["type"], "document")
    extra_lines = [f"Citation Key: {entry['key']}"]
    if f.get("isbn"):
        extra_lines.append(f"ISBN: {f['isbn']}")

    item: dict[str, Any] = {
        "itemType": item_type,
        "title": f.get("title", "") or f.get("booktitle", ""),
        "creators": parse_authors(f.get("author", "")),
        "date": f.get("year", "") + (f"-{f['month']}" if f.get("month") else ""),
        "DOI": normalize_doi(f.get("doi", "")),
        "url": f.get("url", ""),
        "abstractNote": f.get("abstract", ""),
        "language": f.get("language", ""),
        "extra": "\n".join(extra_lines),
        "tags": [],
        "collections": [],
        "relations": {},
    }

    if item_type == "journalArticle":
        item["publicationTitle"] = f.get("journal", "")
        item["volume"] = f.get("volume", "")
        item["issue"] = f.get("number", "") or f.get("issue", "")
        item["pages"] = f.get("pages", "")
        item["ISSN"] = f.get("issn", "")
    elif item_type == "book":
        item["publisher"] = f.get("publisher", "")
        item["place"] = f.get("address", "") or f.get("location", "")
        item["ISBN"] = f.get("isbn", "")
        item["edition"] = f.get("edition", "")
    elif item_type == "bookSection":
        item["bookTitle"] = f.get("booktitle", "")
        item["publisher"] = f.get("publisher", "")
        item["place"] = f.get("address", "") or f.get("location", "")
        item["pages"] = f.get("pages", "")
        item["ISBN"] = f.get("isbn", "")
        if f.get("editor"):
            for ed in parse_authors(f["editor"]):
                ed["creatorType"] = "editor"
                item["creators"].append(ed)
    elif item_type == "conferencePaper":
        item["proceedingsTitle"] = f.get("booktitle", "")
        item["publisher"] = f.get("publisher", "")
        item["pages"] = f.get("pages", "")
    elif item_type == "thesis":
        item["thesisType"] = f.get("type", "PhD thesis" if entry["type"] == "phdthesis" else "Master's thesis")
        item["university"] = f.get("school", "") or f.get("institution", "")
        item["place"] = f.get("address", "")
    elif item_type == "report":
        item["institution"] = f.get("institution", "") or f.get("school", "")
        item["reportNumber"] = f.get("number", "")
    elif item_type == "webpage":
        item["websiteTitle"] = f.get("howpublished", "")

    return {k: v for k, v in item.items() if v not in (None, "", []) or k in ("creators", "tags", "collections", "relations")}


def post_batch(api_key: str, group_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    url = f"{ZOTERO_API}/groups/{group_id}/items"
    body = json.dumps(items).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Zotero-API-Key": api_key,
            "Zotero-API-Version": "3",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Zotero API {exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=DEFAULT_BIB)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, help="Cap entries imported (for testing)")
    args = parser.parse_args(argv)

    api_key = os.environ.get("ZOTERO_API_KEY")
    library_type = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
    group_id = os.environ.get("ZOTERO_GROUP_ID")

    if library_type != "group" or not group_id:
        print("Need ZOTERO_LIBRARY_TYPE=group and ZOTERO_GROUP_ID", file=sys.stderr)
        return 2
    if not api_key and not args.dry_run:
        print("Need ZOTERO_API_KEY (or use --dry-run)", file=sys.stderr)
        return 2

    text = args.bib.read_text(encoding="utf-8")
    entries = []
    for entry_type, body in split_bib_entries(text):
        parsed = parse_entry(entry_type, body)
        if parsed and parsed["key"]:
            entries.append(parsed)
    if args.limit:
        entries = entries[: args.limit]

    items = [to_zotero_item(entry) for entry in entries]
    print(f"Parsed {len(entries)} entries from {args.bib}")

    if args.dry_run:
        print(json.dumps(items[:2], ensure_ascii=False, indent=2))
        print(f"... (showing first 2 of {len(items)})")
        return 0

    successes: list[str] = []
    failures: list[dict[str, Any]] = []
    for batch_start in range(0, len(items), BATCH_SIZE):
        batch = items[batch_start : batch_start + BATCH_SIZE]
        try:
            payload = post_batch(api_key, group_id, batch)
        except RuntimeError as exc:
            print(f"batch {batch_start}: ERROR {exc}", file=sys.stderr)
            for entry in entries[batch_start : batch_start + len(batch)]:
                failures.append({"key": entry["key"], "error": "batch failed"})
            continue
        successful_idx = payload.get("successful", {})
        failed_idx = payload.get("failed", {})
        for idx_str, _ in successful_idx.items():
            idx = int(idx_str)
            successes.append(entries[batch_start + idx]["key"])
        for idx_str, err in failed_idx.items():
            idx = int(idx_str)
            failures.append({"key": entries[batch_start + idx]["key"], "error": err})
        print(f"batch {batch_start}-{batch_start + len(batch) - 1}: {len(successful_idx)} ok, {len(failed_idx)} failed")
        time.sleep(0.5)

    print(f"\nDone. Imported {len(successes)} / {len(entries)} entries.")
    if failures:
        print(f"\nFailures ({len(failures)}):")
        for failure in failures[:20]:
            print(f"  {failure['key']}: {failure['error']}")
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
