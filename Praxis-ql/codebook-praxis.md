# Codebook PRAXIS

**Versione**: 1.0  
**Data**: 2026-04-19  
**Corpus di riferimento**: docenti in servizio, futuri docenti, studenti  
**Base empirica**: `Praxis-ql/raw/`, `Praxis-ql/wiki/`, `Praxis-ql/wiki/sintesi-cross-coorte.md`

## 1. Scopo

Questo codebook formalizza una griglia tematico-interpretativa per l'analisi qualitativa del corpus PRAXIS sull'uso educativo della GenAI. Il codebook non sostituisce il framework PRAXIS, ma lo rende operativamente codificabile su risposte aperte.

La sua costruzione segue una logica insieme deduttiva e induttiva:

- `deduttiva`, perche' i sei codici principali derivano dal framework PRAXIS;
- `induttiva`, perche' i sottocodici prendono forma a partire dai pattern ricorrenti effettivamente emersi nei dati.

## 2. Processo di costruzione del codebook

Il codebook prende forma progressivamente attraverso piu' giornate di lavoro collegiale. Nel corso di queste sessioni i valutatori rileggono le risposte aperte, confrontano le attribuzioni, discutono le etichette iniziali e verificano i casi ambigui.

Il processo non procede per applicazione rigida di una griglia prefissata, ma per affinamento successivo. Le etichette troppo vicine vengono accorpate; quelle troppo ampie vengono differenziate; quelle poco stabili vengono ridefinite o abbandonate. Il codebook finale e' quindi il risultato di un vero e proprio merge interpretativo tra proposte iniziali, ricorrenze emerse nel corpus e decisioni condivise maturate nel confronto. In questo modo non coincide con un elenco preliminare di voci, ma con l'esito di una convergenza interpretativa costruita nel tempo.

Il risultato e' una griglia condivisa che mantiene il framework PRAXIS come struttura di livello alto, ma ne specifica operativamente i contenuti attraverso sottocodici stabilizzati nel confronto analitico.

## 3. Unita' di codifica

L'unita' di codifica e' il segmento minimo di testo dotato di senso compiuto rispetto alla domanda e al contesto della risposta. Puo' coincidere con:

- una frase;
- una parte di frase;
- un esempio operativo;
- una valutazione o presa di posizione;
- un prompt riportato dal partecipante.

## 4. Regole generali di codifica

1. La stessa risposta puo' ricevere piu' codici.
2. La stessa domanda puo' attivare piu' dimensioni analitiche.
3. Si codifica il contenuto espresso, non quello inferito oltre il testo.
4. Si privilegia il segmento piu' piccolo possibile, evitando di assegnare lo stesso codice a un intero paragrafo se il contenuto e' piu' articolato.
5. I codici `P`, `R`, `A`, `X`, `I`, `S` non sono mutuamente esclusivi.
6. Quando un segmento descrive insieme uso e valutazione, si applica doppia codifica.

## 5. Struttura del codebook

I codici principali sono:

- `P` = Practice patterns
- `R` = Readiness beliefs
- `A` = Adequacy of support
- `X` = eXpectations
- `I` = Interpersonal & Institutional trust
- `S` = Skepticisms

## 6. Codici principali e sottocodici

### P. Practice patterns

**Definizione**  
Descrive che cosa i partecipanti fanno concretamente con l'IA, per quali compiti, con quali strumenti e con quale grado di articolazione operativa.

**Includere quando**  
Il segmento nomina usi concreti, strumenti, attivita', prompt, compiti o destinatari dell'azione.

**Escludere quando**  
Il segmento non descrive una pratica, ma esprime solo giudizi, paure o opinioni astratte.

**Sottocodici**

#### P1. Produzione di materiali didattici o di studio
Uso dell'IA per generare schede, verifiche, quiz, riassunti, mappe, esercizi, spiegazioni o materiali di supporto.

Indicatori tipici:
- creare verifiche;
- generare quiz;
- fare riassunti;
- produrre mappe concettuali;
- preparare materiali.

Ancoraggi empirici:
- docenti attuali: generazione di verifiche e quiz;
- studenti: riassunti, spiegazioni, schemi;
- futuri docenti: facilitazione del proprio studio.

