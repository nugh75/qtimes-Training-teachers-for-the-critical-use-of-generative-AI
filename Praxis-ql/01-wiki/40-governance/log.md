# Wiki Maintenance Log

Append-only record of ingests, queries, and maintenance.
## [2026-04-19] ingest | metodologia.md (Creazione praxis-framework)
## [2026-04-19] ingest | insegnanti_attuali_vigo15.md - 0050.md (Creazione base insegnanti-attuali PRAXIS)
## [2026-04-19] ingest | insegnanti_attuali_ucci20.md - 0100.md (Integrazione PRAXIS Round 2)
## [2026-04-19] ingest | insegnanti_attuali_sano10.md - 0150.md (Integrazione PRAXIS Round 3)
## [2026-04-19] ingest | insegnanti_attuali_ini08.md - 0200.md (Integrazione PRAXIS Round 4)
## [2026-04-19] ingest | insegnanti_attuali_onti31.md - 0250.md (Integrazione PRAXIS Round 5)
## [2026-04-19] ingest | insegnanti_attuali_anta05.md - 0300.md (Integrazione PRAXIS Round 6)
## [2026-04-19] ingest | insegnanti_attuali_ista13.md - 0350.md (Integrazione PRAXIS Round 7)
## [2026-04-19] ingest | insegnanti_attuali_asio15.md - 0358.md (Finale Insegnanti Attuali)
## [2026-04-19] ingest | insegnanti_futuri_orgi03.md - 0050.md (Integrazione PRAXIS Futuri Batch F1)
## [2026-04-19] ingest | insegnanti_futuri_prella42.md - 0099.md (Finale Insegnanti Futuri)
## [2026-04-19] ingest | studenti_elli9.md - 0050.md (Integrazione PRAXIS Studenti Batch S1)
## [2026-04-19] ingest | studenti_vese2.md - 0100.md (Integrazione PRAXIS Studenti Batch S2)
## [2026-04-19] ingest | studenti_osta30.md - 0150.md (Integrazione PRAXIS Studenti Batch S3)
## [2026-04-19] ingest | studenti_ieri23.md - 0200.md (Integrazione PRAXIS Studenti Batch S4)
## [2026-04-19] ingest | studenti_0201.md - 0250.md (Integrazione PRAXIS Studenti Batch S5)
## [2026-04-19] ingest | studenti_0251.md - 0273.md (Integrazione PRAXIS Studenti Batch S6 — FINALE) ✅
## [2026-04-19] ingest | studenti_erto07.md - 0273.md (Finale Studenti Batch S6)
## [2026-04-19] maintenance | studenti — aggancio batch file orfani (206 file scansionati, 32 con contenuto)
Aggiornate 9 sotto-pagine: uso-strumentale-evasivo, interrogatore-e-autovalutazione, profili-di-non-uso-1-6, profili-di-non-uso-7-9, adequacy-of-support-studenti, supporto-vs-sostituzione, autonomia-cognitiva-a-rischio, sfiducia-tecnica-e-strutturale, evoluzione-del-tabu, zone-di-esclusione-s6. Nessuna nuova sotto-pagina creata. Pattern nuovi: sfiducia epistemica assoluta, vuoto cognitivo differito, identità arcaica auto-dichiarata, Consensus come strumento bibliografico, prompt multi-componente esplicito.

Integrato l'ultimo batch di 23 risposte nella sintesi PRAXIS di `01-wiki/studenti/studenti.md`. Principali acquisizioni:
- **P**: consolidamento uso strumentale-evasivo; flashcards (R251); triage per noia (R253); uso euristico sofisticato (R272)
- **R**: tre nuovi profili di non-uso (preferenza materiale, analfabetismo funzionale, rifiuto per protezione cognitiva); lock-in cognitivo (R272)
- **A**: ecologia dei dispositivi — telefono vs. computer come problema ambientale (R264)
- **X**: critica quadridimensionale dell'impoverimento (R273); dipendenza come destino collettivo (R253)
- **I**: sfiducia tecnica massiccia; privacy della fotocamera (R258); paywall come marker inverso (R266); limite relazionale categoriale (R265)
- **S**: espressioni matematiche, produzione testuale creativa, relazioni umane come nuove zone di esclusione; rifiuto globale (R254); distinzione scaffolding/completamento (R272)

