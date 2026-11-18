# Query versions: known-item recall and corpus size (OpenAlex, title and abstract)

Known-item file: `research/protocol/known-items-verified.json`.

Known items verified: 28; indexed in OpenAlex by DOI: 27.

| Version | Corpus size (sum over sub-queries, before union) | Known items retrieved / indexed | Missed |
|---|---|---|---|
| v0.3 A AND B (broad B) | 65761 | 25 / 27 | 10.1038/s43588-025-00840-7, 10.18653/v1/2024.starsem-1.34 |
| v0.1 A AND B AND C | 21227 | 17 / 27 | 10.1038/s41562-023-01659-w, 10.1038/s43588-025-00840-7, 10.1073/pnas.2405460121, 10.1093/pnasnexus/pgae233, 10.1093/pnasnexus/pgaf135, 10.18653/v1/2023.eacl-main.235, 10.18653/v1/2024.naacl-long.466, 10.18653/v1/2024.starsem-1.34, 10.18653/v1/2025.findings-acl.1147, 10.48550/arxiv.2305.00050 |
| v0.5 A AND B-narrow | 9980 | 24 / 27 | 10.1038/s43588-025-00840-7, 10.1098/rsos.231393, 10.18653/v1/2024.starsem-1.34 |
| v0.5b A AND B-narrow plus added phrases | 10361 | 27 / 27 | none |
| v0.6 A AND (broad B plus protocol families) | 81655 | 27 / 27 | none |

Sub-query strings for v0.5b (B-narrow plus added phrases):

- B1: `"cognitive bias" OR "cognitive biases" OR "heuristics and biases" OR "decision heuristics" OR "theory of mind" OR "false belief" OR "false-belief" OR "anchoring effect" OR "anchoring bias" OR "framing effect" OR "framing effects"`
- B2: `"judgment and decision making" OR "judgement and decision making" OR "decision bias" OR "decision biases" OR "human judgment" OR "risky choice" OR "risk preference" OR "conjunction fallacy" OR "base rate" OR "base-rate" OR "cognitive reflection"`
- B3: `Wason OR syllogism OR syllogistic OR "working memory" OR psycholinguistic OR psycholinguistics OR "garden path" OR priming`
- B4: `"moral judgment" OR "cognitive psychology" OR "cognitive science" OR "machine psychology" OR "developmental psychology"`
- B5: `"analogical reasoning" OR "causal reasoning" OR "probabilistic reasoning" OR "moral dilemma" OR "moral dilemmas" OR "trolley problem" OR "sunk cost" OR "gambler's fallacy" OR "Many Labs" OR "replication of classic" OR "human-like reasoning" OR "moral machine" OR "psychology experiments" OR "psychological experiments" OR "experiments in psychology" OR "scenario-based experiments" OR "human subject studies" OR "behavioral experiments" OR "behavioural experiments" OR "script knowledge"`

Caveat: v0.5b phrases were added after seeing which known items v0.5 missed, so its known-item recall is an optimistic (in-sample) estimate; the human audit and citation chasing provide the out-of-sample check.

Not indexed in OpenAlex by DOI: 10.48550/arxiv.2305.16572, 10.48550/arxiv.2405.16042