#### P2. Individualizzazione e personalizzazione
Uso dell'IA per adattare spiegazioni, testi, attivita', consegne o percorsi al profilo del singolo studente o gruppo.

Indicatori tipici:
- semplificare un testo per DSA;
- creare percorsi BES;
- adattare contenuti al livello cognitivo;
- personalizzare lo studio.

Ancoraggi empirici:
- `santi13`, `Stini27`, `ogri20`, `Ioli28`.

#### P3. Inclusione e accessibilita'
Uso dell'IA per favorire accesso comunicativo, linguistico o cognitivo a contenuti altrimenti poco accessibili.

Indicatori tipici:
- CAA;
- immagini per agende visive;
- traduzioni per NAI;
- supporti multimodali;
- accesso per studenti fragili.

Ancoraggi empirici:
- `santi13`, `anti03`, `eddu02`, `NALI26`.

#### P4. Supporto allo studio, simulazione, tutoraggio
Uso dell'IA come interrogatore simulato, sparring partner, supporto allo studio, allenamento o chiarificazione.

Indicatori tipici:
- simulare interrogazioni;
- fare domande;
- esercitarsi per esami;
- ricevere spiegazioni;
- autocorreggersi.

Ancoraggi empirici:
- coorte studenti, specie in `wiki/studenti.md`.

#### P5. Strategie operative di produzione
Uso dell'IA per ottenere specifici formati o trasformazioni del contenuto, come riassunti, schemi, mappe, spiegazioni, traduzioni, riscritture, esempi o visualizzazioni.

Indicatori tipici:
- riassumere;
- fare schemi o mappe;
- spiegare meglio;
- tradurre;
- riscrivere un testo;
- generare esempi;
- produrre immagini o video.

#### P6. Ecosistema di strumenti
Riferimento a piattaforme, tool o combinazioni di strumenti usati in modo differenziato.

Indicatori tipici:
- ChatGPT;
- Gemini;
- NotebookLM;
- Canva AI;
- Copilot;
- DeepSeek;
- Consensus.

#### P7. Prompting visibile
Presenza di prompt riportati, parafrasati o descritti come esempio concreto d'uso.

Indicatori tipici:
- "uso prompt come...";
- "chiedo all'IA di...";
- prompt diretti o strutturati.

Nota operativa:
`P7` si usa quando il prompt documenta la pratica. Se il prompt segnala anche competenza o inesperienza, si aggiunge `R`.

---

### R. Readiness beliefs

**Definizione**  
Riguarda la competenza percepita, pratica o teorica, nell'uso dell'IA, compresa la sicurezza operativa e la consapevolezza dei propri limiti.

**Includere quando**  
Il segmento parla di saper usare o non saper usare l'IA, capire o non capire come funziona, sentirsi pronti o impreparati.

**Escludere quando**  
Il segmento parla solo di mancanza di formazione istituzionale: in quel caso si codifica `A`, eventualmente insieme a `R`.

**Sottocodici**

#### R1. Competenza pratica percepita
Autovalutazione della propria capacita' di usare strumenti e prompt.

Indicatori tipici:
- so usare;
- non so usarla bene;
- riesco a formulare prompt;
- mi manca pratica.

#### R2. Competenza teorica o epistemologica
Consapevolezza dei limiti, dei meccanismi o del funzionamento dell'IA.

Indicatori tipici:
- capisco i limiti;
- non so come funziona;
- rischio di affidarmi senza capire;
- l'output va verificato.

#### R3. Gap tra uso personale e uso didattico
Scarto tra familiarita' personale con l'IA e capacita' di integrarla in chiave pedagogica.

Ancoraggi empirici:
- futuri docenti che usano l'IA per se', ma non per la didattica.

#### R4. Competenza di prompting
Valutazione implicita o esplicita della capacita' di formulare prompt efficaci.

Indicatori tipici:
- prompt dettagliati;
- richiesta vaga;
- non so cosa chiedere;
- so che un buon prompt cambia il risultato.

Nota operativa:
`R4` spesso co-occorre con `P7`.

#### R5. Non-uso per impreparazione o rifiuto competente
Ragioni del non uso legate a insicurezza, mancanza di competenza, scelta epistemica o resistenza consapevole.

