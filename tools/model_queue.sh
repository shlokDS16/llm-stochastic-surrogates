#!/usr/bin/env bash
# Sequential model downloads (link-limited at ~2 MB/s). Run from the project root in the background.
cd "$(dirname "$0")/.."
PY=.venv/Scripts/python.exe
while ! grep -q olmo2-1b-instruct runs/models/MODELS.jsonl 2>/dev/null; do sleep 30; done
fetch(){ $PY -I tools/fetch_model.py "$1" "$2" >> runs/models/dl-$2.log 2>&1; }
quant(){ $PY -I tools/quantize_model.py "$1" --delete-raw >> runs/models/q-$1.log 2>&1; }
fetch allenai/OLMo-2-1124-7B-Instruct olmo2-7b-instruct && quant olmo2-7b-instruct
fetch Qwen/Qwen2.5-1.5B-Instruct qwen2.5-1.5b-instruct
fetch ibm-granite/granite-3.3-2b-instruct granite-3.3-2b-instruct
fetch Qwen/Qwen2.5-7B-Instruct qwen2.5-7b-instruct && quant qwen2.5-7b-instruct
fetch ibm-granite/granite-3.3-8b-instruct granite-3.3-8b-instruct && quant granite-3.3-8b-instruct
echo QUEUE_DONE >> runs/models/queue.log
