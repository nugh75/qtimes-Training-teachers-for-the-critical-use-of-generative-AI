#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRAXIS_DIR="$REPO_ROOT/Praxis-ql"
cd "$REPO_ROOT"

TS="$(date +%Y%m%d-%H%M%S)"

QWEN_MODEL="${QWEN_MODEL:-qwen3.5:9b}"
GEMMA_MODEL="${GEMMA_MODEL:-gemma4:31b}"

WORKERS="${WORKERS:-1}"
QWEN_TIMEOUT="${QWEN_TIMEOUT:-900}"
TARGET_TIMEOUT="${TARGET_TIMEOUT:-900}"
HEARTBEAT_SECONDS="${HEARTBEAT_SECONDS:-30}"

QWEN_OVERWRITE="${QWEN_OVERWRITE:-0}"
TARGET_OVERWRITE="${TARGET_OVERWRITE:-0}"
LOG_QUEUED="${LOG_QUEUED:-0}"
TARGET_MAX_JACCARD="${TARGET_MAX_JACCARD:-0.9999}"

LOG_DIR="$PRAXIS_DIR/04-label/labels"
mkdir -p "$LOG_DIR"

PH1_LOG="$LOG_DIR/qwen-pass-${TS}.log"
PH2_LOG="$LOG_DIR/targeted-gemma31b-${TS}.log"
PH2_JSON="$LOG_DIR/double-coding-agreement-targeted-${TS}.json"
PH2_CSV="$LOG_DIR/double-coding-item-agreement-targeted-${TS}.csv"

STEMS_FILE="$LOG_DIR/review-target-stems-${TS}.txt"
ITEMS_FILE="$LOG_DIR/review-target-items-${TS}.csv"

REFERENCE_CSV="${REFERENCE_CSV:-}"
if [[ -z "$REFERENCE_CSV" ]]; then
  REFERENCE_CSV="$(ls -1t "$LOG_DIR"/*item-agreement*.csv 2>/dev/null | head -n 1 || true)"
fi

QWEN_ARGS=()
TARGET_OVERWRITE_ARGS=()
QUEUE_ARGS=()

if [[ "$QWEN_OVERWRITE" == "1" ]]; then
  QWEN_ARGS+=(--overwrite)
fi
if [[ "$TARGET_OVERWRITE" == "1" ]]; then
  TARGET_OVERWRITE_ARGS+=(--overwrite)
fi
if [[ "$LOG_QUEUED" == "1" ]]; then
  QUEUE_ARGS+=(--log-queued)
fi

echo "[check] Verifica modelli Ollama su server..."
python3 - "$QWEN_MODEL" "$GEMMA_MODEL" <<'PY'
import json
import sys
import urllib.request

models = [sys.argv[1], sys.argv[2]]
try:
    with urllib.request.urlopen("http://192.168.129.14:11434/api/tags", timeout=10) as r:
        payload = json.load(r)
except Exception as exc:  # noqa: BLE001
    print(f"ERRORE: impossibile contattare Ollama: {exc}", file=sys.stderr)
    sys.exit(2)

available = {m.get("name", "") for m in payload.get("models", [])}
missing = [m for m in models if m not in available]
if missing:
    print("ERRORE: modelli mancanti su Ollama: " + ", ".join(missing), file=sys.stderr)
    sys.exit(3)

print("OK: modelli disponibili -> " + ", ".join(models))
PY

echo
echo "[phase-1] Qwen su file esistenti/corpus"
echo "Log: $PH1_LOG"
echo "Config: model=$QWEN_MODEL workers=$WORKERS timeout=$QWEN_TIMEOUT overwrite=$QWEN_OVERWRITE"

python3 scripts/label_raw_with_ollama.py \
  --model "$QWEN_MODEL" \
  --workers "$WORKERS" \
  --timeout "$QWEN_TIMEOUT" \
  "${QWEN_ARGS[@]}" 2>&1 | tee "$PH1_LOG"

QWEN_OUT_DIR="$(python3 - "$QWEN_MODEL" <<'PY'
from label_raw_with_ollama import default_output_dir_for_model
import sys
print(default_output_dir_for_model(sys.argv[1]))
PY
)"

echo
echo "[phase-2 prep] Estrazione target N1/controversie"
echo "Reference CSV: ${REFERENCE_CSV:-<nessuno>}"
echo "Qwen out dir: $QWEN_OUT_DIR"

python3 - "$REFERENCE_CSV" "$QWEN_OUT_DIR" "$STEMS_FILE" "$ITEMS_FILE" "$TARGET_MAX_JACCARD" <<'PY'
import csv
import json
import re
import sys
from pathlib import Path

reference_csv = (sys.argv[1] or "").strip()
qwen_out_dir = Path(sys.argv[2])
stems_out = Path(sys.argv[3])
items_out = Path(sys.argv[4])
max_jaccard = float(sys.argv[5])

stems = set()
rows = []

if reference_csv:
    p = Path(reference_csv)
    if p.exists() and p.is_file():
        with p.open("r", encoding="utf-8", newline="") as f:
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
                    rows.append(
                        {
                            "raw_stem": stem,
                            "item_index": row.get("item_index", ""),
                            "reason_flags": "|".join(
                                x for x in ["mismatch" if mismatch else "", "n1" if has_n1 else ""] if x
                            ),
                            "exact_match": row.get("exact_match", ""),
                            "jaccard": row.get("jaccard", ""),
                            "source": "reference_csv",
                        }
                    )

if qwen_out_dir.exists():
    for path in sorted(qwen_out_dir.glob("*.json")):
        if path.name in {"summary.jsonl", "summary.csv", "failures.json"}:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        has_n1 = False
        for item in payload.get("items", []):
            for code in item.get("codes", []):
                if str(code).startswith("N1"):
                    has_n1 = True
                    break
            if has_n1:
                break

        if has_n1:
            stem = path.stem
            stems.add(stem)
            rows.append(
                {
                    "raw_stem": stem,
                    "item_index": "*",
                    "reason_flags": "n1",
                    "exact_match": "",
                    "jaccard": "",
                    "source": "qwen_labels",
                }
            )

stems_out.parent.mkdir(parents=True, exist_ok=True)
items_out.parent.mkdir(parents=True, exist_ok=True)

stems_out.write_text("\n".join(sorted(stems)) + ("\n" if stems else ""), encoding="utf-8")

with items_out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["raw_stem", "item_index", "reason_flags", "exact_match", "jaccard", "source"],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"selected_stems={len(stems)}")
print(f"selected_rows={len(rows)}")
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
echo "[phase-2] Gemma4:31b solo su controversie/N1"
echo "Target stems: $STEMS_FILE ($TARGET_COUNT stems)"
echo "Log: $PH2_LOG"
echo "Report JSON: $PH2_JSON"
echo "Report CSV: $PH2_CSV"
echo "Config: models=${GEMMA_MODEL},${QWEN_MODEL} workers=$WORKERS timeout=$TARGET_TIMEOUT overwrite=$TARGET_OVERWRITE"

python3 scripts/double_code_models.py \
  --models "${GEMMA_MODEL},${QWEN_MODEL}" \
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
echo "Fase 1 (Qwen): $PH1_LOG"
echo "Target: $STEMS_FILE | $ITEMS_FILE"
echo "Fase 2 (targeted): $PH2_JSON | $PH2_CSV"