Ancoraggi empirici:
- profili di non uso tra gli studenti;
- futuri docenti che dichiarano insufficienza tecnica.

---

### A. Adequacy of support

**Definizione**  
Codifica il supporto o il mancato supporto offerto da istituzioni, universita', scuole, corsi, infrastrutture e condizioni organizzative.

**Includere quando**  
Il segmento attribuisce opportunita' o ostacoli al contesto formativo o organizzativo.

**Escludere quando**  
Il segmento riguarda solo una difficolta' personale non collegata al sistema.

**Sottocodici**

#### A1. Assenza di formazione formale
Mancanza di corsi, accompagnamento, inserimento curricolare o aggiornamento professionale.

Indicatori tipici:
- nessuno ci ha formato;
- l'universita' non tratta il tema;
- mancano corsi;
- autoformazione necessaria.

#### A2. Supporto insufficiente o diseguale
Supporto esistente ma percepito come sporadico, tardivo o inadeguato.

#### A3. Vincoli infrastrutturali ed economici
Ostacoli legati a dispositivi, connessione, licenze, paywall, LIM obsolete o accesso diseguale.

#### A4. Uso compensativo dell'IA
L'IA viene usata per colmare lacune del sistema formativo o didattico.

Indicatori tipici:
- materiali scolastici insufficienti;
- slide mancanti;
- mancanza di sostegno istituzionale;
- bisogno di raggiungere studenti che il sistema non raggiunge.

Ancoraggi empirici:
- studenti che usano l'IA per capire il libro;
- docenti che la usano per BES/DSA in assenza di risorse adeguate.

---

### X. eXpectations

**Definizione**  
Raccoglie aspettative, benefici attesi, trasformazioni percepite e visioni sul cambiamento generato dall'IA.

**Includere quando**  
Il segmento dice che cosa l'IA puo' migliorare, cambiare o rendere possibile.

**Escludere quando**  
Il segmento esprime un timore o una barriera: in quel caso si valuta `S`, eventualmente in compresenza.

**Sottocodici**

#### X1. Efficienza e risparmio di tempo
Aspettative di velocizzazione, alleggerimento o ottimizzazione del lavoro.

#### X2. Semplificazione e comprensione
Aspettative di chiarificazione, semplificazione, comprensione piu' rapida e focalizzazione dei concetti.

#### X3. Personalizzazione e attenzione al singolo
Aspettativa che l'IA renda possibile una modulazione piu' fine sul singolo studente o sul singolo percorso di studio.

#### X4. Inclusione e accesso
Aspettative di maggiore equita', adattamento e accessibilita' per studenti con bisogni diversi.

#### X5. Autonomia, organizzazione e supporto al percorso
Aspettative di miglioramento nell'organizzazione dello studio, nell'autocorrezione, nel supporto allo studio o nella gestione del lavoro.

#### X6. Coinvolgimento, arricchimento e innovazione
Aspettative di maggiore interesse, varieta', arricchimento dei materiali e innovazione delle pratiche.

#### X7. Cambiamento condizionato
Apertura positiva accompagnata da condizioni: uso critico, supervisione, limiti, controllo umano.

Ancoraggi empirici:
- futuri docenti in `cambiamento-positivo.md`.

---

### I. Interpersonal & Institutional trust

**Definizione**  
Riguarda la fiducia o sfiducia nell'affidabilita' della tecnologia e nella capacita' degli attori umani di usarla responsabilmente.

**Includere quando**  
Il segmento valuta la credibilita' dell'output, il bisogno di verifica, l'affidamento all'IA o agli altri utenti.

**Escludere quando**  
Il segmento parla di rischio o paura senza riferimento alla fiducia: in quel caso si valuta `S`.

**Sottocodici**

#### I1. Fiducia tecnica condizionata
L'IA viene considerata utile, ma solo se verificata, controllata o usata entro limiti precisi.

Indicatori tipici:
- e' utile ma va controllata;
- non mi fido ciecamente;
- bisogna verificare.

#### I2. Sfiducia tecnica
Dubbi legati a errori, allucinazioni, approssimazioni, traduzioni scorrette, versioni sbagliate.

Ancoraggi empirici:
- studenti su latino, greco, matematica;
- docenti su bias e output opachi.

