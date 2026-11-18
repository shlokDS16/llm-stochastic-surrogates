# SPEC for Fig 11 (key `dstudy`, `\FigDstudy`): decision study

Script `analysis/acme/figures/fig_dstudy.py` (needs `dstudy_boot.csv` from `analysis/acme/dstudy_boot.py`); output
`paper/acme/figures/fig-dstudy.pdf` + 600 dpi PNG + `<file>.source.json`. Synthetic test only so far. Run in order:
`.venv/Scripts/python.exe -I analysis/acme/dstudy_boot.py --gstudy runs/acme-gstudy/A1 [--exclude <exclude.csv given to gstudy.py>]`, then
`.venv/Scripts/python.exe -I analysis/acme/figures/fig_dstudy.py --gstudy runs/acme-gstudy/A1`.
`floats.tex` has `\acmefigure{dstudy}{6cm}` (one column); ten items as small multiples need the text width: change to
`\acmefigurewide{dstudy}{8.6cm}` (figure drawn 16.0 x 8.6 cm).

## Claim
How many wordings (and orders) a study needs before the standard error of a model's mean effect falls below one laboratory's sampling error
and below the D-study target, item by item, with bootstrap intervals over wordings.

## Layout
One panel per item (5 x 2), x = number of wordings from 1 to the largest in `dstudy.csv`, y = SE in ML1 SD units (log axis). Curves: one order
(blue, solid), two orders (vermillion, dashed; only items with two orders), shaded 95 percent bootstrap interval over wordings (same colours).
Reference lines: the item's single-site SE c_p (grey; `arml_scales.csv`, `se_single_sd_units`) and the target (dotted; `NUMBERS['bm.dstudy.target']`,
asserted equal to the default of `gstudy.dstudy_min_design`). A marker on each curve at the first n_w below c_p, and the number printed in the
panel ("n_w = k", or "> max" when never reached). The SE is the D-study of one model drawn from the model-pooled variance components of the
item (gstudy.dstudy), not a per-model curve: gstudy.py has no per-model D-study.

## Reads
`<gstudy>/dstudy.csv`, `<gstudy>/dstudy_boot.csv`, `runs/human-ml1-acme/arml_scales.csv`, `make_autonumbers.NUMBERS`.
`dstudy_boot.py` imports the frozen gstudy.py unchanged, repeats the wording bootstrap with the same seeds, estimator and B, and asserts that its point
components equal `components_by_item.csv` and its point SE equals `dstudy.csv` before it writes the intervals (so a wrong --exclude is caught).
The figure refuses to run without `dstudy_boot.csv` (M9 asks for the bands) unless `--no-bands` is given.
