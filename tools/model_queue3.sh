#!/usr/bin/env bash
# Third stage: the two 7-8B models. bf16 is a transient download (quantised to NF4 and deleted at once), so the retained models stay under 30 GB.
cd "$(dirname "$0")/.."
PY=.venv/Scripts/python.exe
fetch(){ $PY -I tools/fetch_model.py "$1" "$2" --transient --revision "$3" >> runs/models/dl-$2.log 2>&1; }
quant(){ $PY -I tools/quantize_model.py "$1" --delete-raw >> runs/models/q-$1.log 2>&1; }
fetch Qwen/Qwen2.5-7B-Instruct qwen2.5-7b-instruct a09a35458c702b33eeacc393d103063234e8bc28 && quant qwen2.5-7b-instruct
fetch ibm-granite/granite-3.3-8b-instruct granite-3.3-8b-instruct 51dd4bc2ade4059a6bd87649d68aa11e4fb2529b && quant granite-3.3-8b-instruct
echo QUEUE3_DONE >> runs/models/queue.log
