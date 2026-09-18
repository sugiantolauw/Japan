# JapanAI — LLM Application Evaluation Design

Evaluation of a Japanese news-article summarizer: 250 candidate summaries across
50 XL-Sum Japanese articles, methods undisclosed.

| Path | Contents |
|---|---|
| `DEFINITION_OF_DONE.md` | The contract: done-criteria, task allocation by model tier, enforcement |
| `data/` | Supplied data, unmodified |
| `runs/split.json` | Seeded 10/10/30 split by article, with the pre-split leak disclosed |
| `runs/evidence_log.md` | Close-reading observations — the exploration record |
| `code/provenance_check.py` | Audits that each output was produced by its assigned actor |
| `.claude/agents/` | Pinned-model subagent definitions (judge, keypoints, builder) |

Status: Phase 0 complete, Phase 1 (exploration) in progress — 4 of 10 exploration
articles read closely. Seven generation arms identified so far.
