# Pipeline Canonica `dati -> corpus` (PRAXIS)

**Versione**: 1.0  
**Data**: 2026-04-21  
**Scopo**: rendere riproducibile e verificabile la catena che parte dai dati immutabili (`dati/`) e arriva al corpus operativo.

## 1. Principi

1. `dati/` e' la sorgente di verita' empirica ed e' immutabile.
2. `02-corpus/` e' derivato e operativo.
3. La fase `dati -> corpus` deve essere deterministica (stessi input, stessi stem, stesso numero record).
4. Le eccezioni di naming storico sono esplicite in `corpus-stem-overrides.json`.

## 2. Input ufficiali

- `dati/Inseganti-attuali.xlsx`
- `dati/Inseganti-futuri.xlsx`
- `dati/Studenti.xlsx`

## 3. Step A - Build iniziale del corpus

Script canonico:

```bash
python3 ../scripts/build_corpus_from_dati.py \
  --dati-dir ../dati \
  --output-dir corpus \
  --manifest-out 04-label/labels/corpus-build-manifest.json \
  --write \
  --overwrite
```

Note:
- senza `--write` il comando e' dry-run (nessuna scrittura);
- `--overwrite` e' richiesto se i file esistono gia';
- il formato prodotto e' compatibile con il parser legacy di `label_raw_with_ollama.py`.

## 4. Step B - Etichettatura LLM sul corpus

Esempio:

```bash
python3 ../scripts/label_raw_with_ollama.py \
  --input-dir corpus \
  --model gemma4:e4b \
  --workers 2
```

Output atteso: `04-label/labels/ollama-*/`.

## 5. Step C - Ristrutturazione item-based del corpus

Conversione dei markdown in formato item-based con anchor e legenda:

```bash
python3 ../scripts/restructure_raw_to_items.py --all --write
```

Output atteso: file in `02-corpus/*.md` con blocchi:

- frontmatter
- `## Item N {#item-N}`
- `**Q**`, `**A**`, `**Codes**`, `**Reason**`

## 6. Verifiche minime di riproducibilita'

1. Il manifest `04-label/labels/corpus-build-manifest.json` deve esistere.
2. `records_total` nel manifest deve essere coerente con i file `*.md` generati dal build.
3. Le eccezioni di naming usate dal build devono essere tracciate in `skipped/overrides_used`.
4. Gli script a valle (`label_raw_with_ollama.py`, `restructure_raw_to_items.py`) devono poter processare i file senza parse error.

## 7. Compatibilita' storica

- Override stem legacy: `corpus-stem-overrides.json`.
- Fase Opus: storica, documentata separatamente come non pienamente riproducibile.
