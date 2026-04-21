#!/usr/bin/env python3
"""Arricchisce le pagine wiki stub con testo discorsivo generato dall'LLM.

Per ogni pagina stub (generata da ensure_wiki_coverage.py):
1. Legge tutti i file raw citati nella pagina.
2. Legge eventuali label JSON per contesto.
3. Invia il tutto a Ollama con un system prompt che richiede
   prosa qualitativa in stile wiki (come da instructions/).
4. Sostituisce il contenuto della pagina mantenendo metadati e link.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib import error, request

ROOT_DIR = Path(__file__).resolve().parents[1]
WIKI_DIR = ROOT_DIR / "wiki"
RAW_DIR = ROOT_DIR / "raw"
LABELS_DIR = ROOT_DIR / "labels" / "ollama-gemma4"
DEFAULT_HOST = "http://192.168.129.14:11434"
DEFAULT_MODEL = "gemma4:e4b"
LOGGER = logging.getLogger("enrich_wiki_stubs")

STUB_MARKER = "Pagina generata automaticamente"
CATCHALL_MARKER = "Record non classificati"
RAW_REF_RE = re.compile(r"raw/([^\s)]+?)\.md")

# ---------- Istruzioni per l'LLM ----------

SYSTEM_PROMPT = r"""Sei un redattore esperto di analisi qualitativa per una wiki di ricerca educativa basata sul framework PRAXIS.

COMPITO: Ricevi una pagina wiki stub (con metadati e lista di source link) e il contenuto testuale dei file raw citati. Devi riscrivere la pagina in forma discorsiva, ricca, qualitativa.

REGOLE DI STILE (da instructions/language-and-style.md):
- Scrivi sempre in italiano.
- Unica eccezione: i termini inglesi del framework PRAXIS (Practice patterns, Readiness beliefs, Adequacy of support, eXpectations, Interpersonal & Institutional trust, Skepticisms).
- Linguaggio chiaro, piano, utile — evita gergo inutile.
- L'analisi deve essere esclusivamente qualitativa. NON usare tecniche quantitative, campionamenti, statistiche, misurazioni numeriche o test di ipotesi.

REGOLE DI CITAZIONE (da instructions/citation-rules.md):
- Ogni affermazione fattuale DEVE referenziare il file sorgente.
- Formato: (source: [codice](path/filename.md)) — ogni citazione DEVE essere un link markdown.
- Biunivocita': ogni tag (source: ...) contiene esattamente UN link. Mai raggruppare piu' fonti in un unico tag.
- No abbreviazioni: non usare cfr., e segg., ecc. Ogni fonte va citata esplicitamente.
- Se due fonti si contraddicono, annota la contraddizione esplicitamente.

FORMATO PAGINA (da instructions/page-format.md):
- Mantieni il titolo H1 e i metadati iniziali (Dimensione, Popolazione, Last updated) ESATTAMENTE come sono.
- Riscrivi il **Summary** in 2-3 frasi sostanziali che descrivono i temi emergenti.
- Dopo il separatore ---, scrivi il contenuto analitico.
- Organizza in sezioni H2 tematiche (NON una sezione per record, ma per TEMA emergente).
- Integra le citazioni nel corpo del testo in modo fluido (vedi esempio sotto).
- Termina con la sezione "## Pagine correlate" gia' presente.

STILE DI SCRITTURA — ESEMPIO:
Non scrivere liste o elenchi puntati. Scrivi prosa discorsiva dove le voci dei rispondenti sono intrecciate con l'analisi. Esempio:

"Il fenomeno piu' immediato e' la copia. Amor11 lo descrive con una formula secca: il contro dell'IA e' la «passivita' nello studio, gli studenti tendono a copiare senza capire» (source: [amor11](../../../raw/insegnanti_attuali_amor11.md)). Atti24, docente di lingua straniera, racconta un impatto diretto..."

