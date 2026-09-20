# Evaluating a Japanese News Summarizer — submission

**Read `report.md` first.** This file covers how to run things and how AI was used.

## Deliverables

| path | contents |
|---|---|
| `report.md` | exploration, design, validation, limitations |
| `scores.jsonl` | 250 rows, one per `summary_id` |
| `code/` | everything used to produce the scores and the validation |
| `runs/` | all intermediate artifacts, including every judge verdict |

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
| `rank_coverage_first`, `rank_unweighted_sum`, `score_sum` | alternative orderings, see report §3.5b |
| `rationale` | the judge's own one- or two-sentence justification |

**Use the four dimension scores, not `within_article_rank`.** The frozen ranking rule has a
known defect (report §3.5): it sorts on faithfulness first, and a verbatim copy of the
article is maximally faithful, so lead extracts win 24/50 articles. The rank is reported
because it is what was frozen, not because it is the best ordering. Use `rank_unweighted_sum` instead: it is the only rule tested that respects all 17
reference-over-truncation orderings, scores highest on overall structural compliance (99%
vs 95%), and cuts degenerate copies taking first place from 25/50 to 4/50. Report §3.5b.

## Reproducing

Python 3.11, standard library only. No third-party packages, no `requirements.txt` needed.

```bash
# verification — runs against the committed artifacts, no model calls
python3 code/provenance_check.py          # each output came from its assigned model
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
`code/provenance_check.py` enforces the role→model mapping on every output row.

**Decisions that were mine:** the four dimensions and their anchors; the evidence boundary;
the lexicographic rule (and its defect); the split and freeze discipline; every hypothesis
in `runs/PREDICTIONS*.md` and the decision to record failures rather than amend them; the
choice to validate through constructed ground truth given that I do not read Japanese; and
every decision not to fix a frozen artifact after the freeze.

**AI-assisted:** all Japanese-language judgement, the perturbation substitution and antonym
tables, the key-point propositions, and the analysis code.

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

**Established.** The judge detects scripted entity and quantity corruptions at 100%, does
not penalise meaning-preserving paraphrase (0/33 false positives), scores byte-identical
candidates identically (8/8), and reproduces every structural arm signature while blind to
the arms.

**Not established.** Whether its quality judgements match a native Japanese reader's;
whether it ranks the 101 abstractive candidates correctly, since no ground truth exists for
that subset; and whether the aggregate per-arm figures are free of the up-to-2.3-point
rater effect between judge instances.
