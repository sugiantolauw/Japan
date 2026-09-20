# Development-set results — rubric v1.1, 50 candidates, 10 articles

Scored blind. `verify_judge.py` passes on the final file: 0 evidence strings fail the
verbatim check.

**But the raw pass was not clean.** The judge agent reported correcting **16
verbatim-evidence failures** during its own run — all cases where it spliced two
non-adjacent article spans together with "…" and presented the result as one quotation.
The final file's clean bill of health therefore understates the raw error rate: roughly
8% of evidence strings were initially not verbatim. This is a measured judge failure mode
and belongs in the validation section, not in a footnote.

## Scores by structural arm (judge blind to arm)

| arm | n | faith | cover | coher | select |
|---|---|---|---|---|---|
| abstractive | 20 | 2.85 | 2.10 | 4.00 | 4.00 |
| lead extract | 10 | **4.00** | 1.80 | 2.90 | 2.50 |
| reference | 12 | 3.33 | 1.83 | 4.00 | 4.00 |
| permutation | 2 | 3.50 | 2.00 | **2.50** | 4.00 |
| truncation | 3 | 2.33 | 1.33 | **1.00** | 4.00 |
| misattached | 3 | **0.00** | **0.00** | **4.00** | **4.00** |

## Predictions

**P2 — now PASSES.** Misattached candidates score 0/0/4/4 exactly. The v1.1 scoping of
selection to material *type* rather than topical relevance fixed the collapse seen in the
pilot. The diagnostic vector — fluent, well-formed prose about the wrong article — is
preserved.

**P4 — PASSES 2/2.** Permutations differ from their own reference on coherence alone
(−2 and −1), with faithfulness, coverage and selection identical. Same text, different
order, and only the order-sensitive dimension moved.

**P3 — FAILS 0/3, for three different reasons.** This is the substantive result.

### Pair 1 (42520667, J=0.70) — the test was wrong, the judge was right

A genuine minimal pair: マシュハド→タブリーズ and 52人→72人. Faithfulness **4 vs 0**:
sensitivity is excellent. It "failed" because coverage also moved (4 vs 2) — but the
corrupted candidate genuinely omits `シリア介入への不満`, which its sibling includes. The
pair is not content-identical, so coverage *should* differ. My specificity criterion
assumed minimality that natural pairs do not have.

### Pair 2 (35278497, J=0.45) — the test's premise was wrong

I assumed every near-twin pair is one clean and one corrupted candidate. Here **both are
faulty**: `…1fd162f1` reverses polarity (`約100件に下方修正` when the article reports an
upward revision past 500), and `…af8a0e59` asserts 516件, 4割 and 10日, none of which
appear in the source. Faithfulness 1 vs 2 is a defensible reading of two different
defects, not a failure to separate.

### Pair 3 (45583472, J=0.45) — a REAL rubric defect

`…86972732` invents an entire NHS regulatory mandate (calorie warning labels compulsory
from next year). `…a1f7946d` is clean. Scores: **2 vs 4**.

Faithfulness 2 is *correct under v1.1*, whose anchor reads "contains UNSUPPORTED claims
material to the meaning; nothing CONTRADICTED". A fabricated policy is unsupported rather
than contradicted — the article simply never mentions it.

**That is the defect.** The scale keys severity on the supported/contradicted axis alone,
so a wholly fabricated event caps at 2 while a single swapped digit scores 0–1. Inventing
a government regulation is at least as harmful as misstating a number, and the rubric
ranks it as less serious. Three of the six corruption types observed in exploration —
fabricated quotation, fabricated event, hallucinated status — all land in this
under-penalised bucket.

## Fix: rubric v1.2

Faithfulness now distinguishes *absent detail* from *invented content*:

- **2** — material UNSUPPORTED **detail**: a plausible fact absent from the source
  (a descriptor, an unstated date) that does not invent an event or an attribution.
- **1** — one CONTRADICTED claim, **or one fabricated event, action, policy or
  quotation** — content invented rather than merely missing.
- **0** — multiple such claims, or a candidate describing an event the article does not
  cover at all.

## What P3 tells us about the instrument, not just the rubric

Natural near-twin pairs are a weak sensitivity test: they are not minimal, the clean/
corrupted premise does not always hold, and at J≈0.45 two candidates may differ in
content for legitimate reasons. The **perturbation suite is the sound instrument** —
there the pairs are minimal by construction and ground truth is certain, because the
corruption was scripted. P3 stays in the record as failed, with the diagnosis that the
test was partly ill-posed. The perturbation run is what will actually establish
sensitivity and specificity.

## Also noted

Mean claims per candidate rose from 2.9 (v1) to **3.78** (v1.1) — the finer-decomposition
instruction moved it, but short 1–2 sentence candidates legitimately yield fewer claims.
Claim statuses: SUPPORTED 144, UNSUPPORTED 41, CONTRADICTED 4, AMBIGUOUS 0.
