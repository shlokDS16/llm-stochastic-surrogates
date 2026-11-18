# SPEC for Fig 7 (key `design`, `\FigDesign`, one column or two): benchmark design schematic

Owner of the figure: Section 7.4 (`paper/acme/07-benchmark.tex`). To be drawn by `figure-smith`; this file is the brief. Output:
`paper/acme/figures/fig-design.pdf` (vector, fonts embedded) plus a 300 dpi PNG for inspection; script
`analysis/acme/figures/fig_design.py`. Placeholder size in `floats.tex`: one column, height about 6 cm; change `\FigDesign` to
`\acmefigurewide` if the four blocks below do not fit legibly at one column. No model outcome appears in this figure: it is a design
drawing and every count is a design constant.

## Message of the figure
One flow from the design cells to the effect array, with the two arms, the readout gate and the human anchor visible, so that a reader
sees how one answer probability becomes one effect and which facets the decomposition crosses. It beats E12 Fig 1 (blueprint 5) by
printing the level count on every facet and by marking what is exact and what is sampled.

## Counts (no number typed by hand)
Take every count from `\NUM` keys by importing `NUMBERS` from `analysis/acme/make_autonumbers.py` (`sys.path.insert(0, "analysis/acme");
from make_autonumbers import NUMBERS`) and assert before drawing: items `n.items` (ten, in `n.effects` effects), models `n.models`,
wordings `n.wordings`, orders `n.orders.max` (for `n.items.twoorder` items; one level for `n.items.oneorder`), temperatures `n.temps`
(`temps.levels`), set-ups at the reference temperature `bm.cells.T1` and across temperatures `bm.cells.all`, Arm S draws `bm.s.draws` for
`bm.s.nw` wordings at `bm.s.temps`, tree cap `bm.tree.cap`, valid-mass threshold `bm.vm.thr` on all but `bm.vm.frac` percent of prompts,
Many Labs 1 sites `n.sites`. Print them as digits (convert the number words with a small dict in the script).

## Layout (left to right, four blocks; one colour-blind-safe palette, 8 to 9 pt sans-serif)
1. **Design cells** (left). Five stacked boxes, one per facet, each labelled with its symbol and level count: item (10, 7 effects),
   model M (14), wording W (10, W0 verbatim), order O (2 for five items, 1 for five), condition x (2). A sixth box, "temperature T (4)",
   drawn dashed and attached to Arm L only, because it is applied to the logits after the forward pass.
2. **Rendering and readout** (centre). A box "prompt: chat template of the model, same text for all models" feeding two parallel lanes:
   - Arm L (solid outline, label "exact"): "one forward pass, float32 output layer", then "answer paths summed (choice, yes-no, rating)" and
     "digit tree to the cap (numeric items)"; output "answer probability P". The readout gate sits at the end of this lane as a diamond:
     "valid mass at least 0.9 on all but 5 percent of prompts" with two exits, "pair enters the array" and "pair excluded".
   - Arm S (dashed outline, label "sampled"): "W0 to W3, T 0.7 and 1.0, 50 draws per cell, recorded seeds", then "parse answer", then
     "sampled effect"; a dotted double arrow between the two lanes labelled "agreement gate G4 (diagnostic, outside H1 to H3)".
3. **Effect array** (centre right). A small 3-D block drawn as stacked slabs with axes M, W, O and a fourth slab series for T; caption
   inside: "effect in Many Labs 1 SD units". Arrow to two boxes: "variance shares (Eq. share), H1 and H3" and "set-up spread s (Eq. setup),
   H2, D-study".
4. **Human anchor** (right, drawn apart, grey fill). "Many Labs 1: 36 sites" feeding two boxes, "single-site SE c" (labelled "precision
   benchmark") and "between-site SD S^H with interval", both "in Many Labs 1 SD units"; a bracket joins them to the set-up spread box with
   the words "common scale, not an equivalence".

## Rules
- Exact items drawn solid, sampled items drawn dashed, human items grey; the legend sits inside the figure, not in the caption.
- No result value, no model name, no tool name (D-AI). Text in the figure at least 7 pt at final size; arrows end on box edges and never
  cross a label.
- Panel letters are not needed (one schematic). The caption in `floats.tex` already names the blocks; keep the wording identical to it.

## As drawn (figure-smith, 2026-11-07)
Script `analysis/acme/figures/fig_design.py`; output `fig-design.pdf` (vector, TrueType fonts embedded). Changed to a wide float: `\FigDesign` in `floats.tex` is now an explicit `figure*` (16.0 cm by 9.0 cm) with the caption text unchanged and no `\captionTODO`. Every count comes from `NUMBERS` (items, effects, models, wordings, orders and the two item groups, temperatures, cap, valid-mass threshold and fraction, Arm S draws and temperatures, sites) and is cross-checked by the design arithmetic (14 x 10 x (5 x 2 + 5) = bm.cells.T1; times temperatures = bm.cells.all). Equation numbers in the two read-out boxes come from the aux file (asserted against a fallback). Differences from the brief:
- Condition x is labelled "binary indicator" and carries no count: no NUM key holds the number of conditions, and the numeral may not be typed.
- The temperature box is drawn dash-dot (not dashed) so that dashed stays reserved for the sampled arm; its arrow joins Arm L between the forward pass and the readout, as the temperature acts on the logits.
- The cells at the reference temperature (bm.cells.T1) and across temperatures (bm.cells.all) are not printed in the image; the effect array shows the four facet axes with their level counts (M, W, O, T) instead.
- The readout gate diamond holds "valid mass at least 0.9"; "on all but 5 percent of prompts" is the line directly under it (the full sentence does not fit inside a diamond at 7 pt). Exits: "pair excluded" (left) and "pair enters the array" (right).
- The set-up spread box sits above the variance-shares box so that the bracket from the two yardsticks meets it at the bracket midpoint. "both in Many Labs 1 SD units" is a note under the between-site box.
- The legend holds exact, sampled and human data; the dotted double arrow and the dash-dot box are labelled in place.
Caption check: the caption in `floats.tex` matches the drawing, but it does not mention the agreement gate G4 or the "common scale, not an equivalence" bracket, which the figure shows.
