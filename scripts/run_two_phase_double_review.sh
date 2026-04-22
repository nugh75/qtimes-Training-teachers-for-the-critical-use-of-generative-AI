#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRAXIS_DIR="$REPO_ROOT/Praxis-ql"
cd "$REPO_ROOT"

MODE="${1:-full}" # full | sample30
TS="$(date +%Y%m%d-%H%M%S)"

MODELS="${MODELS:-gemma4:e4b,qwen3.5:9b}"
WORKERS="${WORKERS:-1}"
TIMEOUT="${TIMEOUT:-300}"
HEARTBEAT_SECONDS="${HEARTBEAT_SECONDS:-30}"
OVERWRITE="${OVERWRITE:-0}"
LOG_QUEUED="${LOG_QUEUED:-0}"

# Phase-2 tuning
TARGET_TIMEOUT="${TARGET_TIMEOUT:-$TIMEOUT}"
TARGET_OVERWRITE="${TARGET_OVERWRITE:-0}"
TARGET_MAX_JACCARD="${TARGET_MAX_JACCARD:-0.9999}"

LOG_DIR="$PRAXIS_DIR/04-label/labels"
mkdir -p "$LOG_DIR"

PH1_LOG="$LOG_DIR/double-coding-${MODE}-${TS}.log"
PH1_JSON="$LOG_DIR/double-coding-agreement-${MODE}-${TS}.json"
PH1_CSV="$LOG_DIR/double-coding-item-agreement-${MODE}-${TS}.csv"

STEMS_FILE="$LOG_DIR/review-target-stems-${MODE}-${TS}.txt"
ITEMS_FILE="$LOG_DIR/review-target-items-${MODE}-${TS}.csv"

PH2_LOG="$LOG_DIR/double-coding-targeted-${MODE}-${TS}.log"
PH2_JSON="$LOG_DIR/double-coding-agreement-targeted-${MODE}-${TS}.json"
PH2_CSV="$LOG_DIR/double-coding-item-agreement-targeted-${MODE}-${TS}.csv"

MODE_ARGS=()
OVERWRITE_ARGS=()
QUEUE_ARGS=()
TARGET_OVERWRITE_ARGS=()

if [[ "$MODE" != "full" && "$MODE" != "sample30" ]]; then
  echo "Uso: $0 [full|sample30]" >&2
  exit 1
fi

if [[ "$OVERWRITE" == "1" ]]; then
  OVERWRITE_ARGS+=(--overwrite)
fi
if [[ "$LOG_QUEUED" == "1" ]]; then
  QUEUE_ARGS+=(--log-queued)
fi
if [[ "$TARGET_OVERWRITE" == "1" ]]; then
  TARGET_OVERWRITE_ARGS+=(--overwrite)
fi

if [[ "$MODE" == "sample30" ]]; then
  SAMPLE_JSON="$LOG_DIR/incoherent-review-sample-${TS}.json"
  SAMPLE_CSV="$LOG_DIR/incoherent-review-sample-${TS}.csv"
  SAMPLE_STEMS="/tmp/incoherent_sample_stems_${TS}.txt"

  python3 scripts/sample_incoherent_review.py \
    --sample-size 30 \
    --seed 42 \
    --json-out "$SAMPLE_JSON" \
    --csv-out "$SAMPLE_CSV"

  jq -r '.sample[].raw_stem' "$SAMPLE_JSON" | sort -u > "$SAMPLE_STEMS"
  MODE_ARGS+=(--stems-file "$SAMPLE_STEMS")
fi

echo "[check] Verifica modelli Ollama su server..."
python3 - "$MODELS" <<'PY'
import json
import sys
import urllib.request

models = [m.strip() for m in sys.argv[1].split(',') if m.strip()]
missing = []
try:
    with urllib.request.urlopen("http://192.168.129.14:11434/api/tags", timeout=10) as r:
        payload = json.load(r)
except Exception as exc:  # noqa: BLE001
    print(f"ERRORE: impossibile contattare Ollama: {exc}", file=sys.stderr)
    sys.exit(2)

available = {m.get("name", "") for m in payload.get("models", [])}
for model in models:
    if model not in available:
        missing.append(model)

if missing:
    print("ERRORE: modelli mancanti su Ollama: " + ", ".join(missing), file=sys.stderr)
    sys.exit(3)

print("OK: modelli disponibili -> " + ", ".join(models))
PY