Aggiornato `01-wiki/practice-patterns-insegnanti-attuali.md` con le pagine `insegnanti-futuri` e `studenti` precedentemente mancanti.

## 2026-04-19 — Citation Enrichment Pass (lint)
- **Scope**: Tutte le pagine wiki (insegnanti-attuali, insegnanti-futuri, studenti)
- **Action**: Aggiunta sistematica di `(source: filename.md)` dopo ogni affermazione fattuale, citazione diretta e claim specifico, come prescritto da AGENTS.md.
- **Metodo**: Grep mapping claim→source file sul corpus raw, poi riscrittura completa delle tre pagine.
- **Files modificati**: `01-wiki/insegnanti-attuali.md`, `01-wiki/insegnanti-futuri.md`, `01-wiki/studenti/studenti.md`
- **Copertura**: ~70 citazioni aggiunte in insegnanti-attuali, ~20 in insegnanti-futuri, ~60 in studenti (incluso arricchimento dei batch S1-S5 precedentemente privi di source).
## [2026-04-19] maintenance | batch linkage — aggancio fonti raw a sotto-temi wiki
- **Scope**: Tutti e 3 i corpora (insegnanti_attuali, insegnanti_futuri, studenti)
- **Pre-linkage**: 232 file raw citati nella wiki / 731 totali
- **Post-linkage**: 721 file raw citati nella wiki / 731 totali (10 esclusi perché vuoti/minimi)
- **Copertura**: 100% dei file con contenuto sostanziale
- **insegnanti_attuali**: 243 nuovi link distribuiti su 15 sotto-pagine
- **insegnanti_futuri**: 74 nuovi link distribuiti su 9 sotto-pagine
- **studenti**: 172 nuovi link distribuiti su 12 sotto-pagine
- **Metodo**: Classificazione automatica per keyword PRAXIS → sotto-tema, con quote rappresentativa. Citazioni aggiunte nella sezione "Fonti aggiuntive (batch linkage)" di ogni sotto-pagina.
- **Lint**: 0 link rotti verificati post-operazione.

## [2026-04-19] lint | rewrite-narrativo

- **Operazione**: Riscrittura narrativa di 56 pagine wiki (24 insegnanti-attuali, 16 insegnanti-futuri, 16 studenti).
- **Modifiche applicate**:
  1. Rimossi codici record numerici (R146, R256, ecc.) — mantenuti i codici respondente (ANZO06, sini22, ecc.)
  2. Corrette etichette citazione: codici respondente al posto di numeri record
  3. Espanse citazioni troncate ("...") con testo completo dai file raw
  4. Sezioni "Fonti aggiuntive (batch linkage)" convertite in paragrafi tematici narrativi con attribuzioni variate e raggruppamento per sotto-tema
  5. Aggiunti metadati mancanti (Summary, Sources, Last updated)
- **Risultato**: Tutte le pagine wiki ora hanno struttura discorsiva con citazioni per esteso, raggruppate tematicamente e integrate in prosa narrativa.

## [2026-04-19] rewrite | adequacy-of-support insegnanti-attuali

- **Operazione**: Riscrittura manuale e approfondita delle 4 pagine in `01-wiki/insegnanti-attuali/adequacy-of-support/`.
- **Modifiche applicate**:
  1. Indice riscritto con introduzione narrativa ai tre assi (materiale, economico, culturale) e citazione Stini27
  2. `logistica-e-dispositivi.md`: da 13 fonti riformulate in un paragrafo a 16 fonti organizzate in 4 sezioni tematiche (dispositivi, connettività, aule informatiche, riduzione schermi)
  3. `paywall.md`: da 2 citazioni scollegate a 3 fonti strutturate in 3 sezioni (muro del pagamento, scelta tool gratuiti, problema strutturale)
  4. `resistenza-manageriale.md`: da 10 fonti in gran parte fuori tema a 12 fonti pertinenti organizzate in 4 sezioni (dirigenze contrarie, scetticismo colleghi, freno normativo, autoformazione)
  5. Rimosse tutte le citazioni erroneamente classificate nella versione precedente
