# Evaluating a Japanese News Summarizer — submission

**Read `report.md` first.** This file covers how to run things and how AI was used.

## Deliverables

| path | contents |
|---|---|
| `report.md` | exploration, design, validation, limitations |
| `scores.jsonl` | 250 rows, one per `summary_id` |
| `code/` | everything used to produce the scores and the validation |
| `runs/` | all intermediate artifacts, including every judge verdict |
| `.claude/agents/` | the pinned-model subagent definitions |
| `annotations/packets/` | the blind review packet, built then left unused (see below) |

## `scores.jsonl` schema

One JSON object per line, 250 rows, joins to `data/summaries.jsonl` on `summary_id`.

| field | meaning |
|---|---|
| `summary_id`, `article_id` | join keys |
| `faithfulness`, `coverage`, `coherence`, `selection` | 0–4, frozen rubric v1.2 (`code/prompts/rubric.md`) |
| `within_article_rank` | 1 = best, ties preserved, under the frozen lexicographic rule |
| `n_claims`, `n_contradicted`, `n_unsupported` | from the judge's claim decomposition |
| `structural_arm` | derived from text relations, **not** from the judge |
| `baseline_a_score`, `baseline_b_score` | the two comparison baselines |
| `judge_batch` | 0–4; which judge instance scored it. **Needed to interpret cross-article comparisons** — see report §3.4 and limitation 3 |
| `rank_coverage_first`, `rank_unweighted_sum`, `score_sum` | alternative orderings, see report §3.4 |
| `rationale` | the judge's own one- or two-sentence justification |

**The four dimension scores are the primary result. Every overall rank is exploratory.**

The frozen rule has a known defect (report §3.4): it sorts faithfulness first, and a
verbatim copy cannot be unfaithful, so a lead extract is ranked first in 25 of 50 articles.
`rank_unweighted_sum` satisfies more of the expected structural orderings — but "satisfies
more structural priors" is not the same as "is correct", and **no rule here has independent
quality labels behind it**. All three ranks are shipped as a sensitivity analysis, not as
an answer. If you need a single ordering, `rank_unweighted_sum` is the least bad one
tested; treat it accordingly.

## Reproducing

Python 3.11, standard library only. No third-party packages, no `requirements.txt` needed.

**Reproducibility is verified, not just claimed.** Re-running all three deterministic
scripts from scratch produces **byte-identical** output to what is committed
(`perturbations.jsonl`, `baselines.jsonl`, `human_review_selection.json` all diff clean
against seed 20260918).

```bash
# rebuild and validate the deliverable from the saved judge verdicts
python3 code/assemble_scores.py           # regenerates scores.jsonl
python3 code/validate_submission.py       # 250 rows, ranges, join integrity
python3 code/analyze_results.py           # recomputes the main quantitative results in report.md

# verification — runs against the committed artifacts, no model calls
python3 code/provenance_check.py          # checks declared producer metadata (see caveat below)
python3 code/verify_keypoints.py          # key points: 3-6 units, verbatim excerpts, one main event
python3 code/verify_judge.py runs/judge/all_b0.jsonl   # every cited excerpt is verbatim in its article

# deterministic artifacts — regenerate exactly, seed 20260918
python3 code/build_perturbations.py       # the 137 constructed-corruption items
python3 code/baselines.py                 # both baselines over all 250
python3 code/build_human_packet.py        # the blind review packet
```

**Judge verdicts are not regenerable from a script here.** They were produced by Claude
Sonnet 5 subagents under the prompts in `code/prompts/`, and all 250 verdicts plus all 137
perturbation verdicts are committed under `runs/judge/`. Every number in the report is
computed from those committed files, so the analysis reproduces exactly. Re-running the
judge against a live API would produce fresh verdicts that will differ.

## How AI was used

AI use was heavy, structured, and is the honest answer to "which decisions were yours".

**Model roles were separated deliberately**, so that no single model designed the rubric,
applied it, and validated the result:

| work | model |
|---|---|
| exploration, rubric design, adjudication, this report | Claude Opus 5 (orchestrator) |
| key-point extraction, judging all 250, judging 137 perturbations, baselines, tooling | Claude Sonnet 5 (subagents, `.claude/agents/`) |

Every judge instance was **blind**: given the rubric, the article and one candidate, and
explicitly denied the `reference_summary` field, the structural arm census, the
predictions file, the perturbation answers, and every other judge's output.
`code/provenance_check.py` checks the **declared** producer metadata on every output row
against the role→model mapping. It cannot verify which model actually ran — it detects
misrouted or unstamped output, not a dishonest stamp.

**Division of labour, stated plainly.** Claude proposed and implemented the exploration,
the rubric, the experiments, the scoring runs and the first draft of this report. My role
was to direct and interrogate it: I set the scope, pushed back on conclusions, chose to
freeze rather than keep tuning, commissioned an independent review of the finished package,
and required the corrections that followed — the invalid date labels, the overstated
paraphrase claim, the untested rater-effect claim, and the reproducibility defects. Where
the report says a claim was withdrawn or softened, that happened because the work was
challenged, not because it was right the first time.

The design decisions are ones I reviewed and approved rather than originated
unaided. The submission and its limitations are my responsibility.

**A note on the human review.** I do not read Japanese, so no native-speaker validation was
performed. A blind review packet was built (`runs/human_review*.json`,
`annotations/packets/`) before I confirmed this, and is included unused. The report treats
this as a limitation rather than working around it — see limitation 4.

**Where the AI caught my errors.** Four defects in my own frozen artifacts were found by
the subagents executing against them, not by me: key points returned as topic labels rather
than propositions; perturbations that left summaries contradicting themselves; perturbations
with impossible values (`23月`); and a self-contradictory faithfulness anchor. Each was
reported unprompted rather than papered over. They are documented in `runs/KNOWN_ERRORS.md`
rather than quietly fixed, because several were found after the freeze.

## Honest summary of what this evaluation does and does not establish

**Established.** The judge detects scripted corruptions at 95% overall on labels that
survive a semantic audit — entity and quantity swaps at 100% — raises no false
contradiction on meaning-preserving paraphrase (0/33), scores byte-identical
candidates identically (8/8), and reproduces every structural arm signature while blind to
the arms.

**Not established.** Whether its quality judgements match a native Japanese reader's;
whether it ranks the 101 abstractive candidates correctly, since no ground truth exists for
that subset; whether its scores are *stable* under paraphrase, as opposed to raising no
false contradiction (only 15/33 controls kept the same score, confounded by rater effect);
whether it detects date corruptions at all, since those labels proved invalid; and whether
any per-arm figure or within-article ranking is free of the rater effect between judge
instances.
