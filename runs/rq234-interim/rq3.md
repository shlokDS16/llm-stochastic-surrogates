# RQ3 (interim): human comparison types, human sample sizes, metrics

Design-weighted domain estimates (percent of eligible studies; 95% t-interval, linearised stratified variance on merged strata; * = zero-variance estimate, see csv for exact unweighted interval). k/n = unweighted studies with the feature / unweighted eligible respondents. Interim run.

claude: 102 respondents, 72 eligible, 27 estimation groups, df 75; codex: 102 respondents, 74 eligible, 27 estimation groups, df 75

`types_any` = share of eligible studies listing the type among D.types (a study can list several); `primary_type` = the type the main results rest on; `human_n|reported` = a numeric human_n is given; `outcome_types` = E.outcome_types.


| feature | Claude % (95% CI) | Claude k/n | Codex % (95% CI) | Codex k/n | kappa | agree % | rule |
|---|---|---|---|---|---|---|---|
| types_any/none | 19.4 (8.2 to 30.6) | 14/72 | 20.2 (3.4 to 37.1) | 10/74 | 0.57 | 89.2 | FAIL |
| types_any/own_sample | 35.7 (17.3 to 54.2) | 21/72 | 38.6 (19.9 to 57.3) | 23/74 | 0.887 | 95.4 | pass |
| types_any/published_norms | 47.6 (30.5 to 64.7) | 40/72 | 50.2 (38.5 to 61.9) | 49/74 | 0.631 | 83.1 | pass |
| types_any/replication_dataset | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | None | 100.0 | pass |
| types_any/crowd_norms | 3.5 (0.0 to 7.9) | 3/72 | 4.6 (0.0 to 9.8) | 4/74 | 0.651 | 96.9 | pass |
| primary_type/none | 19.4 (8.2 to 30.6) | 14/72 | 19.5 (2.7 to 36.2) | 9/74 | 0.715 | 83.1 | pass |
| primary_type/own_sample | 33.4 (15.2 to 51.6) | 20/72 | 34.2 (16.0 to 52.5) | 21/74 | 0.715 | 83.1 | pass |
| primary_type/published_norms | 43.7 (26.4 to 61.0) | 35/72 | 43.9 (32.2 to 55.7) | 42/74 | 0.715 | 83.1 | pass |
| primary_type/replication_dataset | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.715 | 83.1 | pass |
| primary_type/crowd_norms | 3.5 (0.0 to 7.9) | 3/72 | 2.4 (0.0 to 6.4) | 2/74 | 0.715 | 83.1 | pass |
| human_n/reported | 40.4 (21.5 to 59.3) | 28/72 | 44.2 (25.0 to 63.4) | 31/74 | 1.0 | 100.0 | pass |
| outcome_types/accuracy | 38.6 (26.0 to 51.2) | 35/72 | 27.7 (16.3 to 39.1) | 30/74 | 0.938 | 96.9 | pass |
| outcome_types/bias_magnitude | 32.2 (14.1 to 50.2) | 17/72 | 74.9 (64.3 to 85.5) | 49/74 | 0.22 | 53.8 | FAIL |
| outcome_types/effect_size | 46.6 (34.5 to 58.7) | 25/72 | 38.1 (26.9 to 49.3) | 24/74 | 0.245 | 66.2 | FAIL |
| outcome_types/choice_distribution | 30.4 (19.4 to 41.3) | 21/72 | 49.9 (32.1 to 67.8) | 30/74 | 0.476 | 75.4 | FAIL |
| outcome_types/human_correlation | 14.9 (6.8 to 23.1) | 15/72 | 14.6 (6.4 to 22.8) | 15/74 | 0.808 | 93.8 | pass |
| outcome_types/other | 25.3 (8.6 to 41.9) | 18/72 | 33.0 (15.6 to 50.4) | 23/74 | 0.147 | 67.7 | FAIL |
| outcome_types/agreement | 0.0 (0.0 to 0.0) * | 0/72 | 0.1 (0.0 to 0.4) | 1/74 | None | None | NA |
| outcome_types/effect | 0.0 (0.0 to 0.0) * | 0/72 | 0.1 (0.0 to 0.4) | 1/74 | None | None | NA |


## human_n (participants), unweighted summary among eligible studies reporting it; weighted median is a point value only