- **Risultato**: Ogni pagina ha ora un testo narrativo esteso che spiega il sotto-tema e lo supporta con citazioni per esteso dal corpus raw.

## [2026-04-19] rewrite | expectations insegnanti-attuali

- **Operazione**: Riscrittura manuale e approfondita delle 3 pagine in `01-wiki/insegnanti-attuali/expectations/`.
- **Modifiche applicate**:
  1. Indice riscritto con introduzione narrativa al paradosso inclusione vs. peggioramento
  2. `inclusione-digitale.md`: da 8 citazioni meccaniche ("Un rispondente pone l'accento su...") a 14 fonti organizzate in 3 sezioni (personalizzazione BES/DSA, accessibilità, paradosso divario digitale)
  3. `peggioramento-efficace.md`: da 21 citazioni in gran parte fuori tema a 18 fonti pertinenti organizzate in 4 sezioni (delega/copia, atrofia pensiero critico, impoverimento linguistico, paradosso docente vs. alunno)
  4. Rimosse tutte le citazioni erroneamente classificate e le intestazioni ripetitive meccaniche
- **Risultato**: Ogni pagina ha ora un testo narrativo esteso che spiega il sotto-tema e lo supporta con citazioni per esteso dal corpus raw.
## [2026-04-19] rewrite | interpersonal-trust insegnanti-attuali
- **Scope**: 4 file nella cartella `01-wiki/insegnanti-attuali/interpersonal-trust/`
- **Modifiche**:
  1. Indice riscritto con introduzione narrativa sui tre assi della sfiducia (pedagogico, relazionale, tecnico)
  2. `filosofia-della-fatica.md`: da 6 citazioni frammentate a 13 fonti organizzate in 4 sezioni (visione montessoriana, narcotizzazione cervello, scorciatoia e pigrizia, principio del minimo sforzo)
  3. `paradosso-digitale.md`: da 0 fonti e una frase orfana a 11 fonti organizzate in 3 sezioni (fiducia cieca e incompetenza di base, delega totale, dipendenza come regressione)
  4. `bias-e-allucinazione.md`: da 4 fonti di cui 2 fuori tema a 14 fonti pertinenti organizzate in 4 sezioni (errori diretti, inaffidabilità informazioni, supervisione come condizione, discriminazione algoritmica e privacy)
  5. Rimosse tutte le citazioni erroneamente classificate, le intestazioni ripetitive meccaniche e i soggetti mancanti prima delle citazioni
- **Risultato**: Ogni pagina ha ora un testo narrativo esteso con citazioni verificate dal corpus raw.
## [2026-04-19] rewrite | practice-patterns insegnanti-attuali
- **Scope**: 8 file nella cartella `01-wiki/insegnanti-attuali/practice-patterns/`
- **Modifiche**:
  1. Indice riscritto con introduzione narrativa sulla polarizzazione dell'adozione e i tre assi organizzativi (come si chiede, per chi si adatta, con cosa si lavora)
  2. `prompt-engineering.md`: da 55 fonti di cui molte misclassificate a 16 fonti pertinenti organizzate in 5 sezioni (gradiente sofisticazione, assegnazione di ruolo, generazione verifiche, prompt multimodali, prompt iterativo)
  3. `individualizzazione-bes-dsa.md`: da 43 fonti di cui molte misclassificate a 19 fonti pertinenti organizzate in 5 sezioni (esercizi accessibili, mappe e schede, verifiche parallele, adattamento INVALSI, ruolo docente sostegno)
  4. `caa-autismo-non-verbale.md`: 3 fonti riorganizzate in 3 sezioni narrative (traduzione CAA, testi per autismo basso funzionamento, immagini agende visive)
  5. `nai-e-traduzione.md`: da 12 a 8 fonti pertinenti organizzate in 3 sezioni (traduttore simultaneo NAI, intercomprensione come sperimentazione, traduzione come scorciatoia)
  6. `udl-e-gamification.md`: 4 fonti riorganizzate in 3 sezioni (quadro UDL bio-psico-sociale, UDA inclusive classi composite, produzione multimodale inclusiva)
  7. `strumenti-settoriali.md`: da 7 a 5 fonti pertinenti organizzate in 4 sezioni (grafica Firefly/Topaz, progettazione 3D AutoCAD/Oculus, informatica Java, rischio appiattimento)
  8. `piattaforme-e-role-playing.md`: da 35 fonti di cui molte semplici preferenze strumento a 15 fonti pertinenti organizzate in 5 sezioni (ecosistema piattaforme, quiz e verifiche, presentazioni visive, role-playing pedagogico, gamification inclusiva)
  9. Rimosse tutte le sezioni meccaniche con pattern ripetitivo e le citazioni misclassificate
