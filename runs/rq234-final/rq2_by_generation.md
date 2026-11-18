# RQ2 by model generation (descriptive)

Generation of an effect row: the first matching row of `analysis/fulltext/model_generation.csv` applied to the model name only; only if the name gives none, the release_date year of the matching B.models entry if stated; else unknown (name first because extractor release dates are sometimes query or version dates; rule fixed before any result by generation was inspected; see the docstring of `rq234_analysis.py`). G1 = pre-instruction-era and early instruction models, G2 = 2023-era chat models, G3 = 2024 and later. Unweighted counts of extracted effect rows and of studies; no test, no weights, no interval (rows are not a design sample and a study can contribute rows to several generations, so study counts are not additive).

## claude

Rows 813 in 80 studies; unknown share 7.5%; source: {'none': 61, 'name': 750, 'release_date': 2}.

| outcome_kind | derived_label | G1 rows (studies) | G2 rows (studies) | G3 rows (studies) | unknown rows (studies) |
|---|---|---|---|---|---|
| effect | ALL | 63 (11) | 58 (17) | 211 (27) | 39 (7) |
| effect | ATTENUATED | 0 (0) | 1 (1) | 0 (0) | 0 (0) |
| effect | DIFFERENT | 1 (1) | 1 (1) | 8 (2) | 0 (0) |
| effect | EXAGGERATED | 2 (1) | 0 (0) | 20 (4) | 0 (0) |
| effect | HUMAN-LIKE | 1 (1) | 13 (3) | 19 (5) | 0 (0) |
| effect | INSUFFICIENT | 0 (0) | 2 (1) | 8 (4) | 1 (1) |
| effect | NO-HUMAN-REFERENCE | 6 (2) | 9 (2) | 91 (12) | 28 (3) |
| effect | SAME-DIRECTION-UNQUANTIFIED | 30 (5) | 22 (8) | 46 (11) | 10 (4) |
| effect | SUPER-NORMATIVE | 23 (4) | 10 (7) | 12 (6) | 0 (0) |
| effect | UNCLASSIFIED-MODEL-ONLY | 0 (0) | 0 (0) | 7 (2) | 0 (0) |
| accuracy | ALL | 67 (10) | 117 (17) | 128 (13) | 10 (3) |
| accuracy | ABOVE-HUMAN | 0 (0) | 1 (1) | 15 (4) | 0 (0) |
| accuracy | BELOW-HUMAN | 31 (5) | 58 (8) | 15 (4) | 1 (1) |
| accuracy | HUMAN-LEVEL | 6 (4) | 13 (4) | 2 (1) | 0 (0) |
| accuracy | INSUFFICIENT | 16 (4) | 27 (6) | 71 (7) | 0 (0) |
| accuracy | NO-HUMAN-REFERENCE | 14 (1) | 18 (3) | 25 (3) | 9 (2) |
| agreement | ALL | 18 (6) | 36 (8) | 54 (6) | 12 (1) |
| agreement | AGREEMENT-ONLY | 18 (6) | 36 (8) | 54 (6) | 12 (1) |

## codex

Rows 678 in 81 studies; unknown share 5.9%; source: {'name': 638, 'none': 40}.

| outcome_kind | derived_label | G1 rows (studies) | G2 rows (studies) | G3 rows (studies) | unknown rows (studies) |
|---|---|---|---|---|---|
| effect | ALL | 33 (13) | 98 (19) | 205 (33) | 17 (7) |
| effect | DIFFERENT | 1 (1) | 2 (1) | 1 (1) | 1 (1) |
| effect | EXAGGERATED | 1 (1) | 0 (0) | 8 (2) | 0 (0) |
| effect | HUMAN-LIKE | 0 (0) | 11 (2) | 4 (2) | 0 (0) |
| effect | INSUFFICIENT | 5 (3) | 15 (6) | 38 (8) | 0 (0) |
| effect | NO-HUMAN-REFERENCE | 0 (0) | 26 (3) | 77 (11) | 12 (3) |
| effect | SAME-DIRECTION-UNQUANTIFIED | 20 (10) | 40 (12) | 70 (15) | 4 (3) |
| effect | SUPER-NORMATIVE | 6 (3) | 4 (3) | 7 (2) | 0 (0) |
| accuracy | ALL | 60 (10) | 71 (15) | 87 (14) | 22 (6) |
| accuracy | ABOVE-HUMAN | 2 (1) | 9 (7) | 16 (4) | 2 (1) |
| accuracy | BELOW-HUMAN | 39 (6) | 27 (7) | 20 (3) | 9 (2) |
| accuracy | HUMAN-LEVEL | 4 (2) | 7 (3) | 2 (2) | 2 (1) |
| accuracy | INSUFFICIENT | 15 (6) | 22 (6) | 45 (8) | 8 (3) |
| accuracy | NO-HUMAN-REFERENCE | 0 (0) | 6 (1) | 4 (2) | 1 (1) |
| agreement | ALL | 17 (7) | 31 (8) | 36 (9) | 1 (1) |
| agreement | AGREEMENT-ONLY | 17 (7) | 31 (8) | 36 (9) | 1 (1) |
