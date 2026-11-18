#!/usr/bin/env bash
# Generic one-at-a-time GPU queue. Usage: bash analysis/acme/gpu_queue.sh <jobs.txt> <rundir>
# jobs.txt: one shell command per line (each a fresh python process, itself resumable); '#' lines skipped.
# A job whose line is in <rundir>/jobs.done is skipped, so the queue can be restarted after a crash.
# Lock runs/gpu.lock (one GPU job at a time); nvidia-smi telemetry every 30 s; before each job waits for GPU <= 80 C if above 85 C
# and for at least 6 GB available RAM / 8 GB free commit charge; a failed job is retried once, then logged and skipped.
# Stop file: touch <rundir>/STOP to end the queue after the current job.
set -u
cd "$(dirname "$0")/../.."
JOBS=$1; RUN=$2
mkdir -p "$RUN"; LOG="$RUN/queue.log"; DONE="$RUN/jobs.done"; touch "$DONE"
LOCK=runs/gpu.lock
if [ -e "$LOCK" ]; then echo "lock held: $(cat $LOCK)" | tee -a "$LOG"; exit 3; fi
echo "$RUN $$ $(date -Iseconds)" > "$LOCK"
( while true; do echo "$(date -Iseconds),$(nvidia-smi --query-gpu=memory.used,temperature.gpu,power.draw --format=csv,noheader,nounits)" >> "$RUN/telemetry.csv"; sleep 30; done ) &
TEL=$!
trap 'rm -f "$LOCK"; kill $TEL 2>/dev/null' EXIT
mem_ok() { .venv/Scripts/python.exe -I -c "
import sys; sys.path.insert(0,'analysis/acme'); import scoring; r=scoring.free_ram_gb(); print(r); sys.exit(0 if r['avail_phys_gb']>=6 and r['avail_commit_gb']>=8 else 1)"; }
while IFS= read -r job || [ -n "$job" ]; do
  job=${job%$'\r'}   # job list may be checked out with CRLF
  case "$job" in ''|'#'*) continue;; esac
  if grep -Fxq "$job" "$DONE"; then continue; fi
  if [ -e "$RUN/STOP" ]; then echo "$(date -Iseconds) STOP file, ending" >> "$LOG"; break; fi
  t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | tr -d ' \r')
  if [ "${t:-0}" -gt 85 ]; then echo "$(date -Iseconds) GPU ${t}C, cooling" >> "$LOG"; while [ "${t:-0}" -gt 80 ]; do sleep 30; t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | tr -d ' \r'); done; fi
  n=0; until m=$(mem_ok); do n=$((n+1)); [ $n -eq 1 ] && echo "$(date -Iseconds) waiting for memory: $m" >> "$LOG"; sleep 60; [ $n -gt 60 ] && break; done
  for attempt in 1 2; do
    echo "$(date -Iseconds) start [$attempt] $job" >> "$LOG"
    tag=$(echo "$job" | md5sum | cut -c1-8)
    bash -c "$job" >> "$RUN/job-$tag.log" 2>&1
    rc=$?
    echo "$(date -Iseconds) end rc=$rc $job" >> "$LOG"
    if [ $rc -eq 0 ]; then echo "$job" >> "$DONE"; break; fi
    sleep 20
  done
done < "$JOBS"
echo "$(date -Iseconds) queue finished" >> "$LOG"