| coder | subset | n | min | q1 | median | q3 | max | weighted_median_point_only |
|---|---|---|---|---|---|---|---|---|
| claude | all_reported | 28 | 8.0 | 68.8 | 166.5 | 363.8 | 1156.0 | 140.0 |
| claude | primary_type_own_sample | 19 | 12.0 | 73.0 | 159.0 | 400.0 | 1156.0 | 140.0 |
| codex | all_reported | 31 | 1.0 | 59.0 | 169.0 | 407.0 | 51776.0 | 140.0 |
| codex | primary_type_own_sample | 21 | 1.0 | 50.0 | 140.0 | 500.0 | 1000.0 | 140.0 |


### claude: D.metric strings (lower-cased, unweighted counts among eligible respondents; top 25)

| metric | studies |
|---|---|
| not_reported | 14 |
| qualitative comparison of direction and significance with the findings of the three original studies; no human data are analysed in this paper | 1 |
| pearson r of stimulus means; krippendorff alpha; classification accuracy; jensen-shannon divergence | 1 |
| spearman rs between group-level dissimilarity matrices (rsa); icc; inter-subject rs | 1 |
| spearman correlation of model typicality ranking with human category-production norms (table 3, 7-10); human distance/ratio effects taken from the literature, no human data analysed; none for blimp and raven | 1 |
| proportion of participants judging the rule break permissible per vignette, binarised to permissible/not (majority); also mae and cross-entropy against the proportion (sec 5.1) | 1 |
| proportion of subject coreference per verb class and connective (logit mixed-effects interaction); proportion of explanation relations | 1 |
| forced-choice accuracy by subset and verb (table 7, fig. 4-6); by-item spearman correlation with model scores (sec. 5.4) | 1 |
| proportion correct (about 83% on false belief questions), drawn as dashed lines or triangles in figs. 2, 3, 5 | 1 |
| qualitative overlap of group cluster membership and of cluster-level emotion/behaviour ratings with the published human findings; no statistic | 1 |
| proportion correct per task and language | 1 |
| win rate against each bot; two-fold cross-validated normalised likelihood of behavioural models | 1 |
| mean 5-point credibility rating of the target article, treatment versus control, independent t-test | 1 |
| proportion of heads; first-flip heads rate; alternation rate (about 60%); 8-flip sequence statistics (runs, n-grams); best achievable mse for predicting human flips (just above 0.24); all taken from earlier published studies, not collected here (sec 5.3 limitation 4) | 1 |
| mean originality rating (1-5 likert, human raters) per idea, mixed-effects model | 1 |
| accuracy against majority-preferred reading (exp 1); mean 1-7 naturalness rating normalised to 0-1 as proxy alpha (exp 2) | 1 |
| accuracy (%) | 1 |
| word count, part-of-speech proportions, synset novelty and survival, age of acquisition, rated happiness and sadness | 1 |
| mean proportion of holistic (relation-based) matches per province | 1 |
| published serial position curves (recall or recognition accuracy; murdock 1963, oberauer 2003, fig 2) | 1 |
| majority choice of participants in the replicated studies; qualitative comparison of effects | 1 |
| share of yes/no votes per scenario; kl divergence between model decision distribution and vote share; match with human majority | 1 |
| mean proportion of correct most-likely diagnoses per condition | 1 |
| proportion of conjunctive responses (p2); unique combinations and number of actions or checks (p3) | 1 |
| garden-path effect and reading time in ms; correlation rho with model measures | 1 |


### claude: es_metric strings on v1.1 effect rows (unweighted rows; top 25)

| es_metric | rows |
|---|---|
| null | 559 |
| accuracy % | 40 |
| spearman rs, group-level dsm vs human dsm | 22 |
| token novelty reduction vs random-turn baseline (dailydialog) | 16 |
| mean /cohen's d/ over process features (lower = closer to humans) | 15 |
| percent of 9 runs matching human-typical answer, per prompt (no per-paradigm pooled value) | 12 |
| accuracy, test condition | 11 |
| spearman rs, group-level dsm vs spose distances (carlson-image stimuli) | 8 |
| spearman rho | 7 |
| proportion heads minus 0.5 (fair-coin baseline), t=1.0 | 6 |
| alternation rate minus 0.5 (bernoulli), framing-baseline prompt; human 'about 60%' | 6 |
| p-score (mean over 9 dilemmas) | 6 |
| percent correct final answers, mean over 5 seeds | 5 |
| overall score / maximum achievable score (llm-llm play) | 5 |
| spearman rho with human typicality norms (latent representation, mean over 27 categories) | 4 |
| accuracy against human majority choice | 4 |
| mean drop in proportion correct (control minus biased), pooled by authors over the three intrinsic-bias experiments (p1 and p2) | 4 |
| proportion correct | 4 |
| percent cooperation (dominant choice), 1 run per condition | 3 |
| mixed-model beta (structure x continuation type); human = written group | 3 |
| spearman rho with human typicality norms (prompted in-filling ranking, mean of 50 runs per category, 27 categories) | 2 |
| weighted f1 against human-majority permissibility label (mean of four prompt paraphrases) | 2 |
| weighted f1 against human-majority permissibility label | 2 |
| pearson r between i-caus and i-cons verb biases | 2 |
| pearson r with human stimulus-mean ratings (range 0.528-0.945 across 10 appraisals; 0.671-0.970 across 8 emotion dimensions) | 1 |


