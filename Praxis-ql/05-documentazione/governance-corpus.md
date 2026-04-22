# Governance Corpus PRAXIS

**Versione**: 1.0  
**Data**: 2026-04-21  
**Stato**: approvato (baseline operativa)

## 1. Scopo

Questo documento congela le regole ufficiali del progetto PRAXIS per:

- allineare dati, corpus, etichettatura, wiki e articolo;
- separare in modo netto fonti empiriche e riferimenti bibliografici;
- garantire tracciabilita' completa fino al testo finale dell'articolo.

## 2. Principi non negoziabili

1. L'articolo finale e' qualitativo.
2. Il materiale quantitativo e' usato solo come supporto di letteratura e inquadramento dei soggetti.
3. La fonte di verita' empirica e' `dati/` (immutabile).
4. Il corpus operativo e' derivato da `dati/`, arricchito e versionato separatamente.
5. Le decisioni su conflitti 01-wiki/label sono caso per caso e devono essere registrate.
6. La tracciabilita' end-to-end e' obbligatoria.

## 3. Ruoli degli artefatti

- `dati/`: sorgente primaria immutabile (truth source).
- `Praxis-ql/02-corpus/` (target): record operativi arricchiti e citabili.
- `archive/raw-legacy/` (target): archivio storico del precedente `raw/`.
- `Praxis-ql/04-label/labels/`: output di etichettatura automatica, double coding e consolidamento.
- `Praxis-ql/04-label/labelstudio/`: ambiente e bundle per revisione umana totale.
- `Praxis-ql/01-wiki/`: base analitica diretta per l'articolo, con citazioni al corpus.
- `archive/labeling-legacy/analisi_mu.db`: prima labelizzazione storica usata come supporto nella costruzione del codebook; non e' fonte di verita' corrente.

## 4. Stato della fase Opus

La fase Opus 4.6 e' riconosciuta come fase storica iniziale che ha contribuito alla prima costruzione di record arricchiti e wiki.  
Questa fase va descritta come **storica non pienamente riproducibile** nella metodologia.
Riferimento operativo: `fase-opus-storica.md`.

## 5. Politica citazioni

1. Citazioni empiriche: solo da dati/corpus.
2. Citazioni bibliografiche: standard QTimes, separate dalle citazioni empiriche.
3. Non mescolare mai riferimento bibliografico e riferimento empirico nello stesso meccanismo citazionale.

## 6. Revisione umana

Le correzioni umane in Label Studio devono coprire tutto il corpus (non solo campioni).  
La versione finale etichettata deve essere consolidata in un artefatto unico e dichiarato.

## 7. Conflitti wiki vs label

In caso di conflitto tra evidenza narrativa wiki ed etichetta strutturata:

1. valutazione caso per caso;
2. registrazione obbligatoria nel registro decisionale;
3. applicazione coerente della decisione agli artefatti coinvolti.

Registro ufficiale: `01-wiki/40-governance/decision-log-wiki-vs-label.md`.

## 8. Tracciabilita' obbligatoria

Ogni evidenza usata nell'articolo deve poter essere tracciata lungo la catena:

`dato -> record/item corpus -> codice finale -> pagina wiki -> sezione articolo -> decisione`

Formato ufficiale richiesto: tabella markdown.

## 9. Priorita' operativa corrente

La priorita' immediata e' la ripulitura strutturale del repository, seguita da:

1. formalizzazione pipeline `dati -> corpus`;
2. revisione umana totale;
3. chiusura tracciabilita' e registro decisionale;
4. rifinitura metodologica dell'articolo.

## 10. Riferimento pipeline canonica

La pipeline operativa ufficiale e' documentata in `pipeline-dati-corpus.md`, con:

- script canonico `../scripts/build_corpus_from_dati.py` (esecuzione da `Praxis-ql/`);
- manifest di build per tracciabilita' (`04-label/labels/corpus-build-manifest.json`);
- passaggi successivi verso labeling e ristrutturazione item-based.

## 11. Istruzione primaria per Opus

La prima istruzione da fornire a Opus e' il file root `AGENTS.md`, seguito da questo documento e dal piano operativo `progetto-allineamento.md`.
