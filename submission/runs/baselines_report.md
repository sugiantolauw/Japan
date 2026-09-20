# Deterministic baselines — frozen rules and development evidence

Produced by: `builder` agent, from `code/baselines.py` (all thresholds frozen before
`code/baselines.py` was ever run against development, held-out, or exploration articles
beyond the 10 development articles used to set them). Output: `runs/baselines.jsonl`
(250 rows). Reusable ranking/CI utilities: `code/rank_utils.py`.

No evaluative judgement about summary quality was made by hand. Every number below is
computed by `code/baselines.py` and the snippets in this report; nothing is eyeballed.

## Purpose

These two scorers exist to answer one question about the (separately built) LLM judge:
**does the expensive semantic judge add anything over cheap, model-free signals?**
Baseline A uses only surface features of the candidate and the article. Baseline B is
explicitly allowed to read `reference_summary` — that is its entire point, and the
comparison against it is diagnostic, not a handicap.

## Tuning discipline

All thresholds and weights in `code/baselines.py` were chosen by inspecting **only** the
10 development articles named in `runs/split.json` → `splits.development`
(`43411421, 41396293, 35278497, 51395937, 45583472, 40504740, 50285251, 36285464,
42520667, 46601033` — 50 candidate summaries). The exploration and held-out articles were
never inspected to pick a parameter. The frozen constants and the exact development
statistics that produced them are recorded as comments at the top of `baselines.py` and
reproduced below. After freezing, both baselines were applied unchanged to all 250
candidates in one pass (`python3 code/baselines.py`).

---

## Baseline A — structural heuristic

Uses only: char-5-gram copy rate against the article, presence of terminal punctuation,
sentence count, character length, and the mean article-position of the candidate's
matched n-grams. No reference, no model, no arm labels — the label mapping in
`runs/arm_census.json` was used only *after* the fact, to describe what the frozen rule
responds to, never to fit it.

**Score = 1 − (penalty_copy + penalty_punct + penalty_length + penalty_leadpos)**, floored
at 0. Each penalty is a fraction of a fixed weight; the four weights sum to 1.0, so a
candidate that trips every penalty at full severity bottoms out at exactly 0.

| component | rule | weight | frozen threshold(s) | development evidence |
|---|---|---|---|---|
| copy-rate extremes | ramps in from `COPY_HIGH` to 1.0, and from `COPY_LOW` down to 0.0 | 0.40 | `COPY_HIGH=0.90`, `COPY_LOW=0.02` | dev `lead_extract` copy rate 0.95–1.00 vs dev max for every other arm 0.53; dev `misattached` copy rate 0.00–0.01 vs dev min for every other arm 0.03. Both thresholds sit at roughly the midpoint between the two groups, with margin on both sides — not fit to a boundary case. |
| missing terminal punctuation | flat penalty if the candidate doesn't end in `。！？.!?」』` | 0.25 | — | dev `truncation` candidates were missing terminal punctuation 3/3; every other dev arm was 0/50-of-arm. Clean, deterministic marker. |
| length / sentence-count extremes | ramps outside `[LEN_MIN, LEN_MAX]` chars or `[SENT_MIN, SENT_MAX]` sentences, whichever is more extreme | 0.15 | `LEN_MIN=40`, `LEN_MAX=260`, `SENT_MIN=1`, `SENT_MAX=4` | dev legitimate range across all non-degenerate arms was 44–252 chars and 1–4 sentences; bounds padded ~10% past the observed extremes. |
| front-loaded copy ("lead-bias") | flat penalty if ≥5 matched n-grams, copy rate ≥ `LEADPOS_COPY_THRESH`, **and** mean matched-position ≤ `LEAD_POS_THRESH` | 0.20 | `LEADPOS_COPY_THRESH=0.85`, `LEAD_POS_THRESH=0.15`, min matches = 5 | every dev `lead_extract` candidate had mean position ≤0.116 at copy rate ≥0.95; the highest copy rate among dev candidates with a front-loaded position but a legitimate arm was 0.42 (position 0.144–0.567 for that group). 0.85/0.15 sit strictly between the two groups. This term specifically targets the rubric's named Selection failure (captions/bylines at the article's opening), separately from generic near-total copying. |

