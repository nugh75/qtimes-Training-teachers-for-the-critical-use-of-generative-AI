# Proposta estensione sentiment + emozioni (Qwen)

**Summary**: Proposta operativa per evolvere lo script attuale da sentiment a sentiment+emozioni mantenendo coerenza con il framework PRAXIS e con la pipeline corpus esistente.

**Sources**: `scripts/sentiment_qwen_by_cohort.py`, `Praxis-ql/02-corpus/`, `Praxis-ql/04-label/labels/ollama-qwen3-5-9b-sentiment/`

**Last updated**: 2026-04-22

---

## 1) Obiettivo

Passare da una classificazione solo `positive|neutral|negative` a una lettura piu' articolata:

- sentiment (come oggi);
- emozioni principali espresse nel testo;
- evidenza testuale minima per audit qualitativo.

L'output resta descrittivo e di supporto alla lettura qualitativa, non sostitutivo della codifica PRAXIS.

## 2) Stato attuale sintetico

Lo script corrente:

- analizza item per item solo sul campo risposta `A`;
- produce sentiment, score, confidence, reason;
- aggrega CSV/JSONL globali e per coorte.

Questo impianto e' gia' solido per estendere il payload con un livello emozionale.

## 3) Proposta di schema (v1)

Per ogni item mantenere il blocco sentiment e aggiungere `emotions`:

```json
{
  "index": 4,
  "sentiment": "negative",
  "score": -0.62,
  "confidence": 0.84,
  "reason": "Percezione di rischio e perdita di controllo.",
  "emotions": [
    {
      "label": "frustrazione",
      "intensity": "alta",
      "confidence": 0.79,
      "evidence": "non riesco a gestire la classe con questi strumenti"
    },
    {
      "label": "ansia",
      "intensity": "media",
      "confidence": 0.66,
      "evidence": "ho paura di sbagliare davanti agli studenti"
    }
  ]
}
```

Regole:

- massimo 2 emozioni per item (`primary` + `secondary` implicite dall'ordine);
- `intensity` ordinale: `bassa|media|alta`;
- `evidence` deve essere una micro-citazione del solo campo `A`;
- se nessuna emozione e' rilevabile: `emotions: []` e motivo esplicito in `reason`.

## 4) Tassonomia emozioni consigliata

Set iniziale compatto (12 etichette):

- `gioia`
- `entusiasmo`
- `fiducia`
- `sollievo`
- `curiosita`
- `sorpresa`
- `preoccupazione`
- `ansia`
- `paura`
- `frustrazione`
- `rabbia`
- `tristezza`

Nota: e' una tassonomia operativa per labeling, non una teoria psicometrica.

## 5) Modifiche tecniche allo script

Estensione minima di `scripts/sentiment_qwen_by_cohort.py`:

- nuovo prompt con schema JSON che includa `emotions`;
- validatori aggiuntivi (`VALID_EMOTIONS`, `VALID_INTENSITY`);
- sanitizzazione robusta di label/intensity/evidence;
- nuovi output aggregati:
- `all_items_sentiment_emotions.csv`
- `all_items_sentiment_emotions.jsonl`
- `summary_emotions_by_cohort.csv`
- `summary_emotions_by_question.csv`
- nuova `schema_version` nel JSON record per retrocompatibilita'.

CLI consigliata:

- `--mode sentiment|sentiment_emotions` (default: `sentiment`);
- `--max-emotions 2`;
- `--output-dir` separato (es. `ollama-qwen3-5-9b-sentiment-emotions`).

## 6) Qualita' e audit

Controlli proposti:

- fallback a `emotions: []` su output modello invalido;
- file `failures.json` come gia' in uso;
- campione di revisione umana mirato su:
- item con `confidence < 0.55`;
- item con `sentiment=neutral` ma emozioni negative forti;
- item con evidenza mancante o troppo generica.

## 7) Piano di adozione

Fase 1 (pilot tecnico):

- run su 30-50 record con `--limit`;
- verifica validita' JSON, copertura item e qualita' delle evidenze.

Fase 2 (run completo):

- esecuzione full corpus su `Praxis-ql/02-corpus/`;
- produzione aggregati per coorte e domanda.

Fase 3 (integrazione analitica):

- aggiornamento pagina labels/wiki e dashboard sentiment;
- confronto qualitativo tra PRAXIS codes e segnali emozionali.

## 8) Beneficio atteso

La pipeline rimane leggera ma guadagna un livello interpretativo utile per leggere tono emotivo, tensioni e risorse percepite nelle tre coorti, con tracciabilita' item-level.