echo
echo "[phase-1] Full review su corpus selezionato"
echo "Dettagli log: $PH1_LOG"
echo "Report JSON:  $PH1_JSON"
echo "Report CSV:   $PH1_CSV"
echo "Config: models=$MODELS workers=$WORKERS timeout=$TIMEOUT heartbeat=$HEARTBEAT_SECONDS overwrite=$OVERWRITE mode=$MODE"

python3 scripts/double_code_models.py \
  --models "$MODELS" \
  --workers "$WORKERS" \
  --timeout "$TIMEOUT" \
  --heartbeat-seconds "$HEARTBEAT_SECONDS" \
  --detailed-log "$PH1_LOG" \
  --json-out "$PH1_JSON" \
  --csv-out "$PH1_CSV" \
  "${OVERWRITE_ARGS[@]}" \
  "${QUEUE_ARGS[@]}" \
  "${MODE_ARGS[@]}"

echo
echo "[phase-2 prep] Costruzione target stems (N1 e/o disaccordo)"
python3 - "$PH1_CSV" "$STEMS_FILE" "$ITEMS_FILE" "$TARGET_MAX_JACCARD" <<'PY'
import csv
import re
import sys

csv_path = sys.argv[1]
stems_out = sys.argv[2]
items_out = sys.argv[3]
max_jaccard = float(sys.argv[4])

stems = set()
rows_out = []

with open(csv_path, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames or []
    code_fields = [h for h in fields if h.startswith("codes_")]

    for row in reader:
      stem = (row.get("raw_stem") or "").strip()
      if not stem:
          continue

      exact = (row.get("exact_match") or "").strip().lower() == "true"
      try:
          jaccard = float((row.get("jaccard") or "0").strip())
      except ValueError:
          jaccard = 0.0

      codes = "|".join((row.get(c, "") or "") for c in code_fields)
      has_n1 = re.search(r"(^|\|)N1[a-zA-Z0-9]*($|\|)", codes) is not None
      mismatch = (not exact) and (jaccard <= max_jaccard)

      if mismatch or has_n1:
          stems.add(stem)
          rows_out.append({
              "raw_stem": stem,
              "item_index": row.get("item_index", ""),
              "reason_flags": "|".join(
                  x for x in ["mismatch" if mismatch else "", "n1" if has_n1 else ""] if x
              ),
              "exact_match": row.get("exact_match", ""),
              "jaccard": row.get("jaccard", ""),
          })

with open(stems_out, "w", encoding="utf-8") as f:
    for stem in sorted(stems):
        f.write(stem + "\n")

with open(items_out, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["raw_stem", "item_index", "reason_flags", "exact_match", "jaccard"],
    )
    writer.writeheader()
    writer.writerows(rows_out)

print(f"selected_stems={len(stems)}")
print(f"selected_items={len(rows_out)}")
print(f"stems_out={stems_out}")
print(f"items_out={items_out}")
PY

TARGET_COUNT="$(wc -l < "$STEMS_FILE" | tr -d '[:space:]')"
if [[ "$TARGET_COUNT" == "0" ]]; then
  echo
echo "[phase-2] Nessun target selezionato: salto passata mirata."
  echo "Stems file: $STEMS_FILE"
  echo "Items file: $ITEMS_FILE"
  exit 0
fi

echo
echo "[phase-2] Passata mirata su stems selezionati"
echo "Target stems: $STEMS_FILE ($TARGET_COUNT stems)"
echo "Dettagli log:  $PH2_LOG"
echo "Report JSON:   $PH2_JSON"
echo "Report CSV:    $PH2_CSV"
echo "Config: models=$MODELS workers=$WORKERS timeout=$TARGET_TIMEOUT heartbeat=$HEARTBEAT_SECONDS overwrite=$TARGET_OVERWRITE"

python3 scripts/double_code_models.py \
  --models "$MODELS" \
  --workers "$WORKERS" \
  --timeout "$TARGET_TIMEOUT" \
  --heartbeat-seconds "$HEARTBEAT_SECONDS" \
  --stems-file "$STEMS_FILE" \
  --detailed-log "$PH2_LOG" \
  --json-out "$PH2_JSON" \
  --csv-out "$PH2_CSV" \
  "${TARGET_OVERWRITE_ARGS[@]}" \
  "${QUEUE_ARGS[@]}"

echo
echo "Workflow completato."
echo "Fase 1: $PH1_JSON | $PH1_CSV"
echo "Target: $STEMS_FILE | $ITEMS_FILE"
echo "Fase 2: $PH2_JSON | $PH2_CSV"
