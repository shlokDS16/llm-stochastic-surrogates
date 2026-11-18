# Brief for RQ1 abstract-level coding (amendment v0.9; frozen before the first batch)

Model: Claude Sonnet (subagent). One batch per agent run. You are blind to every screening label: do not open
anything under `data/processed/screen/` or `data/processed/fulltext-pilot/`.

Read `research/protocol/screening/criteria.md` and `research/protocol/extraction-form.md` (sections A-C) first,
then your batch `data/processed/rq1/rq1-batch-NN.tsv` (one record per line: `<id><TAB><year><TAB><title> || <abstract>`;
the abstract may be empty) in 50-line chunks with offset and limit until every line is read.

Code each record from its title and abstract only. Write `data/processed/rq1/rq1-batch-NN.jsonl`, one JSON line
per record in file order, with exactly these keys:
- `id`: as in the file.
- `meets_criteria_on_abstract`: "yes" (a pretrained generative language model is itself tested on at least one
  task from cognitive psychology or a neighbouring experimental field and new results on its behaviour are
  reported), "no", or "unclear".
- `failed_criterion`: when "no", one of `not-llm`, `tool-use`, `questionnaire-only`, `benchmark-only`,
  `neural-only`, `no-new-data`, `other`; else null.
- `paradigms`: list of {"name": short name as in the abstract, "family": one code of HB, JDM, RE, TOM, MEM,
  LANG, LEARN, NUM, MOR, DEV, OTH (extraction form section C)}; empty list if none is named.
- `models`: list of model names as written (for example "GPT-4", "Llama 2 70B"); empty if none is named.
- `model_families`: list from GPT, Claude, Gemini, Llama, Mistral, Qwen, OLMo, other (deduplicated).
- `n_models_stated`: integer if the abstract states how many models were tested, else null.
- `languages`: list of the languages of the task items if stated (for example "English", "Chinese"), else [].
- `modality`: "text", "image+text" or "not_stated".
- `human_comparison`: "yes" if the abstract says model results are compared with human data, "no" if it says
  there is none, "not_stated" otherwise.
- `rq1_codable`: true if at least one paradigm family and at least one model or model family are named.

Rules: code only what the title and abstract say; never guess a model or paradigm from your knowledge of the
paper; unknown is an empty list or "not_stated". Do not search the web and do not open other files.
Write the output with the Write tool in one call. Reply in at most 3 lines: batch number, records coded, counts
of meets_criteria yes / no / unclear.
