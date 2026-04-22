# Fase Opus Storica (Non Pienamente Riproducibile)

**Versione**: 1.0  
**Data**: 2026-04-21  
**Stato**: riferimento metodologico storico

## 1. Scopo del documento

Questo documento formalizza la posizione ufficiale del progetto sulla fase iniziale svolta con Opus 4.6:

- e' riconosciuta come fase storica di bootstrap;
- non e' trattata come pipeline riproducibile end-to-end;
- i suoi output sono accettati solo se tracciabili ai dati di origine.

## 2. Perimetro della fase Opus

La fase Opus ha contribuito alla prima costruzione di:

- record arricchiti (oggi confluiti nel corpus operativo);
- pagine wiki analitiche iniziali;
- prime decisioni di classificazione poi riesaminate da pipeline successive.

## 3. Perche' non e' pienamente riproducibile

Al momento non risultano documentati in modo completo e verificabile:

1. prompt esatti usati in ogni passaggio;
2. configurazioni runtime complete (parametri, versioni, seed, policy);
3. ordine rigoroso dei passaggi e dipendenze tra output intermedi;
4. ambiente di esecuzione congelato e rieseguibile.

Di conseguenza, la fase non soddisfa i requisiti di riproducibilita' metodologica richiesti per una pipeline canonica.

## 4. Decisione metodologica operativa

1. La fase Opus resta nel progetto solo come **contesto storico**.
2. La pipeline ufficiale riproducibile parte da `dati/` e segue `pipeline-dati-corpus.md`.
3. Nessuna inferenza dell'articolo finale puo' dipendere solo dalla fase Opus.
4. Ogni evidenza citata deve essere verificabile nella catena:

`dati -> corpus -> 04-label/labels/wiki -> articolo`

## 5. Impatto sugli artefatti

- `02-corpus/` resta utilizzabile, ma come corpus operativo corrente da verificare e rifinire.
- `01-wiki/` resta base di lavoro, ma richiede conferma tramite tracciabilita' e revisione umana.
- output generati in fase Opus non documentata non costituiscono, da soli, fonte di verita'.
- `archive/labeling-legacy/analisi_mu.db` e' mantenuto come traccia storica della prima labelizzazione (supporto al codebook), non come pipeline canonica.

## 6. Collegamento con i passi di allineamento

Questo documento chiude il passo 4 del progetto di allineamento e si collega a:

- `governance-corpus.md`
- `pipeline-dati-corpus.md`
- `progetto-allineamento.md`
