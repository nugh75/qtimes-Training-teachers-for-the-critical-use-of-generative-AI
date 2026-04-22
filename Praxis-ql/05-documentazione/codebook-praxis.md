# Codebook PRAXIS

**Versione**: 1.1
**Data**: 2026-04-21
**Corpus di riferimento**: docenti in servizio, futuri docenti, studenti
**Base empirica**: `Praxis-ql/02-corpus/`, `Praxis-ql/01-wiki/`, `Praxis-ql/01-wiki/10-framework/sintesi-cross-coorte.md`
**Glossario ID partecipanti**: `Praxis-ql/05-documentazione/codebook-id-map.md` (uso interno)

## 1. Scopo

Questo codebook formalizza una griglia tematico-interpretativa per l'analisi qualitativa del corpus PRAXIS sull'uso educativo della GenAI. Il codebook non sostituisce il framework PRAXIS, ma lo rende operativamente codificabile su risposte aperte.

La sua costruzione segue una logica insieme deduttiva e induttiva:

- `deduttiva`, perche' i sei codici principali derivano dal framework PRAXIS;
- `induttiva`, perche' i sottocodici prendono forma a partire dai pattern ricorrenti effettivamente emersi nei dati.

## 2. Processo di costruzione del codebook

Il codebook prende forma progressivamente attraverso piu' giornate di lavoro collegiale. Nel corso di queste sessioni i valutatori rileggono le risposte aperte, confrontano le attribuzioni, discutono le etichette iniziali e verificano i casi ambigui.

Il processo non procede per applicazione rigida di una griglia prefissata, ma per affinamento successivo. Le etichette troppo vicine vengono accorpate; quelle troppo ampie vengono differenziate; quelle poco stabili vengono ridefinite o abbandonate. Il codebook finale e' quindi il risultato di un vero e proprio merge interpretativo tra proposte iniziali, ricorrenze emerse nel corpus e decisioni condivise maturate nel confronto. In questo modo non coincide con un elenco preliminare di voci, ma con l'esito di una convergenza interpretativa costruita nel tempo.

Come traccia storica del primo ciclo di etichettatura e' archiviato `archive/labeling-legacy/analisi_mu.db`. Questo artefatto ha avuto un ruolo di supporto nella maturazione iniziale del codebook, ma non sostituisce la pipeline canonica corrente.

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
7. Gli ancoraggi empirici citati nel codebook descrivono **profili tipologici** (coorte + ruolo + tratto rilevante), non ID di partecipanti. La mappa `ID → profilo` e' tenuta separata in `codebook-id-map.md` come strumento interno di tracciabilita'.

## 5. Struttura del codebook

I codici principali sono:

- `P` = Practice patterns
- `R` = Readiness beliefs
- `A` = Adequacy of support
- `X` = eXpectations
- `I` = Interpersonal & Institutional trust
- `S` = Skepticisms

Ogni sottocodice e' presentato con quattro campi uniformi:

- **Definizione operativa**: cosa cade sotto il codice, in una frase.
- **Indicatori lessicali**: espressioni e formule ricorrenti nel corpus che fanno scattare il codice.
- **Esempi di segmento**: frasi-tipo che illustrano un'attribuzione corretta.
- **Non confondere con**: codici vicini e criterio di distinzione.

Gli **ancoraggi empirici** (quando presenti) aggiungono il profilo tipologico della coorte in cui il pattern e' prevalente.

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

**Definizione operativa**
Uso dell'IA per generare artefatti didattici o di studio: schede, verifiche, quiz, riassunti, mappe, esercizi, spiegazioni, slide, materiali di supporto.

**Indicatori lessicali**
- "creo verifiche con l'IA"; "genero quiz"; "faccio riassumere"; "produco mappe concettuali"; "preparo materiali"; "le chiedo di fare una scheda"; "genera esercizi"; "crea un test".

**Esempi di segmento**
- "Uso ChatGPT per creare verifiche a risposta multipla sulla Divina Commedia."
- "Mi faccio generare schemi riassuntivi prima dell'esame."

**Non confondere con**
- `P5` (strategie di produzione): `P1` nomina l'**artefatto finale** (verifica, quiz, mappa). `P5` nomina la **trasformazione** (riassumere, schematizzare, tradurre) senza specificare il prodotto d'uso didattico.
- `P4` (supporto allo studio): se il materiale serve a esercitarsi o farsi interrogare, prevale `P4`.

**Ancoraggi empirici**
- docenti in servizio: generazione di verifiche, quiz, esercizi parametrici;
- studenti: riassunti, spiegazioni, schemi per studio personale;
- futuri docenti: materiali per facilitare il proprio studio universitario.

