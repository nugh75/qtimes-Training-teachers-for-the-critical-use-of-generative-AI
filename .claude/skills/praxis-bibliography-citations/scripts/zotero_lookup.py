#!/usr/bin/env python3
"""Search a Zotero library through the Web API or a local zotero.sqlite file."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ZOTERO_API = "https://api.zotero.org"


@dataclass
class ZoteroConfig:
    library_type: str
    library_id: str
    api_key: str | None

    @property
    def prefix(self) -> str:
        if self.library_type == "group":
            return f"/groups/{self.library_id}"
        return f"/users/{self.library_id}"


def env_config(args: argparse.Namespace) -> ZoteroConfig | None:
    library_type = args.library_type or os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
    library_type = library_type.lower().strip()
    api_key = args.api_key or os.environ.get("ZOTERO_API_KEY")

    if library_type == "group":
        library_id = args.group_id or os.environ.get("ZOTERO_GROUP_ID")
    else:
        library_id = args.user_id or os.environ.get("ZOTERO_USER_ID")

    if not library_id:
        return None
    return ZoteroConfig(library_type=library_type, library_id=library_id, api_key=api_key)


def request_zotero(path: str, params: dict[str, Any], config: ZoteroConfig) -> Any:
    params = {key: value for key, value in params.items() if value is not None}
    params.setdefault("v", 3)
    url = f"{ZOTERO_API}{path}?{urlencode(params)}"
    headers = {"Zotero-API-Version": "3", "User-Agent": "praxis-bibliography-citations/1.0"}
    if config.api_key:
        headers["Zotero-API-Key"] = config.api_key
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            data = response.read().decode("utf-8")
            if "json" in content_type:
                return json.loads(data)
            return data
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Zotero API returned {exc.code}: {detail[:500]}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Zotero API request failed: {exc}") from exc


def zotero_api_search(config: ZoteroConfig, query: str, limit: int, qmode: str) -> list[dict[str, Any]]:
    payload = request_zotero(
        f"{config.prefix}/items",
        {
            "format": "json",
            "include": "data,bibtex",
            "q": query,
            "qmode": qmode,
            "limit": limit,
            "sort": "dateModified",
            "direction": "desc",
        },
        config,
    )
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Zotero API response")
    return payload


def zotero_api_item_bibtex(config: ZoteroConfig, item_key: str) -> str:
    return request_zotero(f"{config.prefix}/items/{quote(item_key)}", {"format": "bibtex"}, config)


def item_summary(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data", {})
    creators = data.get("creators", [])
    authors = []
    for creator in creators:
        if creator.get("name"):
            authors.append(creator["name"])
        else:
            name = " ".join(part for part in [creator.get("firstName"), creator.get("lastName")] if part)
            if name:
                authors.append(name)
    return {
        "key": item.get("key") or data.get("key"),
        "title": data.get("title", ""),
        "itemType": data.get("itemType", ""),
        "creators": authors,
        "date": data.get("date", ""),
        "publicationTitle": data.get("publicationTitle", ""),
        "publisher": data.get("publisher", ""),
        "doi": data.get("DOI") or data.get("doi") or "",
        "url": data.get("url", ""),
        "bibtex": item.get("bibtex", ""),
    }


def find_default_zotero_db() -> Path | None:
    candidates = [
        Path.home() / "Zotero" / "zotero.sqlite",
        Path.home() / ".zotero" / "zotero" / "zotero.sqlite",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def sqlite_field_id(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute("SELECT fieldID FROM fields WHERE fieldName = ?", (name,)).fetchone()
    return int(row[0]) if row else None


def sqlite_values_for_item(conn: sqlite3.Connection, item_id: int, field_ids: dict[str, int | None]) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, field_id in field_ids.items():
        if field_id is None:
            continue
        row = conn.execute(
            """
            SELECT itemDataValues.value
            FROM itemData
            JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
            WHERE itemData.itemID = ? AND itemData.fieldID = ?
            LIMIT 1
            """,
            (item_id, field_id),
        ).fetchone()
        if row and row[0]:
            values[name] = str(row[0])
    return values


def sqlite_creators_for_item(conn: sqlite3.Connection, item_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT creatorData.firstName, creatorData.lastName, creatorData.name
        FROM itemCreators
        JOIN creators ON itemCreators.creatorID = creators.creatorID
        JOIN creatorData ON creators.creatorDataID = creatorData.creatorDataID
        WHERE itemCreators.itemID = ?
        ORDER BY itemCreators.orderIndex
        """,
        (item_id,),
    ).fetchall()
    creators = []
    for first_name, last_name, name in rows:
        if name:
            creators.append(str(name))
        else:
            creators.append(" ".join(part for part in [first_name, last_name] if part))
    return [creator for creator in creators if creator]


