# Large language models as stochastic surrogates of human participants: data and code

Data and code for the article "Large Language Models as Stochastic Surrogates of Human Participants: A Review of
Verification, Validation and Uncertainty Practice in Cognitive Experiments" by Shlok Kumar Goenka, M. Thenmozhi and
Lawanya Shri M (Vellore Institute of Technology, Vellore, India).
DOI of this deposit: https://doi.org/10.5281/zenodo.24046587

Every number in the article is generated from a file in this deposit. `paper/acme/autonumbers.tex` holds one LaTeX macro
per number, and the comment of each macro names the run file and the field it came from. `MANIFEST.sha256` lists the
SHA-256 hash of every file.

## Contents

| Folder | What it holds |
|---|---|
| `analysis/` | All analysis code. `analysis/acme/` holds the case study: prompt construction and manifests, the exact-probability readout (Arm L) and the sampled readout (Arm S), the gates, the variance-component estimators and their synthetic checks, the route table, and the generators of every table, figure and number. Other subfolders hold the search, screening, coding and review analyses. |
| `tools/` | Helper scripts (ledger, manifests, packaging, model download and quantization, search and coding harnesses). |
| `data/processed/` | Search records (bibliographic fields only), screening labels of every pass, abstract-level coding, full-text extraction of both coding passes (`extraction/`), the crossing recode of both passes (`crossing/`), the PRISMA counts and the Many Labs 1 summaries used as the human reference (`ml1/`). |
| `runs/` | One folder per run with its outputs and environment file. `runs/acme-L/` holds the per-cell answer probabilities of the exact readout (one folder per model, one JSON Lines file per item); `runs/acme-S*/` the sampled answers; `runs/acme-gstudy/` and `runs/acme-S-gstudy/` the variance components and the route table; `runs/acme-equivalence/` the wording-equivalence check; `runs/crossing/` the recode agreement. |
| `research/protocol/` | Search strings and log, screening and coding briefs, extraction form, recall checks. |
| `research/relaunch/` | The frozen analysis plan of the case study (`PREREG-acme.md`), its dated errata (`PREREG-acme-ERRATA.md`) and the exploratory register (`EXPLORATORY-acme.md`). The plan was registered on OSF Registries (https://osf.io/t82jc). |
| `research/ledgers/claims.jsonl` | The sources of literature numbers quoted in the text. |
| `paper/acme/` | The generated numbers (`autonumbers.tex`), the figures and the tables of the article. |

## Reproducing the results

Python 3; the packages are in `requirements.txt`, and runs record their environment details in their own folders. The exact readout needs a CUDA GPU (about 12 GB) and the open-weight models
listed in the models table of the article at the pinned revisions; `tools/fetch_model.py` downloads them. Every other step runs on
a CPU from the files in this deposit, for example:

    python analysis/acme/gstudy.py --help
    python analysis/acme/make_autonumbers.py

## What is not included

- Full texts and abstracts of the reviewed studies (third-party copyright): every "abstract" field and column has been
  removed; prompt files that embed passages of full texts are left out.
- The Many Labs 1 raw data: cite and download them from their public release (Klein et al. 2014, Journal of Open
  Psychology Data, https://doi.org/10.5334/jopd.ad; OSF https://osf.io/wx7ck).
- Model weights (download from Hugging Face at the revisions in the models table), program binaries and environments.

## Licence

Data, documentation and figures: Creative Commons Attribution 4.0 International (CC BY 4.0). Source code: MIT License
(see `LICENSE`).

## Citation

See `CITATION.cff`. Please cite the article and this deposit.