- **Risultato**: Ogni pagina ha ora un testo narrativo strutturato con citazioni verificate e pertinenti al sotto-tema specifico.
## [2026-04-19] rewrite | skepticisms insegnanti-attuali
- **Scope**: 4 file nella cartella `01-wiki/insegnanti-attuali/skepticisms/`
- **Modifiche**:
  1. Indice riscritto con introduzione narrativa sui tre livelli di preoccupazione (cognizione, relazione, lavoro)
  2. `impoverimento-cognitivo.md`: da 73 fonti di cui la maggior parte elencate meccanicamente a 19 fonti pertinenti organizzate in 4 sezioni (pensiero critico sotto assedio, cervello che si seda, creatività e voce personale, ottenere senza sforzo)
  3. `crollo-relazionale.md`: da 23 fonti con filler meccanico a 16 fonti pertinenti organizzate in 4 sezioni (rapporto educativo insostituibile, isolamento e cyberbullismo, valutazione automatica come tabù, disumanizzazione)
  4. `ansia-occupazionale.md`: da 32 fonti di cui molte misclassificate a 13 fonti pertinenti organizzate in 3 sezioni (paura perdita del posto, imperativo non-sostituzione, identità professionale minacciata)
  5. Eliminate tutte le citazioni misclassificate (practice patterns, readiness beliefs), le duplicazioni tra pagine, e le sezioni meccaniche
- **Risultato**: Ogni pagina ha ora un testo narrativo strutturato con citazioni verificate, senza sovrapposizioni tra sotto-temi.
## [2026-04-19] rewrite | readiness-beliefs insegnanti-attuali
- **Scope**: 1 file `01-wiki/insegnanti-attuali/readiness-beliefs-insegnanti-attuali.md`
- **Modifiche**:
  1. Da 68 fonti elencate meccanicamente a 25 fonti pertinenti organizzate in 5 sezioni narrative (confessione di incompetenza, formazione come prerequisito, paura e disagio emotivo, fattore anagrafico, prime aperture)
  2. Eliminate tutte le citazioni misclassificate appartenenti ad altre dimensioni (skepticisms su impoverimento cognitivo, sostituzione docente, valutazione automatica; practice patterns su creazione test e rielaborazione BES)
  3. Rimosso completamente il pattern meccanico "Diversi rispondenti pongono l'accento su"
  4. Aggiunta cornice interpretativa che collega impreparazione individuale a vuoto formativo istituzionale
- **Risultato**: Pagina narrativa strutturata con citazioni verificate e pertinenti alla sola dimensione readiness.

## 2026-04-19 — Insegnanti futuri: tutte le 6 dimensioni PRAXIS

### Adequacy of support (A)
- **File**: `01-wiki/insegnanti-futuri/03-adequacy-of-support/adequacy-of-support-insegnanti-futuri.md`
- **Intervento**: Riscrittura completa. 16 fonti pertinenti in 4 sezioni (formazione universitaria assente, autoformazione come norma, scuola senza infrastruttura, necessità di formazione specifica). Rimossa struttura meccanica.

