# Mappa ID → profilo partecipante (uso interno)

**Versione**: 1.0
**Data**: 2026-04-21
**Ruolo**: documento di servizio del codebook PRAXIS. Non sostituisce il codebook, ne garantisce tracciabilita' tra ID grezzi (file `02-corpus/`) e profili tipologici citati negli ancoraggi empirici.

## 1. Motivazione

Il codebook pubblico (`codebook-praxis.md`) descrive gli ancoraggi empirici dei sottocodici con profili tipologici (coorte + ruolo + tratto rilevante), non con ID di partecipanti. Questa scelta evita che un lettore esterno si imbatta in sigle opache come `santi13` o `Stini27` senza contesto interpretativo.

Gli ID restano tuttavia necessari per:

- verifica empirica interna al gruppo di ricerca;
- tracciabilita' tra citazioni del codebook e file grezzi del corpus in `02-corpus/`;
- revisione della codifica e audit inter-rater.

Per questo si mantiene qui una mappa ID → profilo, aggiornabile ma a uso interno.

## 2. Convenzioni

- **ID**: stringa di riferimento usata nei file `02-corpus/insegnanti_attuali_<ID>.md`, `02-corpus/insegnanti_futuri_<ID>.md`, `02-corpus/studenti_<ID>.md`.
- **Coorte**: una tra `docente in servizio`, `futuro docente`, `studente`.
- **Ruolo / ambito**: disciplina, ordine scolastico, area di lavoro o di studio.
- **Tratto rilevante**: caratteristica del profilo che motiva la citazione nel codebook (es. `esperienza BES/DSA`, `uso di CAA`, `classe NAI`, `non-uso consapevole`).
- **Sottocodici attivi**: sottocodici in cui il partecipante e' stato citato come ancoraggio empirico.

## 3. Mappa

| ID | Coorte | Ruolo / ambito | Tratto rilevante | Sottocodici attivi | File corpus |
|----|--------|----------------|------------------|--------------------|----------|
| `santi13` | docente in servizio | sostegno / inclusione | uso IA per CAA, individualizzazione BES/DSA | `P2`, `P3` | `02-corpus/insegnanti_attuali_santi13.md` |
| `Stini27` | docente in servizio | secondaria (letteratura) | prompt engineering intermedio, citazione su infrastrutture | `P1`, `P4`, `P5`, `P7`, `A3` | `02-corpus/insegnanti_attuali_stini27.md` |
| `ogri20` | docente in servizio | BES/DSA | individualizzazione e adattamento verifiche | `P2` | `02-corpus/insegnanti_attuali_ogri20.md` |
| `Ioli28` | docente in servizio | BES/DSA | personalizzazione testi e consegne | `P2` | `02-corpus/insegnanti_attuali_ioli28.md` |
| `anti03` | docente in servizio | sostegno / CAA | traduzione in pittogrammi, autismo non verbale | `P3` | `02-corpus/insegnanti_attuali_anti03.md` |
| `eddu02` | docente in servizio | sostegno | accessibilita' multimodale | `P3` | `02-corpus/insegnanti_attuali_eddu02.md` |
| `NALI26` | docente in servizio | italiano L2 / classi NAI | traduzioni per alunni neo-arrivati | `P3` | `02-corpus/insegnanti_attuali_nali26.md` |
| `damo20` | docente in servizio | secondaria (letteratura) | prompt engineering di base, verifica Divina Commedia | `P1`, `P7` | `02-corpus/insegnanti_attuali_damo20.md` |
| `Ione` | docente in servizio | scienze | prompt engineering avanzato (questionario astronomia) | `P1`, `P7` | `02-corpus/insegnanti_attuali_ione_2.md` |

> **Nota**: la tabella riporta **solo gli ID attualmente citati come ancoraggi empirici nel codebook e nelle pagine wiki collegate**. Quando un nuovo ID viene aggiunto o rimosso dal codebook, va aggiornata anche questa mappa.

## 4. Regole di aggiornamento

1. Ogni nuova citazione empirica inserita nel codebook con riferimento a un ID deve essere accompagnata da una riga in questa tabella. Se l'ID compare gia', se ne aggiornano i campi `Tratto rilevante` e `Sottocodici attivi`.
2. La compilazione dei campi avviene leggendo il file `02-corpus/` indicato e, quando utile, la pagina wiki di coorte collegata.
3. Se un profilo e' incerto, si lascia il campo vuoto con marcatore `da verificare` anziche' inferirlo.
4. Gli aggiornamenti strutturali (colonne, convenzioni) sono tracciati in `Praxis-ql/01-wiki/40-governance/log.md` sotto la stessa data.
5. Se un ID viene rimosso dal codebook, la riga resta qui come archivio storico con nota `non piu' citato dal codebook`.

## 5. Relazione con il codebook

- Il codebook resta leggibile da un lettore esterno senza questa mappa.
- I valutatori interni usano la mappa per risalire dal profilo tipologico al record di corpus, verificare la codifica e controllare la coerenza inter-rater.
- Quando un nuovo valutatore entra nel gruppo, la mappa serve come chiave di lettura del corpus insieme alla lista in `01-wiki/20-labels/labels-praxis.md`.
