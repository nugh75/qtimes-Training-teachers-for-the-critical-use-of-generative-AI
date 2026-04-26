---
name: praxis-article-style
description: Use this skill when writing, editing, or reviewing prose in PRAXIS scientific articles targeted at QTimes – Journal of Education, Technology and Social Studies (files in `Praxis-ql/05-documentazione/articolo-*.md`). Enforces QTimes editorial norms (norme-redazionali_qtimes_6), language register (Italian, first-person plural "noi"), terminology consistency for the PRAXIS framework, structural conventions (numbered paragraphs, mandatory Conclusioni section, bilingual abstract EN+IT), citation/quotation formatting, acronym handling, and anti-patterns. Out of scope: bibliography management (use praxis-bibliography-citations), wiki content (has its own page-format rules), corpus citations.
---

# PRAXIS Article Style

## Authority

Target journal: **QTimes – Journal of Education, Technology and Social Studies** (Anicia, ISSN 2038-3282).

Editorial rules in priority order:

1. `docs/norme-redazionali/norme-redazionali_qtimes_6.md` — journal norms (binding for submission)
2. `docs/instructions/language-and-style.md` — repository-level language conventions
3. This skill — operational application

When journal norms and user preferences conflict, **journal norms win** for any text destined for submission. Surface the conflict explicitly.

## Mandatory orientation

Before writing or editing prose in `Praxis-ql/05-documentazione/articolo-*.md`:

- Read `docs/norme-redazionali/norme-redazionali_qtimes_6.md` in full.
- Read `docs/instructions/language-and-style.md`.
- Skim the article frontmatter and existing structure to match tone and tense.

## Core rules

### Language

- **Italian**, formal academic register. Plain, clear prose. No jargon, no archaisms, no idioms.
- **First-person plural "noi"** for the authors' voice ("proponiamo", "abbiamo osservato", "i nostri dati").
- **Active over passive** when natural in Italian; never use "si è fatto" if "abbiamo fatto" reads well.
- **Smooth flow (binding).** Prose must read smoothly: each sentence connects to the next, each paragraph builds on the previous one. Apply concretely:
  - Use connectives that mark the logical move (*infatti*, *tuttavia*, *di conseguenza*, *al contrario*, *in questa prospettiva*, *da qui*) instead of dropping disconnected statements.
  - Open paragraphs with a hook to what came before ("A questa novità si sommano...", "Per rispondere serve..."), avoid starting cold with a new subject.
  - Vary sentence length: alternate short declarative sentences with longer articulated ones. Avoid runs of identical-length sentences.
  - Affirmative phrasing over negation chains. Replace "non è X ma Y" with "è Y" or "anziché X, Y" when the contrast is preserved.
  - End paragraphs with a sentence that prepares the next move, not with a recap.
  - Read the passage aloud (mentally) before committing: if it stutters, rewrite.

### Italics (the only emphasis allowed)

QTimes forbids **bold** and underline in body text. Italics replace them. Use italics for:

- foreign words, especially **English** (e.g. *prompting*, *ghostwriting*, *artificial intelligence* when the term is introduced in English before its Italian equivalent);
- technical terms on first use or when emphasized (e.g. *coorte*, *sotto-tema*);
- titles of works inside prose (e.g. *Apocalittici e integrati*);
- the six PRAXIS framework labels in English (Practice patterns, Readiness beliefs, Adequacy of support, eXpectations, Interpersonal & Institutional trust, Skepticisms).

### Acronyms

- First occurrence: full form followed by acronym in parentheses. Example: "intelligenza artificiale (IA)", "Technology Acceptance Model (TAM)".
- Subsequent occurrences: acronym only.
- Every acronym used in the article must appear in a final **Glossario** section.

### Structure (binding)

| Section | Rule |
|---|---|
| Title | Two titles, English + Italian, max 2 lines each. |
| Authors | Name + affiliation + active e-mail. For double-blind submission, replace with "XXX". |
| Abstract EN | Max 10 lines. No bold. First. |
| Keywords (EN) | 3–5, comma-separated, English. |
| Abstract IT | Max 10 lines. Translation of EN. No bold. |
| Parole chiave | 3–5, comma-separated, **English** (per QTimes norms, even in IT block). |
| Numbered paragraphs | Every section numbered: `1 – Introduzione`, `2 – ...`. Includes Introduzione and Conclusioni. Sub-sections also numbered (1.1, 1.2). |
| **Conclusioni** | Mandatory final paragraph before bibliography. |
| Riferimenti bibliografici | After Conclusioni. Pandoc-rendered from `reference.bib` via the `praxis-bibliography-citations` skill. |
| Glossario | After bibliography. Acronyms + key technical terms in alphabetical order. |

### Length

- **40.000 characters total** (spaces, header, bibliography included). Hard cap. Track length while editing.

### Citations and quotations