#### I3. Fiducia o sfiducia negli utenti
Riguarda se studenti o docenti sapranno usare l'IA in modo etico, responsabile e non sostitutivo.

#### I4. Fiducia relazionale e pedagogica
Riferimento all'insostituibilita' della relazione educativa, dell'empatia o del giudizio umano.

#### I5. Privacy e affidamento dei dati
Dubbi sulla gestione dei dati, delle immagini e delle informazioni personali affidate al sistema.

---

### S. Skepticisms

**Definizione**  
Raccoglie timori, riserve, rischi percepiti, confini normativi e pratiche ritenute non raccomandate.

**Includere quando**  
Il segmento nomina cio' che non si dovrebbe fare con l'IA, oppure espone danni potenziali o gia' percepiti.

**Escludere quando**  
Il segmento formula una semplice cautela tecnica senza esplicita paura o norma: in quel caso si puo' usare `I`.

**Sottocodici**

#### S1. Delega cognitiva eccessiva
Timore che l'IA faccia al posto del soggetto il lavoro mentale.

Indicatori tipici:
- pigrizia;
- dipendenza;
- non fare piu' nulla da soli;
- anestetizzare il cervello.

#### S2. Ghostwriting e plagio
Rifiuto dell'uso dell'IA per testi, temi, tesi, elaborati o compiti spacciati come propri.

#### S3. Appiattimento, omologazione, perdita di creativita'
Timore di uniformazione degli output, impoverimento espressivo o riduzione della soggettivita'.

#### S4. Erosione del pensiero critico
Timore che l'IA riduca analisi autonoma, riflessione, comprensione profonda o sforzo cognitivo.

#### S5. Informazioni false, imprecisione, affidabilita' debole
Timore che l'IA produca errori, allucinazioni, approssimazioni o contenuti non verificati.

#### S6. Sostituzione del docente o della relazione educativa
Paura che l'IA occupi impropriamente spazi di insegnamento, accompagnamento o mediazione umana.

#### S7. Ambiti off-limits
Zone di esclusione d'uso: relazioni umane, scrittura soggettiva, valutazione, lingue classiche, matematica, medicina, diagnosi, counseling.

Nota operativa:
`S7` si usa quando il partecipante delimita esplicitamente un confine normativo: "qui non va usata".

---

## 7. Matrice sintetica di co-occorrenza

Le co-occorrenze piu' frequenti attese nel corpus sono:

- `P + R`: quando una pratica mostra anche livello di competenza;
- `P + X`: quando l'uso concreto e' descritto come vantaggioso;
- `R + A`: quando la percezione di incompetenza e' attribuita alla mancanza di formazione;
- `I + S`: quando la sfiducia si traduce in timore o interdizione;
- `P + S`: quando una pratica e' citata come uso esistente ma non raccomandato;
- `P + I + S`: quando il partecipante descrive uso concreto, bisogno di verifica e rischio percepito nello stesso segmento.

## 8. Esempi di applicazione

### Esempio 1
"Uso ChatGPT per semplificare testi per studenti DSA."

Codici:
- `P2` individualizzazione e personalizzazione
- `P3` inclusione e accessibilita'

### Esempio 2
"Non lo uso nella didattica perche' non saprei formulare bene i prompt."

Codici:
- `R1` competenza pratica percepita
- `R4` competenza di prompting

### Esempio 3
"L'universita' non ci prepara davvero a usare questi strumenti."

Codici:
- `A1` assenza di formazione formale
- `R3` gap tra uso personale e uso didattico, se il contrasto e' esplicito

### Esempio 4
"Va bene per aiutare, non per scrivere una tesi al posto mio."

Codici:
- `I1` fiducia tecnica condizionata
- `S2` ghostwriting e plagio
- `S7` ambiti off-limits

## 9. Nota metodologica finale

Questo codebook e' pensato come strumento di codifica analitica condivisa, aperto a ulteriori affinamenti ma gia' stabilizzato nei suoi nuclei principali attraverso il confronto tra valutatori. Puo' essere ulteriormente sviluppato in due direzioni:

- maggiore granularita' interna ai sottocodici, se si passa alla microanalisi sistematica dei record;
- riduzione e accorpamento, se serve una versione piu' sintetica per articolo o appendice metodologica.
