#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRAXIS_DIR="$REPO_ROOT/Praxis-ql"
cd "$REPO_ROOT"

MODE="${1:-full}" # full | sample30
TS="$(date +%Y%m%d-%H%M%S)"
WORKERS="${WORKERS:-1}"
TIMEOUT="${TIMEOUT:-900}"
HEARTBEAT_SECONDS="${HEARTBEAT_SECONDS:-30}"
OVERWRITE="${OVERWRITE:-0}"   # 1 => forza rilabel completo
LOG_QUEUED="${LOG_QUEUED:-0}" # 1 => logga tutte le righe [queued]

LOG_DIR="$PRAXIS_DIR/04-label/labels"
mkdir -p "$LOG_DIR"

DETAIL_LOG="$LOG_DIR/double-coding-${MODE}-${TS}.log"
JSON_OUT="$LOG_DIR/double-coding-agreement-${MODE}-${TS}.json"
CSV_OUT="$LOG_DIR/double-coding-item-agreement-${MODE}-${TS}.csv"

MODE_ARGS=()
OVERWRITE_ARGS=()
VERBOSE_QUEUE_ARGS=()

if [[ "$OVERWRITE" == "1" ]]; then
  OVERWRITE_ARGS+=(--overwrite)
fi
if [[ "$LOG_QUEUED" == "1" ]]; then
  VERBOSE_QUEUE_ARGS+=(--log-queued)
fi

if [[ "$MODE" == "sample30" ]]; then
  SAMPLE_JSON="$LOG_DIR/incoherent-review-sample-${TS}.json"
  SAMPLE_CSV="$LOG_DIR/incoherent-review-sample-${TS}.csv"
  STEMS_FILE="/tmp/incoherent_sample_stems_${TS}.txt"

  python3 scripts/sample_incoherent_review.py \
    --sample-size 30 \
    --seed 42 \
    --json-out "$SAMPLE_JSON" \
    --csv-out "$SAMPLE_CSV"

  jq -r '.sample[].raw_stem' "$SAMPLE_JSON" | sort -u > "$STEMS_FILE"
  MODE_ARGS+=(--stems-file "$STEMS_FILE")
elif [[ "$MODE" != "full" ]]; then
  echo "Uso: $0 [full|sample30]" >&2
  exit 1
fi

echo "Avvio double-coding (${MODE})"
echo "Dettagli log: $DETAIL_LOG"
echo "Report JSON:  $JSON_OUT"
echo "Report CSV:   $CSV_OUT"
echo "Config: workers=$WORKERS timeout=$TIMEOUT heartbeat=$HEARTBEAT_SECONDS overwrite=$OVERWRITE log_queued=$LOG_QUEUED"

python3 scripts/double_code_models.py \
  --models "gemma4:31b,qwen3:32b" \
  --workers "$WORKERS" \
  --timeout "$TIMEOUT" \
  --heartbeat-seconds "$HEARTBEAT_SECONDS" \
  --detailed-log "$DETAIL_LOG" \
  --json-out "$JSON_OUT" \
  --csv-out "$CSV_OUT" \
  "${OVERWRITE_ARGS[@]}" \
  "${VERBOSE_QUEUE_ARGS[@]}" \
  "${MODE_ARGS[@]}"

echo
echo "Run completato."
echo "Ultime righe log:"
tail -n 20 "$DETAIL_LOG" || true
