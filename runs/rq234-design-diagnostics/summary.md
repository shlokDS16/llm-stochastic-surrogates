# Design diagnostics of the interim full-text estimates (B8)

Source run `runs/rq234-final` (110 full texts); script `analysis/fulltext/rq234_design_diagnostics.py`; weights w = N_g / r_g per respondent, N_g the frame size of the estimation group, r_g its respondents (v0.12.1 merge applied). Kish n_eff = (sum w)^2 / sum w^2. Evidence level E4.

| coder | respondents | weights min-max (ratio) | Kish n_eff | eligible | weights min-max (ratio) | Kish n_eff (eligible) | strata | groups | groups with 1 / 0 respondents | df | t |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude | 110 | 1.3-55.0 (41.2) | 67.3 | 80 | 1.3-49.0 (36.8) | 51.8 | 32 | 28 | 0 / 0 | 82 | 1.989 |
| codex | 110 | 1.3-55.0 (41.2) | 67.3 | 81 | 1.3-49.0 (36.8) | 50.5 | 32 | 28 | 0 / 0 | 82 | 1.989 |

| prevalence | coder | k/n | unweighted % | weighted % | Wald 95% | logit 95% | df | Kish n_eff (domain) |
|---|---|---|---|---|---|---|---|---|
| Wording perturbation | claude | 27/80 | 33.8 | 24.4 | 14.4 to 34.3 | 15.8 to 35.6 | 82 | 51.8 |
| Wording perturbation | codex | 32/81 | 39.5 | 28.9 | 16.9 to 40.9 | 18.5 to 42.2 | 82 | 50.5 |
| Any of the judged perturbation types | claude | 48/80 | 60.0 | 54.1 | 41.2 to 66.9 | 41.2 to 66.4 | 82 | 51.8 |
| Any of the judged perturbation types | codex | 47/81 | 58.0 | 49.0 | 36.6 to 61.4 | 36.9 to 61.2 | 82 | 50.5 |
| f2 temperature stated | claude | 31/80 | 38.8 | 42.2 | 30.3 to 54.0 | 31.0 to 54.3 | 82 | 51.8 |
| f2 temperature stated | codex | 38/81 | 46.9 | 50.0 | 37.1 to 62.9 | 37.4 to 62.6 | 82 | 50.5 |
| f11 preregistration cited | claude | 5/80 | 6.2 | 5.3 | 0.0 to 12.4 | 1.3 to 18.8 | 82 | 51.8 |
| f11 preregistration cited | codex | 7/81 | 8.6 | 6.3 | 0.0 to 13.9 | 1.8 to 19.6 | 82 | 50.5 |
| f12 code or data link | claude | 41/80 | 51.2 | 46.4 | 32.9 to 60.0 | 33.4 to 59.9 | 82 | 51.8 |
| f12 code or data link | codex | 53/81 | 65.4 | 62.6 | 48.5 to 76.7 | 47.8 to 75.3 | 82 | 50.5 |

Venue sensitivity: response propensity by venue class (journal or chapter / conference / preprint or other), rescaled within each estimation group so group totals stay N_g.

| prevalence | coder | primary % (95%) | venue-adjusted % (95%) | change (points) |
|---|---|---|---|---|
| Wording perturbation | claude | 24.4 (14.4 to 34.3) | 24.9 (14.7 to 35.1) | +0.5 |
| Any of the judged perturbation types | claude | 54.1 (41.2 to 66.9) | 54.3 (41.5 to 67.2) | +0.3 |
| f2 temperature stated | claude | 42.2 (30.3 to 54.0) | 42.4 (30.5 to 54.2) | +0.2 |
| f11 preregistration cited | claude | 5.3 (0.0 to 12.4) | 5.1 (0.0 to 11.9) | -0.2 |
| f12 code or data link | claude | 46.4 (32.9 to 60.0) | 46.7 (33.2 to 60.2) | +0.3 |
| Wording perturbation | codex | 28.9 (16.9 to 40.9) | 28.8 (16.8 to 40.9) | -0.1 |
| Any of the judged perturbation types | codex | 49.0 (36.6 to 61.4) | 48.5 (36.2 to 60.9) | -0.4 |
| f2 temperature stated | codex | 50.0 (37.1 to 62.9) | 50.2 (37.3 to 63.0) | +0.2 |
| f11 preregistration cited | codex | 6.3 (0.0 to 13.9) | 6.1 (0.0 to 13.4) | -0.2 |
| f12 code or data link | codex | 62.6 (48.5 to 76.7) | 63.1 (49.1 to 77.1) | +0.5 |
