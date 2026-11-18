# RQ2 (interim): share of eligible studies with at least one row of each derived label

Design-weighted domain estimates (percent of eligible studies; 95% t-interval, linearised stratified variance on merged strata; * = zero-variance estimate, see csv for exact unweighted interval). k/n = unweighted studies with the feature / unweighted eligible respondents. Interim run.

claude: 102 respondents, 72 eligible, 27 estimation groups, df 75; codex: 102 respondents, 74 eligible, 27 estimation groups, df 75

Outcome kinds are reported separately and never pooled (amendment v0.11). `ANY` = at least one row of that kind. Labels are derived by `derive_labels.derive`; UNCLASSIFIED-* are the script's explicit non-label codes. Full-sample agreement of the fields behind these rows: E.outcome_kind kappa 0.719 / 82.6% (pass); E.derived_label (script) kappa 0.534 / 60.4% (FAIL), on matched (paradigm family x model family) keys.


| kind | label | Claude % (95% CI) | Claude k/n | Codex % (95% CI) | Codex k/n |
|---|---|---|---|---|---|
| effect | ANY | 64.1 (51.7 to 76.5) | 39/72 | 70.1 (58.6 to 81.5) | 46/74 |
| effect | ATTENUATED | 0.6 (0.0 to 1.8) | 1/72 | 0.0 (0.0 to 0.0) * | 0/74 |
| effect | DIFFERENT | 4.5 (0.0 to 9.9) | 3/72 | 1.9 (0.0 to 3.7) | 3/74 |
| effect | EXAGGERATED | 7.7 (0.4 to 14.9) | 5/72 | 4.7 (0.0 to 10.9) | 3/74 |
| effect | HUMAN-LIKE | 11.1 (3.3 to 18.9) | 7/72 | 3.0 (0.0 to 7.5) | 3/74 |
| effect | INSUFFICIENT | 20.5 (13.1 to 28.0) | 6/72 | 21.1 (5.3 to 36.8) | 12/74 |
| effect | NO-HUMAN-REFERENCE | 19.5 (7.9 to 31.2) | 12/72 | 19.7 (2.9 to 36.5) | 9/74 |
| effect | SAME-DIRECTION-UNQUANTIFIED | 31.3 (13.3 to 49.3) | 19/72 | 40.9 (23.0 to 58.8) | 27/74 |
| effect | SUPER-NORMATIVE | 20.0 (4.0 to 36.1) | 12/72 | 11.2 (0.0 to 25.4) | 7/74 |
| effect | UNCLASSIFIED-MODEL-ONLY | 0.3 (0.0 to 0.9) | 1/72 | 0.0 (0.0 to 0.0) * | 0/74 |
| accuracy | ANY | 34.6 (22.4 to 46.8) | 29/72 | 32.2 (19.3 to 45.2) | 31/74 |
| accuracy | ABOVE-HUMAN | 8.0 (0.0 to 16.7) | 5/72 | 12.4 (2.9 to 21.9) | 10/74 |
| accuracy | BELOW-HUMAN | 17.2 (5.7 to 28.7) | 14/72 | 16.2 (5.0 to 27.4) | 13/74 |
| accuracy | HUMAN-LEVEL | 6.3 (0.0 to 14.1) | 5/72 | 8.2 (0.0 to 16.9) | 6/74 |
| accuracy | INSUFFICIENT | 14.2 (5.8 to 22.7) | 12/72 | 13.9 (5.5 to 22.2) | 15/74 |
| accuracy | NO-HUMAN-REFERENCE | 5.7 (0.8 to 10.7) | 6/72 | 2.0 (0.0 to 5.1) | 3/74 |
| agreement | ANY | 9.9 (4.0 to 15.9) | 14/72 | 20.1 (10.2 to 30.0) | 18/74 |
| agreement | AGREEMENT-ONLY | 9.9 (4.0 to 15.9) | 14/72 | 20.1 (10.2 to 30.0) | 18/74 |


## Rows by paradigm family x derived label (unweighted row counts, descriptive; family = coder's family of the paradigm)


**claude / effect** (344 rows)

| family | ATTENUATED | DIFFERENT | EXAGGERATED | HUMAN-LIKE | INSUFFICIENT | NO-HUMAN-REFERENCE | SAME-DIRECTION-UNQUANTIFIED | SUPER-NORMATIVE | UNCLASSIFIED-MODEL-ONLY | total rows |
|---|---|---|---|---|---|---|---|---|---|---|
| HB | 1 | 2 | 3 | 14 |  | 24 | 32 | 8 |  | 84 |
| JDM |  |  | 5 | 1 | 2 | 27 | 12 |  |  | 47 |
| LANG |  | 1 | 14 | 15 |  | 3 | 13 | 8 |  | 54 |
| LEARN |  |  |  |  | 2 | 5 | 8 |  |  | 15 |
| MEM |  | 6 |  |  |  |  | 14 | 21 |  | 41 |
| MOR |  |  |  |  |  | 18 |  |  |  | 18 |
| NUM |  |  |  |  |  | 3 | 4 |  |  | 7 |
| OTH |  |  |  |  | 6 | 3 | 4 | 3 |  | 16 |
| RE |  |  |  |  |  |  | 13 | 4 | 4 | 21 |
| TOM |  |  |  |  | 1 | 35 | 5 |  |  | 41 |


**claude / accuracy** (315 rows)

| family | ABOVE-HUMAN | BELOW-HUMAN | HUMAN-LEVEL | INSUFFICIENT | NO-HUMAN-REFERENCE | total rows |
|---|---|---|---|---|---|---|
| DEV |  |  |  | 1 |  | 1 |
| HB | 3 | 1 | 2 |  |  | 6 |
| JDM | 3 | 1 |  | 27 |  | 31 |
| LANG |  | 3 | 6 | 13 | 14 | 36 |
| MEM | 1 | 7 |  | 2 |  | 10 |
| MOR |  | 1 | 8 |  |  | 9 |
| NUM |  | 1 |  |  |  | 1 |
| OTH |  | 4 |  |  |  | 4 |
| RE | 8 | 10 |  | 24 | 14 | 56 |
| TOM | 1 | 75 | 3 | 44 | 38 | 161 |


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


**codex / effect** (329 rows)

| family | DIFFERENT | EXAGGERATED | HUMAN-LIKE | INSUFFICIENT | NO-HUMAN-REFERENCE | SAME-DIRECTION-UNQUANTIFIED | SUPER-NORMATIVE | total rows |
|---|---|---|---|---|---|---|---|---|
| DEV |  |  |  |  | 1 |  |  | 1 |
| HB |  | 1 | 6 |  | 23 | 32 | 3 | 65 |
| JDM |  | 5 | 1 | 29 | 26 | 22 |  | 83 |
| LANG |  | 3 |  | 7 |  | 15 | 4 | 29 |
| LEARN |  |  |  | 4 |  | 6 |  | 10 |
| MEM | 2 |  |  |  |  | 16 | 3 | 21 |
| MOR |  |  |  |  | 29 | 15 |  | 44 |
| NUM |  |  |  | 7 |  | 8 |  | 15 |
| OTH |  |  | 5 | 8 | 17 | 13 | 6 | 49 |
| RE |  |  |  |  |  | 2 | 1 | 3 |
| TOM | 2 |  |  | 3 | 3 | 1 |  | 9 |


**codex / accuracy** (235 rows)

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
| TOM | 6 | 42 | 3 | 27 | 7 | 85 |


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