#### P2. Individualizzazione e personalizzazione

**Definizione operativa**
Uso dell'IA per adattare spiegazioni, testi, attivita', consegne o percorsi al profilo del singolo studente (capacita' cognitiva, stile di apprendimento, bisogno educativo) o di un sottogruppo.

**Indicatori lessicali**
- "semplificare un testo per DSA"; "creare un percorso per BES"; "adattare al livello"; "personalizzare"; "versione facilitata"; "verifica parallela"; "ridurre carico cognitivo"; "mio figlio segue diversamente".

**Esempi di segmento**
- "Faccio semplificare i testi della verifica per gli studenti con DSA."
- "Le chiedo di ridurre il numero di richieste per uno studente con disabilita' cognitiva."

**Non confondere con**
- `P3` (inclusione e accessibilita'): `P2` opera sul **livello di difficolta'** o sul **profilo cognitivo**. `P3` opera sul **canale comunicativo** (CAA, lingua, multimodalita').
- `X3` (aspettativa di personalizzazione): `P2` = pratica gia' in atto; `X3` = desiderio o previsione.

**Ancoraggi empirici**
- docenti di sostegno e docenti curricolari con classi BES/DSA;
- docenti che adattano prove INVALSI o verifiche di classe.

#### P3. Inclusione e accessibilita'

**Definizione operativa**
Uso dell'IA per abbattere barriere comunicative, linguistiche, sensoriali o culturali che impediscono l'accesso al contenuto: CAA, traduzione per alunni stranieri, agende visive, testi in LIS, descrizioni per ipovedenti.

**Indicatori lessicali**
- "CAA"; "pittogrammi"; "agenda visiva"; "NAI"; "traduzione per stranieri"; "autismo non verbale"; "alunni fragili"; "accessibilita'"; "supporto multimodale".

**Esempi di segmento**
- "Uso l'IA per trasformare un testo in pittogrammi CAA."
- "Traduco le consegne per gli alunni NAI appena arrivati."

**Non confondere con**
- `P2`: vedi sopra.
- `X4` (aspettativa inclusiva): `P3` = azione fatta; `X4` = beneficio previsto.

**Ancoraggi empirici**
- docenti di sostegno con studenti autistici non verbali;
- docenti di italiano L2 / classi NAI;
- docenti con alunni ipovedenti o con disabilita' sensoriali.

#### P4. Supporto allo studio, simulazione, tutoraggio

**Definizione operativa**
Uso dell'IA come interrogatore simulato, sparring partner, tutor di studio, allenatore per esami o prove. Include autocorrezione e richiesta di chiarimenti.

**Indicatori lessicali**
- "simulo interrogazioni"; "mi fa domande"; "mi esercito con lei"; "mi spiega di nuovo"; "controllo le risposte"; "mi faccio correggere"; "uso come tutor"; "mi interroga su...".

**Esempi di segmento**
- "Prima dell'esame le chiedo di farmi domande a caso sul capitolo."
- "Le faccio correggere i miei esercizi di latino per capire dove sbaglio."

**Non confondere con**
- `P1`: se l'output e' un artefatto condivisibile (verifica, quiz per classe) prevale `P1`. `P4` e' uso **diretto** come interlocutore didattico per se' stessi.
- `X5` (aspettativa di autonomia): `P4` = pratica reale; `X5` = previsione di beneficio.

**Ancoraggi empirici**
- coorte studenti (preparazione esami universitari);
- futuri docenti (studio in vista di concorsi o TFA).

#### P5. Strategie operative di produzione

**Definizione operativa**
Uso dell'IA per ottenere una specifica **trasformazione di contenuto**: riassumere, schematizzare, mappare, spiegare in modo diverso, tradurre, riscrivere, generare esempi, produrre immagini/video/audio.

**Indicatori lessicali**
- "riassumi"; "fai uno schema"; "fammi una mappa"; "spiegamelo meglio"; "in parole semplici"; "traduci in..."; "riscrivi in stile..."; "dammi esempi"; "generami un'immagine"; "fai un video"; "dai esempi concreti".

**Esempi di segmento**
- "Le chiedo di riscrivere il brano in italiano piu' semplice."
- "Mi genera immagini per le slide di biologia."

**Non confondere con**
- `P1`: `P5` e' la **trasformazione** (riassunto, mappa, schema). `P1` e' l'**artefatto didattico finalizzato** (verifica, quiz, materiale di classe).
- `P6`: `P5` descrive la trasformazione, `P6` lo strumento con cui si ottiene.

**Ancoraggi empirici**
- tutte le coorti; particolarmente denso tra studenti universitari.

#### P6. Ecosistema di strumenti

**Definizione operativa**
Riferimento a piattaforme, tool o combinazioni di strumenti usati in modo esplicito e differenziato (spesso con motivazione d'uso: "per X uso Y").

**Indicatori lessicali**
- nomi di prodotto: "ChatGPT", "Gemini", "NotebookLM", "Canva AI", "Copilot", "DeepSeek", "Consensus", "Claude", "Perplexity", "MidJourney";
- formule di scelta: "per i quiz uso..."; "preferisco... per..."; "passo da... a... quando...".

**Esempi di segmento**
- "Per i quiz uso Gemini perche' e' piu' preciso, per la scrittura ChatGPT."
- "Consensus lo uso solo per le ricerche bibliografiche."

**Non confondere con**
- `P5`: se il segmento nomina solo la trasformazione (riassumi, traduci) senza nominare lo strumento, prevale `P5`.
- `A3` (vincoli infrastrutturali): se il partecipante parla di **impossibilita'** di usare uno strumento (paywall, blocco scolastico), prevale `A3`.

**Ancoraggi empirici**
- docenti in servizio con repertorio multi-strumento;
- studenti con uso misto ChatGPT + app specifiche per materia.

#### P7. Prompting visibile

**Definizione operativa**
Presenza di un prompt riportato, parafrasato o descritto come esempio concreto d'uso. L'IA non e' solo nominata: ne e' citato il modo di interrogarla.

**Indicatori lessicali**
- "chiedo all'IA di..."; "uso questo prompt..."; "le scrivo:..."; "gli dico di..."; "cito alla lettera il prompt"; presenza di testo tra virgolette con imperativi di richiesta.

**Esempi di segmento**
- "Le dico: 'Crea 5 domande a risposta aperta sul primo canto dell'Odissea, adatte a prima media'."
- "Uso un prompt tipo: 'Agisci come un docente di sostegno e semplificami questo testo'."

**Non confondere con**
- `R4` (competenza di prompting): `P7` documenta **che il prompt esiste**; `R4` valuta se e' **formulato bene**.
- `P1`/`P5`: se il prompt serve da esempio di pratica, il codice del prodotto (`P1`/`P5`) si aggiunge a `P7`, non lo sostituisce.

**Nota operativa**
`P7` si usa quando il prompt documenta la pratica. Se il prompt segnala anche competenza o inesperienza di formulazione, si aggiunge `R4`.

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

**Definizione operativa**
Autovalutazione della propria capacita' operativa con strumenti e interfacce: saper usare, saper impostare, saper ottenere un risultato utile.

**Indicatori lessicali**
- "so usare"; "non la so usare bene"; "riesco a"; "non riesco a"; "mi manca pratica"; "ci sto prendendo la mano"; "sono alle prime armi"; "me la cavo".

**Esempi di segmento**
- "Me la cavo con ChatGPT, ma con NotebookLM sono fermo."
- "Non la uso perche' non sono pratica."

**Non confondere con**
- `R2`: `R1` e' sapere pratico operativo; `R2` e' comprensione del funzionamento interno.
- `A1` (assenza di formazione): se la ragione dell'incompetenza e' esplicitamente attribuita al sistema formativo, si aggiunge `A1`.

#### R2. Competenza teorica o epistemologica

**Definizione operativa**
Consapevolezza dei meccanismi, dei limiti e della natura probabilistica dell'output dell'IA.

**Indicatori lessicali**
- "capisco i limiti"; "non so come funziona"; "non e' intelligente davvero"; "pesa sui dati con cui e' addestrata"; "puo' inventare"; "l'output va verificato"; "bias"; "modello linguistico".

**Esempi di segmento**
- "So che pesca da dati di addestramento, quindi verifico sempre."
- "Non ho idea di come funzioni dentro, la uso e basta."

**Non confondere con**
- `I1` (fiducia condizionata): `R2` e' consapevolezza cognitiva del funzionamento; `I1` e' la traduzione di quella consapevolezza in una postura di uso controllato.
- `S5` (informazioni false): `R2` e' sapere che puo' sbagliare; `S5` e' paura normativa degli effetti.

#### R3. Gap tra uso personale e uso didattico

**Definizione operativa**
Scarto tra familiarita' personale con l'IA (uso privato, svago, studio individuale) e capacita' percepita di integrarla in chiave pedagogica o professionale.

**Indicatori lessicali**
- "la uso per me ma non con gli studenti"; "a scuola non saprei come"; "nella didattica mi fermo"; "per me si', ma in classe no"; "non so come usarla con i miei alunni".

**Esempi di segmento**
- "La uso quotidianamente per studiare, ma non saprei come portarla in classe."

**Non confondere con**
- `R1`: `R3` non e' incompetenza tecnica generale, ma **asimmetria** tra due sfere d'uso.

**Ancoraggi empirici**
- futuri docenti con uso privato frequente ma assenza di transfer didattico;
- docenti in servizio esperti di IA nella vita personale e cauti nella pratica d'aula.

#### R4. Competenza di prompting

**Definizione operativa**
Valutazione implicita o esplicita della propria (o altrui) capacita' di formulare prompt efficaci: specificita', ruolo, formato, vincoli.

**Indicatori lessicali**
- "so che un buon prompt cambia il risultato"; "non so cosa chiedere"; "le mie richieste sono vaghe"; "piu' dettagli metto, meglio va"; "le dico di agire come..."; "do il contesto".

**Esempi di segmento**
- "Ho imparato che devo darle un ruolo: se le dico 'sei un docente di matematica', funziona meglio."
- "I miei prompt sono troppo generici, infatti esce poco utile."

**Non confondere con**
- `P7`: `P7` documenta il prompt; `R4` valuta la competenza che lo produce.
- `R1`: `R4` e' un sotto-insieme specifico della competenza pratica focalizzato sul prompt.

**Nota operativa**
`R4` spesso co-occorre con `P7`.

#### R5. Non-uso per impreparazione o rifiuto competente

**Definizione operativa**
Ragioni del non uso dichiarate dal partecipante: insicurezza tecnica, mancanza di competenza, scelta epistemica di non usarla, resistenza consapevole.

**Indicatori lessicali**
- "non la uso"; "preferisco non usarla"; "non mi sento pronto"; "non mi interessa"; "per scelta non la uso"; "non mi fido abbastanza per iniziare".

**Esempi di segmento**
- "Non la uso per scelta: voglio che i miei studenti pensino con la propria testa prima."
- "Non so usarla, quindi evito."

**Non confondere con**
- `S4` (erosione pensiero critico): se il non uso e' motivato da paura di danno cognitivo per se' o gli altri, si aggiunge `S4`.
- `A1`: se il non uso e' attribuito alla mancata formazione, si aggiunge `A1`.

**Ancoraggi empirici**
- profili di non uso tra studenti (uso strumentale/evasivo o astensione);
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

**Definizione operativa**
Mancanza di corsi, accompagnamento strutturato, inserimento curricolare o aggiornamento professionale sull'IA.

**Indicatori lessicali**
- "nessuno ci ha formato"; "l'universita' non tratta il tema"; "mancano corsi"; "autoformazione"; "imparato da solo"; "non c'e' nessun piano"; "neanche un'ora al SSIS/TFA".

**Esempi di segmento**
- "All'universita' nessuno ce ne ha mai parlato, ho imparato da sola su YouTube."

**Non confondere con**
- `A2`: `A1` = assenza totale; `A2` = supporto esiste ma inadeguato.
- `R1`: se il segmento parla solo della propria incompetenza senza attribuirla al sistema, resta `R1`.

#### A2. Supporto insufficiente o diseguale

**Definizione operativa**
Supporto esistente ma percepito come sporadico, tardivo, frammentario, diseguale tra scuole/regioni/dipartimenti, o dipendente da singoli colleghi volenterosi.

**Indicatori lessicali**
- "qualche corso c'e' stato, ma..."; "dipende dalla scuola"; "un collega ci ha fatto vedere"; "giornata spot"; "corso opzionale"; "solo chi gia' ne sa si iscrive"; "non sistematico".

**Esempi di segmento**
- "Un corso l'hanno fatto, ma era di due ore e introduttivo, roba inutile."
- "Da noi la scuola vicina ha un corso, qui niente."

**Non confondere con**
- `A1`: se la formazione manca del tutto, `A1`.

#### A3. Vincoli infrastrutturali ed economici

**Definizione operativa**
Ostacoli materiali all'uso: dispositivi insufficienti, connessione debole, licenze a pagamento, paywall, LIM obsolete, aule informatiche contese, blocchi di rete scolastica, Carta del Docente non applicabile.

**Indicatori lessicali**
- "non ci sono PC"; "la rete cade"; "la versione gratis non basta"; "Carta del Docente non copre"; "a pagamento"; "LIM vecchia"; "aula informatica sempre occupata"; "bloccato dalla rete scolastica".

**Esempi di segmento**
- "Le app buone sono a pagamento e la Carta del Docente non le copre."
- "In aula la connessione non regge."

**Non confondere con**
- `A2`: `A3` e' vincolo materiale; `A2` e' inadeguatezza della formazione/supporto umano.

**Ancoraggi empirici**
- docenti in servizio con classi numerose e LIM obsolete;
- studenti universitari con paywall sui tool premium.

#### A4. Uso compensativo dell'IA

**Definizione operativa**
L'IA viene usata per colmare lacune del sistema formativo o didattico: materiali scolastici insufficienti, sostegno non assegnato, libri poco chiari, docenti che non spiegano.

**Indicatori lessicali**
- "il libro non spiega bene"; "le slide non c'erano"; "il prof non l'ha detto"; "non avevamo sostegno"; "quello che a scuola manca"; "supplisce a...".

**Esempi di segmento**
- "Quando il libro non mi spiega bene, lo chiedo a ChatGPT."
- "Per il bambino BES non c'e' sostegno, uso l'IA per i materiali adattati."

**Non confondere con**
- `P2`/`P3`: `A4` aggiunge la dimensione di **compensazione di una mancanza sistemica**; se la pratica e' individualizzazione ordinaria, resta `P2` o `P3`.

**Ancoraggi empirici**
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

**Definizione operativa**
Aspettativa che l'IA velocizzi, alleggerisca o ottimizzi il lavoro (preparazione, correzione, ricerca).

**Indicatori lessicali**
- "risparmio tempo"; "piu' veloce"; "snellisce"; "in pochi minuti"; "alleggerisce il carico"; "mi fa guadagnare tempo"; "e' rapido"; "riduce il lavoro di preparazione".

**Esempi di segmento**
- "Con l'IA preparo una verifica in dieci minuti invece che in un'ora."

**Non confondere con**
- `P5` (strategia produttiva): `X1` e' l'**aspettativa di beneficio**; `P5` e' la pratica che lo produce.

#### X2. Semplificazione e comprensione

**Definizione operativa**
Aspettativa che l'IA chiarifichi concetti difficili, abbassi la curva di comprensione, metta a fuoco i nuclei di un contenuto.

**Indicatori lessicali**
- "rende piu' chiaro"; "spiega in modo semplice"; "aiuta a capire"; "sintetizza il concetto"; "in parole povere"; "fa capire meglio"; "focalizza".

**Esempi di segmento**
- "Mi aspetto che sappia spiegarmi la mitosi meglio del manuale."

**Non confondere con**
- `P5`: trasformare un testo in riassunto e' pratica (`P5`); aspettarsi che cosi' si capisca meglio e' `X2`.

#### X3. Personalizzazione e attenzione al singolo

**Definizione operativa**
Aspettativa che l'IA consenta una modulazione piu' fine sul singolo studente o sul singolo percorso, attenuando la logica di classe indifferenziata.

**Indicatori lessicali**
- "un percorso su misura"; "si adatta al ragazzo"; "finalmente attenzione al singolo"; "livello personalizzato"; "la classe non e' piu' tutta uguale".

**Esempi di segmento**
- "In futuro ogni studente potra' avere un tutor personalizzato."

**Non confondere con**
- `P2`: pratica gia' in atto e' `P2`. Desiderio o previsione e' `X3`.

#### X4. Inclusione e accesso

**Definizione operativa**
Aspettativa di maggiore equita', accessibilita' e adattamento per studenti con bisogni diversi (BES, DSA, disabilita', stranieri, svantaggio socio-economico).

**Indicatori lessicali**
- "aiuta chi fa fatica"; "livella le differenze"; "da' a tutti la stessa possibilita'"; "piu' inclusiva"; "abbatte barriere"; "arriva anche a chi resta indietro".

**Esempi di segmento**
- "Spero che con l'IA anche i ragazzi stranieri riescano a seguire come gli altri."

**Non confondere con**
- `P3`: la pratica di inclusione e' `P3`. L'aspettativa di beneficio inclusivo futuro e' `X4`.

#### X5. Autonomia, organizzazione e supporto al percorso

**Definizione operativa**
Aspettativa che l'IA migliori organizzazione dello studio, autocorrezione, pianificazione, gestione autonoma del carico di lavoro.

**Indicatori lessicali**
- "mi organizzo meglio"; "mi aiuta a pianificare"; "mi correggo da solo"; "autonomia nello studio"; "gestire il tempo"; "seguire il mio ritmo".

**Esempi di segmento**
- "Con l'IA riesco a pianificarmi la sessione d'esame in modo piu' intelligente."

**Non confondere con**
- `P4`: esercitarsi e simulare e' pratica (`P4`). L'aspettativa di una maggiore autonomia e' `X5`.

#### X6. Coinvolgimento, arricchimento e innovazione

**Definizione operativa**
Aspettativa di maggiore interesse degli studenti, varieta' delle attivita', arricchimento dei materiali, rinnovamento delle pratiche didattiche.

**Indicatori lessicali**
- "piu' coinvolgente"; "lezioni piu' vive"; "gli studenti si appassionano"; "rinnovare la didattica"; "rompere la routine"; "attivita' nuove"; "varieta'"; "creativita' didattica".

**Esempi di segmento**
- "Penso che con l'IA si possano fare lezioni piu' coinvolgenti per i ragazzi."

**Non confondere con**
- `X1`: `X1` e' sul **tempo dell'insegnante**; `X6` e' sulla **qualita' dell'esperienza dello studente**.

#### X7. Cambiamento condizionato

**Definizione operativa**
Apertura positiva al cambiamento accompagnata da condizioni esplicite: uso critico, supervisione umana, limiti chiari, verifica.

**Indicatori lessicali**
- "puo' essere utile se..."; "a patto che..."; "purche' controllata"; "dipende da come la si usa"; "bene, ma con criterio"; "non da sola, ma con il docente"; "se la si sa usare".

**Esempi di segmento**
- "Puo' essere una rivoluzione positiva, ma solo se resta sotto controllo umano."

**Non confondere con**
- `I1`: `X7` e' l'**aspettativa condizionata di cambiamento**; `I1` e' la **postura di fiducia tecnica**. Co-occorrono spesso.
- `S7`: se il segmento indica un **divieto** di uso in certi ambiti, prevale `S7`.

**Ancoraggi empirici**
- futuri docenti (posizione dominante nel corpus).

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

**Definizione operativa**
L'IA e' considerata utile, ma la sua affidabilita' e' subordinata a verifica, controllo o uso entro limiti precisi.

**Indicatori lessicali**
- "e' utile ma va controllata"; "non mi fido ciecamente"; "bisogna verificare"; "sempre con revisione"; "mi fido in parte"; "uso ma controllo".

**Esempi di segmento**
- "Mi aiuta molto, ma non pubblicherei mai un suo testo senza averlo letto."

**Non confondere con**
- `R2`: `R2` e' **sapere** che l'IA ha limiti; `I1` e' la **postura pratica** che ne deriva.
- `I2`: `I1` esprime fiducia condizionata; `I2` esprime sfiducia prevalente.

#### I2. Sfiducia tecnica

**Definizione operativa**
Sfiducia dominante nell'affidabilita' dell'output: errori, allucinazioni, approssimazioni, traduzioni scorrette, citazioni inventate, calcoli sbagliati.

**Indicatori lessicali**
- "sbaglia spesso"; "si inventa"; "allucina"; "citazioni finte"; "traduce male il greco/latino"; "non sa la matematica"; "mi ha dato una versione sbagliata"; "dati inventati".

**Esempi di segmento**
- "Per il latino non la uso, inventa la traduzione."
- "Mi ha citato un articolo che non esiste."

**Non confondere con**
- `S5` (informazioni false): `I2` e' **giudizio di affidabilita'** sull'output; `S5` e' **timore normativo** di danno da disinformazione.
- `R2`: `R2` e' consapevolezza epistemologica; `I2` e' valutazione concreta su casi vissuti.

**Ancoraggi empirici**
- studenti su latino, greco, matematica;
- docenti su bias e output opachi.

#### I3. Fiducia o sfiducia negli utenti

**Definizione operativa**
Giudizio sulla capacita' degli altri utenti (studenti, colleghi, docenti) di usare l'IA in modo etico, responsabile, non sostitutivo.

**Indicatori lessicali**
- "gli studenti la useranno per copiare"; "i ragazzi non sanno usarla bene"; "i colleghi non ne sanno nulla"; "dipende dall'utente"; "serve educazione all'uso"; "i piu' giovani se ne abusano".

**Esempi di segmento**
- "Il problema non e' lo strumento, ma chi lo usa: i ragazzi la usano per non studiare."

**Non confondere con**
- `S2`: `I3` e' un **giudizio generale** di affidabilita' sugli utenti; `S2` e' il **divieto specifico** del ghostwriting.

#### I4. Fiducia relazionale e pedagogica

**Definizione operativa**
Affermazione esplicita dell'insostituibilita' della relazione educativa, dell'empatia, del giudizio umano, dell'incontro in classe.

**Indicatori lessicali**
- "l'insegnante non si sostituisce"; "l'empatia non si replica"; "lo sguardo umano"; "la relazione educativa"; "l'IA non capira' mai lo studente davvero"; "c'e' bisogno del rapporto umano".

**Esempi di segmento**
- "Un'IA puo' spiegare, ma non puo' capire quando un ragazzo ha bisogno di essere ascoltato."

**Non confondere con**
- `S6`: `I4` e' **affermazione positiva** del ruolo umano; `S6` e' **paura attiva** di sostituzione.

#### I5. Privacy e affidamento dei dati

**Definizione operativa**
Preoccupazioni o giudizi sul trattamento dei dati personali, delle immagini degli studenti, dei contenuti caricati.

**Indicatori lessicali**
- "privacy"; "dati personali"; "GDPR"; "non carico cose dei miei alunni"; "non si sa dove vanno a finire i dati"; "foto degli studenti no"; "non mi fido a caricare".

**Esempi di segmento**
- "Non carico mai compiti degli studenti: chi mi dice dove finiscono quei dati?"

**Non confondere con**
- `A3`: `A3` e' vincolo infrastrutturale; `I5` e' giudizio sulla gestione dei dati.
- `S7`: se il segmento pone un **divieto** normativo ("qui non va usata"), si aggiunge `S7`.

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

**Definizione operativa**
Timore che l'IA faccia al posto del soggetto il lavoro mentale, generando dipendenza e passivita'.

**Indicatori lessicali**
- "pigrizia"; "dipendenza"; "non fare piu' nulla da soli"; "anestetizza il cervello"; "smettiamo di pensare"; "delega totale"; "non si fatica piu'".

**Esempi di segmento**
- "Il rischio e' che i ragazzi non si sforzino piu' perche' tanto la risposta la da' lei."

**Non confondere con**
- `S4`: `S1` e' **ridurre lo sforzo**; `S4` e' **perdere la capacita' di analisi critica**. `S1` e' la causa operativa, `S4` l'effetto cognitivo piu' profondo.
- `S2`: `S2` e' specifica del ghostwriting su testi.

#### S2. Ghostwriting e plagio

**Definizione operativa**
Rifiuto dell'uso dell'IA per produrre testi, temi, tesi, elaborati o compiti che vengano poi spacciati come propri.

**Indicatori lessicali**
- "scrivere la tesi al posto mio"; "copia-incolla del tema"; "spacciarlo come proprio"; "fare il compito al posto loro"; "l'elaborato non l'ha scritto lui"; "plagio"; "disonesta' accademica".

**Esempi di segmento**
- "Va bene per aiutare, non per farsi scrivere la tesi."
- "Il problema sono gli studenti che si fanno fare i temi dall'IA."

**Non confondere con**
- `S1`: `S1` e' riduzione generica dello sforzo; `S2` e' specificamente consegnare un output come proprio.
- `I3`: `I3` e' giudizio generale sugli utenti; `S2` e' il **divieto** sulla pratica specifica.

#### S3. Appiattimento, omologazione, perdita di creativita'

**Definizione operativa**
Timore di uniformazione degli output, impoverimento espressivo, perdita di voce personale, standardizzazione dei prodotti.

**Indicatori lessicali**
- "tutti gli elaborati sembrano uguali"; "si riconosce lo stile IA"; "impoverisce la creativita'"; "omologa"; "appiattisce"; "perdita di originalita'"; "stesso registro ovunque".

**Esempi di segmento**
- "Alla fine tutti i temi scritti con l'IA si somigliano."

**Non confondere con**
- `S4`: `S3` e' sull'**output** e sullo stile; `S4` e' sul **pensiero** di chi lo produce.

#### S4. Erosione del pensiero critico

**Definizione operativa**
Timore che l'IA riduca capacita' di analisi autonoma, riflessione, comprensione profonda, sforzo cognitivo sostenuto.

**Indicatori lessicali**
- "non pensano piu' con la propria testa"; "perdono il senso critico"; "non analizzano"; "non approfondiscono"; "saltano la riflessione"; "non sviluppano il ragionamento".

**Esempi di segmento**
- "Il problema e' che i ragazzi non sviluppano piu' il senso critico."

**Non confondere con**
- `S1`: vedi sopra.
- `S3`: `S3` riguarda il prodotto; `S4` il processo cognitivo.

#### S5. Informazioni false, imprecisione, affidabilita' debole

**Definizione operativa**
Timore (spesso con valenza normativa) che l'IA produca errori, allucinazioni, disinformazione o contenuti non verificati spacciati come affidabili.

**Indicatori lessicali**
- "da' informazioni sbagliate"; "disinformazione"; "non si puo' fidare"; "fake news"; "allucinazioni pericolose"; "rischio di imparare cose sbagliate"; "verifiche necessarie".

**Esempi di segmento**
- "Il rischio e' che gli studenti prendano per buono quello che dice senza verificare."

**Non confondere con**
- `I2`: `I2` e' **giudizio di affidabilita'** basato su osservazione; `S5` e' il **timore normativo** degli effetti della disinformazione.

#### S6. Sostituzione del docente o della relazione educativa

**Definizione operativa**
Paura che l'IA occupi impropriamente spazi di insegnamento, accompagnamento, mediazione umana; timore di perdere il ruolo professionale o la relazione educativa.

**Indicatori lessicali**
- "sostituisce l'insegnante"; "non serve piu' il prof"; "toglie il ruolo del docente"; "rimpiazza la relazione"; "perderemo il lavoro"; "diventeremo inutili"; "non c'e' piu' bisogno di noi".

**Esempi di segmento**
- "Il timore e' che in futuro non ci sia piu' bisogno degli insegnanti."

**Non confondere con**
- `I4`: `I4` e' affermazione dell'insostituibilita'; `S6` e' paura attiva della sostituzione. Co-occorrono spesso come due facce della stessa dimensione.

#### S7. Ambiti off-limits

**Definizione operativa**
Zone di esclusione d'uso, nominate esplicitamente come confini normativi: relazioni umane, scrittura soggettiva (diari, riflessioni personali), valutazione, lingue classiche, matematica avanzata, medicina, diagnosi, counseling, decisioni etiche.

**Indicatori lessicali**
- "qui non va usata"; "su questo no"; "per queste cose e' sbagliata"; "nessuno userebbe l'IA per..."; "in medicina/diagnosi/counseling no"; "il latino no"; "la valutazione no".

**Esempi di segmento**
- "Va bene per preparare materiali, ma la valutazione deve restare al docente."
- "Per le traduzioni dal greco non la userei: sbaglia e comunque e' un esercizio formativo."

**Non confondere con**
- `S2`: `S2` e' specificamente sul ghostwriting; `S7` copre altri ambiti normativamente esclusi.
- `I2`: `I2` e' giudizio di affidabilita'; `S7` aggiunge il **divieto** esplicito.

**Nota operativa**
`S7` si usa quando il partecipante delimita esplicitamente un confine normativo ("qui non va usata"), non quando esprime solo una cautela.

---

## 7. Matrice sintetica di co-occorrenza

Le co-occorrenze piu' frequenti attese nel corpus sono:

- `P + R`: quando una pratica mostra anche livello di competenza;
- `P + X`: quando l'uso concreto e' descritto come vantaggioso;
- `R + A`: quando la percezione di incompetenza e' attribuita alla mancanza di formazione;
- `I + S`: quando la sfiducia si traduce in timore o interdizione;
- `P + S`: quando una pratica e' citata come uso esistente ma non raccomandato;
- `P + I + S`: quando il partecipante descrive uso concreto, bisogno di verifica e rischio percepito nello stesso segmento;
- `P7 + R4`: quando un prompt riportato rivela anche livello di competenza di prompting;
- `I4 + S6`: quando l'insostituibilita' del docente e la paura di sostituzione compaiono insieme.

## 8. Esempi di applicazione

### Esempio 1
"Uso ChatGPT per semplificare testi per studenti DSA."

Codici:
- `P2` individualizzazione e personalizzazione
- `P3` inclusione e accessibilita'
- `P6` ecosistema di strumenti (ChatGPT nominato)

### Esempio 2
"Non lo uso nella didattica perche' non saprei formulare bene i prompt."

Codici:
- `R1` competenza pratica percepita
- `R4` competenza di prompting
- `R5` non-uso per impreparazione

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

### Esempio 5
"Le dico: 'Agisci come un docente di sostegno e semplificami questo testo per uno studente DSA'."

Codici:
- `P7` prompting visibile
- `P2` individualizzazione e personalizzazione
- `R4` competenza di prompting (uso del ruolo)

### Esempio 6
"Le app buone sono a pagamento e la rete scolastica blocca meta' dei siti."

Codici:
- `A3` vincoli infrastrutturali ed economici

## 9. Nota metodologica finale

Questo codebook e' pensato come strumento di codifica analitica condivisa, aperto a ulteriori affinamenti ma gia' stabilizzato nei suoi nuclei principali attraverso il confronto tra valutatori. Puo' essere ulteriormente sviluppato in due direzioni:

- maggiore granularita' interna ai sottocodici, se si passa alla microanalisi sistematica dei record;
- riduzione e accorpamento, se serve una versione piu' sintetica per articolo o appendice metodologica.

Il versionamento e gli aggiornamenti al codebook e alla mappa ID→profilo sono tracciati in `Praxis-ql/01-wiki/40-governance/log.md`.
