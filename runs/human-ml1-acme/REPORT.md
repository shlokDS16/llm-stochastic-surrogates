# Human benchmark for AF, QA, NR (ML1), single-site SEs, canonical signs, grids

Built 2026-11-06 by `analysis/human_ml1/acme_items.py` (stages `build effects spread reml table grids`; REML step by
`analysis/human_ml1/metafor_acme.R`, a path-only copy of `metafor_human.R`); tests `analysis/human_ml1/tests/test_acme_items.py`
(3 pass). CPU only, no model output read, no existing file in `analysis/human_ml1/` or `runs/human-ml1/` changed, nothing committed.
Input: the labelled cleaned ML1 file (6,344 rows); site key `referrer`, identical to `P1.csv` (36 sites).

## Files
- `data/processed/ml1/AF.csv` (6,292 rows, 36 sites), `QA.csv` (6,325), `NR.csv` (6,276); columns `site,x,y` (AF also `y_yes`, the raw Yes answer).
- `runs/human-ml1-acme/`: `coding_audit.md` (+`audit.json`), `site_effects.csv` (adds `rd`, `v_rd` for AF and NR), `moment_summary.json`,
  `spread_a1.txt/.json` (test inversion), `metafor_results.json/.log`, `benchmark_table.md/.csv`, `single_site_se.csv`,
  `canonical_signs.csv`, `published_comparison.json`.
- `analysis/acme/grids.yaml`.

## Coding and audit (see `coding_audit.md` for the cross-tabs)
Conventions as briefed. x comes from the question answered; the released group variable is audited against it.
- AF (a = forbid question, b = allow question per `Codebook.xlsx`): 0 respondents answered both, 52 neither, **0 contradict
  `allowedforbiddenGroup`**; released composite DV matches the raw answer in all 6,292 cases.
- QA: 0 both, 19 neither, **0 contradict `quoteGroup`**. Raw scale confirmed 1 = strongly agree (Codebook, Measures); y = 10 - raw equals the
  released `quote` for all cases, range 1..9.
- NR: `reciprocityusa` = US question asked first, `usb` = US question second (other-country first). 0 both, 68 neither, **0 contradict
  `reciprocitygroup`** (its label "Asked first" refers to the US question), and 0 respondents whose US-question version and
  other-country-question version imply different orders. `y` equals released `reciprocityus`.
So, unlike the gambler's-fallacy group, none of the three released group variables is miscoded for these items.

## Pooled effects against the ML1 publication (`published_comparison.json`; published = ML1 supplement items 6-8 and manuscript Table 3)
| item | this run | published | agreement |
|---|---|---|---|
| NR | 77.33 percent Yes (US second) vs 63.93 (US first); chi2 135.32, d(phi) 0.297; REML log OR 0.659 [0.521, 0.797], Q 38.89 | 77.3 vs 63.9; chi2 135.32, d 0.3; Q 38.89 | exact |
| QA | Washington M 5.928 (SD 2.207), bin Laden 5.232 (2.113); t(6323) 12.79, d 0.322; REML g 0.309 [0.229, 0.389], Q 67.70 | 5.93 (2.2), 5.23 (2.11); t 12.79, d 0.32; Q 67.69 | exact |
| AF, raw-Yes coding | chi2 3,088.69, d(phi) 1.964; REML Q 180.4, tau 0.901 | chi2 3,088.69, d 1.96; Q 180.40 | exact |
| AF, anti-speech coding (used for the benchmark) | 7.22 percent Yes to forbid vs 23.73 percent No to allow; chi2 328.8, d(phi) 0.470; REML log OR -1.385 [-1.549, -1.220] (d-equivalent -0.76), Q 29.0 (p 0.754), I2 0 | percentages 7.2 and 23.7 agree | percentages agree; effect and Q differ by design, see below |

**AF finding (needs a decision).** The published ML1 allowed/forbidden numbers (d 1.96, Q 180.4, "among the largest effects") are computed on the raw
Yes answer compared across the two questions, which sets "Yes to forbid" (anti-speech) against "Yes to allow" (pro-speech). With the anti-speech
coding (Yes to forbid, No to allow; Rugg's contrast, and the one in the brief) the effect is a log OR of -1.385 (risk difference -0.182 [-0.210, -0.153]),
the log-odds-ratio heterogeneity is nil (tau 0.000 [0.000, 0.360], I2 0, S^H test inversion 0.000 [0.000, 0.465]) but on the risk-difference scale there is
heterogeneity (tau 0.059 [0.030, 0.092], I2 55.6). The raw-Yes coding is kept in `site_effects.csv` as `check_ml1_published_yes_coding` (S^H 0.844
[0.589, 1.078]) so both are available. The LLM readout must use the same coding as the human benchmark; the brief fixes anti-speech coding, so that is the primary row.
The sign of AF is negative (forbid wording lowers the anti-speech share).

## Between-site spread (`benchmark_table.md`, primary rows)
| item | metric | REML mu | REML tau [Q-profile] | S^H moment [basic bootstrap] | S^H test inversion |
|---|---|---|---|---|---|
| AF | log OR | -1.385 | 0.000 [0.000, 0.360] | 0.000 [0.000, 0.571] | 0.000 [0.000, 0.465] |
| QA | g | 0.309 | 0.164 [0.090, 0.282] | 0.180 [0.000, 0.257] | 0.181 [0.085, 0.262] |
| NR | log OR | 0.659 | 0.165 [0.000, 0.345] | 0.000 [0.000, 0.366] | 0.000 [0.000, 0.337] |
Raw-scale (`sens_raw`) rows are also in the table (AF risk difference, QA rating points, NR risk difference).

## Single-site SE and canonical signs
`single_site_se.csv` (all 10 items): `se_single_site_primary` = median over the 36 sites of sqrt(v) of the site's primary effect (log OR for P1, AF, NR;
Hedges g for the rest); also median n1, n0, median pooled SD, and the same statistic on the raw scale (sqrt(s1^2/n1 + s0^2/n0)). Primary values:
P1 0.425, P2a 0.239, P2b 0.265, P2c 0.283, P2d 0.270, P3 0.199, P4 0.206 (log(1+x) scale), AF 0.655, QA 0.202, NR 0.443.
`canonical_signs.csv`: positive for P1, P2a-d, P3, P4, QA, NR; **negative for AF** (x1 = forbid). All 10 pooled REML intervals exclude 0.

## Grids (`analysis/acme/grids.yaml`)
Raw y of all respondents, 1st and 99th percentile (numpy linear), 15 log-spaced values, 2 significant digits, integers, anchors (read from the W0 yaml)
replacing the nearest value and kept exactly. P2a [1,550, 5,900], P2b [201,000, 4,900,000], P2c [2,100, 45,400], P2d [106, 49,000]: each has K = 15.
P4 (`y_raw`) [0 floored to 1, 216]: rounding merges the two lowest points, so the literal rule gives **K = 14** (1 ... 220); the file also holds
`grid_alt_exactly_K` for P4 with 15 unique values (log-spaced with 16 points, then rounded). Pick one before freezing.

## Uncertain or to note
- AF coding choice above (the published ML1 effect is on a different coding than the benchmark).
- Moment-estimator seed 20261106 and test-inversion seed 20261107 differ from the pilot's seeds, so bootstrap intervals are not the pilot's draws.
- Existing `build_tidy.py` points to `.../extracted/Data/Data/...values.dat`; the real folder is `extracted/data/Data` (case-insensitive on Windows, so it works); I used the labels file as briefed and cross-checked group codes against the values file.
- Single-site SE is a median over sites (36 sites, so the average of the two middle values), not the SE at a formula-derived median n.
