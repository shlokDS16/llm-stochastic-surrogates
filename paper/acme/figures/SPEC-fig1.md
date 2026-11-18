# SPEC for Fig 1 (key `framework`, `\FigFramework`, one wide panel): the measurement pipeline of a simulated-participant experiment

Owner of the figure: Section 1 (`paper/acme/01-introduction.tex`, map of the paper). To be drawn by `figure-smith`; this file is the brief.
Output: `paper/acme/figures/fig-framework.pdf` (vector, fonts embedded) plus a 300 dpi PNG for inspection; script
`analysis/acme/figures/fig_framework.py`. Placeholder size in `floats.tex`: two columns (`figure*`), height about 6 cm. The caption is
already final in `floats.tex` (macro `\FigFramework`); its first sentence carries the computational framing (blueprint 16, F1a): a
language model used in place of a participant is a stochastic computational surrogate whose output must be verified, validated and
sensitivity-analysed. No text of the caption goes into the image.

## Message of the figure
One simulated response is produced by a chain of nine stages. Seven of them are inputs or conversion steps of the surrogate, the eighth
turns the output into the effect, and the ninth is the human data against which the effect is validated. Every later section of the
paper attaches to a stage: the review sections read how studies specify, validate and audit it, and the benchmark varies four of the
stages and holds the rest fixed within an item. The same nine stage names are used wherever the paper refers to a stage (Sections 2,
4, 5, 6 and 7); keep the wording exactly as below.

## Data
None. This is a design drawing, so no number from a run file enters the image. Do not print level counts, shares or any result (those
belong to the later figures and to the text via `\NUM`). The section numbers on the tags are the only numerals; take them from the
compiled LaTeX counters if the build allows (labels in the table below), otherwise hard-code and re-check at the final build.

## Nine stages, in order, with both tags (exact wording)

| # | Stage name (box text) | Review tag (section, label) | Benchmark factor tag | Notation in the paper |
|---|---|---|---|---|
| 1 | paradigm | Sec. 4.1 (`sec:spec-task`) | fixed: ten items | item `p` |
| 2 | stimulus | Sec. 4.1 (`sec:spec-task`) | fixed: item materials | condition `x` |
| 3 | wording | Sec. 4.2 (`sec:spec-prompt`); audit Sec. 6.2 (`sec:audit-vary`) | varied: W (random sample) | `\facW` |
| 4 | option order | Sec. 4.2 (`sec:spec-prompt`); audit Sec. 6.2 | varied: O | `\facO` |
| 5 | decoding / temperature | Sec. 4.4 (`sec:spec-decoding`); audit Sec. 6.2 | varied: T | `\facT` |
| 6 | model | Sec. 4.3 (`sec:spec-model`); audit Sec. 6.2 | varied: M (fixed set) | `\facM` |
| 7 | readout | Sec. 4.5 (`sec:spec-readout`) | fixed: exact answer probabilities | valid mass, readout mean |
| 8 | scoring | Sec. 4.5 and Sec. 5.2 (`sec:spec-readout`, `sec:val-effect`) | fixed: scoring map per item | effect (contrast of two conditions) |
| 9 | human reference | Sec. 5.1 (`sec:val-reference`) | yardsticks, not a factor | single-site SE and between-site SD |

The letters W, O, T and M follow the facet notation of Table 2 (`macros.tex`: `\facW`, `\facO`, `\facT`, `\facM`); use the same
letters in roman type. The word "fixed" and the word "varied" are the only two states besides "yardstick".

## Layout
- Width 17.4 cm, height about 6 cm. One horizontal chain of nine boxes, left to right, each about 1.75 cm wide and 1.3 cm high, gaps
  about 0.2 cm; box text 7.5 pt sans-serif, centred, may wrap to two lines ("decoding / temperature", "human reference").
- Arrows: solid arrows 1 to 8 inside the chain, one stage to the next. A dashed arrow from box 9 (human reference) back to box 8
  (scoring), labelled "compared with" in 7 pt. Draw box 8 and box 9 with a shared bracket underneath labelled "validation" so that the
  comparison reads as the place where Section 5 attaches.
