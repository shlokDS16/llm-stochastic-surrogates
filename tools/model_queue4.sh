#!/usr/bin/env bash
# Granite 8B only (the transient bf16 download peaks at about 38.6 GB of the 40 GB project cap; retained models end at about 28 GB).
cd "$(dirname "$0")/.."
PY=.venv/Scripts/python.exe
$PY -I tools/fetch_model.py ibm-granite/granite-3.3-8b-instruct granite-3.3-8b-instruct --transient --revision 51dd4bc2ade4059a6bd87649d68aa11e4fb2529b >> runs/models/dl-granite-3.3-8b-instruct.log 2>&1 && $PY -I tools/quantize_model.py granite-3.3-8b-instruct --delete-raw >> runs/models/q-granite-3.3-8b-instruct.log 2>&1
echo QUEUE4_DONE >> runs/models/queue.log
