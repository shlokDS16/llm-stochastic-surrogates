# Extraction form (DRAFT v0.3, 2026-10-15)

One JSON object per included study in `data/processed/extraction/<study_id>.json`, plus one row
per (study x paradigm x model) in `data/processed/extraction/effects.csv`. Every quantitative
entry carries a location (table, figure, page or section). Unknown is `null` with a note, never a guess.
Use the explicit value `not_reported` when the paper does not state something; missingness is
never treated as a substantive category.

## A. Bibliographic
- study_id (OpenAlex W-id or arXiv id), doi, arxiv_id, title, first_author, year, venue,
  peer_reviewed (yes / preprint), field of first author's affiliation (CS, psychology,
  cognitive science, neuroscience, linguistics, economics, other), country of first affiliation.

## B. Models
- For each model: name, exact version or checkpoint, access (API / open weights), parameter count
  if stated, release date, instruction-tuned or base, family (GPT, Claude, Gemini, Llama, Mistral,
  Qwen, OLMo, other), date of querying.
- n_models, n_model_families.

## C. Paradigms
- For each paradigm: name, family code (HB heuristics and biases; JDM judgement and decision
  making; RE reasoning; TOM theory of mind and social cognition; MEM memory and attention;
  LANG language processing and psycholinguistics; LEARN learning and categorisation;
  NUM numerical cognition; MOR moral judgement tasks; DEV developmental tasks; OTH),
  source paper of the original human paradigm, adapted or novel items, number of items,
  language(s), modality (text / image plus text), contamination risk (classic published items
  used verbatim: yes / no / partly).

## D. Human comparison
- comparison_type: none / own human sample / published norms or original study / large
  replication dataset (for example Many Labs) / crowd norms.
- human n, population, effect metric used for the comparison.

## E. Outcomes and findings
- outcome type: accuracy, bias magnitude, effect size, choice distribution, correlation with
  human data, other.
- Observable results first, per paradigm x model: (i) model effect present? (yes / no /
  not_reported, by the authors' test or interval); (ii) its direction relative to the human or
  normative direction; (iii) human and model effect sizes on the same metric if both are reported;
  (iv) the authors' statistical comparison of model and human (different / not different / not tested).
- Summary label derived by rule, in this order:
  1. INSUFFICIENT if (i) is not_reported and no effect sizes are given.
  2. DIFFERENT if the model effect is significant in the direction opposite to humans.
  3. SUPER-NORMATIVE if humans show the bias or error and the model effect is absent (not
     significant), or the model's accuracy exceeds human accuracy by the authors' test.
  4. EXAGGERATED if both effects are present in the same direction and the model-to-human ratio of
     effect sizes exceeds 2 (or the authors' test shows a larger model effect).
  5. HUMAN-LIKE if both effects are present in the same direction, both are on a common metric,
     and the model-to-human ratio is between 0.5 and 2.
  5b. SAME-DIRECTION-UNQUANTIFIED if both are present in the same direction but no common-metric
     effect sizes are reported (for example only a non-significant model-versus-human test);
     absence of a detected difference is never coded as HUMAN-LIKE.
  6. ATTENUATED if both are present in the same direction and the ratio is below 0.5.
  7. MIXED is derived, never coded directly: when items or conditions of one paradigm for the
     same model carry different labels, the paradigm-level label is MIXED and the item-level
     labels are kept.
- Effect statistics when reported: effect size and its metric, SE or CI, n of samples per item;
  for humans and for the model separately.
- Authors' headline conclusion (paraphrase, at most 25 words).

## F. Reporting quality and robustness (12 items; yes / no / not applicable)
1. exact model version and query date reported
2. decoding parameters reported (temperature, top-p, max tokens)
3. number of samples per item reported and greater than 1
4. full prompts published (paper, appendix or repository)
5. prompt wording perturbation tested (paraphrases)
6. option or answer order perturbation tested
7. temperature or sampling setting varied
8. more than one model version or date compared for the same model family
9. contamination considered (novel items, perturbed items, or explicit test)
10. statistical test or interval reported for the model effect
11. preregistration
12. code and data available
No total score is computed from items 1 to 12; they are analysed item by item.
Also: robustness_outcome (if any perturbation tested): effect survived / weakened / reversed /
not reported.

## G. Notes
- Free-text notes on anything a referee would ask about (at most 60 words).
- extractor (agent and model), date, time spent.

## Pilot-coding rule
Ten diverse studies are coded independently by Claude Sonnet and by Codex. Cohen's kappa is
computed per categorical field (C family, D comparison_type, E observable fields and derived
label, F items) as a reliability diagnostic. A field with kappa below 0.6 is redefined once and
re-piloted, or dropped from quantitative synthesis. Kappa is not treated as evidence of validity.
