# CONTEXT — -qtimes

<!-- ai4educ:context-template v1.0 -->

## Quick Reference
- **Stack**: TODO
- **Entry point**: TODO
- **Test**: TODO

## Recovered from old AGENTS.md
# AGENTS.md - Istruzione Primaria per Opus (PRAXIS)

Questo file e' la prima istruzione da fornire a Opus.

## Sequenza di avvio obbligatoria

1. Leggere questo `AGENTS.md`.
2. Leggere `Praxis-ql/05-documentazione/governance-corpus.md`.
3. Leggere `Praxis-ql/05-documentazione/progetto-allineamento.md`.
4. Applicare il task richiesto senza violare i vincoli sotto.

## Architettura canonica del progetto

```
dati/                               -- fonte di verita' empirica (immutabile)
Praxis-ql/02-corpus/                   -- corpus operativo
archive/raw-legacy/                 -- archivio storico del vecchio raw
Praxis-ql/01-wiki/                     -- base analitica per articolo qualitativo
Praxis-ql/04-label/labels/                   -- output labeling e audit
Praxis-ql/04-label/labelstudio/              -- bundle e stato revisione umana
archive/labeling-legacy/            -- artefatti storici (es. prima labelizzazione)
scripts/                            -- script operativi (entrypoint in root)
docs/instructions/                  -- istruzioni operative trasversali
```

## Regole fondamentali

1. Non modificare mai `dati/`.
2. Trattare `Praxis-ql/02-corpus/` come base operativa; non usare `raw/` come sorgente ufficiale.
3. Mantenere separati riferimenti empirici (dati/corpus) e bibliografia articolo.
4. Non inventare fatti. Se manca evidenza, dichiararlo esplicitamente.
5. In caso di conflitto wiki vs label, registrare la decisione in `Praxis-ql/01-wiki/40-governance/decision-log-wiki-vs-label.md`.
6. Se si modifica la wiki, aggiornare gli indici/log pertinenti.
7. L'analisi e' qualitativa (niente inferenza statistica non richiesta).

## Framework PRAXIS

Riferimento: `Praxis-ql/01-wiki/10-framework/praxis-framework.md`.

- **P**ractice patterns
- **R**eadiness beliefs
- **A**dequacy of support
- **X**pectations
- **I**nterpersonal & Institutional trust
- **S**kepticisms

## Istruzioni operative (root)

| Task | File |
|---|---|
| Ingest fonti | `docs/instructions/ingest.md` |
| Query su wiki | `docs/instructions/query.md` |
| Regole citazione | `docs/instructions/citation-rules.md` |
| Formato pagine | `docs/instructions/page-format.md` |
| Audit/manutenzione | `docs/instructions/lint-and-maintenance.md` |
| Stile e lingua | `docs/instructions/language-and-style.md` |

## Common Tasks (da aggiungere)
TODO
