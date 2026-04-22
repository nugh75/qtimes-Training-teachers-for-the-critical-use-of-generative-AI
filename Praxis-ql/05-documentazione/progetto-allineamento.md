# Progetto Allineamento PRAXIS

**Versione**: 1.0  
**Data avvio**: 2026-04-21

## Obiettivo

Allineare repository, metodologia e pipeline verso un articolo finale qualitativo, con:

- separazione chiara tra dati immutabili e corpus operativo;
- revisione umana completa;
- tracciabilita' totale dalle fonti al testo finale.

## Stato passi

1. `[DONE]` Congelare regole e fonti ufficiali.
2. `[DONE]` Ripulire naming e struttura: `02-corpus/` operativo in `Praxis-ql`, archivio storico in `archive/raw-legacy/`.
3. `[DONE]` Formalizzare pipeline canonica `dati -> corpus`.
4. `[DONE]` Documentare fase Opus come storica non riproducibile.
5. `[PENDING]` Completare revisione umana Label Studio su tutto il corpus (progetto pronto, in attesa esecuzione colleghi + export finale).
6. `[DONE]` Istituire registro decisionale wiki-vs-label.
7. `[DONE]` Costruire tabella markdown di tracciabilita' end-to-end.
8. `[PENDING]` Ripulire output intermedi e duplicati (parziale: `altro/` pulita, `analisi_mu.db` archiviato in `archive/labeling-legacy/`).
9. `[PENDING]` Allineare articolo/metodologia alle regole finali.
10. `[PENDING]` Audit finale di coerenza.

## Criteri di completamento sintetici

- Passo 2: `02-corpus/` operativo in `Praxis-ql` e `archive/raw-legacy/` come archivio storico.
- Passo 3: script canonico documentato e rieseguibile.
- Passo 5: copertura revisione umana 100% item del corpus.
- Passo 6: ogni conflitto con decisione motivata e datata.
- Passo 7: presenza della catena completa `dato -> articolo` per ogni evidenza citata.
- Passo 10: coerenza verificata tra corpus, labels, wiki, articolo.
