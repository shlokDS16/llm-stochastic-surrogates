# G2 smoke summary (CRP-S08, 2026-11-06)

Source: runs/acme-smoke/<model>/smoke.json (analysis/acme/smoke.py) on the pilot prompts W0-W3 (64 F0 prompts; F1 for the VRAM test). Ties = prompts whose bf16-rounded top-2 logit gap is within one bf16 step; parity counts non-tie prompts only (prereg G2). P1 path mass = scored answer paths ('C', ' C', 'Program C', ...). P3 digit mass = first-token digits; for Mistral the digit follows a space token, so this is 0 and ratings are read as paths (amendment A-L3).

| model | status | ties | fwd=gen (non-tie) | pilot parity (non-tie) | P1 path mass min / share<0.9 | P3 1st-token digit mass mean | peak VRAM F0 / F1 GiB | batch F0/F1 | load s |
|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-0.5b-instruct | pass | 11 | 1.000 | n/a (new model) | 0.972 / 0.00 | 1.000 | 1.59 / 1.72 | 100/100 | 8.3 |
| qwen2.5-1.5b-instruct | pass | 9 | 1.000 | 1.000 (n=55) | 0.974 / 0.00 | 1.000 | 4.16 / 4.36 | 100/100 | 7.4 |
| qwen2.5-7b-instruct | pass | 2 | 1.000 | 1.000 (n=62) | 1.000 / 0.00 | 1.000 | 7.18 / 7.42 | 64/64 | 15.4 |
| qwen2.5-14b-instruct | pass | 1 | 0.984 | n/a (new model) | 1.000 / 0.00 | 1.000 | 9.17 / 8.73 | 16/4 | 27.9 |
| olmo2-1b-instruct | pass | 9 | 1.000 | 1.000 (n=55) | 0.878 / 0.25 | 0.960 | 3.79 / 4.92 | 40/40 | 8.7 |
| olmo2-1b-sft | pass | 8 | 1.000 | n/a (new model) | 0.712 / 0.94 | 0.786 | 3.79 / 4.92 | 40/40 | 9.6 |
| olmo2-1b-dpo | pass | 5 | 1.000 | n/a (new model) | 0.874 / 0.25 | 0.677 | 3.79 / 4.92 | 40/40 | 9.7 |
| olmo2-7b-instruct | pass | 3 | 1.000 | 1.000 (n=61) | 0.971 / 0.00 | 0.975 | 5.49 / 6.18 | 6/6 | 16.5 |
| olmo2-13b-instruct | pass | 4 | 1.000 | n/a (new model) | 0.999 / 0.00 | 0.989 | 8.46 / 8.26 | 6/2 | 20.7 |
| granite-3.3-2b-instruct | pass | 5 | 1.000 | 0.983 (n=59) | 0.988 / 0.00 | 1.000 | 6.43 / 7.65 | 80/80 | 11.3 |
| granite-3.3-8b-instruct | pass | 4 | 1.000 | 0.983 (n=60) | 0.911 / 0.00 | 0.989 | 5.54 / 6.31 | 24/24 | 14.0 |
| smollm2-1.7b-instruct | pass | 14 | 1.000 | n/a (new model) | 0.952 / 0.00 | 0.937 | 5.53 / 5.78 | 64/32 | 9.0 |
| phi4-mini-instruct | pass | 22 | 1.000 | n/a (new model) | 0.788 / 0.06 | 0.746 | 4.13 / 4.18 | 48/24 | 13.6 |
| mistral-7b-instruct-v0.3 | pass | 6 | 1.000 | n/a (new model) | 0.050 / 0.69 | 0.000 | 5.76 / 5.09 | 48/16 | 16.7 |

No model failed a G2 criterion; no substitute was used. The queue.log 'FAILED TWICE' lines for Mistral, Qwen2.5-14B and OLMo-2 13B were harness and memory faults (end-of-turn probe; fp32-head chunk size; generate memory with the bf16 embedding table on the GPU), fixed before the passing runs above. Qwen2.5-14B and OLMo-2 13B run with the input-embedding table on CPU (scoring.load, embed_cpu) and smaller batches (models.yaml). OLMo-2 13B path masses sum to 1.0007 at most: NF4 numerics differ slightly with batch composition (pilot limitation).