def sqlite_search(db_path: Path, query: str, limit: int) -> list[dict[str, Any]]:
    uri = f"file:{db_path}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    try:
        field_ids = {
            "title": sqlite_field_id(conn, "title"),
            "date": sqlite_field_id(conn, "date"),
            "publicationTitle": sqlite_field_id(conn, "publicationTitle"),
            "publisher": sqlite_field_id(conn, "publisher"),
            "DOI": sqlite_field_id(conn, "DOI"),
            "url": sqlite_field_id(conn, "url"),
        }
        title_id = field_ids["title"]
        doi_id = field_ids["DOI"]
        url_id = field_ids["url"]
        like = f"%{query}%"
        rows = conn.execute(
            """
            SELECT DISTINCT items.itemID, items.key, itemTypes.typeName
            FROM items
            JOIN itemTypes ON items.itemTypeID = itemTypes.itemTypeID
            LEFT JOIN deletedItems ON items.itemID = deletedItems.itemID
            LEFT JOIN itemData AS titleData
              ON titleData.itemID = items.itemID AND titleData.fieldID = ?
            LEFT JOIN itemDataValues AS titleValue
              ON titleData.valueID = titleValue.valueID
            LEFT JOIN itemData AS doiData
              ON doiData.itemID = items.itemID AND doiData.fieldID = ?
            LEFT JOIN itemDataValues AS doiValue
              ON doiData.valueID = doiValue.valueID
            LEFT JOIN itemData AS urlData
              ON urlData.itemID = items.itemID AND urlData.fieldID = ?
            LEFT JOIN itemDataValues AS urlValue
              ON urlData.valueID = urlValue.valueID
            WHERE deletedItems.itemID IS NULL
              AND itemTypes.typeName NOT IN ('attachment', 'note')
              AND (
                titleValue.value LIKE ?
                OR doiValue.value LIKE ?
                OR urlValue.value LIKE ?
              )
            ORDER BY items.itemID DESC
            LIMIT ?
            """,
            (title_id, doi_id, url_id, like, like, like, limit),
        ).fetchall()
        results = []
        for item_id, key, item_type in rows:
            values = sqlite_values_for_item(conn, int(item_id), field_ids)
            results.append(
                {
                    "key": key,
                    "title": values.get("title", ""),
                    "itemType": item_type,
                    "creators": sqlite_creators_for_item(conn, int(item_id)),
                    "date": values.get("date", ""),
                    "publicationTitle": values.get("publicationTitle", ""),
                    "publisher": values.get("publisher", ""),
                    "doi": values.get("DOI", ""),
                    "url": values.get("url", ""),
                    "bibtex": "",
                }
            )
        return results
    finally:
        conn.close()


def markdown_report(source: str, results: list[dict[str, Any]]) -> str:
    lines = [f"# Zotero Lookup", "", f"- Source: {source}", f"- Results: {len(results)}"]
    for item in results:
        lines.append("")
        lines.append(f"## {item.get('title') or '(untitled)'}")
        lines.append(f"- Zotero key: `{item.get('key')}`")
        if item.get("creators"):
            lines.append(f"- Creators: {', '.join(item['creators'])}")
        if item.get("date"):
            lines.append(f"- Date: {item['date']}")
        venue = item.get("publicationTitle") or item.get("publisher")
        if venue:
            lines.append(f"- Venue/publisher: {venue}")
        if item.get("doi"):
            lines.append(f"- DOI: `{item['doi']}`")
        if item.get("url"):
            lines.append(f"- URL: {item['url']}")
        if item.get("bibtex"):
            first_line = item["bibtex"].strip().splitlines()[0] if item["bibtex"].strip() else ""
            if first_line:
                lines.append(f"- BibTeX starts: `{first_line}`")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Title, DOI, URL, author, or keyword to search")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--bibtex", action="store_true", help="Emit BibTeX when using the Zotero Web API")
    parser.add_argument("--db", type=Path, default=os.environ.get("ZOTERO_DB_PATH"), help="Path to local zotero.sqlite")
    parser.add_argument("--api", action="store_true", help="Force Zotero Web API mode")
    parser.add_argument("--local", action="store_true", help="Force local sqlite mode")
    parser.add_argument("--api-key", help="Zotero API key; defaults to ZOTERO_API_KEY")
    parser.add_argument("--user-id", help="Zotero user ID; defaults to ZOTERO_USER_ID")
    parser.add_argument("--group-id", help="Zotero group ID; defaults to ZOTERO_GROUP_ID")
    parser.add_argument("--library-type", choices=["user", "group"], help="Zotero library type")
    parser.add_argument("--qmode", choices=["titleCreatorYear", "everything"], default="titleCreatorYear")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.api and args.local:
        print("Choose only one of --api or --local", file=sys.stderr)
        return 2

    results: list[dict[str, Any]]
    source: str

    if not args.local:
        config = env_config(args)
    else:
        config = None

    if config:
        raw_results = zotero_api_search(config, args.query, args.limit, args.qmode)
        results = [item_summary(item) for item in raw_results]
        source = f"Zotero Web API {config.prefix}"
        if args.bibtex:
            for item in results:
                if item.get("key") and not item.get("bibtex"):
                    item["bibtex"] = zotero_api_item_bibtex(config, item["key"])
    else:
        db_path = Path(args.db).expanduser() if args.db else find_default_zotero_db()
        if args.api:
            print("Missing Zotero API configuration. Set ZOTERO_USER_ID and optionally ZOTERO_API_KEY.", file=sys.stderr)
            return 2
        if not db_path or not db_path.exists():
            print(
                "No Zotero source configured. Set ZOTERO_USER_ID/ZOTERO_API_KEY for Web API, "
                "or pass --db /path/to/zotero.sqlite.",
                file=sys.stderr,
            )
            return 2
        results = sqlite_search(db_path, args.query, args.limit)
        source = f"local sqlite {db_path}"

    if args.bibtex:
        bibtex_entries = [item.get("bibtex", "").strip() for item in results if item.get("bibtex")]
        print("\n\n".join(bibtex_entries))
    elif args.json:
        print(json.dumps({"source": source, "results": results}, ensure_ascii=False, indent=2))
    else:
        print(markdown_report(source, results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
