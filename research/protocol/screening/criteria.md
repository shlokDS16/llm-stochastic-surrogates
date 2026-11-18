# Screening criteria given to every classifier (frozen before the first batch)

You are screening records for a systematic review. A record is ELIGIBLE only if all of these hold:

1. SUBJECT: a pretrained generative language model (for example GPT, ChatGPT, Claude, Gemini,
   Llama, Mistral, Qwen, or another large language model) is itself the subject being tested.
2. PARADIGM: it is given at least one task from cognitive psychology or a neighbouring
   experimental field, such as heuristics and biases (anchoring, framing, conjunction fallacy,
   base-rate neglect, sunk cost), judgement and decision making under risk, cognitive reflection,
   syllogisms or the Wason selection task, analogical, causal or probabilistic reasoning tasks
   from psychology, theory of mind or false-belief tasks, memory or attention paradigms,
   psycholinguistic paradigms (garden-path sentences, priming, agreement attraction), learning or
   categorisation tasks, moral dilemmas with an experimental manipulation, developmental tasks,
   or replications of classic psychology or behavioural-economics experiments.
3. DATA: the record reports new empirical results on the model's behaviour (answers, choices,
   ratings or response probabilities).

EXCLUDE when any of these is true:
- the language model is only a tool for researchers or for an application (writing, coding,
  clinical or business decision support, grading, judging other outputs, data annotation,
  simulating survey opinions without a cognitive task);
- only personality, values, attitude or clinical-symptom questionnaires are given to the model;
- only general NLP or capability benchmarks without a psychology source (for example maths word
  problems, MMLU, coding);
- only brain or neural-representation alignment, without a behavioural task;
- it is a review, survey, position paper, editorial, dataset deposit or replication package;
- it is not about language models at all.

Answer for each record with exactly one label:
- INCLUDE: clearly meets 1, 2 and 3;
- MAYBE: could meet them but the text is not enough to tell;
- EXCLUDE: clearly fails at least one criterion.

When unsure between INCLUDE and EXCLUDE, answer MAYBE.