### codex: D.metric strings (lower-cased, unweighted counts among eligible respondents; top 25)

| metric | studies |
|---|---|
| not_reported | 12 |
| phishing likelihood ratings and effects; launch and guilt ratings; project continuation decisions | 1 |
| study 1: pearson correlations of mean ratings, accuracy, krippendorff’s alpha, and distributional comparisons; study 2: krippendorff’s alpha against author, average-reader, and majority-label judgments. | 1 |
| spearman rank correlation between flattened group-level dissimilarity matrices | 1 |
| task-specific alignment scores, including magnitude-effect fit r², blimp accuracy, category-norm spearman correlation, and rpm accuracy. | 1 |
| human permissibility response proportions; comparison by model mae and cross-entropy | 1 |
| for coreference, proportions of subject versus object reference and mixed-effects logistic regression; for coherence, proportion of explanations versus other relations and mixed-effects logistic regression. | 1 |
| accuracy; trott et al. human baseline of 83% correct on false-belief questions. | 1 |
| warmth and competence ratings and their cluster patterns; behavioral tendency correlations. the three evaluators assessed response quality, not stereotype judgments. | 1 |
| correct-response rate by task and language; human response patterns used as baseline. | 1 |
| win rate against 15 bots and fitted choice behavior | 1 |
| mean 5-point credibility ratings; decoy effect tested by treatment-control difference in target article ratings | 1 |
| sequence statistics, including first-flip proportions, alternation rates, run distributions, and predictability | 1 |
| human judges' 5-point likert originality ratings; comparisons use linear mixed-effects models. | 1 |
| experiment 1 accuracy against majority-vote preferred-scope labels; experiment 2 human proxy α-score and pearson correlation | 1 |
| accuracy on chinese benchmark questions | 1 |
| word and synset transmission/change; grammatical-category proportions; age of acquisition; human ratings of happiness, sadness, imagery, and emotional impact. | 1 |
| gricean maxim adherence, assessed qualitatively by two judges | 1 |
| percentage of model responses matching human-annotated answers (humanlike rate) | 1 |
| scale/task mean comparisons; t-tests | 1 |
| human item-recognition accuracy and reaction-time effects discussed descriptively; no direct human comparison dataset or common-metric estimates reported | 1 |
| majority-choice agreement for prior studies; no direct human effect-size comparison for experiments 1–3 | 1 |
| absolute difference between human and model proportions of acceptable judgments; rationale value prevalence and normalized shannon entropy | 1 |
| kl divergence between model decision distributions and aggregate human votes; majority-vote agreement | 1 |
| mean proportion of correct diagnoses; chi-square goodness-of-fit comparisons | 1 |


### codex: es_metric strings on v1.1 effect rows (unweighted rows; top 25)

| es_metric | rows |
|---|---|
| null | 520 |
| accuracy | 25 |
| spearman correlation | 18 |
| pearson r | 18 |
| spearman r | 12 |
| partial eta squared, strategy effect | 6 |
| pearson correlation | 5 |
| distance-effect r² | 4 |
| humanlike response rate (%) | 4 |
| proportion-point decrease in diagnostic accuracy (weighted mean across intrinsic-bias experiments) | 4 |
| p-score; exact average not reported in text | 4 |
| β, po-versus-do structure effect (recipient-minus-theme contrast; written human comparison) | 3 |
| originality-rating difference (cross-domain mapping minus user-need), coefficient b | 2 |
| ahs mean score; higher indicates holistic thinking | 2 |
| dss mean score | 2 |
| scs independent subscale mean score | 2 |
| scs interdependent subscale mean score | 2 |
| proportion-point decrease in diagnostic accuracy (weighted mean across extrinsic-bias experiments) | 2 |
| p-score | 2 |
| spearman's rho | 2 |
| kl divergence; majority-vote agreement | 1 |
| mixed-exposure truth-rating offset | 1 |
| median population rounds to consensus (published comparison) | 1 |
| spearman correlation of pairwise message-distance matrices | 1 |
| front-load score i(pos 1) − i(pos 3) | 1 |
