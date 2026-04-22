# Runbook Revisione Umana (Label Studio)

## 1. Obiettivo

Consolidare una codifica umana finale per tutti i 4702 item del corpus PRAXIS.

Istruzioni operative per gli etichettatori:

- `04-label/labelstudio/istruzioni-etichettatori.md`

## 2. Bundle da usare

Usare il bundle full:

- `04-label/labelstudio/review-bundle-full-20260421-233900/`

## 3. Avvio stack Label Studio

Da `Praxis-ql/04-label/labelstudio`:

```bash
docker compose up -d
```

## 4. Creazione progetto e import task (via API)

Prerequisiti:

- URL API Label Studio (es. `http://localhost:8082`)
- token personale

Esempio:

```bash
python3 ../../scripts/build_labelstudio_review_bundle.py \
  --csv ../labels/double-coding-item-agreement-20260421-212336.csv \
  --out-dir review-bundle-full-20260421-233900 \
  --api-url http://localhost:8082 \
  --api-token <TOKEN>
```

In alternativa usare i payload gia' pronti in `review-bundle-full-20260421-233900/`.

## 5. Regole operative di annotazione

1. Ogni task deve avere una scelta `human_codes` non vuota.
2. In caso di dubbio tra wiki e label automatica, applicare decisione caso per caso.
3. Ogni conflitto va registrato nel registro decisionale (passo 6 del progetto).
4. Non chiudere il progetto finche' la copertura non raggiunge il 100% dei task.

## 6. Uscita attesa

Export JSON da Label Studio con annotazioni umane complete, da usare per:

- consolidamento etichette finali;
- audit di coerenza;
- tabella di tracciabilita' articolo.

## 7. Checklist per colleghi (operativa)

1. Aprire il progetto Label Studio full.
2. Filtrare task non completati.
3. Compilare `human_codes` su ogni task assegnato.
4. Verificare che non restino task senza annotazione.
5. Eseguire export finale in JSON (o JSON-MIN) dal pannello Export.
6. Salvare l'export nel repository in `04-label/labelstudio/exports/` con timestamp.
7. Comunicare il path del file export per consolidamento finale.
8. Segnalare i casi ambigui nel task Label Studio (commento o note) e al coordinatore.
