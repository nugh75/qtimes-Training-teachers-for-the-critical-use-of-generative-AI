# Prompt engineering avanzato
**Dimensione**: Modelli d'uso (P)
**Popolazione**: Insegnanti Attuali

**Summary**: Tra gli early adopter emerge un prompt engineering pedagogicamente orientato che va oltre la semplice domanda. Il corpus documenta un gradiente di sofisticazione: dai prompt minimali ("*crea una verifica*") a strutture complesse che assegnano un ruolo all'IA, specificano il profilo della classe, il livello di difficoltà, il formato atteso e persino il tipo di feedback. La generazione di verifiche e quiz domina, ma si osservano anche prompt multimodali (immagini, video, schemi) e prompt iterativi dove il docente parte da materiale proprio e chiede all'IA di espanderlo. La maggioranza dei rispondenti, tuttavia, resta a un livello basilare — il prompt come domanda diretta, senza struttura né ruolo.

**Sources**: 16 risposte raw (vedi citazioni nel testo).

**Last updated**: 2026-04-19

---

## Il gradiente di sofisticazione

La distanza tra i prompt più semplici e quelli più elaborati nel corpus è enorme. Si va da un docente che chiede semplicemente una ricerca — "*Ricerca informazioni sugli stambecchi italiani, tenendo presente che devono emozionare bambini di seconda primaria*" (source: [uzzi13](../../../raw/insegnanti_attuali_uzzi13.md)) — a chi costruisce richieste strutturate con parametri precisi: "*Crea un dialogo in 19 battute sull'importanza di una dieta sana per bambini di 7/8 anni*" (source: [erio24](../../../raw/insegnanti_attuali_erio24.md)), fino a chi usa l'IA per indagini euristiche: "*Controlla quante volte nell'ultimo mese è stata usata la parola gentrificazione negli articoli di n rivista*" (source: [fico70](../../../raw/insegnanti_attuali_fico70.md)). Tano01 descrive la propria metodologia: "*il prompt che di solito creo o è una domanda ben strutturata, oppure indico la tipologia di classe e studenti, l'argomento specifico, le caratteristiche di un eventuale questionario*" (source: [tano01](../../../raw/insegnanti_attuali_tano01.md)).

## L'assegnazione di ruolo

La tecnica più avanzata documentata è l'assegnazione esplicita di un ruolo all'IA. Anco27 costruisce un prompt che vincola il contesto: "*Sei un insegnante di italiano e devi creare cinque esercizi di difficoltà progressiva per la classe 3A sull'analisi del periodo, con focus specifico sul grado delle subordinate*" (source: [anco27](../../../raw/insegnanti_attuali_anco27.md)). Il prompt non chiede solo contenuti ma specifica chi è l'IA (un insegnante), cosa deve fare (creare esercizi), per chi (classe 3A), su cosa (analisi del periodo) e con quale vincolo (focus sulle subordinate). ELLA06 combina il ruolo con istruzioni multiple: "*Sei un docente di matematica del secondo liceo [...] ha semplificato il mio lavoro creando facilmente test e appunti semplificati anche per BES, permettendo di inserire molti più esempi*" (source: [ELLA06](../../../raw/insegnanti_attuali_ella06.md)). Capu15 applica la stessa logica in ambito informatico: "*sono un insegnante di informatica. Sto facendo un progetto Java con Swing e devo visualizzare delle immagini su un JFrame*" (source: [capu15](../../../raw/insegnanti_attuali_capu15.md)).

## La generazione di verifiche e quiz

L'uso dominante del prompt engineering nel corpus è la creazione di verifiche. I prompt mostrano un crescente livello di specificazione:

- Livello base — tipo di prova e argomento: "*Devo creare una verifica per ragazzi di terza superiore sulla Divina Commedia, ho bisogno di tre domande a risposta multipla*" (source: [damo20](../../../raw/insegnanti_attuali_damo20.md)).
- Livello intermedio — formato, numero di domande, fascia d'età e richiesta di spiegazione: "*Crea 5 domande a risposta aperta e 5 a risposta multipla sul primo canto dell'Odissea, adatte a studenti di prima media. Includi anche una breve spiegazione di ogni risposta corretta*" (source: [Stini27](../../../raw/insegnanti_attuali_stini27.md)).
- Livello avanzato — specificazione fine su formato e quantità: "*Creare un questionario di 30 domande a risposta chiusa per ragazzi di terza media sull'unità didattica dell'universo e sistema solare*" (source: [Ione](../../../raw/insegnanti_attuali_ione_2.md)).

Il pattern si ripete in ambiti disciplinari diversi: musica ("*Genera quiz sulla posizione delle note sul pentagramma in chiave di violino*" — source: [bani10](../../../raw/insegnanti_attuali_bani10.md)), scienze dei dati ("*Supponiamo di voler spiegare la correlazione multivariata, puoi fornirmi in forma tabulare i valori di quattro parametri biologici tra loro più o meno correlati positivamente o negativamente per 20 campioni?*" — source: [usso09](../../../raw/insegnanti_attuali_usso09.md)).

## Prompt multimodali

Un sottoinsieme di docenti specifica non solo il contenuto ma il formato dell'output. CATO05 chiede uno schema visivo calibrato sull'età: "*Genera uno schema adatto vedendo questo video per far capire ad un bambino di 8 anni le cause della I guerra mondiale*" (source: [CATO05](../../../raw/insegnanti_attuali_cato05.md)). Acci15 richiede presentazioni strutturate: "*Chiedo di creare una presentazione di x slides su un determinato argomento, includendo punti chiave ed immagini*" (source: [acci15](../../../raw/insegnanti_attuali_acci15.md)). Aisto30 formula un prompt in inglese che combina contenuto, accessibilità e formato multimediale: "*give some info about king Henry 8 Tudor, with also using photos and videos, for a student with SNE*" (source: [aisto30](../../../raw/insegnanti_attuali_aisto30.md)). Ogna07 compone un prompt visivo di notevole complessità: "*Crea un'immagine raffigurante la città di Leonia di Italo Calvino, inserendo le strade piene di rifiuti, con persone che trovano difficoltà a camminare sui marciapiedi e, sullo sfondo, alti palazzi, con luci molto colorate*" (source: [ogna07](../../../raw/insegnanti_attuali_ogna07.md)).

## Il prompt iterativo

Un pattern meno frequente ma significativo è quello del prompt iterativo: il docente non chiede all'IA di creare da zero ma di *espandere* materiale esistente. Tini20 descrive il processo: "*Ho creato già 20 domande (e le inserisco) puoi suggerirmi alternative sempre sullo stesso argomento con lo stesso livello di difficoltà? (E inserisco anche il testo PDF) alla fine verifico/modifico e integro le domande*" (source: [Tini20](../../../raw/insegnanti_attuali_tini20.md)). Qui il docente mantiene il controllo dell'intero processo: parte dalle proprie domande, chiede all'IA varianti calibrate, allega il materiale di riferimento e alla fine "verifica, modifica e integra". È il modello d'uso più maturo nel corpus, dove l'IA è un collaboratore subordinato e non un sostituto.

## Pagine correlate
- [Indice Practice Patterns](practice-patterns-insegnanti-attuali.md)
- [Piattaforme e role-playing](piattaforme-e-role-playing.md)
- [Individualizzazione BES/DSA](individualizzazione-bes-dsa.md)
- [Indice insegnanti attuali](../index-insegnanti-attuali.md)