- Brackets above the chain: over boxes 1 to 7 a bracket labelled "stochastic simulator (computational surrogate)"; over boxes 8 and 9 a
  bracket labelled "effect and human data". The simulator bracket carries a second line in 7 pt, "verification of the estimator, sensitivity
  analysis of the set-up", and the effect bracket "validation against human data". These three tasks (verify, validate, sensitivity-analyse)
  are the framing of the caption's first sentence; keep the wording close to the caption.
- Tags under each box, two chips of height 0.45 cm stacked: the upper chip is the review tag ("Sec. 4.2"), the lower chip the benchmark tag
  ("W varied", "fixed", "yardstick"). Where a stage carries two review sections, put them in the same chip separated by a comma
  ("Sec. 4.5, 5.2"); the audit section 6.2 goes into the same chip after a semicolon for stages 3 to 6 ("Sec. 4.2; 6.2").
- A thin legend line at the foot, 7 pt: "upper chip: review section; lower chip: factor of the benchmark in Section 7". Resolve the
  benchmark section number in the same way as the review tags.

## Colour and craft (blueprint 5, bar 15)
- One colour-blind-safe palette (Okabe and Ito). Varied factors (stages 3 to 6): blue boxes with white text; fixed stages (1, 2, 7, 8): light
  grey boxes with dark text; human reference (9): orange box. The chips take a white fill and a thin outline in the box colour. Do not rely
  on colour alone: the lower chip also spells "varied", "fixed" or "yardstick".
- A single sans-serif face (DejaVu Sans or Arial), nothing below 7 pt. No gradients, no shadows, no 3-D, no icons.
- Panel letters are not needed (one panel). No title and no caption text inside the image. No numerals other than section numbers.
- Inspect the rendered PNG for text overflow in the narrow boxes, overlap of the brackets with the chips and arrows, and the dashed arrow
  crossing the chips; fix before handing back. At print size the longest box text ("decoding / temperature") must stay inside its box.

## Consistency checks before handing back
- The nine stage names equal the list in the caption of `\FigFramework` (paradigm, stimulus, wording, option order, decoding and
  temperature, model, readout, scoring, human reference) and the stage names used in `04-state-of-art-specification.tex` (header comment)
  and `05-state-of-art-validation.tex` (first paragraph).
- Every review tag points to a subsection that exists in the compiled PDF; every varied tag (W, O, T, M) is a facet in
  `paper/acme/macros.tex` and in Eq. (effect) of Section 2.
- The text of Section 1 says that each stage is tagged with the review section that treats it and the benchmark factor that varies it;
  the image must show exactly those two tags.

## As drawn (figure-smith, 2026-11-07)
Script `analysis/acme/figures/fig_framework.py`; output `fig-framework.pdf` (vector, TrueType fonts embedded, 16.0 cm = text width, 5.55 cm high). Nine stage names exactly as in the table; the two chips and the three brackets are as specified. Section numbers are read from the compiled aux file and asserted equal to the fallback table in the script. No count and no run file enter the figure. Differences from the brief:
- Width is the text width of the wrapper (16.0 cm), not 17.4 cm; the boxes are 1.6 cm wide with 0.17 cm gaps (chip text "Sec. 4.2; 6.2" is 1.5 cm at 7 pt).
- "compared with" is a dashed arc above scoring and human reference (the 0.17 cm gap is too small for a label), and the arc is drawn from the human reference back to scoring.
- The validation bracket sits below the lower chips of boxes 8 and 9 (the chips occupy the space directly under the boxes); its label reads "validation (Section 5)".
- The foot legend adds three colour swatches (varied factor, fixed stage, human reference) before the specified legend sentence. All text is 7 pt.
- The upper chip of stages 3 to 6 holds the audit section after a semicolon, as specified; the audit section is Sec. 6.2.
Checks: text-in-box and text-overlap asserts in the script; grey-scale render keeps varied (dark), fixed (light) and human (mid) apart; the lower chip spells the state, so colour is not the only cue.
