---
name: praxis-bibliography-citations
description: Use this skill when working in the PRAXIS repository to write, edit, audit, or add bibliographic citations in scientific articles and article drafts. Use for requests about Pandoc/CSL citation keys, QTimes bibliography consistency, checking whether a cited work exists in `/home/nugh75/-qtimes/docs/bibliografia/reference.bib`, validating BibTeX metadata against OpenAlex, searching the user's Zotero library, importing or comparing Zotero references, finding the right citation key before writing, or preventing wrong/missing bibliographic references. This skill is for bibliographic/article references, not empirical corpus citations.
---

# PRAXIS Bibliography Citations

## Overview

Support PRAXIS article writing by selecting and checking bibliographic citations. The canonical BibTeX file `/home/nugh75/-qtimes/docs/bibliografia/reference.bib` and the dedicated Zotero group `praxis-article-2026` (`ZOTERO_GROUP_ID=6526889`) form a **paired source of truth**. They must remain in lock-step: the skill always verifies sync at the start of any bibliographic task and re-verifies sync after every edit. OpenAlex is used to validate metadata. Empirical corpus citations are out of scope and stay separate from article references.

## Mandatory sync policy

- **Before any edit or citation insertion**: run the sync check.
- **After any edit** (adding entry, fixing metadata, importing from Zotero): run sync with `--sync` to push and pull, then verify drift = 0.
- **Never let drift sit**: if sync reports `only_local` or `only_remote`, resolve it before continuing.
- Citation keys are stored in Zotero's native `citationKey` field (set automatically when `extra: "Citation Key: <key>"` is provided on import). Do not rely on Better BibTeX server-side; the skill uses the Web API only.
- Both directions are valid:
  - `bib → Zotero`: when a new entry is added manually to `reference.bib`, push it to the group.
  - `Zotero → bib`: when items are added through the Zotero web/desktop client, pull and append them to `reference.bib`.

```bash
set -a; source .env; set +a
.venv/bin/python scripts/sync_zotero_group.py             # report drift
.venv/bin/python scripts/sync_zotero_group.py --sync      # push + pull, then re-verify
.venv/bin/python scripts/sync_zotero_group.py --strict    # exit 1 on drift (use in CI / pre-commit)
```

This skill does not manage empirical evidence citations. Keep bibliography references separate from corpus/wiki citations such as `(source: [STEM](../../02-corpus/STEM.md#item-N))`.

## Mandatory Orientation

Before substantive work in the PRAXIS repository, read:

- `AGENTS.md`
- `Praxis-ql/05-documentazione/governance-corpus.md`
- `Praxis-ql/05-documentazione/progetto-allineamento.md`
- `docs/instructions/citation-rules.md` when the task touches citation policy
- `docs/norme-redazionali/norme-redazionali_qtimes_6.md` when formatting the final references section

Do not modify `dati/`. Do not invent a citation key, author, year, DOI, page, journal, publisher, or claim about a source.

## Canonical Files

- Bibliography: `/home/nugh75/-qtimes/docs/bibliografia/reference.bib`
- Project venv: `/home/nugh75/-qtimes/.venv` (lives at project root, shared across skills)
- Article drafts usually use Pandoc citations such as `[@Davis1989PerceivedU]`, `[-@Moretti2000Conjectures]`, or `[@Floridi2025DistantWriting, p. 13]`.
- If an article frontmatter points elsewhere, flag the mismatch and prefer the canonical bibliography above unless the user explicitly requests a migration plan.

## Workflow

### 0. Sync gate (mandatory)

Always run before doing anything else:

```bash
set -a; source .env; set +a
.venv/bin/python scripts/sync_zotero_group.py
```

If `in_sync < local_count` or `in_sync < remote_count`, run `--sync` to reconcile, then continue. Never start a citation task with drift.

### 1. Find the local citation

1. Read or query `docs/bibliografia/reference.bib`.
2. Confirm the exact BibTeX key exists and is unique.
3. Check the entry fields needed for the sentence being written: `author`, `year`, `title`, `journal`/`booktitle`/`publisher`, `doi`, `url`, and pages when relevant.
4. If the key is missing or duplicated, stop and report the problem before writing the article text.

### 2. Verify through OpenAlex

Use `scripts/check_bibliography_openalex.py` whenever possible:

```bash
.venv/bin/python .agents/skills/praxis-bibliography-citations/scripts/check_bibliography_openalex.py --key Davis1989PerceivedU
.venv/bin/python .agents/skills/praxis-bibliography-citations/scripts/check_bibliography_openalex.py --doc Praxis-ql/05-documentazione/articolo-scientifico-praxis-v2-2026-04-20.md
.venv/bin/python .agents/skills/praxis-bibliography-citations/scripts/check_bibliography_openalex.py --query "technology acceptance model teachers adoption"
```

