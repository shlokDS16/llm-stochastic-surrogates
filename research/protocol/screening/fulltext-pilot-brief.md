# Brief for the full-text reference pilot (amendment v0.8 C; frozen before the first reader starts)

You are the full-text eligibility reader for a systematic review. You are blind to every screening label:
do not open anything under `data/processed/screen/` and do not try to infer how the record was screened.

Input: `data/processed/fulltext-pilot/reading-list.jsonl`, the 10 lines your task names (pilot_id, id, title,
year, doi, pdf_url / oa_url / landing). Criteria: `research/protocol/screening/criteria.md` (read it first).

For each record:
1. Obtain the full text from an open-access source only: the `pdf_url` or `oa_url`, else the arXiv version
   (search arXiv by exact title), else the landing page if it shows the full text. Save a PDF to
   `research/sources/pdfs/fulltext-pilot/<pilot_id>.pdf` (git-ignored) with curl and convert it once with
   `"C:\Users\Shlok\AppData\Roaming\Python\Python314\Scripts\markitdown.exe" <pdf> > research/sources/md/fulltext-pilot/<pilot_id>.md`.
   Never use paywall workarounds. If no open full text exists, record `full_text_obtained: false`.
2. Read only what you need: abstract, methods (models used, tasks given), results headings. Do not read
   whole long papers; about 15k tokens per paper is the ceiling.
3. Judge eligibility against the three criteria and the exclusion list:
   - `eligible`: "YES" (meets 1, 2 and 3), "NO" (fails at least one), or "UNCLEAR".
   - `failed_criterion` when NO: one of `not-llm-subject`, `no-psych-paradigm`, `no-new-data`, `tool-use`,
     `questionnaire-only`, `benchmark-only`, `neural-only`, `review-or-position`, `other`.
   - `paradigm`: the cognitive paradigm(s) given to the model, in a few words (empty if none).
   - `evidence`: where you saw it (section name and page), plus at most one quote under 15 words.
   - `borderline`: true if a reasonable reviewer could decide the other way.
4. Also answer from the abstract alone: `rq1_codable_from_abstract`: true if the abstract names the
   paradigm(s) and the model(s) tested well enough to code them.

Write `data/processed/fulltext-pilot/judgements-<k>.jsonl` (your task gives k) with one JSON line per record:
{"pilot_id", "id", "full_text_obtained", "source_used", "eligible", "failed_criterion", "paradigm",
"evidence", "borderline", "rq1_codable_from_abstract"}. Write it with the Write tool in one call at the end.
Reply in at most 4 lines: counts of YES / NO / UNCLEAR / no full text, and how many are borderline.
