# SPEC for Fig 5 (key `validation`, `\FigValidation`, two panels): human comparators and fidelity metrics

Owner of the figure: Section 5 (`paper/acme/05-state-of-art-validation.tex`). To be drawn by `figure-smith`; this file is the brief.
Output: `paper/acme/figures/fig-validation.pdf` (vector, fonts embedded) plus a 300 dpi PNG for inspection; script
`analysis/acme/figures/fig_validation.py`. Placeholder size in `floats.tex`: one column (`figure`), height about 6 cm. If two
panels do not fit legibly at one column, change the macro to `\acmefigurewide` (two columns, 17.4 cm by about 6.5 cm, panels side by
side); decide at the first render.

## Message of the figure
The human references are mostly published norms and own samples, none is a multi-site dataset, and about one study in five has
no human comparison; the metrics divide into two that two readings reproduce (accuracy against a key, correlation with human
responses) and four that they do not. Both panels are design-weighted shares of eligible studies from the full-text sample, so
estimates with design-based intervals; they are not counts of a complete frame.

## Data (all from one run; no number typed by hand)
- File: `runs/rq234-final/rq3.csv`. Columns used (prefix `claude_` = first coding pass, `codex_` = second coding pass; label them
  "first pass" and "second pass" in the figure, never by the prefix): `feature, <pass>_k, <pass>_n_domain, <pass>_est_pct,
  <pass>_lo_pct, <pass>_hi_pct, <pass>_cp_unweighted_pct, kappa, percent_agreement, passes_v012_rule`.
- Alternative route to the same values: `\NUM{val.*}` keys of `analysis/acme/make_autonumbers.py` (`_section5_numbers`), which
  assert equality with the rendered tables `runs/rq234-final/rq3.md`. Import `NUMBERS` from that module for the check
  (`sys.path.insert(0, "analysis/acme"); from make_autonumbers import NUMBERS`) and assert that every plotted value equals the
  matching key (`val.ref.*`, `val.met.*`).
- Assert before drawing: `n_domain` is 80 (first pass) and 81 (second pass) for every row, equal to `\NUM{rm.nElig1}` and
  `\NUM{rm.nElig2}`.

## Panel (a): human reference types listed by the eligible studies (`feature` starts with `rq3|types_any|`)
- Rows, top to bottom: published_norms, own_sample, none ("No human comparison"), crowd_norms, replication_dataset
  ("Replication dataset (multi-site)"). Spell the labels out; no codes.
- Encoding: horizontal dot-and-interval rows. x = design-weighted share of eligible studies in percent (0 to 100, linear, one
  shared axis label "percent of eligible studies"). Per row, two marks offset vertically by a fixed amount: first pass = filled
  circle, second pass = open diamond; the 95 percent interval (`lo_pct`, `hi_pct`) as a thin horizontal line through the mark. Same
  mark shapes and offsets in panel (b).
- All five fields met the agreement rule (`passes_v012_rule == True`), so every row carries an interval. The replication-dataset row
  has a zero estimate with zero variance (`lo == hi == 0`): draw the point at zero and the exact unweighted upper bound from
  `<pass>_cp_unweighted_pct` (string "0.0-4.5": use the part after the hyphen) as a short arrow or bar ending at that bound, and
  write "0 of 80, 0 of 81" at the right of the row (take the counts from `<pass>_k` and `<pass>_n_domain`).
- Right of each row print `k/n` for both passes in 7 pt grey (first pass above, second pass below), e.g. from `<pass>_k` and
  `<pass>_n_domain`.
- Do not draw the primary-type shares (`rq3|primary_type|*`); they are in the text. Do not add a legend entry for them.

## Panel (b): metric types assigned to the human comparison (`feature` starts with `rq3|outcome_types|`)
- Rows, top to bottom, grouped by the rule status so that the split is visible: first the two fields that met the rule
  (accuracy against a key; correlation with human responses), then a thin separator and the label "pass-specific, no interval",
  then the four that failed it (effect size; bias magnitude; choice distribution; other). Use the `passes_v012_rule` column to
  decide the group; the order inside each group is the order given here. Omit the two sparse types `agreement` and `effect`
  (`kappa` is empty, one study at most) and say so in the footer note.
- Fields that met the rule: same dot-and-interval encoding as panel (a).
- Fields that failed the rule: two unconnected marks (same shapes as above) with NO interval; no line between the two marks, because
  a connecting line reads as an interval. Print `kappa` of the field in 7 pt grey at the right (from the `kappa` column, two
  decimals). Use a hatched light-grey band behind these four rows so that the "no interval" status is visible without the label.

## Colour, size, craft (blueprint 5 craft rules)
- One colour-blind-safe palette (Okabe and Ito 2008): first pass `#0072B2`, second pass `#D55E00`; grey `#555555` for annotations;
  shapes differ as well as colours (circle against diamond), so the figure survives greyscale. Check with a deuteranopia and a
  protanopia simulation.
- 8 to 9 pt sans-serif single face, tick labels 8 pt, annotations 7 pt minimum. Panel letters "(a)" and "(b)" bold, 9 pt, upper left
  outside the axes; the text cites them as `Fig.~\ref{fig:validation}a` and `Fig.~\ref{fig:validation}b`.
- Share a legend for the two passes once (above panel a): filled circle "first pass", open diamond "second pass".
- No title and no caption text inside the image (the caption is in `floats.tex`, macro `\FigValidation`). No result numbers in the
  caption.
- Footer note inside the image, 7 pt, one line: "Design-weighted shares of eligible studies with 95 percent design-based intervals where the
  field met the agreement rule; a study can list several types; two sparse metric types not shown." Do not repeat the plotted numbers.
- Uncertainty is in the same panel as the estimate (interval lines), and for the failed fields the absence of an interval is the
  message.
- Inspect the rendered PNG for overlap of the `k/n` text with the interval lines, legibility of the hatch, the arrow on the
  zero row, and the pass offsets; fix before handing back.

## As drawn (figure-smith, 2026-11-07)
Changed to two columns (`figure*`, 16.0 cm text width by 6.7 cm); a one-column version cannot hold both panels at 7 pt. Arial; `kappa` printed as a Greek letter.
The zero row also prints "exact upper bound 4.5" next to the bar. Caption finalised in `floats.tex`.
