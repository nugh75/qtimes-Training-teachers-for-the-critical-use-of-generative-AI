# Registro Decisionale Wiki vs Label

**Versione**: 1.0  
**Data avvio**: 2026-04-21  
**Scopo**: tracciare decisioni caso-per-caso quando wiki narrativa e labeling strutturato non coincidono.

## Regole minime

1. Ogni conflitto apre una riga nuova.
2. Nessuna decisione senza motivazione esplicita.
3. Ogni decisione deve indicare i file aggiornati.
4. Stato decisione: `open`, `decided`, `applied`, `verified`.

## Tabella decisioni

| ID | Data | Ambito | Evidenza wiki | Evidenza label | Decisione | Motivazione | File impattati | Decision by | Stato |
|---|---|---|---|---|---|---|---|---|---|
| D-001 | 2026-04-21 | bootstrap registro | registry assente | policy governance richiede tracciamento conflitti | istituito registro markdown ufficiale | requisito metodologico step 6 progetto allineamento | `01-wiki/40-governance/decision-log-wiki-vs-label.md`, `governance-corpus.md`, `progetto-allineamento.md` | team PRAXIS | applied |
| D-002 | 2026-04-21 | revisione umana | completamento dichiarato fuori repo | assenza export annotazioni umane versionate localmente | in attesa import/export finale da Label Studio | serve evidenza locale per audit end-to-end | `04-label/labelstudio/*` (export da aggiungere), `04-label/labels/*` (consolidato finale) | team PRAXIS | open |

## Uso operativo

- Quando emerge un conflitto su uno specifico item, compilare `Ambito` con `raw_stem#item-N`.
- Dopo applicazione delle modifiche ai file, aggiornare `Stato` da `decided` a `applied`.
- L'audit finale puo' segnare `verified` solo se la modifica e' tracciabile in diff e coerente con 02-corpus/01-wiki/articolo.