REGOLE IMPORTANTI:
- Cita TUTTI i raw forniti almeno una volta nel testo.
- I path dei source link devono usare percorsi relativi corretti (../../../raw/... per pagine in sottocartelle a 3 livelli, ../../raw/... per 2 livelli).
- NON inventare citazioni o contenuti non presenti nei raw.
- NON aggiungere conclusioni prescrittive o raccomandazioni.
- Analizza i dati; non prescrivere soluzioni.
- Usa le virgolette caporali « » per le citazioni dirette italiane.
- Se un record ha risposte vuote o solo "-", menzionalo brevemente come non-rispondente e vai avanti.
- NON scrivere mai conteggi, percentuali, o "X su Y rispondenti".
- Produci SOLO il testo markdown della pagina, senza commenti o spiegazioni aggiuntive.
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wiki-dir", type=Path, default=WIKI_DIR)
    p.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    p.add_argument("--labels-dir", type=Path, default=LABELS_DIR)
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--dry-run", action="store_true", help="Solo elenca le stub, non genera.")
    p.add_argument("--limit", type=int, help="Limita il numero di stub da processare.")
    p.add_argument("--only", type=str, help="Processa solo questo file stub (percorso relativo a wiki/).")
    p.add_argument("--timeout", type=int, default=300, help="Timeout per chiamata LLM in secondi.")
    return p.parse_args()


def find_stubs(wiki_dir: Path) -> list[Path]:
    """Trova le pagine stub generate automaticamente."""
    stubs: list[Path] = []
    for p in sorted(wiki_dir.rglob("*.md")):
        if p.name.startswith("index") or p.name == "log.md":
            continue
        text = p.read_text(encoding="utf-8")
        if STUB_MARKER in text or CATCHALL_MARKER in text:
            stubs.append(p)
    return stubs


def extract_raw_stems(wiki_page: Path) -> list[str]:
    """Estrae gli stem dei raw citati in una pagina wiki."""
    text = wiki_page.read_text(encoding="utf-8")
    stems: list[str] = []
    for m in RAW_REF_RE.finditer(text):
        stems.append(m.group(1))
    return list(dict.fromkeys(stems))  # deduplica preservando ordine


def load_raw_content(raw_dir: Path, stem: str) -> str | None:
    """Carica il contenuto di un file raw."""
    path = raw_dir / f"{stem}.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_label(labels_dir: Path, stem: str) -> dict[str, Any] | None:
    """Carica il label JSON di un record."""
    path = labels_dir / f"{stem}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def compute_source_path_prefix(wiki_page: Path, wiki_dir: Path) -> str:
    """Calcola il prefisso di path relativo per i link (source: ...)."""
    rel = wiki_page.relative_to(wiki_dir)
    depth = len(rel.parts) - 1
    up = "/".join([".."] * (depth + 1))
    return f"{up}/raw"


