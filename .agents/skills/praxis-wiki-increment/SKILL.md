---
name: praxis-wiki-increment
description: Use this skill when working in the PRAXIS repository to analyze Praxis-ql/02-corpus qualitatively and propose evidence-backed increments to existing Praxis-ql/01-wiki thematic threads. Use for requests about enriching PRAXIS wiki pages, finding corpus evidence for a coorte/dimensione/sotto-tema, drafting wiki additions from corpus items, or auditing whether a theme should be extended. The skill treats corpus items as primary evidence, labels as auxiliary routing, and Qwen/Ollama as a controlled suggestion aid.
---

# PRAXIS Wiki Increment

## Purpose

Analyze `Praxis-ql/02-corpus/` and propose qualitative additions to existing PRAXIS wiki threads. The default output is a proposal in chat: target wiki pages, item-level evidence, suggested Italian prose, and conflict notes. Do not edit the wiki unless the user explicitly approves the proposed integration.

## Non-negotiable constraints

- Read these files before doing substantive work:
  - `AGENTS.md`
  - `Praxis-ql/05-documentazione/governance-corpus.md`
  - `Praxis-ql/05-documentazione/progetto-allineamento.md`
  - relevant files in `docs/instructions/`, especially `citation-rules.md`, `page-format.md`, `query.md`, and `language-and-style.md`.
- Never modify `dati/`.
- Use `Praxis-ql/02-corpus/` as the official empirical source. Do not use `raw/` as source of truth.
- Keep empirical corpus citations separate from bibliography/article references.
- Do not invent facts. If evidence is missing, say so.
- The analysis is qualitative. Do not add statistical inference, hypothesis tests, or unsupported quantitative claims.
- Prefer enriching existing wiki sub-themes. Propose a new thread only when no existing page can hold the evidence without distortion.

## Inputs to expect

Users will usually name one of:

- a coorte: `studenti`, `insegnanti-attuali`, `insegnanti-futuri`;
- a PRAXIS dimension: `Practice patterns`, `Readiness beliefs`, `Adequacy of support`, `eXpectations`, `Interpersonal trust`, `Skepticisms`, or `P/R/A/X/I/S`;
- a sotto-tema or wiki page, for example `ghostwriting-plagio` or `studenti/06-skepticisms/ghostwriting-plagio.md`.

If the request is broad, narrow the work to a manageable coorte/dimensione/sotto-tema and state that boundary.

## Workflow

### 1. Orientation

1. Identify the requested coorte, PRAXIS dimension, or target sotto-tema.
2. Read `Praxis-ql/01-wiki/00-indice/index-wiki.md`.
3. Read the target wiki page and nearby pages in the same coorte/dimension folder.
4. Inspect existing corpus citations in the target page and note whether they are item-anchored.
5. Select candidate corpus records using several signals:
   - existing wiki citations and `**Cited in:**` backlinks in corpus records;
   - label JSON in `Praxis-ql/04-label/labels/ollama-gemma4/` as routing only;
   - `rg` lexical searches over `Praxis-ql/02-corpus/`;
   - uncited or weakly integrated items surfaced by audit/mapping reports.

### 2. Qualitative analysis

1. Read candidate items directly in `Praxis-ql/02-corpus/*.md`.
2. Treat item answers as the authority. Labels, code counts, summaries, and model notes are hints, not evidence.
3. Extract only evidence that can support a concrete wiki claim.
4. Preserve contradictions and minority positions instead of smoothing them away.
5. If a claim conflicts with labels or an existing wiki interpretation, flag it for `Praxis-ql/01-wiki/40-governance/decision-log-wiki-vs-label.md`.

### 3. Optional Qwen support

Qwen is a controlled suggestion aid, not an empirical authority. Use it only when it helps surface patterns, tensions, or possible phrasing, and verify every suggestion against the corpus before using it.

Defaults:

- host: `http://192.168.129.14:11434`
- model: `qwen3.5:9b`

When using Qwen, keep prompts narrow and evidence-bound. Ask it to return candidate patterns with cited record/item identifiers, then verify those identifiers manually in `02-corpus/`.

Minimal prompt shape:

```text
Analizza solo gli item forniti dal corpus PRAXIS.
Obiettivo: proporre possibili incrementi qualitativi per la pagina wiki TARGET.
Vincoli: non inventare, non generalizzare oltre gli item, restituisci solo pattern con record/item e breve evidenza.
```

### 4. Proposal in chat

Before editing the wiki, return a concise proposal with:

- **Target pages**: existing wiki pages to increment.
- **Evidence**: item-level corpus evidence with markdown links to `Praxis-ql/02-corpus/STEM.md#item-N` when possible.
- **Suggested prose**: Italian narrative text ready to be inserted, with corpus source links in the project format.
- **Conflicts/notes**: label-vs-wiki conflicts, weak evidence, missing anchors, or cases needing human decision.
- **Post-approval actions**: index/log/mapping/backlink/traceability steps needed if the user approves.

Wiki citation format must remain:

```markdown
(source: [STEM](../../02-corpus/STEM.md#item-N))
```

Adjust the relative path from the target wiki page. Keep one source link per `(source: ...)` tag.

## Approved integration workflow

Only after explicit user approval:

1. Edit only the confirmed wiki pages.
2. Update page metadata: `Sources` and `Last updated`.
3. Add or update `[[wiki-links]]` and related pages only when genuinely useful.
4. Update `Praxis-ql/01-wiki/00-indice/index-wiki.md` if pages are created, renamed, or substantially reframed.
5. Append a dated entry to `Praxis-ql/01-wiki/40-governance/log.md`.
6. Register any wiki-vs-label decision in `Praxis-ql/01-wiki/40-governance/decision-log-wiki-vs-label.md`.
7. When empirical citations changed, run or recommend the deterministic checks below.

## Deterministic checks

Use existing scripts as checks and maintenance tools; do not let them replace qualitative reading.

- Coherence and citation audit:
  - `python scripts/audit_citation_mapping.py`
  - `python scripts/build_citation_mapping_final.py`
- Backlinks and traceability after approved citation changes:
  - `python scripts/add_item_backlinks.py --all --write`
  - `python scripts/build_traceability_table.py`
- Coverage diagnostic only:
  - `python scripts/ensure_wiki_coverage.py --dry-run`

Prefer dry runs when investigating. Do not run write-mode maintenance scripts unless the wiki integration has already been approved.

## Acceptance checks

Before finalizing an approved integration, verify:

- all wiki citations point to `Praxis-ql/02-corpus/`, not `dati/` or `raw/`;
- every factual claim has an empirical source or is marked as missing evidence;
- no `(source: ...)` tag contains multiple links;
- no unsupported statistical or quantitative inference was added;
- modified wiki pages still follow `docs/instructions/page-format.md`;
- relevant index/log/decision artifacts are updated when required.
