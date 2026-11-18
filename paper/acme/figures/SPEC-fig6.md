# SPEC for Fig 6 (renders as Fig. 5 in current float order; label FigAudit) (key `audit`, `\FigAudit`, two panels): practice for each source of simulator uncertainty, and the per-pass trend

Owner of the figure: Section 6 (`paper/acme/06-uncertainty-audit.tex`). To be drawn by `figure-smith`; this file is the brief.
Output: `paper/acme/figures/fig-audit.pdf` (vector, fonts embedded) plus a 300 dpi PNG for inspection; script
`analysis/acme/figures/fig_audit.py`. Placeholder in `floats.tex`: `\acmefigurewide{audit}{9cm}` (two columns, 17.4 cm wide, about
9 to 10 cm high). Panel (a) takes the left 62 percent of the width, panel (b) the right 38 percent. If panel (a) is not legible at
sixteen rows, raise the height to 11 cm and change the height argument in `floats.tex`; do not drop rows.

## Message of the figure
Wording and decoding are the only judged perturbation types that both coding passes read alike, and each is run by a minority of
eligible studies. Order, model version, seed and contamination rest on fields that failed the agreement rule, so their two
pass-specific values are shown without an interval. Repeated sampling of one prompt is the most common variation item and varies
only the sample, not the set-up. Temperature and code links are stated by many studies, the version and a preregistration by few.
The trend panel shows that the odds ratios per year are sensitivity displays; most intervals include one and no direction is
claimed. Design-weighted shares of eligible studies from the full-text sample, never counts of a complete frame.

## Data (all from one run; no number typed by hand)
- Shares, panel (a): `runs/rq234-final/rq4.csv`. Match rows on `feature`. Columns (prefix `claude_` = first coding pass, `codex_` =
  second coding pass; label them "first pass" and "second pass" in the figure, never by the prefix): `<pass>_k`, `<pass>_n_domain`,
  `<pass>_est_pct`, `<pass>_lo_pct`, `<pass>_hi_pct`, `kappa`, `percent_agreement`, `passes_v012_rule`.
- Trend, panel (b): `runs/rq234-final/rq4_trend.csv`. Columns: `coder` (`claude` = first pass, `codex` = second pass), `feature`,
  `OR_per_year`, `or_lo`, `or_hi`, `status` (`fitted` or `descriptive_only`), `passes_v012_rule`, `events`, `non_events`.
- Optional nonresponse bounds: `runs/rq234-final/nonresponse_bounds.csv` (`bound_lo_pct`, `bound_hi_pct`), not drawn in the figure,
  mentioned in the footer.
- Alternative route to the same values: the `\NUM{au.*}` keys of `analysis/acme/make_autonumbers.py` (`_section6_numbers`), which
  assert equality with the rendered table `runs/rq234-final/rq4.md`; keys `sp.f1.*`, `sp.f2.*` of `_section4_numbers` for the
  version and the temperature. Import `NUMBERS` from that module (`sys.path.insert(0, "analysis/acme"); from make_autonumbers import
  NUMBERS`) and assert that every plotted share equals its key (rounded to one decimal) and that every trend odds ratio equals
  `au.tr.*` where one exists.
- Assert before drawing: `n_domain` is 80 (first pass) and 81 (second pass) for every row except `f6_applicable|yes` (40 and 45);
  80 and 81 equal `\NUM{rm.nElig1}` and `\NUM{rm.nElig2}`.

## Panel (a): shares of eligible studies, three row groups, one shared x axis (percent of eligible studies, 0 to 100, linear)
Group headers in bold 8 pt, thin separators. Spell the labels out; no codes (`f5`, `f3`) in the figure. Rows, top to bottom
(feature key in `rq4.csv`, label, rule status at the time of writing; read the status from `passes_v012_rule` and do not hard-code it):

Group 1, "Perturbation run (type listed by the study)":
1. `robustness_tested|yes`, "At least one judged type" (met the rule)
2. `perturbation|wording`, "Prompt wording" (met)
3. `perturbation|decoding`, "Decoding setting" (met)
4. `perturbation|option_order`, "Option order" (failed)
5. `perturbation|model_version`, "Model version" (failed)
6. `perturbation|seeds`, "Seeds" (failed)
7. `perturbation|contamination`, "Contamination" (failed)

Group 2, "Variation item (variants compared in the coded text)":
8. `f7|yes`, "Two or more sampling settings" (met)
9. `f3|yes`, "Identical prompt sampled repeatedly" (met)
10. `f9|yes`, "Novel or perturbed items against memorisation" (met)
11. `f5|yes`, "Two or more wordings" (failed)
12. `f6_applicable|yes`, "Option order varied, studies that list options" (failed; denominators 40 and 45, say so in the label or at the right)
13. `f8|yes`, "Two or more model snapshots" (failed)

