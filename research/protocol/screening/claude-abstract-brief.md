# Brief for the Claude stage-2 classifier (title and abstract; frozen before the first batch)

Model: Claude Sonnet (subagent). One batch per agent run. Amendment v0.4 applies.

You screen titles and abstracts for a systematic review. Read the criteria in
`research/protocol/screening/criteria.md` first, then the batch file named in your task
(`data/processed/screen/abstract-batch-NN.tsv`; one record per line:
`<id><TAB><title> || <abstract, first 1,500 characters>`; the abstract may be empty when the
database has none). Read the batch in chunks with offset and limit until every line is read.
Judge each record against the criteria using the title and abstract only.

Write `data/processed/screen/abstract-batch-NN.claude.jsonl` with exactly one JSON line for EVERY
record in the batch, in file order:
`{"id": "<id exactly as in the file>", "label": "INCLUDE" | "MAYBE" | "EXCLUDE", "code": "<code>"}`.
Unlike the title stage, nothing is implied by omission: a missing record blocks the merge.

`code` is one short reason code:
- INCLUDE or MAYBE: `ok`, or `no-abstract` when the decision rests on the title alone.
- EXCLUDE: the first criterion that fails: `not-llm`, `tool-use` (model used as a tool),
  `questionnaire-only` (personality, values, attitudes or clinical scales only), `benchmark-only`
  (no psychology source), `neural-only` (brain or representation alignment without a behavioural
  task), `no-new-data` (review, survey, position paper, editorial, dataset or replication package),
  `other`.

Stage-2 rules:
- A record with no abstract is judged on its title with the title-stage leniency: if the title
  names a language model together with a cognitive-psychology topic, answer MAYBE.
- Human-like behaviour studies that give a model a classic experimental task (biases, reasoning,
  theory of mind, memory, psycholinguistics, moral dilemmas with a manipulation, games from
  behavioural economics, learning or categorisation) and report its answers are INCLUDE.
- When unsure between INCLUDE and EXCLUDE, answer MAYBE.
- Do not search the web, do not open other files, do not explain your labels beyond the code.

Reply in at most 3 lines: batch number, number of records read, counts of INCLUDE, MAYBE, EXCLUDE.
