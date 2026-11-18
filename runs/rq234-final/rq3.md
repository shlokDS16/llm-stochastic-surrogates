# RQ3 (interim): human comparison types, human sample sizes, metrics

Design-weighted domain estimates (percent of eligible studies; 95% t-interval, linearised stratified variance on merged strata; * = zero-variance estimate, see csv for exact unweighted interval). k/n = unweighted studies with the feature / unweighted eligible respondents. Interim run.

claude: 110 respondents, 80 eligible, 28 estimation groups, df 82; codex: 110 respondents, 81 eligible, 28 estimation groups, df 82

`types_any` = share of eligible studies listing the type among D.types (a study can list several); `primary_type` = the type the main results rest on; `human_n|reported` = a numeric human_n is given; `outcome_types` = E.outcome_types.


| feature | Claude % (95% CI) | Claude k/n | Codex % (95% CI) | Codex k/n | kappa | agree % | rule |
|---|---|---|---|---|---|---|---|
| types_any/none | 21.7 (11.7 to 31.7) | 17/80 | 20.8 (9.1 to 32.5) | 13/81 | 0.662 | 90.3 | pass |
| types_any/own_sample | 35.0 (22.0 to 48.0) | 24/80 | 35.7 (21.8 to 49.6) | 25/81 | 0.898 | 95.8 | pass |
| types_any/published_norms | 46.0 (33.0 to 59.1) | 42/80 | 52.7 (39.5 to 65.9) | 51/81 | 0.68 | 84.7 | pass |
| types_any/replication_dataset | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | None | 100.0 | pass |
| types_any/crowd_norms | 3.3 (0.0 to 7.6) | 3/80 | 4.5 (0.0 to 9.8) | 4/81 | 0.652 | 97.2 | pass |
| primary_type/none | 21.7 (11.7 to 31.7) | 17/80 | 20.0 (8.4 to 31.6) | 12/81 | 0.751 | 84.7 | pass |
| primary_type/own_sample | 32.7 (20.0 to 45.3) | 23/80 | 31.2 (18.0 to 44.5) | 23/81 | 0.751 | 84.7 | pass |
| primary_type/published_norms | 42.4 (29.0 to 55.7) | 37/80 | 46.4 (33.2 to 59.5) | 44/81 | 0.751 | 84.7 | pass |
| primary_type/replication_dataset | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.751 | 84.7 | pass |
| primary_type/crowd_norms | 3.3 (0.0 to 7.6) | 3/80 | 2.4 (0.0 to 6.6) | 2/81 | 0.751 | 84.7 | pass |
| human_n/reported | 40.5 (26.7 to 54.2) | 32/80 | 42.3 (27.6 to 57.1) | 34/81 | 1.0 | 100.0 | pass |
| outcome_types/accuracy | 35.6 (24.9 to 46.2) | 36/80 | 25.6 (15.8 to 35.4) | 31/81 | 0.943 | 97.2 | pass |
| outcome_types/bias_magnitude | 25.8 (13.5 to 38.1) | 19/80 | 73.6 (62.9 to 84.3) | 55/81 | 0.211 | 52.8 | FAIL |
| outcome_types/effect_size | 44.5 (32.0 to 57.1) | 28/80 | 35.4 (23.3 to 47.5) | 25/81 | 0.253 | 66.7 | FAIL |
| outcome_types/choice_distribution | 35.4 (23.6 to 47.2) | 25/80 | 54.6 (41.5 to 67.8) | 35/81 | 0.511 | 76.4 | FAIL |
| outcome_types/human_correlation | 14.7 (6.5 to 23.0) | 15/80 | 14.9 (6.3 to 23.5) | 15/81 | 0.812 | 94.4 | pass |
| outcome_types/other | 28.2 (16.4 to 39.9) | 20/80 | 32.0 (18.4 to 45.6) | 24/81 | 0.132 | 68.1 | FAIL |
| outcome_types/agreement | 0.0 (0.0 to 0.0) * | 0/80 | 0.1 (0.0 to 0.4) | 1/81 | None | None | NA |
| outcome_types/effect | 0.0 (0.0 to 0.0) * | 0/80 | 0.1 (0.0 to 0.4) | 1/81 | None | None | NA |


## human_n (participants), unweighted summary among eligible studies reporting it; weighted median is a point value only


