# Pre-registered predictions — written before any candidate was scored

Rubric v1 (`code/prompts/rubric.md`) implies a specific score profile for each structural
arm. These are recorded now so the validation can **falsify** the design rather than
rationalise whatever comes out. Arms are known from `runs/arm_census.json`; the judge is
blind to them.

Scale 0–4 per dimension. Ranges where exploration showed genuine variation.

| arm | faith. | cover. | coher. | select. | reasoning |
|---|---|---|---|---|---|
| abstractive — clean | 4 | 3–4 | 4 | 4 | the intended good summary |
| abstractive — corrupted | 0–1 | 3–4 | 4 | 4 | **only faithfulness moves**; its clean sibling is otherwise identical |
| reference verbatim | 2–4 | 2–3 | 4 | 4 | unsupported claims in some (37426493); often thin (48116477, 45715110) |
| permutation of reference | 2–4 | 2–3 | **2** | 4 | identical to its reference except order |
| truncation of reference | 3–4 | 2 | **1** | 4 | cut mid-sentence; loses the tail of the content |
| lead extract | **4** | 1–2 | 3–4 | **1** | verbatim from source ⇒ maximally faithful, minimally useful |
| misattached | **0** | **0** | 4 | 4 | fluent and well-formed, about a different article |

## The falsifiable claims

1. **Lead extracts score 4 on faithfulness and ≤2 on coverage.** If the judge penalises
   faithfulness here it is conflating "bad summary" with "false" — the exact failure the
   dimension separation exists to prevent.
2. **Misattached candidates score 0 on faithfulness *and* 0 on coverage, while scoring 4
   on coherence and selection.** If coherence or selection drops, the judge is leaking a
   global quality impression into dimensions that should be blind to it.
3. **Corrupted/clean sibling pairs differ on faithfulness by ≥3 and on every other
   dimension by ≤1.** This is the paired sensitivity *and* specificity test in one.
   n=26 pairs. It is the sharpest single check available.
4. **Permutations differ from their own reference only on coherence.** Same text, same
   claims, different order. Any other dimension moving is judge noise.
5. **The reference arm does not sweep first place.** Exploration found references with
   unsupported claims and one-sentence coverage against three-sentence abstractive
   candidates that cover everything. Under the lexicographic rule the clean abstractive
   should outrank the reference in a substantial minority of articles.
6. **Duplicate-reference pairs receive identical scores.** 8 articles, byte-identical
   candidates. Any difference is pure judge variance, measured without cache.

## What would falsify the design rather than the judge

- If corrupted and clean siblings are **not** separated on faithfulness, claim-level
  checking has failed at the task it was chosen for, and the rubric needs rework — not
  the prompt.
- If every arm collapses into 3–4 across all dimensions, the scale lacks discrimination
  and the anchors are too lenient.
- If prediction 5 fails **and** reading the disagreements shows the references really were
  better, then the exploration reading was biased, and the report must say so.

## Predictions I am least confident in

- Reference faithfulness range (2–4) is wide. Only 4 of 50 references were read closely.
- Lead-extract coherence (3–4): captions splice awkwardly into the first sentence, so this
  may land lower than predicted.
- Truncation coverage (2): depends heavily on where the cut falls, which varies.
