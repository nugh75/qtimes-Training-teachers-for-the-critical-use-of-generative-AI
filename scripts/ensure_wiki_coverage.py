#!/usr/bin/env python3
"""Garantisce che ogni file corpus sia citato da almeno un sottotema wiki.

Per ogni record corpus non ancora citato:
1. Legge il label JSON (dimensioni, subcodes, note).
2. Trova il sottotema wiki più adatto nella popolazione/dimensione giusta.
3. Se nessun sottotema esistente è pertinente, ne crea uno nuovo.
4. Inietta il source link nella sezione appropriata del sottotema.
5. Rigenera il grafo wiki (opzionale, --rebuild-graph).

Tutto deterministico — nessuna chiamata LLM.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
RAW_DIR = ROOT_DIR / "02-corpus"
WIKI_DIR = ROOT_DIR / "01-wiki"
LABELS_DIR = ROOT_DIR / "04-label" / "labels" / "ollama-gemma4"

POPULATION_MAP = {
    "Insegnanti in servizio": "insegnanti-attuali",
    "Insegnanti pre-service": "insegnanti-futuri",
    "Studenti": "studenti",
}

POPULATION_LABELS = {
    "insegnanti-attuali": "Insegnanti Attuali",
    "insegnanti-futuri": "Insegnanti Futuri",
    "studenti": "Studenti",
}

DIM_SLUG = {
    "P": "practice-patterns",
    "R": "readiness-beliefs",
    "A": "adequacy-of-support",
    "X": "expectations",
    "I": "interpersonal-trust",
    "S": "skepticisms",
}

DIM_FULL_NAMES = {
    "P": "Modelli d'uso (P)",
    "R": "Readiness beliefs (R)",
    "A": "Adequacy of support (A)",
    "X": "eXpectations (X)",
    "I": "Interpersonal & Institutional trust (I)",
    "S": "Skepticisms (S)",
}

# Mappa subcode → slug sottotema esistente (per popolazione).
# Costruita dinamicamente da _build_subcode_routing().
# Struttura: { pop_slug: { subcode: wiki_page_path } }

# Subcodes raggruppati per affinità tematica per la creazione di nuove pagine.
SUBCODE_THEME_GROUPS: dict[str, dict[str, str]] = {
    "P": {
        "P1": "produzione-materiali",
        "P2": "individualizzazione-personalizzazione",
        "P3": "inclusione-accessibilita",
        "P4": "tutoraggio-simulazione",
        "P5": "strategie-produzione",
        "P6": "ecosistema-strumenti",
        "P7": "prompting-pratico",
    },
    "R": {
        "R1": "competenza-pratica",
        "R2": "competenza-epistemologica",
        "R3": "gap-uso-personale-didattico",
        "R4": "competenza-prompting",
        "R5": "non-uso-consapevole",
    },
    "A": {
        "A1": "assenza-formazione",
        "A2": "supporto-insufficiente",
        "A3": "vincoli-infrastrutturali",
        "A4": "uso-compensativo",
    },
    "X": {
        "X1": "efficienza-tempo",
        "X2": "semplificazione-comprensione",
        "X3": "personalizzazione-singolo",
        "X4": "inclusione-accesso",
        "X5": "autonomia-organizzazione",
        "X6": "coinvolgimento-innovazione",
        "X7": "cambiamento-condizionato",
    },
    "I": {
        "I1": "fiducia-tecnica-condizionata",
        "I2": "sfiducia-tecnica",
        "I3": "fiducia-negli-utenti",
        "I4": "fiducia-relazionale",
        "I5": "privacy-dati",
    },
    "S": {
        "S1": "delega-cognitiva",
        "S2": "ghostwriting-plagio",
        "S3": "appiattimento-omologazione",
        "S4": "erosione-pensiero-critico",
        "S5": "informazioni-false",
        "S6": "sostituzione-docente",
        "S7": "ambiti-off-limits",
    },
}

SUBCODE_DESCRIPTIONS: dict[str, str] = {
    "P1": "Produzione di materiali didattici o di studio",
    "P2": "Individualizzazione e personalizzazione",
    "P3": "Inclusione e accessibilità",
    "P4": "Supporto allo studio, simulazione, tutoraggio",
    "P5": "Strategie operative di produzione",
    "P6": "Ecosistema di strumenti",
    "P7": "Prompting visibile",
    "R1": "Competenza pratica percepita",
    "R2": "Competenza teorica o epistemologica",
    "R3": "Gap tra uso personale e uso didattico",
    "R4": "Competenza di prompting",
    "R5": "Non-uso per impreparazione o rifiuto competente",
    "A1": "Assenza di formazione formale",
    "A2": "Supporto insufficiente o diseguale",
    "A3": "Vincoli infrastrutturali ed economici",
    "A4": "Uso compensativo dell'IA",
    "X1": "Efficienza e risparmio di tempo",
    "X2": "Semplificazione e comprensione",
    "X3": "Personalizzazione e attenzione al singolo",
    "X4": "Inclusione e accesso",
    "X5": "Autonomia, organizzazione e supporto al percorso",
    "X6": "Coinvolgimento, arricchimento e innovazione",
    "X7": "Cambiamento condizionato",
    "I1": "Fiducia tecnica condizionata",
    "I2": "Sfiducia tecnica: errori e allucinazioni",
    "I3": "Fiducia o sfiducia negli utenti",
    "I4": "Fiducia relazionale e pedagogica",
    "I5": "Privacy e affidamento dei dati",
    "S1": "Delega cognitiva eccessiva",
    "S2": "Ghostwriting e plagio",
    "S3": "Appiattimento, omologazione, perdita di creatività",
    "S4": "Erosione del pensiero critico",
    "S5": "Informazioni false e imprecisione",
    "S6": "Sostituzione del docente o della relazione educativa",
    "S7": "Ambiti off-limits",
}

# Mapping manuale subcodes → pagine wiki esistenti.
# Chiave = pop_slug, valore = { subcode: stem_pagina_wiki }
# Se un subcode non è mappato, si crea una nuova pagina.
EXISTING_SUBCODE_MAP: dict[str, dict[str, str]] = {
    "insegnanti-attuali": {
        "P7": "prompt-engineering",
        "P6": "strumenti-settoriali",
        "P3": "caa-autismo-non-verbale",
        "P2": "individualizzazione-bes-dsa",
        "S4": "impoverimento-cognitivo",
        "S6": "crollo-relazionale",
        "S1": "impoverimento-cognitivo",
        "I2": "bias-e-allucinazione",
        "I4": "filosofia-della-fatica",
        "I3": "paradosso-digitale",
        "A3": "paywall",
        "A2": "logistica-e-dispositivi",
        "A1": "resistenza-manageriale",
        "X4": "inclusione-digitale",
        "X6": "inclusione-digitale",
        "X7": "peggioramento-efficace",
    },
    "insegnanti-futuri": {
        "P4": "facilitazione-accademica",
        "P5": "facilitazione-accademica",
        "P6": "uso-cross-disciplinare",
        "S2": "plagio-e-disonesta",
        "S4": "impoverimento-cognitivo",
        "S5": "copyright",
        "I4": "relazione-educativa",
        "I3": "sostituzione-docente",
        "X7": "cambiamento-positivo",
        "X3": "omologazione",
    },
    "studenti": {
        "P4": "interrogatore-e-autovalutazione",
        "P5": "uso-strumentale-evasivo",
        "R5": "profili-di-non-uso-1-6",
        "X2": "supporto-vs-sostituzione",
        "X3": "autonomia-cognitiva-a-rischio",
        "S7": "zone-di-esclusione-s6",
        "S4": "evoluzione-del-tabu",
        "I2": "sfiducia-tecnica-e-strutturale",
        "I5": "conferma-sfiducia-e-privacy",
    },
}

RAW_REF_RE = re.compile(r"(?:raw|corpus)/([^\s)]+?)\.md")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--corpus-dir",
        "--raw-dir",
        dest="raw_dir",
        type=Path,
        default=RAW_DIR,
    )
    p.add_argument("--wiki-dir", type=Path, default=WIKI_DIR)
    p.add_argument("--labels-dir", type=Path, default=LABELS_DIR)
    p.add_argument("--dry-run", action="store_true", help="Mostra cosa farebbe senza scrivere.")
    p.add_argument("--rebuild-graph", action="store_true", help="Rigenera wiki-graph-data.json.")
    p.add_argument("--limit", type=int, help="Limita il numero di record corpus da processare.")
    return p.parse_args()


def find_cited_stems(wiki_dir: Path) -> set[str]:
    """Trova tutti gli stem corpus citati nelle pagine wiki."""
    cited: set[str] = set()
    for p in wiki_dir.rglob("*.md"):
        text = p.read_text(encoding="utf-8")
        for m in RAW_REF_RE.finditer(text):
            cited.add(m.group(1))
    return cited


def load_label(labels_dir: Path, stem: str) -> dict[str, Any] | None:
    path = labels_dir / f"{stem}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def primary_subcode(label: dict[str, Any]) -> str | None:
    """Subcode dominante del record (per conteggio o primo in lista)."""
    counts = label.get("code_counts", {})
    subcodes = label.get("record_subcodes", [])
    if counts:
        return max(counts, key=lambda k: counts[k])
    if subcodes:
        return subcodes[0]
    return None


def resolve_wiki_page(
    pop_slug: str,
    dim_letter: str,
    subcode: str,
    wiki_dir: Path,
) -> Path | None:
    """Trova la pagina wiki esistente (sottotema, NON indice) per un subcode, o None."""
    mapping = EXISTING_SUBCODE_MAP.get(pop_slug, {})
    dim_slug = DIM_SLUG[dim_letter]

    if subcode in mapping:
        stem = mapping[subcode]
        # Prova nella dir della dimensione
        candidate = wiki_dir / pop_slug / dim_slug / f"{stem}.md"
        if candidate.exists():
            return candidate
        # Prova come file singolo nella dir pop
        candidate2 = wiki_dir / pop_slug / f"{stem}.md"
        if candidate2.exists():
            return candidate2

    # NON fallback a indice: restituisce None → verrà creata nuova pagina
    return None


def compute_raw_relative_link(wiki_page: Path, raw_stem: str, wiki_dir: Path) -> str:
    """Calcola il path relativo dal file wiki al file corpus."""
    rel = wiki_page.relative_to(wiki_dir)
    depth = len(rel.parts) - 1  # -1 perché l'ultimo è il file
    up = "/".join([".."] * (depth + 1))  # +1 per uscire da 01-wiki/
    return f"{up}/02-corpus/{raw_stem}.md"


def create_new_subtheme_page(
    pop_slug: str,
    dim_letter: str,
    subcode: str,
    wiki_dir: Path,
) -> Path:
    """Crea una nuova pagina wiki di sottotema."""
    dim_slug = DIM_SLUG[dim_letter]
    theme_groups = SUBCODE_THEME_GROUPS.get(dim_letter, {})
    slug = theme_groups.get(subcode, subcode.lower())

    dim_dir = wiki_dir / pop_slug / dim_slug
    dim_dir.mkdir(parents=True, exist_ok=True)

    page_path = dim_dir / f"{slug}.md"
    if page_path.exists():
        return page_path

    title = SUBCODE_DESCRIPTIONS.get(subcode, slug.replace("-", " ").title())
    pop_label = POPULATION_LABELS.get(pop_slug, pop_slug)
    dim_full = DIM_FULL_NAMES.get(dim_letter, dim_letter)
    today = date.today().isoformat()

    # Trova pagina indice
    index_stem = f"{dim_slug}-{pop_slug}"
    index_link = f"[Indice {dim_slug.replace('-', ' ').title()}]({index_stem}.md)"

    content = f"""# {title}
