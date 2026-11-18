# Clause split of the observed fragile labels (A1, 42 grids)

Source: `runs/pilot-side-by-side/table_a1.csv`; script `analysis/pilot/rule_clause_split.py`; recomputed labels equal the stored labels in 42/42 grids. Evidence level E4.

Fragile grids: 41 of 42. Sigma clause only (sign stability < 0.6, range clause not met): 2; range clause only (dbar-2S < 0 < dbar+2S, sigma >= 0.6): 10; both: 29.

By paradigm (fragile grids):

| paradigm | sigma only | range only | both |
|---|---|---|---|
| P1 | 0 | 1 | 4 |
| P2a | 0 | 2 | 4 |
| P2b | 0 | 1 | 5 |
| P2c | 1 | 1 | 4 |
| P2d | 0 | 5 | 1 |
| P3 | 1 | 0 | 5 |
| P4 | 0 | 0 | 6 |


Grids with sigma >= 0.9 (4):

| model | paradigm | sigma | llm_mu | llm_S | rule_outcome | clause | dbar_minus_2S_lower |
|---|---|---|---|---|---|---|---|
| granite-3.3-2b-instruct | P2d | 1.000 | 7.938 | 8.955 | fragile | range only | -11.230 |
| qwen2.5-7b-instruct | P1 | 0.938 | 6.769 | 2.123 | stable | none | 0.804 |
| qwen2.5-7b-instruct | P2a | 1.000 | 1.161 | 0.773 | fragile | range only | -0.629 |
| qwen2.5-7b-instruct | P2d | 0.938 | 3.586 | 1.843 | fragile | range only | -1.505 |
