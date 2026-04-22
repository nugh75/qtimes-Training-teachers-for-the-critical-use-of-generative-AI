# Lingua e stile

- Scrivere sempre in italiano: titoli, nomi dei sotto-temi, descrizioni.
- Unica eccezione: i termini inglesi del framework PRAXIS (Practice patterns, Readiness beliefs, Adequacy of support, eXpectations, Interpersonal & Institutional trust, Skepticisms).
- Linguaggio chiaro, piano, utile — evitare gergo inutile.
- Nomi dei file: minuscolo con trattini (es. `impoverimento-cognitivo.md`).
- L'analisi deve essere esclusivamente qualitativa. Tralasciare tecniche quantitative, campionamenti, statistiche, misurazioni numeriche o test di ipotesi dalle fonti.

## Indicizzazione e logging

- [Praxis-ql/01-wiki/00-indice/index-wiki.md](../../Praxis-ql/01-wiki/00-indice/index-wiki.md): orientato ai contenuti, per categoria, con descrizione di una riga.
- [Praxis-ql/01-wiki/40-governance/log.md](../../Praxis-ql/01-wiki/40-governance/log.md): cronologico, append-only.

Formato log:

```markdown
## [AAAA-MM-GG] ingest | nome-fonte
## [AAAA-MM-GG] query | argomento
## [AAAA-MM-GG] lint | health-check
```
