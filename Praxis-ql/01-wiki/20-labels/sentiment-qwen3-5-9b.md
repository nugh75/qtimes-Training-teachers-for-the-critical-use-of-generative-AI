# Sentiment + Emozioni Qwen3.5 9B per Coorte

Questa pagina riassume l'esecuzione `sentiment+emozioni` sul corpus PRAXIS con `qwen3.5:9b`.

## Metodo (breve)

- Modello: `qwen3.5:9b` via Ollama remoto.
- Modalita': `thinking=False` (no-thinking).
- Unita' analizzata: solo il testo della risposta (`A`) per ogni item.
- Classi sentiment: `positive`, `neutral`, `negative`.
- Emozioni tracciate: `gioia`, `entusiasmo`, `fiducia`, `sollievo`, `curiosita`, `sorpresa`, `preoccupazione`, `ansia`, `paura`, `frustrazione`, `rabbia`, `tristezza`.
- Coorti: insegnanti in servizio, insegnanti pre-service, studenti.

## Risultati per coorte

Fonte: [summary_by_cohort.csv](../../04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/summary_by_cohort.csv)

| Coorte | Item totali | Positive | Neutral | Negative | Emozioni totali | Avg emozioni/item | Avg score | Avg confidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| insegnanti_in_servizio | 2220 | 598 | 1105 | 517 | 1417 | 0.638288 | 0.040775 | 0.868689 |
| insegnanti_pre_service | 502 | 77 | 331 | 94 | 218 | 0.434263 | -0.016235 | 0.868884 |
| studenti | 1895 | 635 | 886 | 374 | 1175 | 0.620053 | 0.118596 | 0.864396 |

## Totale complessivo

- Item totali: 4617
- Positive: 1310
- Neutral: 2322
- Negative: 985
- Emozioni totali: 2810
- Avg emozioni/item: 0.608620
- Avg score (pesata): 0.066517
- Avg confidence (pesata): 0.866948

## Emozioni piu' frequenti (totale)

- preoccupazione: 797
- fiducia: 650
- frustrazione: 448
- entusiasmo: 254
- sollievo: 179

## Output utili

- Dashboard React: [Dashboard sentiment Qwen 3.5 9B](../30-visualizzazioni/sentiment-qwen-dashboard.md)
- Dettaglio item globale CSV: [all_items_sentiment_emotions.csv](../../04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/all_items_sentiment_emotions.csv)
- Dettaglio item globale JSONL: [all_items_sentiment_emotions.jsonl](../../04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/all_items_sentiment_emotions.jsonl)
- CSV separati per coorte: [by_cohort](../../04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/by_cohort/)
- Distribuzione emozioni per coorte: [summary_emotions_by_cohort.csv](../../04-label/labels/ollama-qwen3-5-9b-sentiment-emotions/summary_emotions_by_cohort.csv)

## Nota

Questa analisi e' descrittiva e non sostituisce la codifica qualitativa PRAXIS. Va letta come supporto esplorativo per pattern trasversali tra coorti.
