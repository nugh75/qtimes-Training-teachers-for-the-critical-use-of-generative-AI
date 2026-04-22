---
title: Dashboard sentiment + emozioni Qwen 3.5 9B
aliases:
  - visualizzazione sentiment coorti
tags:
  - labels
  - sentiment
  - emozioni
  - visualizzazioni
---

# Dashboard sentiment + emozioni per coorte

Questa pagina raccoglie la visualizzazione React dei risultati di sentiment+emozioni ottenuti con modello Qwen 3.5 9B sul corpus PRAXIS.

## Accesso dashboard

- Dashboard interattiva: https://ai-qual.ai4educ.org/viz/sentiment/
- Report sintetico (tabella e metodo): [[sentiment-qwen3-5-9b]]

## Cosa mostra

- Distribuzione positive/neutral/negative per ciascuna coorte.
- Confronto tra avg score e avg confidence per coorte.
- Frequenza emozioni sul corpus e top emozioni per coorte.
- KPI globali su tutto il corpus analizzato (incluso avg emozioni/item).

## Note metodologiche

- Unita di analisi: item (una risposta alla volta).
- Testo usato per classificazione: solo campo risposta (A).
- Prompt in modalita no-thinking.
- Questo livello e descrittivo e non sostituisce la codifica qualitativa PRAXIS.

## Dati sorgente

- `Praxis-ql/04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/summary_by_cohort.csv`
- `Praxis-ql/04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/summary_emotions_by_cohort.csv`
- `Praxis-ql/04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/all_items_sentiment_emotions.csv`
- `Praxis-ql/04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/all_items_sentiment_emotions.jsonl`
