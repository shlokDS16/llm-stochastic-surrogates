# Brief for the Claude title-stage classifier (frozen before the first batch)

Model: Claude Haiku (subagent). One batch per agent run. Amendment v0.6 applies.

You screen titles for a systematic review. Read the criteria in
`research/protocol/screening/criteria.md` first, then the batch file named in your task
(`data/processed/screen/title-batch-NN.tsv`; one record per line: `<id><TAB><title>`; at most
1,500 lines, so one Read call with limit 2000 covers it). Judge each title against the criteria
using the title alone.

Write `data/processed/screen/title-batch-NN.claude.jsonl` containing one JSON line ONLY for each
record you do NOT exclude:
`{"id": "<id exactly as in the file>", "label": "INCLUDE"}` or `{"id": "...", "label": "MAYBE"}`.
Every record you leave out counts as EXCLUDE. If you would keep no records, write the file empty
(it must still exist: an absent file blocks the merge).

Title-stage rules:
- Titles are often uninformative. If a title mentions language models (or GPT, ChatGPT, LLM,
  Claude, Gemini, Llama and similar) together with anything from cognitive psychology,
  decision making, reasoning, theory of mind, biases, memory, moral judgement, games,
  psycholinguistics, human-likeness or comparison with humans, answer MAYBE unless it is clearly
  excluded.
- Clear excludes: language models used as tools (clinical decision support, grading, judging
  outputs, coding, education tools, recommender or business uses), surveys and reviews, datasets
  or replication packages, papers not about language models.
- Do not search the web, do not open other files, do not explain your labels.

Reply in at most 3 lines: batch number, number of records read, number kept (INCLUDE + MAYBE).