### Expectations (X)
- **File**: `01-wiki/insegnanti-futuri/expectations/expectations-insegnanti-futuri.md` (indice) + 2 sotto-temi
- **Sotto-temi riscritti**:
  - `cambiamento-positivo.md` — 12 fonti, 3 sezioni (velocità e semplificazione, personalizzazione e inclusione, condizione uso critico)
  - `omologazione.md` — 8 fonti, 2 sezioni (livellamento del processo educativo, appiattimento dello sforzo)
- **Intervento**: Riscrittura completa con citazioni verificate. 22 fonti totali.

### Interpersonal trust (I)
- **File**: `01-wiki/insegnanti-futuri/interpersonal-trust/interpersonal-trust-insegnanti-futuri.md` (indice) + 2 sotto-temi
- **Sotto-temi riscritti**:
  - `relazione-educativa.md` — 8 fonti, 3 sezioni (relazione come principio primo, empatia come discrimine, macchina e essere pensante)
  - `sostituzione-docente.md` — 7 fonti, 2 sezioni (sostituzione come pratica non raccomandata, linea rossa del lavoro umano)
- **Intervento**: Riscrittura completa. 15 fonti totali.

### Practice patterns (P)
- **File**: `01-wiki/insegnanti-futuri/practice-patterns/practice-patterns-insegnanti-futuri.md` (indice) + 2 sotto-temi
- **Sotto-temi riscritti**:
  - `facilitazione-accademica.md` — 13 fonti, 4 sezioni. Assorbito contenuto da prompt-engineering-come-gap.md (eliminato).
  - `uso-cross-disciplinare.md` — 5 fonti, 3 sezioni (attività integrate, template e declinazione, verifica strutturata)
- **File eliminato**: `prompt-engineering-come-gap.md` (1 sola fonte, contenuto integrato in facilitazione-accademica)
- **Intervento**: Riscrittura completa. 18 fonti totali.

### Readiness beliefs (R)
- **File**: `01-wiki/insegnanti-futuri/readiness-beliefs-insegnanti-futuri.md`
- **Intervento**: Riscrittura completa. 12 fonti in 3 sezioni (dichiarazione di incompetenza, gap tra studente e docente, rara eccezione chi si sente pronto).

### Skepticisms (S)
- **File**: `01-wiki/insegnanti-futuri/skepticisms/skepticisms-insegnanti-futuri.md` (indice) + 3 sotto-temi
- **Sotto-temi riscritti**:
  - `plagio-e-disonesta.md` — 11 fonti, 3 sezioni (copia-incolla senza riflessione, compiti/verifiche/esami, invalidazione della prova)
  - `omologazione.md` — 12 fonti, 3 sezioni (mente che si spegne, perdita di creatività, dipendenza come traiettoria). Rinominato concettualmente in "Impoverimento cognitivo e dipendenza" per differenziarsi da expectations/omologazione.
  - `copyright.md` — 1 fonte, pagina breve ma analiticamente densa
- **Intervento**: Riscrittura completa. 24 fonti totali.

### Nota metodologica
Per tutte le dimensioni: ogni citazione verificata tramite grep sui file raw/insegnanti_futuri_*.md. Eliminate citazioni misclassificate e fabbricate. Struttura meccanica sostituita con narrativa analitica. Formato pagine conforme a page-format.md e citation-rules.md.


## 2026-04-19 — Studenti: tutte le 6 dimensioni PRAXIS

### Practice patterns (P)
- **Scope**: 3 file in `01-wiki/studenti/practice-patterns/`
- **Modifiche**:
  1. Indice riscritto con introduzione sulla polarizzazione tra uso strumentale-evasivo (dominante) e interrogatore-autovalutativo (minoranza)
  2. `uso-strumentale-evasivo.md`: da 110 fonti a 33 fonti pertinenti in 6 sezioni (riassunto come funzione egemone, semplificazione pedagogica, traduzione e delega, logica della velocità, triage per noia, eccezione euristica)
  3. `interrogatore-e-autovalutazione.md`: conteggio fonti corretto da 25 a 17

