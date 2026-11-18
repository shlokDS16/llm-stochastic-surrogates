# SPEC for Fig 3 (key `corpus`, `\FigCorpus`, two panels): corpus-to-structure

Owner of the figure: Section 4 (`paper/acme/04-state-of-art-specification.tex`). To be drawn by `figure-smith`; this file is the brief.
Output: `paper/acme/figures/fig-corpus.pdf` (vector, fonts embedded) plus a 300 dpi PNG for inspection; script
`analysis/acme/figures/fig_corpus.py`. Placeholder size in `floats.tex`: two columns (`figure*`), height about 6 cm.

## Message of the figure
The coded studies map onto the structure of Section 4. Panel (a): the literature grew by two orders of magnitude from 2018 to
2026 and the leading paradigm family changed; the families fall into three groups, each tied to the subsection that treats its
specification problem. Panel (b): the model families that abstracts name diversified, and the share of abstracts naming no family
rose. Both panels are counts or shares of a complete frame (2,022 records), not estimates: draw no error bars or intervals and
say so in the footer note (see "Annotations").

## Panel (a): records by first named paradigm family and publication year (stacked bars)
- Data file: `runs/rq1-fig2-years/fig2_data.csv`, rows with `view == "A"`.
  Columns: `view, year, first_family, n, partial_year`. Years 2018 to 2026 (`year` integer; `partial_year == 1` only for 2026).
  `first_family` in {HB, JDM, RE, TOM, MEM, LANG, LEARN, NUM, MOR, DEV, OTH, none}.
- Check before drawing (assert): the sum of `n` per year equals `runs/rq1-fig2-years/metrics.json` key `total_by_year.A[year]`,
  and the grand total equals 2,022 (`runs/rq1-tables/T-RQ1a.csv`, row "N (denominator)", column `A_n`). The same series is
  in `runs/rq1-tables/T-RQ1d.csv` (rows `view == A`, `bin_type == year`).
- Encoding: x = publication year (categorical, 2018 to 2026); y = number of records (linear, from 0; no broken axis);
  stack = first named paradigm family, drawn in this order from the bottom, which is also the legend order and groups the
  families by subsection:
  1. group "choice and judgement" (to Section 4.2, prompt wording and order): JDM, HB, MOR, RE
  2. group "mental-state and developmental" (to Section 4.1, item source): TOM, DEV
  3. group "language, memory, learning, numerical" (to Section 4.5, readout): LANG, MEM, LEARN, NUM
  4. ungrouped: OTH (other), none (no family named in the abstract)
- Group-to-subsection labels: draw a thin bracket to the right of the legend entries of each group with the label
  "Sec. 4.2", "Sec. 4.1", "Sec. 4.5" (take the numbers from the compiled LaTeX counters if feasible, otherwise hard-code and
  re-check at the final build; the labels are `sec:spec-prompt`, `sec:spec-task`, `sec:spec-readout`). OTH and none carry no bracket.
  The grouping is the authors' analytic grouping, not a coded variable; the caption states this through the group names.
- Totals: print the year total above each bar (2018 to 2025 as integers; 2026 as the integer followed by a dagger or "partial").
  The 2018 to 2021 bars are barely visible at this scale; the printed totals carry them.
- 2026: hatched outline or lighter edge plus the word "partial" under the tick (search ran on 2026-10-16).
- Colour-blind-safe palette (Okabe and Ito 2008, hex codes below). Hue = group, lightness step = family within the group,
  and a distinct hatch for each family inside a group so that adjacent segments never rely on lightness alone:
  - choice and judgement: blue `#0072B2` family; JDM `#0072B2` solid, HB `#56B4E9` solid, MOR `#0072B2` with hatch "//" on a
    white fill, RE `#56B4E9` with hatch "\\\\" on a white fill
  - mental-state and developmental: vermillion `#D55E00` for TOM, `#E69F00` for DEV
  - language, memory, learning, numerical: bluish green `#009E73` for LANG, light green `#8FD1B5` for MEM,
    `#009E73` hatched "xx" on white for LEARN, `#8FD1B5` hatched ".." on white for NUM
  - OTH `#999999`; none `#FFFFFF` fill with a `#555555` outline and "//" hatch (it means "abstract silent", not a family)
  Check with a deuteranopia and a protanopia simulation (colorspacious or the matplotlib `cvd` tools) and confirm that the
  segment order is still readable; the stack order and the direct legend labels are the fallback.
