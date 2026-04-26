#!/usr/bin/env python3
"""Bidirectional sync between reference.bib and the dedicated Zotero group.

Reads ZOTERO_API_KEY, ZOTERO_LIBRARY_TYPE=group, ZOTERO_GROUP_ID from environment.
Citation keys are stored in Zotero `extra: "Citation Key: <key>"` so they survive
without Better BibTeX server-side.

Modes:
  (default)        report-only: shows drift, no changes
  --push           push entries that are only in reference.bib → Zotero
  --pull           append entries that are only in Zotero → reference.bib
  --sync           shorthand for --push --pull
  --strict         exit 1 if any drift remains after the chosen mode

Usage:
  set -a; source .env; set +a
  .venv/bin/python scripts/sync_zotero_group.py [--push|--pull|--sync] [--strict]
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


BIB_PATH = Path("/home/nugh75/-qtimes/docs/bibliografia/reference.bib")
ZOTERO_API = "https://api.zotero.org"
BATCH_SIZE = 50
ENTRY_RE = re.compile(r"^@[A-Za-z]+\{([^,\s]+),", re.MULTILINE)
CITATION_KEY_RE = re.compile(r"^Citation Key:\s*(\S+)", re.MULTILINE)

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

ZOTERO_TO_BIBTEX_TYPE = {
    "journalArticle": "article",
    "book": "book",
    "bookSection": "incollection",
    "conferencePaper": "inproceedings",
    "report": "techreport",
    "thesis": "phdthesis",
    "webpage": "misc",
    "manuscript": "unpublished",
    "computerProgram": "software",
    "dataset": "misc",
    "document": "misc",
    "preprint": "article",
    "magazineArticle": "article",
    "newspaperArticle": "article",
}


def env_or_die(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return value


def clean_value(value: str) -> str:
    value = value.strip().strip(",")
    value = re.sub(r"\s+", " ", value)
    for old, new in {r"\&": "&", r"\%": "%", r"\_": "_", "{": "", "}": ""}.items():
        value = value.replace(old, new)
    return value.strip()


def split_bib_entries(text: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
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
        raw = text[at:j]
        entries.append((entry_type.lower(), body, raw))
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


def parse_bib_entry(entry_type: str, body: str) -> dict[str, Any] | None:
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
        if not raw or raw.lower() in ("others", "et al"):
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


def bib_to_zotero_item(entry: dict[str, Any]) -> dict[str, Any]:
    f = entry["fields"]
    item_type = BIBTEX_TO_ZOTERO_TYPE.get(entry["type"], "document")
    item: dict[str, Any] = {
        "itemType": item_type,
        "title": f.get("title", "") or f.get("booktitle", ""),
        "creators": parse_authors(f.get("author", "")),
        "date": f.get("year", ""),
        "DOI": normalize_doi(f.get("doi", "")),
        "url": f.get("url", ""),
        "abstractNote": f.get("abstract", ""),
        "language": f.get("language", ""),
        "extra": f"Citation Key: {entry['key']}",
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
        if f.get("editor"):
            for editor in parse_authors(f["editor"]):
                editor["creatorType"] = "editor"
                item["creators"].append(editor)
    elif item_type == "conferencePaper":
        item["proceedingsTitle"] = f.get("booktitle", "")
        item["publisher"] = f.get("publisher", "")
        item["pages"] = f.get("pages", "")
    elif item_type == "thesis":
        item["thesisType"] = f.get("type", "PhD thesis")
        item["university"] = f.get("school", "") or f.get("institution", "")
    elif item_type == "report":
        item["institution"] = f.get("institution", "") or f.get("school", "")
        item["reportNumber"] = f.get("number", "")
    return {k: v for k, v in item.items() if v not in (None, "", []) or k in ("creators", "tags", "collections", "relations")}


def zotero_item_to_bibtex(item: dict[str, Any], cite_key: str) -> str:
    data = item.get("data", item)
    item_type = data.get("itemType", "document")
    bib_type = ZOTERO_TO_BIBTEX_TYPE.get(item_type, "misc")
    fields: list[tuple[str, str]] = []
    authors = []
    editors = []
    for creator in data.get("creators", []):
        kind = creator.get("creatorType", "author")
        if creator.get("name"):
            full = creator["name"]
        else:
            last = creator.get("lastName", "")
            first = creator.get("firstName", "")
            full = f"{last}, {first}".strip(", ") if last else first
        if not full:
            continue
        if kind == "editor":
            editors.append(full)
        else:
            authors.append(full)
    if authors:
        fields.append(("author", " and ".join(authors)))
    if editors:
        fields.append(("editor", " and ".join(editors)))
    title = data.get("title", "")
    if title:
        fields.append(("title", title))
    date = data.get("date", "")
    year_match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", date)
    if year_match:
        fields.append(("year", year_match.group(1)))
    venue_keys = [
        ("journalArticle", "publicationTitle", "journal"),
        ("bookSection", "bookTitle", "booktitle"),
        ("conferencePaper", "proceedingsTitle", "booktitle"),
    ]
    for kind, src, dst in venue_keys:
        if item_type == kind and data.get(src):
            fields.append((dst, data[src]))
    if data.get("publisher"):
        fields.append(("publisher", data["publisher"]))
    if data.get("place"):
        fields.append(("address", data["place"]))
    if data.get("volume"):
        fields.append(("volume", data["volume"]))
    if data.get("issue"):
        fields.append(("number", data["issue"]))
    if data.get("pages"):
        fields.append(("pages", data["pages"]))
    if data.get("DOI"):
        fields.append(("doi", data["DOI"]))
    if data.get("ISSN"):
        fields.append(("issn", data["ISSN"]))
    if data.get("ISBN"):
        fields.append(("isbn", data["ISBN"]))
    if data.get("url"):
        fields.append(("url", data["url"]))
    if data.get("abstractNote"):
        fields.append(("abstract", data["abstractNote"]))
    if item_type == "thesis" and data.get("university"):
        fields.append(("school", data["university"]))
    body = ",\n  ".join(f"{name} = {{{value}}}" for name, value in fields)
    return f"@{bib_type}{{{cite_key},\n  {body}\n}}\n"


def fetch_group_items(api_key: str, group_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    start = 0
    page_size = 100
    while True:
        params = urlencode({"format": "json", "limit": page_size, "start": start, "itemType": "-attachment || note"})
        url = f"{ZOTERO_API}/groups/{group_id}/items?{params}"
        req = Request(url, headers={"Zotero-API-Key": api_key, "Zotero-API-Version": "3"})
        try:
            with urlopen(req, timeout=30) as response:
                page = json.loads(response.read().decode("utf-8"))
                total = int(response.headers.get("Total-Results", "0"))
        except (HTTPError, URLError) as exc:
            print(f"Zotero API error: {exc}", file=sys.stderr)
            sys.exit(1)
        if not page:
            break
        items.extend(page)
        start += page_size
        if start >= total:
            break
    return items


def extract_citation_key(item: dict[str, Any]) -> str | None:
    data = item.get("data", {})
    native = (data.get("citationKey") or "").strip()
    if native:
        return native
    extra = data.get("extra", "") or ""
    match = CITATION_KEY_RE.search(extra)
    return match.group(1) if match else None


def post_items(api_key: str, group_id: str, items: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    successes = 0
    failures: list[dict[str, Any]] = []
    for batch_start in range(0, len(items), BATCH_SIZE):
        batch = items[batch_start : batch_start + BATCH_SIZE]
        body = json.dumps(batch).encode("utf-8")
        req = Request(
            f"{ZOTERO_API}/groups/{group_id}/items",
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
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            print(f"push batch {batch_start}: HTTP {exc.code}: {detail[:200]}", file=sys.stderr)
            for index in range(len(batch)):
                failures.append({"index": batch_start + index, "error": f"HTTP {exc.code}"})
            continue
        successes += len(payload.get("successful", {}))
        for index_str, err in payload.get("failed", {}).items():
            failures.append({"index": batch_start + int(index_str), "error": err})
        time.sleep(0.5)
    return successes, failures


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=BIB_PATH)
    parser.add_argument("--push", action="store_true", help="Upload bib-only entries to Zotero")
    parser.add_argument("--pull", action="store_true", help="Append Zotero-only entries to reference.bib")
    parser.add_argument("--sync", action="store_true", help="Shorthand for --push --pull")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if drift remains after chosen mode")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)
    if args.sync:
        args.push = True
        args.pull = True

    api_key = env_or_die("ZOTERO_API_KEY")
    library_type = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
    if library_type != "group":
        print("ZOTERO_LIBRARY_TYPE must be 'group'", file=sys.stderr)
        return 2
    group_id = env_or_die("ZOTERO_GROUP_ID")
    if not args.bib.exists():
        print(f"reference.bib not found at {args.bib}", file=sys.stderr)
        return 2

    bib_text = args.bib.read_text(encoding="utf-8")
    bib_entries: dict[str, dict[str, Any]] = {}
    for entry_type, body, raw in split_bib_entries(bib_text):
        parsed = parse_bib_entry(entry_type, body)
        if parsed and parsed["key"]:
            bib_entries.setdefault(parsed["key"], parsed)

    remote_items = fetch_group_items(api_key, group_id)
    remote_by_key: dict[str, dict[str, Any]] = {}
    remote_no_key: list[dict[str, Any]] = []
    for item in remote_items:
        key = extract_citation_key(item)
        if key:
            remote_by_key.setdefault(key, item)
        else:
            remote_no_key.append(item)

    local_keys = set(bib_entries.keys())
    remote_keys = set(remote_by_key.keys())
    only_local = sorted(local_keys - remote_keys)
    only_remote = sorted(remote_keys - local_keys)
    common = sorted(local_keys & remote_keys)

    pushed = 0
    push_failures: list[dict[str, Any]] = []
    if args.push and only_local:
        items_to_push = [bib_to_zotero_item(bib_entries[key]) for key in only_local]
        pushed, push_failures = post_items(api_key, group_id, items_to_push)

    appended = 0
    if args.pull and only_remote:
        new_blocks = ["\n"]
        for key in only_remote:
            block = zotero_item_to_bibtex(remote_by_key[key], key)
            new_blocks.append(block + "\n")
        with args.bib.open("a", encoding="utf-8") as bib_file:
            bib_file.write("".join(new_blocks))
        appended = len(only_remote)

    if args.push or args.pull:
        remote_items = fetch_group_items(api_key, group_id)
        remote_by_key = {}
        for item in remote_items:
            key = extract_citation_key(item)
            if key:
                remote_by_key.setdefault(key, item)
        bib_text = args.bib.read_text(encoding="utf-8")
        bib_entries = {}
        for entry_type, body, raw in split_bib_entries(bib_text):
            parsed = parse_bib_entry(entry_type, body)
            if parsed and parsed["key"]:
                bib_entries.setdefault(parsed["key"], parsed)
        local_keys = set(bib_entries.keys())
        remote_keys = set(remote_by_key.keys())
        only_local = sorted(local_keys - remote_keys)
        only_remote = sorted(remote_keys - local_keys)
        common = sorted(local_keys & remote_keys)

    payload = {
        "bib_path": str(args.bib),
        "group_id": group_id,
        "local_count": len(local_keys),
        "remote_count": len(remote_keys),
        "in_sync": len(common),
        "only_local": only_local,
        "only_remote": only_remote,
        "remote_no_citation_key": len(remote_no_key),
        "actions": {
            "pushed": pushed,
            "push_failures": push_failures,
            "appended_to_bib": appended,
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"bib:    {args.bib}")
        print(f"group:  {group_id}")
        print(f"local:  {len(local_keys)} entries")
        print(f"remote: {len(remote_keys)} entries with Citation Key")
        print(f"sync:   {len(common)}")
        if remote_no_key:
            print(f"remote items without 'Citation Key:' in extra: {len(remote_no_key)}")
        if pushed or appended:
            print(f"actions: pushed={pushed} appended_to_bib={appended}")
        if only_local:
            print(f"\nonly_local ({len(only_local)}):")
            for key in only_local[:30]:
                print(f"  - {key}")
            if len(only_local) > 30:
                print(f"  ... and {len(only_local) - 30} more")
        if only_remote:
            print(f"\nonly_remote ({len(only_remote)}):")
            for key in only_remote[:30]:
                print(f"  - {key}")
            if len(only_remote) > 30:
                print(f"  ... and {len(only_remote) - 30} more")

    drift = bool(only_local or only_remote)
    if args.strict and drift:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