### Expectations (X)
- **Scope**: 3 file in `01-wiki/studenti/expectations/`
- **Modifiche**:
  1. Indice riscritto con summary analitico su supporto vs. sostituzione come preoccupazione centrale
  2. `supporto-vs-sostituzione.md`: riscrittura con 22 fonti in 4 sezioni (cornice binaria, fantasia a rischio, dipendenza come destino, sostituzione come minaccia). Integrate 6 citazioni da Ulteriori evidenze, eliminate 9 misclassificate
  3. `autonomia-cognitiva-a-rischio.md`: riscrittura con 19 fonti in 3 sezioni (impoverimento quadridimensionale, autonomia come identità, delega come meccanismo). Integrate 5 citazioni da Ulteriori evidenze, eliminate 3 misclassificate

### Skepticisms (S)
- **Scope**: 3 file in `01-wiki/studenti/skepticisms/`
- **Modifiche**:
  1. Indice riscritto con tabù come concetto organizzatore
  2. `evoluzione-del-tabu.md`: riscrittura con 30 fonti in 4 sezioni (tabù produzione testuale, esercizi delega e plagio, libro che non basta, lingue classiche e zone professionali). Eliminata OSTA30 (misclassificata), rimossi riferimenti batch
  3. `zone-di-esclusione-s6.md`: riscrittura con 13 fonti in 4 sezioni (espressioni matematiche, scrittura come atto irriducibile, relazioni umane e zone professionali, rifiuto globale). Integrata coll01, eliminate Roni18 e zano18 (expectations). Rimosso "S6" dal titolo

### Interpersonal trust (I)
- **Scope**: 3 file in `01-wiki/studenti/interpersonal-trust/`
- **Modifiche**:
  1. Indice riscritto con tre livelli di sfiducia (tecnica, strutturale, epistemica)
  2. `sfiducia-tecnica-e-strutturale.md`: riscrittura con 24 fonti in 5 sezioni (allucinazioni, verifica obbligatoria, paywall e fiducia inversa, privacy e sfiducia strutturale, sfiducia epistemica). Integrate lico31 e nini09, eliminata Rosi06 (practice patterns)
  3. `conferma-sfiducia-e-privacy.md`: riscrittura con 7 fonti in 4 sezioni (errori confermati, privacy fotocamera, paywall come segnale inverso, relazioni umane come confine). Eliminate Ello18 e nani19 (practice patterns)

### Readiness beliefs (R)
- **Scope**: 3 file in `01-wiki/studenti/readiness-beliefs/`
- **Modifiche**:
  1. Indice riscritto con summary analitico sulla tassonomia dei nove profili di non-uso e il lock-in cognitivo. Eliminate citazioni misclassificate (ioni10 → expectations, Vese2 → skepticisms)
  2. `profili-di-non-uso-1-6.md`: riscrittura con 21 fonti in 6 sezioni (orgoglio competitivo, barriere pratiche, scelta epistemica, procrastinazione adattiva, uso cinico consapevole, intrappolamento da dipendenza). Integrate Alessandra aprile 28 e ecco19/09/81 da Ulteriori evidenze
  3. `profili-di-non-uso-7-9.md`: riscrittura con 17 fonti in 4 sezioni (preferenza materiale, analfabetismo funzionale, rifiuto per protezione cognitiva, lock-in cognitivo). Integrata asio30, eliminata ele07 (misclassificata: skepticisms). Rimossi riferimenti batch ("S6")

### Adequacy of support (A)
- **File**: `01-wiki/studenti/03-adequacy-of-support/adequacy-of-support-studenti.md`
- **Intervento**: Riscrittura completa con 7 fonti in 3 sezioni (IA come safety net, uso compensativo tacito, ecologia dei dispositivi). Integrata Mili08 da Ulteriori, eliminate azza13 (troppo generica) e Mele08 (misclassificata)

### Nota metodologica
Per tutte le dimensioni: eliminate sezioni meccaniche "Ulteriori evidenze dalle fonti", summary generici "Sotto-tema che esplora...", pattern ripetitivi "Diversi rispondenti pongono l'accento su...". Citazioni misclassificate rimosse (non trasferite). Riferimenti batch (S1-S6) eliminati. Ogni citazione mantenuta verificata tramite grep su raw/studenti_*.md.