| coder | subset | n | min | q1 | median | q3 | max | weighted_median_point_only |
|---|---|---|---|---|---|---|---|---|
| claude | all_reported | 32 | 8.0 | 75.8 | 182.0 | 425.5 | 1156.0 | 169.0 |
| claude | primary_type_own_sample | 22 | 12.0 | 82.8 | 161.5 | 426.8 | 1156.0 | 169.0 |
| codex | all_reported | 34 | 1.0 | 68.2 | 182.0 | 454.5 | 51776.0 | 148.0 |
| codex | primary_type_own_sample | 23 | 1.0 | 59.0 | 140.0 | 484.5 | 1000.0 | 140.0 |


### claude: D.metric strings (lower-cased, unweighted counts among eligible respondents; top 25)

| metric | studies |
|---|---|
| not_reported | 17 |
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
| hinting task total score out of 20 (corcoran and klein scoring) and z-score of the model relative to the normative distribution | 1 |
| 7-point mean ratings of offence severity and of restorative-justice support, compared by t tests, one-sample z tests, mixed models and mediation | 1 |
| accuracy (%) | 1 |
| word count, part-of-speech proportions, synset novelty and survival, age of acquisition, rated happiness and sadness | 1 |
| cohen's d compared descriptively with meta-analytic human range d = .58 to .87 stated in the discussion | 1 |
| mean proportion of holistic (relation-based) matches per province | 1 |
| published serial position curves (recall or recognition accuracy; murdock 1963, oberauer 2003, fig 2) | 1 |
| majority choice of participants in the replicated studies; qualitative comparison of effects | 1 |
| share of yes/no votes per scenario; kl divergence between model decision distribution and vote share; match with human majority | 1 |


### claude: es_metric strings on v1.1 effect rows (unweighted rows; top 25)

| es_metric | rows |
|---|---|
| null | 583 |
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
| cohen's d | 4 |
| accuracy against human majority choice | 4 |
| mean drop in proportion correct (control minus biased), pooled by authors over the three intrinsic-bias experiments (p1 and p2) | 4 |
| proportion correct | 4 |
| standardised mean difference (approximated cohen's d from mixed model for llms; hedges' g for humans) | 3 |
| standardised mean difference (approximated cohen's d from mixed model for llms; cohen's d for humans) | 3 |
| percent cooperation (dominant choice), 1 run per condition | 3 |
| mixed-model beta (structure x continuation type); human = written group | 3 |
| spearman rho with human typicality norms (prompted in-filling ranking, mean of 50 runs per category, 27 categories) | 2 |
| weighted f1 against human-majority permissibility label (mean of four prompt paraphrases) | 2 |


### codex: D.metric strings (lower-cased, unweighted counts among eligible respondents; top 25)

| metric | studies |
|---|---|
| not_reported | 15 |
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
| hinting task scores using corcoran and klein scoring systems; model and human score comparison | 1 |
| seven-item rj support rating scale and four-item offence-severity rating scale, both 1–7; condition contrasts and human–llm mean comparisons | 1 |
| accuracy on chinese benchmark questions | 1 |
| word and synset transmission/change; grammatical-category proportions; age of acquisition; human ratings of happiness, sadness, imagery, and emotional impact. | 1 |
| gricean maxim adherence, assessed qualitatively by two judges | 1 |
| cohen's d | 1 |
| percentage of model responses matching human-annotated answers (humanlike rate) | 1 |
| scale/task mean comparisons; t-tests | 1 |
| human item-recognition accuracy and reaction-time effects discussed descriptively; no direct human comparison dataset or common-metric estimates reported | 1 |
| majority-choice agreement for prior studies; no direct human effect-size comparison for experiments 1–3 | 1 |


### codex: es_metric strings on v1.1 effect rows (unweighted rows; top 25)

| es_metric | rows |
|---|---|
| null | 541 |
| accuracy | 25 |
| spearman correlation | 18 |
| pearson r | 18 |
| spearman r | 12 |
| partial eta squared, strategy effect | 6 |
| pearson correlation | 5 |
| distance-effect r² | 4 |
| cohen's d; study reports four effects, mean d calculated from reported values | 4 |
| humanlike response rate (%) | 4 |
| proportion-point decrease in diagnostic accuracy (weighted mean across intrinsic-bias experiments) | 4 |
| p-score; exact average not reported in text | 4 |
| cohen's d (llm approximated) / hedges' g (human) | 3 |
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
| percent selecting local letter | 1 |