Group 3, "Stated only (documentation)":
14. `f2|yes`, "Decoding temperature stated" (met)
15. `f12|yes`, "Link to code or data" (met)
16. `f1|yes`, "Exact model version and query date" (rule met through percent agreement only; kappa close to zero; draw WITHOUT an
    interval, as Section 4 does, and print "kappa 0.05" at the right; take the value from the `kappa` column)
17. `f11|yes`, "Preregistration cited" (met; the t interval is truncated at zero for both passes: let the interval start at zero and
    add a small tick at zero; do not substitute the logit interval)

- Encoding: horizontal dot-and-interval rows. Per row, two marks offset vertically by a fixed amount: first pass = filled circle,
  second pass = open diamond. Rows whose field met the rule: the 95 percent design-based interval (`lo_pct`, `hi_pct`) as a thin
  horizontal line through the mark. Rows whose field failed the rule (and row 16): two unconnected marks, NO interval, no line between
  them (a connecting line reads as an interval). Put a hatched light-grey band behind the failed rows so that the "no interval"
  status is visible without the header, and print `kappa` (two decimals) in 7 pt grey at the right.
- Right of each row print `k/n` for both passes in 7 pt grey (first pass above, second below), from `<pass>_k` and `<pass>_n_domain`.
- Row 1 is the only row that mixes types: it is the share that ran at least one of the six judged types; set it apart by a thin
  line under it.
- Documentation rows (group 3) and variation rows (groups 1 and 2) answer different questions; do NOT draw a bracket, arrow or label
  that compares a group 3 row with a group 1 or 2 row, and do not align groups on one x position with a guide line.
- Do not draw nonresponse bounds; mention them in the footer.

## Panel (b): odds ratio per publication year, per pass (sensitivity displays)
- Rows, top to bottom: `robustness_tested|yes` ("At least one judged type"), `perturbation|wording`, `perturbation|decoding`,
  `perturbation|option_order`, `perturbation|model_version`, `perturbation|seeds`, `perturbation|contamination`. Same labels as panel (a).
- x axis: odds ratio per year on a log scale (ticks 0.25, 0.5, 1, 2, 4), reference line at 1. Same marks as panel (a) (circle first
  pass, diamond second pass), 95 percent interval (`or_lo`, `or_hi`) drawn for every fitted model, because the intervals belong to
  the within-pass trend fit and not to a prevalence. Rows whose field failed the agreement rule (`passes_v012_rule == False`) get the
  same hatched band as in panel (a), so the reader sees which fits rest on an unreliable field.
- A row and pass with `status == descriptive_only` has no mark: write "not fitted" in 7 pt grey at the row (fewer than ten studies with
  or without the item). In the data at the time of writing this applies to first-pass seeds and contamination.
- Do not annotate which intervals exclude one, do not colour them, and do not add a trend line or an arrow for direction. The text
  states that the three intervals that exclude one (all in the second pass) are reported for completeness.
- Share the row labels of panel (a) group 1 by aligning panel (b) rows with group 1 if the layout allows; otherwise repeat the labels.

## Colour, size, craft (blueprint 5 craft rules)
- One colour-blind-safe palette (Okabe and Ito 2008), identical to Fig 5: first pass `#0072B2`, second pass `#D55E00`; grey `#555555` for
  annotations; shapes differ as well as colours (circle against diamond), so the figure survives greyscale. Check with a deuteranopia
  and a protanopia simulation.
- 8 to 9 pt sans-serif single face, tick labels 8 pt, annotations 7 pt minimum. Panel letters "(a)" and "(b)" bold, 9 pt, upper left
  outside the axes; the text cites them as `Fig.~\ref{fig:audit}a` and `Fig.~\ref{fig:audit}b`.
- Share one legend for the two passes (above panel a): filled circle "first pass", open diamond "second pass".
- No title and no caption text inside the image (the caption is in `floats.tex`, macro `\FigAudit`). No result numbers in the caption.
- Footer note inside the image, 7 pt, one line: "Design-weighted shares of eligible studies with 95 percent design-based intervals where the
  field met the agreement rule; trend fits are exploratory sensitivity displays; nonresponse bounds are in the text." Do not repeat
  the plotted numbers.
- Uncertainty is in the same panel as the estimate (interval lines); for failed fields the absence of an interval is the message.
- Inspect the rendered PNG for overlap of the `k/n` text with interval lines, legibility of the hatch, the zero tick on row 17, the
  pass offsets, and that the "not fitted" notes do not collide with marks; fix before handing back.

## As drawn (figure-smith, 2026-11-07)
Width 16.0 cm (text width), height 12.0 cm. At 17 rows the two-line k/n block does not fit the row pitch, so k/n is printed in two columns headed "first" and "second" (first pass, second pass) at 7 pt grey, with kappa in a third column.
Version row (`f1|yes`) prints kappa with three decimals (0.045) to match `\NUM{sp.f1.kappa}` in the text. Panel (b) rows align with group 1; the x label reads "odds ratio per year".
Footer has three lines and explains the hatched band and the version row. Caption statement the data contradict: see report (version row has no interval although its field met the rule).