**Dimensione**: {dim_full}
**Popolazione**: {pop_label}

**Summary**: Pagina generata automaticamente per raccogliere i record corpus assegnati al subcode {subcode} ({SUBCODE_DESCRIPTIONS.get(subcode, '')}) non ancora coperti da altri sottotemi.

**Sources**: vedi citazioni nel testo.

**Last updated**: {today}

---

## Record collegati

<!-- I source link seguenti sono stati generati automaticamente da ensure_wiki_coverage.py -->

## Pagine correlate
- {index_link}
- [Indice {pop_label.lower()}](../index-{pop_slug}.md)
"""
    page_path.write_text(content, encoding="utf-8")
    return page_path


def inject_source_link(
    wiki_page: Path,
    raw_stem: str,
    record_code: str,
    wiki_dir: Path,
) -> bool:
    """Inietta un source link nel sottotema wiki. Ritorna True se modificato."""
    text = wiki_page.read_text(encoding="utf-8")

    # Già citato?
    if raw_stem in text:
        return False

    rel_link = compute_raw_relative_link(wiki_page, raw_stem, wiki_dir)
    source_line = f"(source: [{record_code}]({rel_link}))"

    # Trova punto di inserimento: prima di "## Pagine correlate" o in fondo
    correlate_match = re.search(r"^## Pagine correlate", text, flags=re.MULTILINE)
    record_match = re.search(r"^## Record collegati", text, flags=re.MULTILINE)

    if record_match:
        # Inserisci dopo "## Record collegati" e eventuali commenti
        insert_pos = record_match.end()
        # Salta fino alla fine del paragrafo o commento
        rest = text[insert_pos:]
        skip_match = re.match(r"(\s*\n(?:<!--.*?-->\s*\n)?)", rest, re.DOTALL)
        if skip_match:
            insert_pos += skip_match.end()
        new_line = f"\n- {source_line}\n"
        text = text[:insert_pos] + new_line + text[insert_pos:]
    elif correlate_match:
        insert_pos = correlate_match.start()
        new_line = f"- {source_line}\n\n"
        text = text[:insert_pos] + new_line + text[insert_pos:]
    else:
        text = text.rstrip() + f"\n\n- {source_line}\n"

    wiki_page.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    args = parse_args()
    wiki_dir = args.wiki_dir.resolve()
    raw_dir = args.raw_dir
    labels_dir = args.labels_dir

    # 1. Trova record corpus non citati
    all_stems = sorted(p.stem for p in raw_dir.glob("*.md"))
    cited = find_cited_stems(wiki_dir)
    uncited = [s for s in all_stems if s not in cited]

    if args.limit:
        uncited = uncited[: args.limit]

    print(f"Corpus totali: {len(all_stems)}")
    print(f"Già citati: {len(cited)}")
    print(f"Da coprire: {len(uncited)}")
    print()

    # 2. Per ogni non-citato, trova dove inserirlo
    stats = Counter[str]()
    pages_created: list[str] = []
    pages_modified: set[str] = set()
    assignments: list[dict[str, str]] = []

    for stem in uncited:
        label = load_label(labels_dir, stem)
        if label is None:
            # No label → crea comunque un collegamento dal nome del file
            # Inferisci popolazione dal nome
            if stem.startswith("insegnanti_attuali_"):
                pop_slug = "insegnanti-attuali"
            elif stem.startswith("insegnanti_futuri_"):
                pop_slug = "insegnanti-futuri"
            elif stem.startswith("studenti_"):
                pop_slug = "studenti"
            else:
                stats["unknown_pop"] += 1
                continue
            label = {"group": POPULATION_LABELS.get(pop_slug, ""), "record_code": stem}
            stats["no_label_recovered"] += 1

        group = label.get("group", "")
        pop_slug_from_map = POPULATION_MAP.get(group)
        if pop_slug_from_map is not None:
            pop_slug = pop_slug_from_map
        elif not isinstance(pop_slug, str):
            stats["unknown_pop"] += 1
            continue

        dims = label.get("record_dimensions", [])
        subcodes = label.get("record_subcodes", [])
        record_code = label.get("record_code", stem)

        # Strategia: usa la dimensione col subcode dominante
        dominant = primary_subcode(label)

        if dominant:
            target_dim = dominant[0]
            target_subcode = dominant
        elif subcodes:
            target_subcode = subcodes[0]
            target_dim = target_subcode[0]
        elif dims:
            target_dim = dims[0]
            target_subcode = f"{target_dim}1"
        else:
            # Nessuna dimensione: assegna a pagina catch-all
            target_dim = None
            target_subcode = None

        # Gestione pagina per record senza dimensioni
        if target_dim is None:
            # Pagina catch-all per record non classificati
            catchall_dir = wiki_dir / pop_slug
            catchall_dir.mkdir(parents=True, exist_ok=True)
            catchall_path = catchall_dir / "non-classificati.md"
            if not catchall_path.exists():
                pop_label = POPULATION_LABELS.get(pop_slug, pop_slug)
                today = date.today().isoformat()
                catchall_path.write_text(
                    f"# Record non classificati\n"
                    f"**Popolazione**: {pop_label}\n\n"
                    f"Record per i quali la classificazione automatica non ha "
                    f"assegnato dimensioni PRAXIS.\n\n"
                    f"**Last updated**: {today}\n\n---\n\n"
                    f"## Record collegati\n\n"
                    f"## Pagine correlate\n"
                    f"- [Indice {pop_label.lower()}](index-{pop_slug}.md)\n",
                    encoding="utf-8",
                )
                pages_created.append(str(catchall_path.relative_to(ROOT_DIR)))
                stats["created"] += 1

            wiki_page = catchall_path
        else:
            # Trova o crea la pagina wiki
            wiki_page = resolve_wiki_page(pop_slug, target_dim, target_subcode, wiki_dir)

            if wiki_page is None:
                # Crea nuova pagina
                if args.dry_run:
                    theme_slug = SUBCODE_THEME_GROUPS.get(target_dim, {}).get(
                        target_subcode, target_subcode.lower()
                    )
                    new_path = wiki_dir / pop_slug / DIM_SLUG[target_dim] / f"{theme_slug}.md"
                    print(f"  [CREATE] {new_path.relative_to(ROOT_DIR)}")
                    pages_created.append(str(new_path.relative_to(ROOT_DIR)))
                    stats["would_create"] += 1
                else:
                    wiki_page = create_new_subtheme_page(
                        pop_slug, target_dim, target_subcode, wiki_dir
                    )
                    pages_created.append(str(wiki_page.relative_to(ROOT_DIR)))
                    stats["created"] += 1

        if wiki_page is not None and not args.dry_run:
            modified = inject_source_link(wiki_page, stem, record_code, wiki_dir)
            if modified:
                pages_modified.add(str(wiki_page.relative_to(ROOT_DIR)))
                stats["injected"] += 1
            else:
                stats["already_present"] += 1
        elif args.dry_run:
            stats["would_inject"] += 1

        assignments.append({
            "stem": stem,
            "pop": pop_slug,
            "dim": target_dim,
            "subcode": target_subcode,
            "page": str(wiki_page.relative_to(ROOT_DIR)) if wiki_page else "(new)",
        })

    # Report
    print("--- Risultati ---")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print()

    if pages_created:
        print(f"Pagine create ({len(pages_created)}):")
        for p in sorted(set(pages_created)):
            print(f"  + {p}")
        print()

    if pages_modified:
        print(f"Pagine modificate ({len(pages_modified)}):")
        for p in sorted(pages_modified):
            print(f"  ~ {p}")
        print()

    # Salva report JSON
    report_path = labels_dir.parent / "coverage-report.json"
    if not args.dry_run:
        report_path.write_text(
            json.dumps(
                {
                    "total_raw": len(all_stems),
                    "previously_cited": len(cited),
                    "processed": len(uncited),
                    "stats": dict(stats),
                    "pages_created": sorted(set(pages_created)),
                    "pages_modified": sorted(pages_modified),
                    "assignments": assignments,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Report salvato: {report_path}")

    # 3. Rigenera grafo wiki
    if args.rebuild_graph and not args.dry_run:
        print("\nRigenerazione grafo wiki...")
        import subprocess

        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "build_wiki_graph_data.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Grafo wiki rigenerato.")
            print(result.stdout)
        else:
            print(f"Errore nella rigenerazione: {result.stderr}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
