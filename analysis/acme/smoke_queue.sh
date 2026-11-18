#!/usr/bin/env bash
# G2 smoke queue: one model per fresh process (Windows commit-charge lesson, os error 1455), one GPU job at a time (runs/gpu.lock),
# nvidia-smi telemetry every 30 s, batch halved on out-of-memory (up to 3 times), a model failing twice is recorded for substitution.
# Usage: bash analysis/acme/smoke_queue.sh [model ...]   (default: the whole roster, small models first). Resumable: passed models skip.
set -u
cd "$(dirname "$0")/../.."
PY=.venv/Scripts/python.exe
OUT=runs/acme-smoke
mkdir -p "$OUT"
LOG="$OUT/queue.log"
LOCK=runs/gpu.lock
if [ -e "$LOCK" ]; then echo "lock held: $(cat $LOCK)"; exit 3; fi
echo "acme-smoke $$ $(date -Iseconds)" > "$LOCK"
trap 'rm -f "$LOCK"; kill $TEL 2>/dev/null' EXIT
( while true; do echo "$(date -Iseconds),$(nvidia-smi --query-gpu=memory.used,temperature.gpu,power.draw --format=csv,noheader,nounits)" >> "$OUT/telemetry.csv"; sleep 30; done ) &
TEL=$!
MODELS=${*:-"qwen2.5-0.5b-instruct qwen2.5-1.5b-instruct olmo2-1b-instruct olmo2-1b-sft olmo2-1b-dpo granite-3.3-2b-instruct smollm2-1.7b-instruct phi4-mini-instruct qwen2.5-7b-instruct olmo2-7b-instruct granite-3.3-8b-instruct mistral-7b-instruct-v0.3 qwen2.5-14b-instruct olmo2-13b-instruct"}
for m in $MODELS; do
  if [ -f "$OUT/$m/smoke.json" ] && grep -q '"status": "pass"' "$OUT/$m/smoke.json"; then echo "$(date -Iseconds) $m already passed" >> "$LOG"; continue; fi
  bs0=$($PY -I -c "import yaml;print(yaml.safe_load(open('analysis/acme/models.yaml'))['models']['$m']['bs_f0'])")
  bs1=$($PY -I -c "import yaml;print(yaml.safe_load(open('analysis/acme/models.yaml'))['models']['$m']['bs_f1'])")
  fails=0; halvings=0
  while true; do
    t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | tr -d ' \r')
    while [ "${t:-0}" -gt 85 ]; do echo "$(date -Iseconds) GPU ${t}C, waiting" >> "$LOG"; sleep 60; t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | tr -d ' \r'); done
    echo "$(date -Iseconds) start $m bs_f0=$bs0 bs_f1=$bs1" >> "$LOG"
    $PY -I analysis/acme/smoke.py --model "$m" --bs-f0 "$bs0" --bs-f1 "$bs1" > "$OUT/$m.stdout.log" 2>&1
    rc=$?
    echo "$(date -Iseconds) end $m rc=$rc $(grep "^$m " "$OUT/$m.stdout.log" | cut -c1-400)" >> "$LOG"
    if [ $rc -eq 0 ]; then break; fi
    if [ $rc -eq 2 ] && [ $halvings -lt 3 ]; then halvings=$((halvings+1)); bs1=$(( (bs1+1)/2 )); bs0=$(( (bs0+1)/2 )); continue; fi
    fails=$((fails+1))
    if [ $fails -ge 2 ]; then echo "$(date -Iseconds) $m FAILED TWICE (substitute rule)" >> "$LOG"; break; fi
  done
done
echo "$(date -Iseconds) queue done" >> "$LOG"