def call_ollama(
    host: str,
    model: str,
    system: str,
    user_prompt: str,
    timeout: int = 300,
) -> str:
    """Chiama l'API Ollama e restituisce la risposta."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 8192,
        },
    }).encode("utf-8")

    req = request.Request(
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")
    except error.URLError as e:
        LOGGER.error("Errore connessione Ollama: %s", e)
        raise
    except Exception as e:
        LOGGER.error("Errore chiamata Ollama: %s", e)
        raise


def build_user_prompt(
    wiki_page: Path,
    wiki_dir: Path,
    raw_dir: Path,
    labels_dir: Path,
) -> str:
    """Costruisce il prompt utente con la stub e tutti i raw citati."""
    stub_text = wiki_page.read_text(encoding="utf-8")
    raw_stems = extract_raw_stems(wiki_page)
    source_prefix = compute_source_path_prefix(wiki_page, wiki_dir)

    parts: list[str] = []
    parts.append("=== PAGINA WIKI STUB ===")
    parts.append(stub_text)
    parts.append("")
    parts.append(f"Percorso pagina: {wiki_page.relative_to(wiki_dir)}")
    parts.append(f"Prefisso per i source link: {source_prefix}/")
    parts.append("")

    parts.append(f"=== FILE RAW CITATI ({len(raw_stems)}) ===")
    for i, stem in enumerate(raw_stems, 1):
        content = load_raw_content(raw_dir, stem)
        label = load_label(labels_dir, stem)

        parts.append(f"\n--- RAW {i}/{len(raw_stems)}: {stem}.md ---")
        if content:
            parts.append(content)
        else:
            parts.append(f"[File non trovato: {stem}.md]")

        if label:
            subcodes = label.get("record_subcodes", [])
            dims = label.get("record_dimensions", [])
            if subcodes or dims:
                parts.append(f"\nLabel: dimensioni={dims}, subcodes={subcodes}")
        parts.append("")

    parts.append("=== ISTRUZIONI FINALI ===")
    parts.append(
        "Riscrivi la pagina wiki con testo discorsivo e analitico. "
        "Mantieni i metadati iniziali (titolo, dimensione, popolazione, last updated). "
        "Riscrivi il Summary. Crea sezioni H2 tematiche. "
        "Integra le citazioni in modo fluido. Cita tutti i raw almeno una volta. "
        f"Usa i percorsi relativi corretti: (source: [codice]({source_prefix}/nomefile.md)). "
        "Produci SOLO il markdown della pagina."
    )

    return "\n".join(parts)


def process_stub(
    wiki_page: Path,
    wiki_dir: Path,
    raw_dir: Path,
    labels_dir: Path,
    host: str,
    model: str,
    timeout: int,
    dry_run: bool = False,
) -> bool:
    """Processa una singola pagina stub. Ritorna True se modificata."""
    rel_path = wiki_page.relative_to(wiki_dir)
    raw_stems = extract_raw_stems(wiki_page)

    if not raw_stems:
        LOGGER.warning("Nessun raw citato in %s — skip", rel_path)
        return False

    if dry_run:
        print(f"  [STUB] {rel_path} — {len(raw_stems)} raw")
        return False

    LOGGER.info("Arricchimento: %s (%d raw)", rel_path, len(raw_stems))

    user_prompt = build_user_prompt(wiki_page, wiki_dir, raw_dir, labels_dir)

    try:
        result = call_ollama(host, model, SYSTEM_PROMPT, user_prompt, timeout=timeout)
    except Exception as e:
        LOGGER.error("Fallito %s: %s", rel_path, e)
        return False

    if not result or len(result.strip()) < 100:
        LOGGER.warning("Risposta troppo corta per %s — skip", rel_path)
        return False

    # Scrivi il risultato
    # Rimuovi eventuali fenced code block wrapper
    cleaned = result.strip()
    if cleaned.startswith("```markdown"):
        cleaned = cleaned[len("```markdown"):].strip()
    if cleaned.startswith("```md"):
        cleaned = cleaned[len("```md"):].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    # Backup
    backup_dir = wiki_dir.parent / "wiki-stubs-backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / rel_path.as_posix().replace("/", "__")
    backup_path.write_text(wiki_page.read_text(encoding="utf-8"), encoding="utf-8")

    wiki_page.write_text(cleaned + "\n", encoding="utf-8")
    LOGGER.info("Scritto: %s (%d chars)", rel_path, len(cleaned))
    return True


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()
    wiki_dir = args.wiki_dir.resolve()
    raw_dir = args.raw_dir
    labels_dir = args.labels_dir

    if args.only:
        target = wiki_dir / args.only
        if not target.exists():
            print(f"File non trovato: {target}", file=sys.stderr)
            return 1
        stubs = [target]
    else:
        stubs = find_stubs(wiki_dir)

    if args.limit:
        stubs = stubs[: args.limit]

    print(f"Pagine stub trovate: {len(stubs)}")

    if args.dry_run:
        for s in stubs:
            raw_stems = extract_raw_stems(s)
            print(f"  {s.relative_to(wiki_dir)} — {len(raw_stems)} raw")
        return 0

    stats = Counter[str]()
    for i, stub in enumerate(stubs, 1):
        rel = stub.relative_to(wiki_dir)
        print(f"\n[{i}/{len(stubs)}] {rel}")
        t0 = time.time()

        ok = process_stub(
            stub, wiki_dir, raw_dir, labels_dir,
            args.host, args.model, args.timeout,
        )

        elapsed = time.time() - t0
        if ok:
            stats["enriched"] += 1
            print(f"  OK ({elapsed:.1f}s)")
        else:
            stats["failed"] += 1
            print(f"  FAIL ({elapsed:.1f}s)")

    print(f"\n--- Risultati ---")
    print(f"  Arricchite: {stats['enriched']}")
    print(f"  Fallite:    {stats['failed']}")
    print(f"  Backup in:  wiki-stubs-backup/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