The script reads the canonical BibTeX by default, checks duplicate/missing keys, and queries OpenAlex by DOI when available or by title otherwise.

Interpretation:

- `verified`: OpenAlex agrees by DOI, or title/year metadata is close enough for normal use.
- `review`: metadata is plausible but not strong enough; inspect manually before citing.
- `not_found`: OpenAlex did not identify the work. Do not infer that the source is invalid; some books, reports, web pages, standards, and laws may be missing from OpenAlex. State the limitation and verify through the official URL/publisher if needed.
- `missing-key` or duplicate-key warnings: do not cite until fixed.

Set `OPENALEX_MAILTO` in the environment when available so OpenAlex can route requests through its polite pool.

### 3. Search Zotero when the local BibTeX is missing or uncertain

Use `scripts/zotero_lookup.py` to search the user's Zotero library before adding or repairing a BibTeX entry.

Web API mode requires:

- `ZOTERO_USER_ID` for a personal library, or `ZOTERO_LIBRARY_TYPE=group` plus `ZOTERO_GROUP_ID` for a group library.
- `ZOTERO_API_KEY` for private libraries. Do not print or commit the key.

Credentials live in `/home/nugh75/-qtimes/.env` (gitignored). Load before invoking the script:

```bash
set -a; source .env; set +a
.venv/bin/python .agents/skills/praxis-bibliography-citations/scripts/zotero_lookup.py --query "Davis perceived usefulness" --api
.venv/bin/python .agents/skills/praxis-bibliography-citations/scripts/zotero_lookup.py --query "10.2307/249008" --db /path/to/zotero.sqlite
```

If Zotero returns a candidate:

1. Compare the Zotero metadata with `reference.bib`.
2. Verify the same work through OpenAlex or official publisher metadata.
3. Use Better BibTeX export or Zotero BibTeX output only as input to a deliberate `reference.bib` edit.
4. Preserve stable citation keys already used in PRAXIS articles unless the user approves a key migration.

### 4. Write the citation safely

Use the exact key from the BibTeX file.

- Parenthetical citation: `[@Key]`
- Multiple works: `[@KeyA; @KeyB]`
- Narrative/suppress-author form when the author is named in prose: `[-@Key]`
- Direct quotation or specific claim with page: `[@Key, p. 13]` or `[@Key, pp. 13-14]`

Avoid naked author-year text when the article is still in Markdown/Pandoc form. Let CSL render the final QTimes style.

### 5. Add or repair a BibTeX entry

Only add or change `reference.bib` when the user explicitly asks, or when the citation cannot be completed otherwise.

Before editing:

1. Verify the source with OpenAlex, DOI, publisher page, journal page, or official institutional page.
2. Search Zotero for the item and prefer its curated metadata when it agrees with OpenAlex/publisher data.
3. Preserve the project's existing key style: `SurnameYearShortTitle`, e.g. `Davis1989PerceivedU`.
4. Include DOI when available; include URL for reports, web pages, legislation, software, or works without DOI.
5. Avoid placeholder authors such as `Unknown` or `Multiple Authors` unless the source itself genuinely lacks named authors and the reason is stated.
6. Re-run the script for the changed key and scan the target article.

### 6. Reconcile after any change (mandatory)

Every workflow ends with reconciliation:

```bash
set -a; source .env; set +a
.venv/bin/python scripts/sync_zotero_group.py --sync
```

Modes:

- `--push`: only_local entries (in `reference.bib`, not in Zotero) → POSTed to the group with `extra: "Citation Key: <key>"`. Zotero promotes that line to the native `citationKey` field automatically.
- `--pull`: only_remote entries (in Zotero, not in `reference.bib`) → appended to `reference.bib` as fresh BibTeX blocks. The native `citationKey` from Zotero becomes the BibTeX key.
- `--sync`: both, in sequence.
- `--strict`: exit 1 if drift remains. Use in `pre-commit` or CI.

After `--sync`, re-run the report and confirm `in_sync == local_count == remote_count` and both `only_local` / `only_remote` are empty. If a push fails for an entry, fix the BibTeX metadata (likely missing required field for the Zotero itemType) and re-run.

The single helper `scripts/import_bib_to_zotero.py` exists for the initial bulk import; for ongoing work use only `sync_zotero_group.py`.

## Response Shape

When helping during article writing, return:

- the recommended citation key and Pandoc snippet;
- the BibTeX metadata used locally;
- the OpenAlex verification status and any mismatch;
- a concise wording suggestion only if the bibliographic source supports it;
- any unresolved risk, such as missing DOI, duplicate key, absent OpenAlex match, or frontmatter using the wrong bibliography path.

Never present an unverified bibliographic fact as certain. If verification is incomplete, say exactly what is missing.