- **Indirect citation**: `(Cognome, anno)` after the claim. Pandoc form: `[@Key]` → renders to `(Davis, 1989)`.
- **Author named in prose**: only year in parens. Pandoc: `[-@Key]` → "Davis (1989) sostiene che...".
- **Direct quotation, short** (≤3 lines): inline with **double English quotes** `"..."` per QTimes norms. Add page: `[@Key, p. 13]`.
- **Direct quotation, long** (>3 lines): block quote, indented, no surrounding quotes. Pandoc: `> ...`.
- **Omissions** within a quotation: `[...]` (square brackets, three dots, no spaces).
- **Note**: user preference was "caporali" (« »); QTimes norms explicitly mandate `"..."`. Norms win for submission. If a separate stylesheet is used for non-submission drafts, document the deviation in frontmatter.

### Footnotes

- Use sparingly. Max 2–3 lines each.
- Number progressively.
- Footnote marker comes **before** punctuation, not after.

### Figures

- All visuals (images, graphs, diagrams, tables) labelled "Figura N".
- Numbered in order of appearance.
- Every figure referenced in text: "(Figura 1)" or "Nella Figura 2 sono illustrati...".
- Caption ≤2 lines. If from external source, prefix "Da" or "Adattato da" + bibliographic ref.

### Anti-patterns (do not write)

- "In conclusione," / "In sintesi," / "Per concludere," → use the numbered Conclusioni paragraph instead.
- "Tale studio" / "il presente lavoro" → "il nostro studio".
- First-person singular ("io ritengo", "ho osservato") → "noi" plural.
- Hedging chains ("forse potrebbe in qualche modo essere considerato") → assert with evidence or remove.
- "Negli ultimi anni" / "Oggigiorno" / "Nell'era digitale" → date the claim or remove.
- Unsupported quantitative claims in a qualitative paper → remove or reframe.
- **Bold** or underlined emphasis → italics only.
- Italian curly/typographic quotes "" '' for English-source punctuation → straight `"..."` per norms.
- Long paragraphs (>200 words) → split.
- Sentences >40 words → split.
- Anglicisms when an Italian word fits ("performance" → "prestazione"; "trend" → "tendenza"). Keep the English in italics only when the Italian loses precision.
- Choppy paragraphs made of disconnected one-sentence units → merge or add connectives.
- Negation chains ("non X, non Y, non Z") → reframe affirmatively.
- Cold openings on a new subject after a paragraph break → add a transition that picks up the prior thread.

### PRAXIS terminology (canonical)

| Italian | English (italicized when used) | Notes |
|---|---|---|
| coorte | cohort | three: studenti, insegnanti-attuali, insegnanti-futuri |
| dimensione | dimension | one of P/R/A/X/I/S |
| sotto-tema | sub-theme | thematic subdivision within a dimension |
| corpus | *corpus* | the empirical dataset in `Praxis-ql/02-corpus/` |
| etichetta | label | model-generated routing tag |
| categoria emergente | emerging category | qualitative coding category |

The six dimension labels in English are not translated:

- Practice patterns
- Readiness beliefs
- Adequacy of support
- eXpectations
- Interpersonal & Institutional trust
- Skepticisms

### Anonymization for double-blind submission

- Replace author names with "XXX" in body, footnotes, and bibliography of the anonymous version.
- Strip identifying institutional references (universities, projects, courses): replace with "XXX".
- Remove file metadata (Word: File → Properties).

## Workflow

### 1. Pre-edit check

1. Confirm target file matches the article path (`Praxis-ql/05-documentazione/articolo-*.md`).
2. Read journal norms and `language-and-style.md`.
3. Read the article frontmatter and current structure.
4. Run the bibliography sync gate (`praxis-bibliography-citations` skill, step 0).

### 2. Edit pass

1. Apply the rules above for any prose change.
2. Insert citations only via `praxis-bibliography-citations`. Never invent a key.
3. New acronyms: define on first use + add to Glossario.
4. New English term: italicize on first use, give the Italian equivalent in parentheses if one exists.
5. Track character count; warn the user when approaching 40.000.

### 3. Post-edit checks

Manual review checklist:

- [ ] All paragraphs numbered? Conclusioni present?
- [ ] Both abstracts within 10 lines, EN first?
- [ ] Keywords/Parole chiave in English, 3–5, comma-separated?
- [ ] No bold or underline in body? Emphasis is italics?
- [ ] Direct quotes use `"..."`, omissions `[...]`?
- [ ] Long quotes (>3 lines) as block quotes without surrounding marks?
- [ ] Footnote markers before punctuation?
- [ ] Acronyms defined on first use and listed in Glossario?
- [ ] First person consistent ("noi"), no slips into "io" or "il presente lavoro"?
- [ ] Anti-patterns absent?
- [ ] Character count under 40.000?
- [ ] Bibliography sync clean (`sync_zotero_group.py --strict`)?

## Response shape

When editing, return a brief summary covering:

- which rules applied;
- which paragraphs were rewritten and why;
- conflicts between user preference and journal norms (with the chosen resolution);
- anti-patterns removed;
- remaining risks (length budget, missing acronym definitions, untranslated English without italics).

When asked for free prose without an existing draft, produce text that already obeys these rules; do not output a "draft to be cleaned later".
