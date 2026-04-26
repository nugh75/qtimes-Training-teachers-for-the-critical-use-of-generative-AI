#!/usr/bin/env python3
"""Check PRAXIS BibTeX citations against the local bibliography and OpenAlex."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


DEFAULT_BIB = Path("/home/nugh75/-qtimes/docs/bibliografia/reference.bib")
OPENALEX_API = "https://api.openalex.org"
CITATION_RE = re.compile(r"(?<![\w.])-?@([A-Za-z][A-Za-z0-9_:\-.]+)")


@dataclass
class BibEntry:
    entry_type: str
    key: str
    fields: dict[str, str]
    raw: str


def clean_value(value: str) -> str:
    value = value.strip().strip(",")
    value = re.sub(r"\s+", " ", value)
    replacements = {
        r"\&": "&",
        r"\%": "%",
        r"\_": "_",
        r"\{": "{",
        r"\}": "}",
        "{": "",
        "}": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.strip()


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = clean_value(value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_doi(value: str | None) -> str:
    if not value:
        return ""
    value = clean_value(value).strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.strip()


def author_last_names(author_field: str | None) -> list[str]:
    if not author_field:
        return []
    names = []
    for part in re.split(r"\s+and\s+", clean_value(author_field)):
        part = part.strip()
        if not part:
            continue
        if "," in part:
            names.append(part.split(",", 1)[0].strip())
        else:
            names.append(part.split()[-1].strip())
    return names


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
            raise ValueError(f"Unclosed BibTeX entry starting near byte {at}")
        body = text[body_start : j - 1]
        raw = text[at:j]
        entries.append((entry_type, body, raw))
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
        escaped = False
        while j < len(body):
            if body[j] == '"' and not escaped:
                break
            escaped = body[j] == "\\" and not escaped
            if body[j] != "\\":
                escaped = False
            j += 1
        return body[i + 1 : j], min(j + 1, len(body))
    j = i
    while j < len(body) and body[j] != ",":
        j += 1
    return body[i:j], j


def parse_entry(entry_type: str, body: str, raw: str) -> BibEntry | None:
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
    return BibEntry(entry_type=entry_type.lower(), key=key, fields=fields, raw=raw)


def load_bib(path: Path) -> tuple[dict[str, BibEntry], dict[str, list[BibEntry]]]:
    text = path.read_text(encoding="utf-8")
    entries: dict[str, BibEntry] = {}
    all_by_key: dict[str, list[BibEntry]] = {}
    for entry_type, body, raw in split_bib_entries(text):
        entry = parse_entry(entry_type, body, raw)
        if not entry or not entry.key:
            continue
        all_by_key.setdefault(entry.key, []).append(entry)
        entries.setdefault(entry.key, entry)
    duplicates = {key: vals for key, vals in all_by_key.items() if len(vals) > 1}
    return entries, duplicates


def scan_doc_citations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    keys = CITATION_RE.findall(text)
    return sorted(set(keys))


def scan_doc_bibliography_paths(path: Path, canonical_bib: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {"paths": [], "warnings": []}

    end = text.find("\n---", 3)
    if end == -1:
        return {"paths": [], "warnings": ["YAML frontmatter is not closed"]}

    frontmatter = text[3:end].splitlines()
    paths: list[str] = []
    for line in frontmatter:
        match = re.match(r"\s*bibliography\s*:\s*(.+?)\s*$", line)
        if match:
            value = match.group(1).strip().strip('"').strip("'")
            if value:
                paths.append(value)

    warnings = []
    canonical_resolved = canonical_bib.expanduser().resolve(strict=False)
    for value in paths:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = (path.parent / candidate).resolve(strict=False)
        else:
            candidate = candidate.resolve(strict=False)
        if candidate != canonical_resolved:
            warnings.append(
                f"Document bibliography points to {value}; canonical PRAXIS bibliography is {canonical_resolved}"
            )

    return {"paths": paths, "warnings": warnings}


def request_json(url: str, timeout: float = 20.0) -> dict[str, Any] | None:
    req = Request(url, headers={"User-Agent": "praxis-bibliography-citations/1.0"})
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"OpenAlex request failed: {exc}") from exc


def openalex_params(params: dict[str, Any]) -> str:
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto
    return urlencode(params)


def get_openalex_by_doi(doi: str) -> dict[str, Any] | None:
    doi = normalize_doi(doi)
    if not doi:
        return None
    work_id = quote(f"https://doi.org/{doi}", safe=":/")
    return request_json(f"{OPENALEX_API}/works/{work_id}")


def search_openalex(title: str, per_page: int) -> list[dict[str, Any]]:
    if not title:
        return []
    params = openalex_params({"search": title, "per-page": per_page})
    payload = request_json(f"{OPENALEX_API}/works?{params}")
    if not payload:
        return []
    return payload.get("results", [])


def work_title(work: dict[str, Any]) -> str:
    return work.get("title") or work.get("display_name") or ""


def work_year(work: dict[str, Any]) -> str:
    year = work.get("publication_year")
    return str(year) if year else ""


def work_doi(work: dict[str, Any]) -> str:
    return normalize_doi(work.get("doi") or "")


def work_venue(work: dict[str, Any]) -> str:
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    if source.get("display_name"):
        return source["display_name"]
    host = work.get("host_venue") or {}
    return host.get("display_name") or ""


def work_authors(work: dict[str, Any], limit: int = 6) -> list[str]:
    authors = []
    for authorship in work.get("authorships", [])[:limit]:
        author = authorship.get("author") or {}
        if author.get("display_name"):
            authors.append(author["display_name"])
    return authors


def compare_entry_to_work(entry: BibEntry, work: dict[str, Any] | None) -> dict[str, Any]:
    local = entry.fields
    if not work:
        return {
            "key": entry.key,
            "status": "not_found",
            "warnings": ["OpenAlex match not found"],
            "local": local_summary(entry),
            "openalex": None,
        }

    local_title = local.get("title", "")
    oa_title = work_title(work)
    title_similarity = SequenceMatcher(None, normalize_text(local_title), normalize_text(oa_title)).ratio()
    local_year = clean_value(local.get("year", ""))
    oa_year = work_year(work)
    local_doi = normalize_doi(local.get("doi"))
    oa_doi = work_doi(work)
    warnings: list[str] = []

    if local_doi and oa_doi and local_doi != oa_doi:
        warnings.append(f"DOI mismatch: local {local_doi} vs OpenAlex {oa_doi}")
    if not local_doi and oa_doi:
        warnings.append(f"Local entry has no DOI; OpenAlex reports {oa_doi}")
    if local_year and oa_year and local_year != oa_year:
        warnings.append(f"Year mismatch: local {local_year} vs OpenAlex {oa_year}")
    if title_similarity < 0.85:
        warnings.append(f"Title similarity is low ({title_similarity:.2f})")

    if local_doi and oa_doi == local_doi:
        status = "verified"
    elif title_similarity >= 0.92 and (not local_year or not oa_year or local_year == oa_year):
        status = "verified"
    elif title_similarity >= 0.75:
        status = "review"
    else:
        status = "not_found"

    return {
        "key": entry.key,
        "status": status,
        "warnings": warnings,
        "local": local_summary(entry),
        "openalex": {
            "id": work.get("id"),
            "title": oa_title,
            "authors": work_authors(work),
            "year": oa_year,
            "venue": work_venue(work),
            "doi": oa_doi,
            "type": work.get("type"),
            "title_similarity": round(title_similarity, 3),
        },
    }


def local_summary(entry: BibEntry) -> dict[str, Any]:
    fields = entry.fields
    return {
        "entry_type": entry.entry_type,
        "key": entry.key,
        "title": fields.get("title", ""),
        "authors": author_last_names(fields.get("author")),
        "year": fields.get("year", ""),
        "venue": fields.get("journal") or fields.get("booktitle") or fields.get("publisher") or "",
        "doi": normalize_doi(fields.get("doi")),
        "url": fields.get("url", ""),
    }


def verify_entry(entry: BibEntry, per_page: int, pause: float) -> dict[str, Any]:
    work = None
    doi = normalize_doi(entry.fields.get("doi"))
    if doi:
        work = get_openalex_by_doi(doi)
        if pause:
            time.sleep(pause)
    if not work:
        results = search_openalex(entry.fields.get("title", ""), per_page=per_page)
        if pause:
            time.sleep(pause)
        if results:
            work = max(
                results,
                key=lambda candidate: SequenceMatcher(
                    None,
                    normalize_text(entry.fields.get("title", "")),
                    normalize_text(work_title(candidate)),
                ).ratio(),
            )
    return compare_entry_to_work(entry, work)


def search_local(entries: dict[str, BibEntry], query: str, limit: int) -> list[tuple[float, BibEntry]]:
    needle = normalize_text(query)
    scored = []
    for entry in entries.values():
        haystack = normalize_text(
            " ".join(
                [
                    entry.key,
                    entry.fields.get("title", ""),
                    entry.fields.get("author", ""),
                    entry.fields.get("journal", ""),
                    entry.fields.get("booktitle", ""),
                    entry.fields.get("publisher", ""),
                    entry.fields.get("year", ""),
                ]
            )
        )
        if not haystack:
            continue
        score = SequenceMatcher(None, needle, haystack).ratio()
        if needle in haystack:
            score += 0.5
        scored.append((score, entry))
    return sorted(scored, key=lambda item: item[0], reverse=True)[:limit]


def markdown_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Bibliography Check")
    lines.append("")
    lines.append(f"- BibTeX: `{payload['bib_path']}`")
    lines.append(f"- Entries: {payload['entry_count']}")

    duplicates = payload.get("duplicates", {})
    if duplicates:
        lines.append(f"- Duplicate keys: {', '.join(sorted(duplicates))}")
    else:
        lines.append("- Duplicate keys: none")

    missing = payload.get("missing_keys", [])
    if missing:
        lines.append(f"- Missing cited keys: {', '.join(missing)}")
    elif "missing_keys" in payload:
        lines.append("- Missing cited keys: none")

    doc_bibliography = payload.get("doc_bibliography")
    if doc_bibliography:
        if doc_bibliography.get("paths"):
            lines.append(f"- Document bibliography paths: {', '.join(doc_bibliography['paths'])}")
        for warning in doc_bibliography.get("warnings", []):
            lines.append(f"- Warning: {warning}")

    if payload.get("local_matches"):
        lines.append("")
        lines.append("## Local Matches")
        for item in payload["local_matches"]:
            entry = item["entry"]
            lines.append("")
            lines.append(f"- `{entry['key']}` ({entry['year']}): {entry['title']}")
            if entry.get("venue"):
                lines.append(f"  - Venue/publisher: {entry['venue']}")
            lines.append(f"  - Citation: `[@{entry['key']}]`; narrative: `[-@{entry['key']}]`")

    if payload.get("checks"):
        lines.append("")
        lines.append("## OpenAlex Checks")
        for result in payload["checks"]:
            local = result["local"]
            oa = result.get("openalex")
            lines.append("")
            lines.append(f"### `{result['key']}` - {result['status']}")
            lines.append(f"- Local: {local.get('title')} ({local.get('year')})")
            if local.get("venue"):
                lines.append(f"- Local venue/publisher: {local['venue']}")
            if local.get("doi"):
                lines.append(f"- Local DOI: `{local['doi']}`")
            if oa:
                lines.append(f"- OpenAlex: {oa.get('title')} ({oa.get('year')})")
                if oa.get("venue"):
                    lines.append(f"- OpenAlex venue: {oa['venue']}")
                if oa.get("doi"):
                    lines.append(f"- OpenAlex DOI: `{oa['doi']}`")
                if oa.get("id"):
                    lines.append(f"- OpenAlex ID: {oa['id']}")
                lines.append(f"- Title similarity: {oa.get('title_similarity')}")
            for warning in result.get("warnings", []):
                lines.append(f"- Warning: {warning}")
            lines.append(f"- Pandoc: `[@{result['key']}]`")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=DEFAULT_BIB, help="BibTeX file to read")
    parser.add_argument("--doc", type=Path, help="Markdown article to scan for Pandoc citation keys")
    parser.add_argument("--key", action="append", default=[], help="BibTeX key to verify; may be repeated")
    parser.add_argument("--query", help="Search local BibTeX entries before verifying the best matches")
    parser.add_argument("--all", action="store_true", help="Verify every BibTeX entry")
    parser.add_argument("--no-openalex", action="store_true", help="Only check local BibTeX and cited keys")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    parser.add_argument("--limit", type=int, default=5, help="Local query result limit")
    parser.add_argument("--max-openalex-results", type=int, default=5, help="OpenAlex search result count")
    parser.add_argument("--pause", type=float, default=0.05, help="Pause between OpenAlex requests")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on missing keys, duplicate keys, or unverified checks")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.bib.exists():
        print(f"BibTeX file not found: {args.bib}", file=sys.stderr)
        return 2

    entries, duplicates = load_bib(args.bib)
    keys: list[str] = []
    local_matches: list[dict[str, Any]] = []
    doc_bibliography: dict[str, Any] | None = None

    if args.doc:
        if not args.doc.exists():
            print(f"Document not found: {args.doc}", file=sys.stderr)
            return 2
        keys.extend(scan_doc_citations(args.doc))
        doc_bibliography = scan_doc_bibliography_paths(args.doc, args.bib)
    keys.extend(args.key)

    if args.query:
        matches = search_local(entries, args.query, args.limit)
        local_matches = [{"score": round(score, 3), "entry": local_summary(entry)} for score, entry in matches]
        if not keys and matches:
            keys.append(matches[0][1].key)

    if args.all:
        keys.extend(entries.keys())

    keys = sorted(set(keys))
    missing_keys = [key for key in keys if key not in entries]
    check_keys = [key for key in keys if key in entries]
    checks: list[dict[str, Any]] = []

    if not args.no_openalex:
        for key in check_keys:
            try:
                checks.append(verify_entry(entries[key], per_page=args.max_openalex_results, pause=args.pause))
            except Exception as exc:  # Keep the report useful when one remote check fails.
                checks.append(
                    {
                        "key": key,
                        "status": "review",
                        "warnings": [str(exc)],
                        "local": local_summary(entries[key]),
                        "openalex": None,
                    }
                )

    payload = {
        "bib_path": str(args.bib),
        "entry_count": len(entries),
        "duplicates": {key: [entry.entry_type for entry in vals] for key, vals in duplicates.items()},
        "missing_keys": missing_keys,
        "doc_bibliography": doc_bibliography,
        "local_matches": local_matches,
        "checks": checks,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(markdown_report(payload))

    if args.strict:
        has_bad_check = any(result["status"] != "verified" for result in checks)
        has_bad_doc_bib = bool(doc_bibliography and doc_bibliography.get("warnings"))
        if duplicates or missing_keys or has_bad_check or has_bad_doc_bib:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
