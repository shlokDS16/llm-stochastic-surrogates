# SPEC for Fig 10 (key `yardsticks`, `\FigYardsticks`, page-wide float about 15 cm tall): sites and set-ups on one axis

Script `analysis/acme/figures/fig_yardsticks.py`; output `paper/acme/figures/fig-yardsticks.pdf` + 600 dpi PNG + `<file>.source.json`.
Synthetic test only so far. Run: `.venv/Scripts/python.exe -I analysis/acme/figures/fig_yardsticks.py [--gstudy runs/acme-gstudy/A1] [--effects effects.csv]`.
`floats.tex` gives `\acmefigurewide{yardsticks}{7cm}`; the drawing needs about 15 cm (14 model rows plus the site band must carry 7 pt labels), so
change the height argument to 15cm (width stays the text width, 16.0 cm).

## Claim
Simulated set-up effects and Many Labs 1 site effects can be read on one axis (ML1-SD units): per item, whether the spread of a model's fixed
set-ups is wider or narrower than the spread of the human sites and than one laboratory's sampling error. The caption must state the distinct
estimands (C3, blueprint 14): sites are sample estimates (sampling variation over laboratories, with intervals); set-ups are deterministic
effects of fixed design choices (no interval); a yardstick, not an equivalence.

## Layout
One panel per item (5 x 2). Per panel, top to bottom: (1) pooled human effect (black diamond, Wald interval) with the between-site SD S^H as a
grey bar centred on it; (2) the Many Labs 1 sites, sample estimates with 95 percent intervals (green), sorted by estimate; (3) one row per model:
every wording x order cell of the main array at the reference temperature (vermillion dots, deterministic, no interval), the model mean (tick)
and a bar of mean +- its set-up SD s. Light blue band across the panel: pooled +- single-site SE c. Panel title: item, and the ratios of the
median set-up SD over models to c and to S^H (`yardsticks.csv`, `__median__` rows); an asterisk marks an S^H interval that reaches 0 (the ratio
is then not read as "humans agree"). Units: effect / sd_within, the unit of gstudy.py. Legend and the one-line key (s, c, S) are inside the
figure. Models drawn for an item are those in `setup_sd.csv` for that item (valid-mass exclusions respected).

## Reads
`<gstudy>/setup_sd.csv`, `<gstudy>/yardsticks.csv`, `<gstudy>/summary.json`, the effects table named in `summary.json` `config.effects` (or
`--effects`): the per-cell effects are NOT in the gstudy directory, so the figure re-reads the effects table gstudy.py read (real model output;
the guard requires it under runs/ when the output goes to paper/); `runs/human-ml1-acme/{arml_scales,pooled_sd_units,pooled_site_inputs}.csv`.
Site effect = `yi` / sd_within with `sqrt(vi)` / sd_within. Checked on synthetic data only: the lead should confirm on the real render that the
pooled diamond sits inside the site cloud (sign convention of `pooled_site_inputs.csv`).

## Not shown
The S^H interval is not drawn, only its estimate; it is in `yardsticks.csv` and Table 6.
