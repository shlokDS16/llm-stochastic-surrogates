# SPEC for Fig 9 (key `shares`, `\FigShares`, two columns): variance components per item and pooled

Script `analysis/acme/figures/fig_shares.py`; output `paper/acme/figures/fig-shares.pdf` (vector, fonts embedded) plus a 600 dpi PNG and
`<file>.source.json`. Written and tested on synthetic data only (CRP-S09 P2 figprep); the real render happens once the G-study of the real
Arm L exists. Run: `.venv/Scripts/python.exe -I analysis/acme/figures/fig_shares.py [--gstudy runs/acme-gstudy/A1]`.

## Claim (one, supported by the figure alone)
Where the variance of the manipulation effect sits: which component (model, order, wording and their interactions) carries it, item by item,
with an interval on every point. Caption rule: no result numbers in the caption (floats.tex); the reader takes the values from the axis.

## Layout (blueprint M9: no stacks)
One panel per variance component (M, O, M x O, W, M x W, W x O, residual; only those present in `components_by_item.csv`), shared item axis
(rows in the order of `runs/human-ml1-acme/arml_scales.csv`), one pooled row below the items on a grey band. Dot = share, line = 95 percent
interval from the same file (`share_lo`, `share_hi`; studentized under estimator A1, percentile under prereg: the axis label says which, read
from `summary.json`). Open circle on the M x W panel marks a one-order item, whose M x W term holds the residual (gstudy.py labels it MW).
A term absent from an item's design (the O terms of one-order items) has no mark. Arrowheads mark an interval cut at the axis limit.
Width one text width (16.0 cm), height 7.4 cm; text 7 to 7.5 pt; palette Okabe and Ito.

## Reads
`<gstudy>/components_by_item.csv` (analysis T1), `<gstudy>/pooled_shares.csv` (T1_3facet, mean), `<gstudy>/summary.json`,
`runs/human-ml1-acme/arml_scales.csv` (item order only). The pooled row is the mean over items, as in H1 to H3; the exploratory median is not drawn.

## Needs from the lead
Nothing beyond the gstudy directory. The stub caption in floats.tex says "studentized interval": that holds only under A1; under prereg the
axis label of the figure says "percentile", so make the caption match the estimator chosen.
