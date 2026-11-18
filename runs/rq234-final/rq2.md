# RQ2 (interim): share of eligible studies with at least one row of each derived label

Design-weighted domain estimates (percent of eligible studies; 95% t-interval, linearised stratified variance on merged strata; * = zero-variance estimate, see csv for exact unweighted interval). k/n = unweighted studies with the feature / unweighted eligible respondents. Interim run.

claude: 110 respondents, 80 eligible, 28 estimation groups, df 82; codex: 110 respondents, 81 eligible, 28 estimation groups, df 82

Outcome kinds are reported separately and never pooled (amendment v0.11). `ANY` = at least one row of that kind. Labels are derived by `derive_labels.derive`; UNCLASSIFIED-* are the script's explicit non-label codes. Full-sample agreement of the fields behind these rows: E.outcome_kind kappa 0.731 / 83.8% (pass); E.derived_label (script) kappa 0.565 / 63.0% (FAIL), on matched (paradigm family x model family) keys.


| kind | label | Claude % (95% CI) | Claude k/n | Codex % (95% CI) | Codex k/n |
|---|---|---|---|---|---|
| effect | ANY | 62.6 (49.9 to 75.3) | 45/80 | 71.9 (61.4 to 82.5) | 52/81 |
| effect | ATTENUATED | 0.6 (0.0 to 1.8) | 1/80 | 0.0 (0.0 to 0.0) * | 0/81 |
| effect | DIFFERENT | 4.5 (0.0 to 9.9) | 4/80 | 2.0 (0.1 to 4.0) | 4/81 |
| effect | EXAGGERATED | 7.6 (0.4 to 14.8) | 5/80 | 4.8 (0.0 to 11.2) | 3/81 |
| effect | HUMAN-LIKE | 14.3 (4.2 to 24.4) | 8/80 | 6.5 (0.0 to 14.6) | 4/81 |
| effect | INSUFFICIENT | 13.6 (3.1 to 24.1) | 6/80 | 18.1 (7.3 to 28.9) | 12/81 |
| effect | NO-HUMAN-REFERENCE | 21.8 (11.3 to 32.3) | 15/80 | 20.3 (8.7 to 31.9) | 12/81 |
| effect | SAME-DIRECTION-UNQUANTIFIED | 27.6 (15.2 to 39.9) | 20/80 | 38.4 (25.9 to 50.9) | 28/81 |
| effect | SUPER-NORMATIVE | 18.1 (6.7 to 29.6) | 13/80 | 8.1 (0.0 to 16.4) | 7/81 |
| effect | UNCLASSIFIED-MODEL-ONLY | 3.7 (0.0 to 10.3) | 2/80 | 0.0 (0.0 to 0.0) * | 0/81 |
| accuracy | ANY | 36.2 (23.9 to 48.4) | 31/80 | 30.3 (18.6 to 42.0) | 32/81 |
| accuracy | ABOVE-HUMAN | 6.0 (0.0 to 12.0) | 5/80 | 10.4 (3.0 to 17.9) | 10/81 |
| accuracy | BELOW-HUMAN | 15.6 (6.0 to 25.1) | 15/80 | 15.1 (5.5 to 24.8) | 14/81 |
| accuracy | HUMAN-LEVEL | 7.6 (0.0 to 15.8) | 6/80 | 6.5 (0.2 to 12.8) | 6/81 |
| accuracy | INSUFFICIENT | 14.7 (6.3 to 23.1) | 13/80 | 13.8 (5.5 to 22.1) | 16/81 |
| accuracy | NO-HUMAN-REFERENCE | 5.7 (0.8 to 10.5) | 6/80 | 2.0 (0.0 to 5.2) | 3/81 |
| agreement | ANY | 9.8 (3.6 to 16.0) | 14/80 | 20.5 (10.1 to 30.9) | 18/81 |
| agreement | AGREEMENT-ONLY | 9.8 (3.6 to 16.0) | 14/80 | 20.5 (10.1 to 30.9) | 18/81 |


## Rows by paradigm family x derived label (unweighted row counts, descriptive; family = coder's family of the paradigm)


**claude / effect** (371 rows)