- Legend: one column, in stack order from top to bottom of the stack, to the right of the axes, with family names spelled out
  ("Judgement and decision making", "Heuristics and biases", "Moral judgement", "Reasoning", "Theory of mind and social
  cognition", "Developmental tasks", "Language and psycholinguistics", "Memory and attention", "Learning and categorisation",
  "Numerical cognition", "Other", "No family named"). Names as in `analysis/rq1/rq1_common.py#FAMILY_NAMES`.

## Panel (b): model families named in abstracts, by publication year (annotated heat map)
- Data source: the function `rq1_model_family_by_bin("year")` in `analysis/acme/make_autonumbers.py` (import it:
  `sys.path.insert(0, "analysis/acme"); from make_autonumbers import rq1_model_family_by_bin`). It reads the coded batch files
  `data/processed/rq1/rq1-batch-*.jsonl` and `data/processed/records.jsonl` through `analysis/rq1/rq1_common.py#load_frame`,
  the same code path that fills the `\NUM{sp.mfp.*}` keys of the text, so figure and text share one source.
  Columns of the long table: `bin, n_records, family, n_named, share_pct`. Bins: `2018-2021` (pooled), `2022`, `2023`, `2024`,
  `2025`, `2026`. Families (rows): GPT, Claude, Gemini, Llama, Mistral, Qwen, OLMo, other, none named.
- Check before drawing (assert): the sum over bins of `n_named` per family equals the view-A column of
  `runs/rq1-tables/T-RQ1b.csv` (GPT 677, Claude 142, Gemini 141, Llama 137, Mistral 35, Qwen 80, OLMo 4, other 245,
  none named 1,189) and `n_records` over bins sums to 2,022.
- Encoding: rows = model families, in this order from the top: GPT, Claude, Gemini, Llama, Qwen, Mistral, OLMo, other,
  none named (a thin rule above "none named" because it is the complement, not a family); columns = the six bins; cell fill =
  `share_pct` (percent of the records in that bin whose abstract names the family), single-hue sequential scale (viridis or
  cividis, 0 to the maximum cell, one colourbar labelled "percent of records in the year"). Cell text = `share_pct` rounded to
  one decimal, printed in black or white by cell luminance (WCAG contrast at least 4.5). Rows do not sum to 100 because a record
  can name several families.
- Column header: the bin label with the bin size beneath it as `n = ...` (`n_records`: 17, 26, 147, 302, 613, 917). Bins with
  fewer than 30 records (2018-2021 and 2022) get a dotted cell outline and the footer note "bins under 30 records are
  indicative only". 2026 gets the word "partial" under its label.
- Why a heat map and not lines: nine families, tiny early bins and non-additive shares make a line chart unreadable; the
  annotated cells show every number and let the reader see small bins.

## Layout and craft rules (blueprint 5 bar 15)
- Width 17.4 cm (two columns), height about 6.5 cm; panel (a) about 58 percent of the width, panel (b) 42 percent; a single
  8 to 9 pt sans-serif face (DejaVu Sans or Arial) throughout, tick labels 8 pt, annotations 7 pt minimum, no text smaller than 7 pt.
- Panel letters "(a)" and "(b)" bold, 9 pt, upper left outside the axes; the text cites them as `Fig.~\ref{fig:corpus}a` and
  `Fig.~\ref{fig:corpus}b`.
- No title inside the image and no caption text inside the image (the caption is in `floats.tex`, macro `\FigCorpus`).
- Footer note inside the image, 7 pt, one line under panel (a): "Counts of the 2,022 records of the liberal frame; abstract-level
  coding; an empty field means the abstract is silent." Do not repeat numbers that the caption or text carries beyond the
  totals; the totals are the data.
- Uncertainty: none is drawn, because the frame is complete (every record coded) and the quantities are counts and shares
  of that frame, not estimates. Say this in the footer note of panel (b) as well: "shares of the frame, not estimates".
- Inspect the rendered PNG for overlap of the year totals with the bars, legend collision with the brackets, hatch legibility at
  print size, and the heat-map text contrast; fix before handing back.
- No result numbers go into the LaTeX caption (ACME caption rule); the caption in `floats.tex` already describes both panels.

## As drawn (figure-smith, 2026-11-07)
Width is the journal text width 16.0 cm (not 17.4 cm: `\textwidth` of the sn-jnl wrapper), height 7.7 cm; Arial throughout (7 pt annotations, 8 pt ticks).
Panel (a) legend names wrap to two lines for four families; year ticks are rotated 90 degrees; 2026 is marked by a dashed bar outline and the tick text "(partial)".
Panel (b) 2018-2021 header reads "2018-21" and the n labels read "n=17" for width. Caption in `floats.tex` finalised (explicit `figure*`, no `\captionTODO`).
