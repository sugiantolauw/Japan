# Evaluator freeze

Recorded **before** any held-out result was examined.

| item | value |
|---|---|
| frozen rubric | `code/prompts/rubric.md` **v1.2** |
| rubric commit | `cbc808c` |
| split manifest | `runs/split.json`, seed 20260918 |
| key points | `runs/keypoints/` (20 exploration+development articles; held-out extracted at scoring time under the same frozen prompt) |
| baselines | `code/baselines.py`, thresholds fixed on development articles only |
| perturbations | `runs/perturbations.jsonl`, 137 items, exploration+development only |

## What may still change after this point

Nothing that affects scoring. Permitted: analysis code, report prose, and additional
validation measurements. Forbidden: rubric anchors, dimension definitions, the ranking
rule, baseline thresholds, and the key-point extraction prompt.

## Rubric version history, and why each change was made

- **v1 → v1.1** (pilot, 3 development articles). The judge scored a misattached candidate
  0 on *selection*, reading "summary-appropriate" as "appropriate for this article". That
  collapses selection into coverage and destroys the diagnostic vector for fluent prose
  about the wrong story. Selection rescoped to material *type*. Claim decomposition also
  tightened — 2.9 claims per candidate was too coarse to expose corruptions inside
  compound claims.
- **v1.1 → v1.2** (full development run, 50 candidates). A candidate inventing an entire
  NHS regulatory mandate scored 2, because severity keyed on the supported/contradicted
  axis and a fabrication is *unsupported* rather than contradicted — while a swapped digit
  scored 0–1. Severity now keys on *invention*: fabricated events, actions, policies and
  quotations score 1 alongside contradictions.

Both defects were found on development data. Scoring all 250 before piloting would have
propagated them silently through every result.

## Consequence for the final scores

The development set was scored under v1.1. Because v1.2 changes the faithfulness scale,
**all 250 candidates are re-scored under v1.2** so the delivered `scores.jsonl` is
internally consistent under one rubric version. The v1.1 development results are retained
in `runs/judge/dev_v11.jsonl` as the evidence that motivated the change.
