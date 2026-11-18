# Model identifiers used in CRP-S03 (for the methods and the AI-use statement)
- Codex (OpenAI) via codex-cli 0.162.1: model line in every raw log reads `model: gpt-6-luna`, provider openai
  (e.g. runs/extraction-pilot/codex/150.raw.log; research/debates/2026-10-16-CRP-S03-extraction-form-v11/round-12-codex.raw.log).
  Used as protocol critic (debates) and as the second extraction coder.
- Claude subagents in CRP-S03 were dispatched with the model alias `sonnet` (paper-reader, statistician, lab-engineer,
  figure-smith, latex-typesetter, manuscript-writer); the Claude Code environment of 2026-10-16 lists the current Sonnet as
  `claude-sonnet-5-5`. The orchestrating session ran on `claude-opus-5-5`. TO CONFIRM for CRP-S01/S02 screeners (Haiku, Sonnet):
  check those sessions' records before stating exact versions.
- Local open-weight raters: OLMo-2-7B and Qwen2.5-7B-Instruct (revision in protocol amendment v0.8); embedding model
  BAAI/bge-small-en-v1.5 (runs/rq1-semantic-map/config.json).
