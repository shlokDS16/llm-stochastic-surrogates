#!/usr/bin/env bash
# Second stage of the sequential model downloads. OLMo-2 7B raw is kept until quantised by hand (screening test needs it).
cd "$(dirname "$0")/.."
PY=.venv/Scripts/python.exe
while ! grep -q olmo2-7b-instruct runs/models/MODELS.jsonl 2>/dev/null; do sleep 30; done
fetch(){ $PY -I tools/fetch_model.py "$1" "$2" >> runs/models/dl-$2.log 2>&1; }
quant(){ $PY -I tools/quantize_model.py "$1" --delete-raw >> runs/models/q-$1.log 2>&1; }
fetch Qwen/Qwen2.5-1.5B-Instruct qwen2.5-1.5b-instruct
fetch ibm-granite/granite-3.3-2b-instruct granite-3.3-2b-instruct
while [ -d models/raw/olmo2-7b-instruct ]; do sleep 60; done
fetch Qwen/Qwen2.5-7B-Instruct qwen2.5-7b-instruct && quant qwen2.5-7b-instruct
fetch ibm-granite/granite-3.3-8b-instruct granite-3.3-8b-instruct && quant granite-3.3-8b-instruct
echo QUEUE_DONE >> runs/models/queue.log
