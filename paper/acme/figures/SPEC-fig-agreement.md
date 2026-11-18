# SPEC for the agreement figure (key `agreement`, `\FigAgreement`, two columns): exact against sampled shares

Script `analysis/acme/figures/fig_agreement.py`; output `paper/acme/figures/fig-agreement.pdf` (vector, fonts embedded) plus a 600 dpi PNG and
`<file>.source.json` (SHA-256 of every input). Run: `.venv/Scripts/python.exe -I analysis/acme/figures/fig_agreement.py`. Written by the
figure-smith in CRP-S09 after the gates, to the contract `research/relaunch/acme-gates/S7-REWRITE-SPEC.md` (Exhibits).

## Claim (one, supported by the figure alone)
On the intersection roster, the same wordings and the same two temperatures, the variance shares from sampled answers (Arm S) and from exact
answer probabilities (Arm L) lie close to the identity line for most terms; the figure shows which terms and items depart from it.
Caption rule (floats.tex): no result numbers in the caption.

## Layout
Panel (a): one point per variance term and item (14 terms; the draw component has no Arm L counterpart and is left out), x = Arm S share
(basis E2: draw noise is a component), y = Arm L frozen A1 share (four-facet analysis; no interval drawn because the frozen intervals are not
interpreted at four wordings, E7b item 2). Identity line, grey band of +-0.06 (E7a item 3: differences under 0.06 are not interpreted in the
four-wording arrays). Marker shape and colour (Okabe and Ito) = item: P1, P3, AF, QA, NR. The numeric item P2c (3 models on the intersection
roster, unstable) is drawn as grey crosses. Panel (b): the same differences (Arm S minus Arm L) summed over the terms of each component group
(groups of `analysis/acme/results_route.py`), same band. Width one text width (16.0 cm), height 7.6 cm, text 7 to 7.5 pt.

## Reads
`runs/acme-gstudy/route-table/route_table.csv` (columns (e)-ArmS, (e)-ArmL) and, for group sums, nothing else (single-term values only in (a)).
`--basis E1` (expected-effect shares, no draw noise in the denominator) is available for a check and refuses to write the paper path.

## Notes for the writer
- E2 shares sum to one with the draw component; Arm L has none, so a term can differ by up to the item's draw share for that reason alone
  (P3 has the largest draw share in column (e)); the E1 basis removes this and is the cleaner like-for-like comparison (see the script option).
- P3 is forward order only in both arms (E7b item 1): no O terms.
- Never write "the readouts agree" without the 0.06 rule and the 4-wording bias; P2c is not interpreted.
