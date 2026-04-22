# Istruzioni Etichettatori PRAXIS (Label Studio)

## 1. Obiettivo

Completare la revisione umana dei task Label Studio assegnando i codici finali nel campo `human_codes` per ogni item.

Il lavoro di etichettatura serve a produrre la versione consolidata finale delle etichette per analisi qualitativa e tracciabilita' articolo.

## 2. Accesso a Label Studio (server remoto)

URL ufficiale:

- [https://l-studio.ai4educ.org/](https://l-studio.ai4educ.org/)

Nota importante: nella pagina [https://l-studio.ai4educ.org/user/login](https://l-studio.ai4educ.org/user/login) non e' disponibile l'auto-iscrizione libera. L'iscrizione e' possibile solo tramite link di invito con token (es. `/user/signup/?token=...`) fornito dal coordinatore.

Link di invito:

- [Invito Label Studio (token)](https://l-studio.ai4educ.org/user/signup/?token=Tu57k1cMfM5xzyTk54aZofLwIMqtaxmEqSfsPqJS)
- Se il link risulta scaduto/non valido, richiedere al coordinatore un nuovo link di invito.

Passi di accesso:

1. Aprire il link nel browser.
2. Fare login con le credenziali fornite dal coordinatore.
3. Se richiesto al primo accesso, completare cambio password/profilo.
4. Aprire il progetto:
   - PRAXIS Human Review FULL 20260421-233900

Se non vedi il progetto o ricevi errore di permessi, contatta il coordinatore prima di iniziare.

## 3. Cosa fare una volta dentro

Nella lista task:

1. Filtrare i task non completati.
2. Aprire un task e leggere `question` + `answer`.
3. Usare `model_a_codes` e `model_b_codes` solo come suggerimento.
4. Selezionare uno o piu' codici in `human_codes`.
5. Salvare il task e passare al successivo.

Regole vincolanti:

- `human_codes` non deve mai restare vuoto.
- La multi-codifica e' consentita quando il testo contiene chiaramente piu' dimensioni.
- Non attribuire codici senza evidenza testuale esplicita.
- In caso di dubbio, applicare il codebook; se resta ambiguita', registrare il caso nel registro dubbi.

## 4. Dove trovare le istruzioni del codebook (Quartz)

Documenti da consultare (ordine consigliato), con collegamenti interni Quartz:

1. Codebook PRAXIS:
   - [Codebook PRAXIS](../../05-documentazione/codebook-praxis.md)
   - riferimento principale per definizioni operative e distinzione tra codici.
2. Quadro PRAXIS (framework alto livello):
   - [Framework PRAXIS](../../01-wiki/10-framework/praxis-framework.md)
   - quadro P/R/A/X/I/S.
3. Registro decisionale wiki-vs-label:
   - [Registro decisionale wiki-vs-label](../../01-wiki/40-governance/decision-log-wiki-vs-label.md)
   - casi ambigui gia' risolti e decisioni da riusare.
4. Mappa ID-profili (uso interno):
   - [Mappa ID-profili](../../05-documentazione/codebook-id-map.md)
   - supporto di tracciabilita' per audit interni.

Indice documentazione Quartz:

- [Indice documentazione](../../05-documentazione/index.md)

## 5. Uso dei codici N1

Usare i codici N1 solo quando non e' possibile assegnare in modo affidabile codici sostantivi P/R/A/X/I/S:

- `N1a`: risposta troppo breve o non informativa
- `N1b`: risposta fuori tema rispetto alla domanda
- `N1c`: risposta tautologica o meta-definizione

Nota: dove possibile privilegiare codici sostantivi; N1 e' una categoria di fallback.

## 6. Gestione dubbi e casi difficili

Quando un task e' ambiguo:

1. completare comunque la codifica migliore possibile;
2. aggiungere una nota nel task Label Studio (commento o campo note, se presente);
3. segnalare al coordinatore i casi ad alta incertezza.

Il coordinatore decide se aprire/aggiornare una decisione ufficiale in:

- [Registro decisionale wiki-vs-label](../../01-wiki/40-governance/decision-log-wiki-vs-label.md)

## 7. Criteri di chiusura lavoro

Prima della chiusura:

- nessun task lasciato senza `human_codes`;
- copertura 100% dei task assegnati;
- tutti i dubbi rilevanti registrati.

Export finale (a cura del coordinatore):

- formato: JSON o JSON-MIN;
- destinazione: [Cartella exports](./exports/);
- naming consigliato: human-review-full-YYYYMMDD-HHMM.json.
