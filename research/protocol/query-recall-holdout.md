# Query versions: known-item recall and corpus size (OpenAlex, title and abstract)

Known-item file: `research/protocol/known-items-holdout-verified.json`.

Known items verified: 19; indexed in OpenAlex by DOI: 19.

| Version | Corpus size (sum over sub-queries, before union) | Known items retrieved / indexed | Missed |
|---|---|---|---|
| v0.3 A AND B (broad B) | 65761 | 15 / 19 | 10.1038/s41562-025-02172-y, 10.1287/mksc.2023.0306, 10.48550/arxiv.2311.03839, 10.48550/arxiv.2503.24215 |
| v0.1 A AND B AND C | 21227 | 9 / 19 | 10.1016/j.jbef.2024.100971, 10.1038/s41562-025-02172-y, 10.1145/3715928.3737473, 10.1287/mksc.2023.0306, 10.17605/osf.io/875mw, 10.18653/v1/2025.emnlp-main.917, 10.18653/v1/2025.findings-acl.52, 10.48550/arxiv.2311.03839, 10.48550/arxiv.2503.24215, 10.48550/arxiv.2508.00902 |
| v0.5 A AND B-narrow | 9980 | 11 / 19 | 10.1016/j.chbah.2025.100227, 10.1038/s41562-025-02172-y, 10.1038/s42256-025-01049-z, 10.1145/3715928.3737473, 10.1287/mksc.2023.0306, 10.48550/arxiv.2311.03839, 10.48550/arxiv.2405.19313, 10.48550/arxiv.2503.24215 |
| v0.5b A AND B-narrow plus added phrases | 10361 | 11 / 19 | 10.1016/j.chbah.2025.100227, 10.1038/s41562-025-02172-y, 10.1038/s42256-025-01049-z, 10.1145/3715928.3737473, 10.1287/mksc.2023.0306, 10.48550/arxiv.2311.03839, 10.48550/arxiv.2405.19313, 10.48550/arxiv.2503.24215 |
| v0.6 A AND (broad B plus protocol families) | 81655 | 17 / 19 | 10.1287/mksc.2023.0306, 10.48550/arxiv.2503.24215 |

Sub-query strings for v0.5b (B-narrow plus added phrases):

- B1: `"cognitive bias" OR "cognitive biases" OR "heuristics and biases" OR "decision heuristics" OR "theory of mind" OR "false belief" OR "false-belief" OR "anchoring effect" OR "anchoring bias" OR "framing effect" OR "framing effects"`
- B2: `"judgment and decision making" OR "judgement and decision making" OR "decision bias" OR "decision biases" OR "human judgment" OR "risky choice" OR "risk preference" OR "conjunction fallacy" OR "base rate" OR "base-rate" OR "cognitive reflection"`
- B3: `Wason OR syllogism OR syllogistic OR "working memory" OR psycholinguistic OR psycholinguistics OR "garden path" OR priming`
- B4: `"moral judgment" OR "cognitive psychology" OR "cognitive science" OR "machine psychology" OR "developmental psychology"`
- B5: `"analogical reasoning" OR "causal reasoning" OR "probabilistic reasoning" OR "moral dilemma" OR "moral dilemmas" OR "trolley problem" OR "sunk cost" OR "gambler's fallacy" OR "Many Labs" OR "replication of classic" OR "human-like reasoning" OR "moral machine" OR "psychology experiments" OR "psychological experiments" OR "experiments in psychology" OR "scenario-based experiments" OR "human subject studies" OR "behavioral experiments" OR "behavioural experiments" OR "script knowledge"`

Caveat: v0.5b phrases were added after seeing which known items v0.5 missed, so its known-item recall is an optimistic (in-sample) estimate; the human audit and citation chasing provide the out-of-sample check.

Not indexed in OpenAlex by DOI: 10.48550/arxiv.2405.18870, 10.48550/arxiv.2406.15981, 10.48550/arxiv.2407.01067, 10.48550/arxiv.2503.06646, 10.48550/arxiv.2505.21301
