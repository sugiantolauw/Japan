# Definition of Done — Japanese Summarizer Evaluation

This file is the contract for the assignment. It says what "finished" means,
which actor performs each task, and how each assignment is verified.
It is deliberately short. The experiment log (`runs/experiments.jsonl`) is
the only other process artifact.

## 1. Done means all of the following hold

### Artifacts
- [ ] `submission/README.md`, `submission/report.md`, `submission/scores.jsonl`, `submission/code/` exist.
- [ ] `scores.jsonl` has exactly 250 rows, one per `summary_id`, every row joinable to
      `data/summaries.jsonl`, each with all dimension scores, the composite rank, and failure flags.
      Schema documented in README.
- [ ] `runs/split.json` (10 exploration / 10 development / 30 held-out, by article, seeded) is committed.
- [ ] The frozen evaluator's commit hash is recorded in `runs/FREEZE.md` **before** any held-out
      result is examined.

### Results
- [ ] Three scorers run on the same items — structural baseline, reference-similarity baseline,
      LLM evaluator — reported as paired differences with article-level bootstrap intervals.
- [ ] Validation evidence exists for each of:
      1. structural detection precision/recall for the completeness and selection dimensions (n=50 articles);
      2. paired sensitivity **and** specificity on the 26 factual-variant pairs;
      3. determinism on the 8 duplicate-reference pairs, run **without** cache;
      4. independent annotation at whatever N the timing test supports, with agreement and intervals;
      5. repeat-run stability on the 10 development articles + the 26 pairs (k=3);
      6. bias regressions against length, copy rate and reference similarity.
- [ ] Every number in the report is reproducible from committed cache by one documented command.
      The live re-run path is documented separately with the caveat that fresh calls vary.

### Honesty
- [ ] Report follows observation → design decision → validation evidence → limitation.
- [ ] Report includes the evaluator's own mistakes and the hypotheses that died
      (wrong-language 0/250; repetition 0/250; sentence-limit violations 2/250).
- [ ] Every claim is marked **established / uncertain / unresolved**. No target is reported
      as "passed" without an interval that supports it.
- [ ] The structural-statistics leak is disclosed: structural detectors were derived from
      full-dataset inspection before the split existed; only the semantic judge is truly held out.
- [ ] AI use is disclosed, including the role separation in §2 and whether annotation was
      human or model-assisted.

### Non-success conditions
Budget exhaustion, a development plateau, or missing independent annotation are stopping
conditions. They are reported as outstanding work. They are never presented as completion.

## 2. Task allocation

| # | Task | Actor | Mechanism | Output |
|---|------|-------|-----------|--------|
| 1 | Split manifest, evidence log, close reading of 10 exploration articles | Orchestrator (main session) | direct | `runs/split.json`, `runs/evidence_log.md` |
| 2 | Rubric design, freeze decision, adjudication of disagreements, report | Orchestrator (main session) | direct | `code/prompts/rubric.md`, `submission/report.md` |
| 3 | Deterministic detectors, both baselines, bootstrap, bias regressions, and all judge/annotation packets | `builder` agent — **Sonnet 5** | Agent tool | `code/*.py`, `annotations/packets/` |
| 4 | Key-point extraction, 50 articles, before any candidate is seen | `keypoints` agent — **Sonnet 5** | Agent tool | `runs/keypoints/*.json` |
| 5 | Primary judge, all 250 summaries, blind | `judge` agent — **Sonnet 5** | Agent tool | `runs/judge/*.jsonl` |
| 6 | Repeat runs k=3, dev articles + 26 pairs | `judge` agent — **Sonnet 5**, fresh contexts | Agent tool | `runs/judge_repeat/*.jsonl` |
| 7 | Cross-tier check, held-out subset only | `judge` agent with **Opus 5** override | Agent tool, `model: opus` | `runs/judge_crosstier/*.jsonl` |
| 8 | Independent annotation | **The other LLM (GPT), fresh session** | paste-ready packets → paste results back | `annotations/gpt/*.json` |
| 9 | Blind human review (optional, strongest signal) | **You** | packets → your ranking | `annotations/human/*.json` |

The orchestrator does tasks 1 and 2 only. It never produces a judge verdict, a key-point set,
or an annotation row. If it does, `code/provenance_check.py` fails.

## 3. Enforcement

**Subagents (tasks 3–7).** Each agent's model is pinned in its definition under
`.claude/agents/<name>.md` (`model:` in the frontmatter). Every Agent tool call is visible in the
session transcript with its model. Every output row carries a `producer` block:

    {"producer": {"role": "judge", "model": "claude-sonnet-5", "agent": "judge", "run_kind": "primary"}}

`code/provenance_check.py` verifies every row under `runs/` has a producer, that the role→model
mapping matches this table, and that no judge/keypoints/annotation row names the orchestrator.

**External actors (tasks 8–9).** The orchestrator writes packets to `annotations/packets/`. It is
forbidden from writing anything under `annotations/gpt/` or `annotations/human/`. Each result file
must carry `{"annotator": "gpt-…" | "human", "fresh_session": true, "saw_orchestrator_context": false}`.
The GPT session must be **fresh** — it must not have seen this planning conversation, which
contains the full arm inventory. A contaminated annotator is pattern-matching to a known
construction, not judging quality.

**What enforcement cannot do.** Nothing here cryptographically proves which model ran inside a
subagent. The audit trail is: the agent definition, the Agent call in the transcript, and the
provenance stamp. The check catches accidental mis-assignment and role-mixing. It does not
catch deliberate deception, and this file does not claim otherwise.

## 4. Cut order if time runs short
1. Synthetic controlled edits (the 26 natural pairs are better evidence).
2. Cross-tier check (task 7).
3. Repeat runs → k=2 (task 6).
Never cut: the split, the freeze, the baselines, the factual-pair test, or the honesty section.
