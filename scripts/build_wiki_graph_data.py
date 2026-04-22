#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
WIKI_DIR = ROOT_DIR / "01-wiki"
DEFAULT_OUTPUT_FILE = ROOT_DIR / "viz" / "wiki" / "wiki-graph-data.json"

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#\s+(.+)$", flags=re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", flags=re.DOTALL)
TITLE_IN_FM_RE = re.compile(r"^title:\s*\"?(.+?)\"?\s*$", flags=re.MULTILINE)


@dataclass
class Page:
    path: Path
    rel: str
    node_id: str
    title: str
    section: str
    group: str
    praxis: str
    subtheme: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Costruisce il dataset grafo per le pagine in 01-wiki/, "
            "usando solo link markdown."
        )
    )
    parser.add_argument("--wiki-dir", type=Path, default=WIKI_DIR)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    return parser.parse_args()


def page_node_id(path: Path, wiki_dir: Path) -> str:
    rel = path.relative_to(ROOT_DIR).as_posix()
    # node id senza estensione: 01-wiki/foo/bar
    return rel[:-3] if rel.endswith(".md") else rel


def detect_title(text: str, fallback: str) -> str:
    fm_match = FRONTMATTER_RE.search(text)
    if fm_match:
        title_match = TITLE_IN_FM_RE.search(fm_match.group(1))
        if title_match:
            return title_match.group(1).strip()
    heading_match = HEADING_RE.search(text)
    if heading_match:
        return heading_match.group(1).strip()
    return fallback


def detect_section(path: Path, wiki_dir: Path) -> str:
    rel_parts = path.relative_to(wiki_dir).parts
    if len(rel_parts) <= 1:
        return "_root"
    return rel_parts[0]


def detect_levels(path: Path, wiki_dir: Path) -> tuple[str, str, str]:
    parts = path.relative_to(wiki_dir).parts
    group = parts[0] if len(parts) >= 2 else "_root"
    praxis = parts[1] if len(parts) >= 3 else "_index"
    subtheme = path.stem
    return group, praxis, subtheme


def load_pages(wiki_dir: Path) -> list[Page]:
    pages: list[Page] = []
    for path in sorted(wiki_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        fallback = path.stem.replace("-", " ")
        title = detect_title(text, fallback=fallback)
        rel = path.relative_to(ROOT_DIR).as_posix()
        group, praxis, subtheme = detect_levels(path, wiki_dir)
        pages.append(
            Page(
                path=path,
                rel=rel,
                node_id=page_node_id(path, wiki_dir),
                title=title,
                section=detect_section(path, wiki_dir),
                group=group,
                praxis=praxis,
                subtheme=subtheme,
            )
        )
    return pages


def strip_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if not target:
        return ""
    # rimuove eventuale titolo markdown: (path "title")
    if " " in target:
        target = target.split(" ", 1)[0].strip()
    target = target.strip("<>").strip()
    if not target:
        return ""
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    return target


def normalize_target_path(source: Path, target: str, wiki_dir: Path) -> Path | None:
    if not target:
        return None
    lowered = target.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "tel:")):
        return None
    if target.startswith("#"):
        return None

    if target.startswith("/"):
        candidate = ROOT_DIR / target.lstrip("/")
    else:
        candidate = (source.parent / target).resolve()

    # solo markdown links verso pagine wiki
    if candidate.suffix == "":
        md_candidate = candidate.with_suffix(".md")
        if md_candidate.exists():
            candidate = md_candidate
        else:
            return None
    if candidate.suffix.lower() != ".md":
        return None
    if not candidate.exists():
        return None

    try:
        candidate.relative_to(wiki_dir.resolve())
    except ValueError:
        return None

    return candidate


def build_graph(pages: list[Page], wiki_dir: Path) -> dict:
    pages_by_abs = {page.path.resolve(): page for page in pages}
    out_counter = Counter[str]()
    in_counter = Counter[str]()
    undirected_edges = Counter[tuple[str, str]]()
    outgoing_map: dict[str, set[str]] = defaultdict(set)

    for page in pages:
        text = page.path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            raw_target = match.group(1)
            target_token = strip_link_target(raw_target)
            target_path = normalize_target_path(
                source=page.path.resolve(),
                target=target_token,
                wiki_dir=wiki_dir,
            )
            if not target_path:
                continue
            target_page = pages_by_abs.get(target_path.resolve())
            if not target_page:
                continue
            if target_page.node_id == page.node_id:
                continue

            outgoing_map[page.node_id].add(target_page.node_id)
            out_counter[page.node_id] += 1
            in_counter[target_page.node_id] += 1

            left, right = sorted([page.node_id, target_page.node_id])
            undirected_edges[(left, right)] += 1

    section_counts = Counter(page.section for page in pages)
    group_counts = Counter(page.group for page in pages)
    praxis_counts = Counter(page.praxis for page in pages)
    nodes = []
    for page in pages:
        out_degree = len(outgoing_map.get(page.node_id, set()))
        in_degree = sum(1 for src in outgoing_map if page.node_id in outgoing_map[src])
        degree = out_degree + in_degree
        nodes.append(
            {
                "id": page.node_id,
                "title": page.title,
                "path": page.rel,
                "section": page.section,
                "group": page.group,
                "praxis": page.praxis,
                "subtheme": page.subtheme,
                "degree": degree,
                "out_degree": out_degree,
                "in_degree": in_degree,
            }
        )

    edges = [
        {"source": source, "target": target, "weight": weight}
        for (source, target), weight in sorted(
            undirected_edges.items(), key=lambda x: (-x[1], x[0][0], x[0][1])
        )
    ]

    return {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "nodes_total": len(nodes),
            "edges_total": len(edges),
        },
        "sections": dict(sorted(section_counts.items())),
        "groups": dict(sorted(group_counts.items())),
        "praxis_elements": dict(sorted(praxis_counts.items())),
        "nodes": nodes,
        "edges": edges,
    }


def main() -> int:
    args = parse_args()
    pages = load_pages(args.wiki_dir)
    payload = build_graph(pages, wiki_dir=args.wiki_dir)

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "wiki_pages": payload["meta"]["nodes_total"],
                "edges": payload["meta"]["edges_total"],
                "output_file": str(args.output_file),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
