# Exact upper bounds for prevalences with zero events among eligible studies

Clopper-Pearson two-sided 95% upper limit = 1 - 0.025^(1/n), UNWEIGHTED (n = eligible studies in the domain). Column `upper_cp_neff_pct` repeats it with n replaced by the Kish effective sample size of the design weights (an approximation that allows for unequal weights; a sensitivity, not an exact design-based interval). The design-based linearised interval is [0, 0] when no study has the feature, so it must not be read as certainty of absence.

| coder | feature | n_domain | events | upper_cp_pct | rule_of_three_pct | n_eff_kish | upper_cp_neff_pct |
|---|---|---|---|---|---|---|---|
| codex | rq2/effect/ATTENUATED | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| codex | rq2/effect/UNCLASSIFIED-MODEL-ONLY | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq3/outcome_types/agreement | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| claude | rq3/outcome_types/effect | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| claude | rq3/primary_type/replication_dataset | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq3/primary_type/replication_dataset | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq3/types_any/replication_dataset | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq3/types_any/replication_dataset | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f10/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f10/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f11/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f11/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f12/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f12/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f12/not_reported | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| claude | rq4/f1/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f1/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| codex | rq4/f3/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f4/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f4/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f5/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f5/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| codex | rq4/f7/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f8/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f8/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
| claude | rq4/f9/na | 72 | 0 | 4.994 | 4.167 | 38.3 | 9.173 |
| codex | rq4/f9/na | 74 | 0 | 4.863 | 4.054 | 38.1 | 9.223 |