The mean-position term is the only use of the "position of the summary's content within
the article" feature as an independent penalty; it is otherwise reported per-candidate in
`features.mean_match_position` for transparency even when it doesn't change the score.
An n-gram order-inversion statistic (whether matched n-grams appear in the same relative
order in the candidate as in the article) was also tested on the development set as a
candidate signal for the `permutation` arm. It did not survive: dev `permutation`
candidates showed inversion rates of 0.00 and 0.33, no more distinctive than the 0.03–0.43
range seen across every other arm, because permutation/truncation are built from the
*reference* summary rather than the article body, so few of their n-grams match the
article at all (see below). It was dropped rather than kept at a token weight.

## Baseline B — reference similarity

**Score = char-5-gram F1 between the candidate and that article's `reference_summary`.**

F1 (not raw Jaccard) was chosen because Jaccard's denominator is the *union* of both
n-gram sets, so it penalizes any length mismatch between a short reference and a longer
(or shorter) candidate twice over — once for the extra n-grams contributed by each side.
F1 keeps precision (fraction of the candidate's n-grams found in the reference) and
recall (fraction of the reference's n-grams found in the candidate) as separate terms
before combining them, which is standard practice for exactly this kind of
length-asymmetric overlap scoring (the same reasoning behind ROUGE using F1 rather than
raw Jaccard). No thresholds to freeze here — it is a single closed-form similarity, and
per the task brief this baseline is explicitly allowed to use the reference field.

---

## Mean score by structural arm (all 250 candidates)

`runs/arm_census.json` labels were joined to `runs/baselines.jsonl` only to build this
table; they play no role in either scoring function.

| arm | n | mean Baseline A | mean Baseline B |
|---|---:|---:|---:|
| abstractive_undetermined | 101 | **1.000** | 0.190 |
| reference | 58 | 1.000 | **1.000** |
| lead_extract | 50 | 0.506 | 0.052 |
| truncation | 17 | 0.671 | 0.687 |
| misattached | 15 | 0.752 | 0.004 |
| permutation | 9 | 1.000 | 0.955 |

Reading this table (deterministic observations, not judgements):

- **Baseline B on `reference` = 1.000 by construction** (F1 of a string against itself).
  It is expected to be high on `permutation`/`truncation` too, since those arms are
  *derived from the reference text* (see the note above), not from the article — so
  Baseline B is, unsurprisingly, most sensitive to "was this built out of the reference,"
  which is exactly the shortcut it is supposed to expose.
- **Baseline A on `lead_extract` = 0.506, not near 0**, because copy rate alone does not
  make a lead extract *incoherent* — the copy-rate and front-loaded-position penalties
  fire (0.40 + 0.20 = 0.60 of the weight), but a lead extract that has terminal
  punctuation and a legal length keeps the other 0.40.
- **Baseline A on `misattached` = 0.752, not near 0.** See the caveat below — this is
  weaker than the task brief's expectation and is reported as found, not adjusted.
- **Baseline A on `permutation` = 1.000 and `truncation` = 0.671**: permutation keeps its
  reference-derived sentences intact and terminated, so nothing in Baseline A's four
  penalty terms fires; truncation's low terminal-punctuation rate is exactly what the
  punctuation penalty is built to catch.

## Caveat: structurally-determined vs. the honest (abstractive-only) subset

Per the task brief, 5 of the 6 arms are **structurally determined** by how the candidate
was built — `reference`, `lead_extract`, `truncation`, `permutation`, `misattached` (149
of 250 candidates) — and can in principle be identified by cheap deterministic detectors
without reading for meaning. Only `abstractive_undetermined` (101 of 250) requires actual
semantic judgement to separate quality within it, because those are the only candidates
whose generation method (and therefore rank) isn't given away by their construction.
Reporting only the pooled 250-candidate numbers above would overstate how much a
model-free baseline can do, because 15 of those structurally-determined candidates
(the `misattached` ones) have essentially no textual overlap with their own article and
are close to a free correct answer for **any** copy-rate-based detector — that must not
be allowed to stand in for "the baseline ranks summaries well."

Per-article means, article-cluster bootstrap (`rank_utils.cluster_bootstrap_ci`,
resampling the 50 articles with replacement, `n=10000`, `seed=20260918`):

| subset | n candidates | mean Baseline A [95% CI] | mean Baseline B [95% CI] |
|---|---:|---|---|
| **All 250** | 250 | 0.864 [0.854, 0.874] | 0.400 [0.374, 0.426] |
| **Structurally-determined** (reference, lead_extract, truncation, permutation, misattached) | 149 | 0.772 [0.755, 0.789] | 0.543 [0.505, 0.579] |
| **abstractive_undetermined only (the honest test)** | 101 | **1.000 [1.000, 1.000]** | 0.189 [0.156, 0.227] |

**The headline finding:** on the one subset that actually requires semantic judgement,
Baseline A assigns **every single candidate the identical score of 1.000** — all 101
abstractive_undetermined candidates fall inside every "normal" band (copy rate 0.02–0.90,
present terminal punctuation, length 40–260 chars, 1–4 sentences, not front-loaded). It
has **zero within-article ranking power** where it matters: for any article with two
abstractive candidates, Baseline A ties them, every time. This is not a bug — it is
Baseline A working exactly as designed (catching degenerate *construction* patterns, not
adjudicating fluent prose against each other) — but it means the honest comparison against
the judge on this subset is "a constant vs. whatever the judge does," which is the
sharpest version of the question this task set out to answer. Baseline B does vary within
the abstractive-only subset (only 1 of 50 articles ties its two abstractive candidates on
Baseline B), so unlike Baseline A it is at least capable of producing a non-trivial
within-article ranking there — whether that ranking is any *good* is a question for the
validation step against independent annotation, not for this report.

**Second honest finding — the frozen misattached detector is not perfect.** The task
brief's expectation was that misattached candidates would have copy rate near zero and be
caught almost perfectly. On development data (n=3 misattached candidates, copy rate
0.00–0.01) that held, and `COPY_LOW=0.02` was frozen with what looked like margin on both
sides. Applied unchanged to all 15 misattached candidates in the full 250, copy rate
actually ranges **0.0000 to 0.0417** — two candidates (`45318822_32e158ee`, copy
rate 0.027; `55155049_bbe6c482`, copy rate 0.0417) fall *above* the frozen threshold and
trip none of Baseline A's four penalties, scoring a perfect 1.000 despite being about the
wrong article entirely. The other 13/15 score between 0.60 and 0.95. `COPY_LOW` was **not**
adjusted after finding this — the tuning-discipline rule is to freeze on development and
report what happens on the rest, not to retune once the answer is known. This is reported
as a limitation of a 50-candidate development sample, not corrected after the fact.

## Reproducing these numbers

```
python3 code/baselines.py                 # writes runs/baselines.jsonl (250 rows)
python3 code/provenance_check.py          # provenance check (does not gate baselines.jsonl;
                                           # see note below)
```

The arm-mean table and the bootstrap table above are produced by joining
`runs/baselines.jsonl` to `runs/arm_census.json` and calling
`rank_utils.cluster_bootstrap_ci` on the per-article means of each subset — no manual
numbers appear in this report.

Note on provenance: `code/provenance_check.py` currently validates producer stamps under
`runs/judge*` and `runs/keypoints/` (per `DEFINITION_OF_DONE.md` §3, which lists the
baselines as a `builder`-agent deliverable but does not name `runs/baselines.jsonl` among
the enforced paths). `runs/baselines.jsonl` still carries a full `producer` block on every
row for consistency and future-proofing, even though the current check does not require it.