| family | ATTENUATED | DIFFERENT | EXAGGERATED | HUMAN-LIKE | INSUFFICIENT | NO-HUMAN-REFERENCE | SAME-DIRECTION-UNQUANTIFIED | SUPER-NORMATIVE | UNCLASSIFIED-MODEL-ONLY | total rows |
|---|---|---|---|---|---|---|---|---|---|---|
| HB | 1 | 2 | 3 | 14 |  | 29 | 33 | 9 |  | 91 |
| JDM |  |  | 5 | 1 | 2 | 27 | 12 |  |  | 47 |
| LANG |  | 1 | 14 | 15 |  | 3 | 13 | 8 |  | 54 |
| LEARN |  |  |  |  | 2 | 16 | 8 |  |  | 26 |
| MEM |  | 7 |  |  |  |  | 14 | 21 |  | 42 |
| MOR |  |  |  | 3 |  | 18 |  |  | 3 | 24 |
| NUM |  |  |  |  |  | 3 | 4 |  |  | 7 |
| OTH |  |  |  |  | 6 | 3 | 4 | 3 |  | 16 |
| RE |  |  |  |  |  |  | 13 | 4 | 4 | 21 |
| TOM |  |  |  |  | 1 | 35 | 7 |  |  | 43 |


**claude / accuracy** (322 rows)

| family | ABOVE-HUMAN | BELOW-HUMAN | HUMAN-LEVEL | INSUFFICIENT | NO-HUMAN-REFERENCE | total rows |
|---|---|---|---|---|---|---|
| DEV |  |  |  | 1 |  | 1 |
| HB | 3 | 1 | 2 |  |  | 6 |
| JDM | 3 | 1 |  | 27 |  | 31 |
| LANG |  | 3 | 6 | 13 | 14 | 36 |
| MEM | 1 | 7 |  | 2 |  | 10 |
| MOR |  | 1 | 8 |  |  | 9 |
| NUM |  | 1 |  |  |  | 1 |
| OTH |  | 4 | 2 |  |  | 6 |
| RE | 8 | 10 |  | 24 | 14 | 56 |
| TOM | 1 | 77 | 3 | 47 | 38 | 166 |


**claude / agreement** (120 rows)

| family | AGREEMENT-ONLY | total rows |
|---|---|---|
| HB | 6 | 6 |
| JDM | 5 | 5 |
| JDM+LEARN | 15 | 15 |
| LANG | 28 | 28 |
| LEARN | 18 | 18 |
| MEM | 3 | 3 |
| MOR | 16 | 16 |
| RE | 5 | 5 |
| TOM | 24 | 24 |


**codex / effect** (353 rows)

| family | DIFFERENT | EXAGGERATED | HUMAN-LIKE | INSUFFICIENT | NO-HUMAN-REFERENCE | SAME-DIRECTION-UNQUANTIFIED | SUPER-NORMATIVE | total rows |
|---|---|---|---|---|---|---|---|---|
| DEV |  |  |  |  | 1 |  |  | 1 |
| HB |  | 1 | 6 |  | 28 | 35 | 3 | 73 |
| JDM |  | 5 | 4 | 29 | 26 | 22 |  | 86 |
| LANG | 1 | 3 |  | 7 |  | 15 | 4 | 30 |
| LEARN |  |  |  | 4 | 11 | 6 |  | 21 |
| MEM | 2 |  |  |  |  | 16 | 3 | 21 |
| MOR |  |  |  |  | 29 | 15 |  | 44 |
| NUM |  |  |  | 7 |  | 8 |  | 15 |
| OTH |  |  | 5 | 8 | 17 | 13 | 6 | 49 |
| RE |  |  |  |  |  | 2 | 1 | 3 |
| TOM | 2 |  |  | 3 | 3 | 2 |  | 10 |


**codex / accuracy** (240 rows)

| family | ABOVE-HUMAN | BELOW-HUMAN | HUMAN-LEVEL | INSUFFICIENT | NO-HUMAN-REFERENCE | total rows |
|---|---|---|---|---|---|---|
| DEV |  | 1 | 2 |  |  | 3 |
| HB | 12 | 1 | 1 | 6 |  | 20 |
| JDM | 3 | 9 |  | 9 |  | 21 |
| LANG | 1 | 7 | 3 | 12 |  | 23 |
| LEARN |  | 1 |  | 5 |  | 6 |
| MEM |  |  |  | 3 | 1 | 4 |
| MOR | 1 | 1 | 6 | 3 |  | 11 |
| NUM |  | 1 |  | 10 |  | 11 |
| OTH |  | 4 |  |  |  | 4 |
| RE | 6 | 26 |  | 12 | 3 | 47 |
| TOM | 6 | 44 | 3 | 30 | 7 | 90 |


**codex / agreement** (85 rows)

| family | AGREEMENT-ONLY | total rows |
|---|---|---|
| HB | 1 | 1 |
| JDM | 3 | 3 |
| LANG | 29 | 29 |
| LEARN | 13 | 13 |
| MOR | 11 | 11 |
| NUM | 6 | 6 |
| OTH | 10 | 10 |
| RE | 2 | 2 |
| TOM | 10 | 10 |
