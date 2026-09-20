# Handoff — what this project found, decided, and got wrong

A working record for anyone (human or model) picking this up. Written to be useful to
someone who has not read the conversation. Facts are cited to the artifact that holds them.

---

## 1. Empirical findings about the dataset

These are the things worth knowing before designing anything.

### 1.1 The dataset is a fixed 4+1 construction template

Three relations are computable with no model (`runs/arm_census.json`):

| component | n | share |
|---|---|---|
| abstractive — clean or corrupted, undetermined | 101 | 40.4% |
| reference verbatim | 58 | 23.2% |
| lead extract (char-5gram copy rate 1.00) | 50 | 20.0% |
| truncation of reference | 17 | 6.8% |
| misattached (summary of a different article) | 15 | 6.0% |
| permutation of reference (sentences reordered) | 9 | 3.6% |

Every article has **one reference, one lead extract, two abstractive candidates, and one
variable degradation** from {truncation, misattached, permutation, duplicate reference}.
49/50 fit exactly; one substitutes a third abstractive.

**Consequence that shapes everything:** only 2 of 5 candidates per article need semantic
judgement. The other 3 are determined by string relations. Any evaluation compared against
a baseline on *all* candidates is measuring the wrong thing.

### 1.2 The reference summary is itself a candidate, and it is not clean

All 50 articles contain a byte-identical copy of their `reference_summary`; 8 contain two.
References carry a **median 85% novel char-5-grams** against their own article (all 50
above 50%). Concrete defects found by reading:

- `37426493`: reference states the divorce reason `「乗り越えがたい相違」` (absent from the
  article) and the date `20日` (article says 19日). One UNSUPPORTED, one CONTRADICTED, in
  the intended-gold candidate.
- `48116477`: 74-character single sentence that never names the subject of the study.
- `51145805`: reference contains a typo (`だっだと`) which propagates into its permuted twin.

**Therefore:** any reference-based metric is disqualified here, not merely weak. Measured:
a reference-similarity baseline scores **exactly 1.0 on all 58 reference candidates** —
a perfect score on 23% of the dataset by construction (`runs/baselines_report.md`).

### 1.3 Six corruption types, none surface-detectable

entity swap · number/date swap · fabricated quotation · fabricated event ·
hallucinated status · **polarity reversal**

Polarity reversal is the hardest: `継続する` (will continue) vs `即時中断` (suspended
immediately) — same entities, same numbers, opposite meaning. Any entity-overlap or
number-matching check passes it.

One failure is not about truth at all: a verbatim mid-article passage defining what Antifa
*is*, fully supported and fluent, which never mentions the news event. This is why
faithfulness and coverage must be separate dimensions.

### 1.4 Other measured facts

- **No positional leakage.** Mean length, sentence count and copy rate are flat across
  positions k=0–4. The opaque ID suffix is honoured in fact.
- **30/50 articles** open with a photo caption or journalist byline spliced into the body.
  Lead extracts ingest these. The evidence boundary must decide explicitly; we include
  them as source (they are in the supplied text) and penalise them under *selection*.
- **Format compliance is a non-issue**: 2/250 exceed three sentences, 0/250 repetition,
  0/250 wrong language, 0/250 meta-preamble.

---

## 2. Hypotheses: 5 survived, 5 died

| hypothesis | outcome |
|---|---|
| verbatim lead extraction | **survived** — 50/50 articles |
| hallucinated numbers / dates / names | **survived** |
| entity swap | **survived** |
| mid-sentence truncation | **survived** — 17/50 |
| off-topic / wrong-article summary | **survived** — 15/50 |
| >3 sentences | died — 2/250 |
| wrong or mixed language | died — 0/250 |
| degenerate repetition | died — 0/250 |
| meta-preamble | died — 0/250 |
| vacuous genericity | died — not observed |

**Every survivor concerns content being wrong; every casualty concerns output being
malformed.** That single division is what moves the design off lexical metrics.

What was *not* anticipated was structural rather than behavioural: the slot template, the
reference injected as a candidate, sentence permutation, duplicate references, polarity
reversal. Those came only from counting relations between texts.

---

## 3. Design decisions worth copying

**Four dimensions, each anchored to an observed candidate** (`code/prompts/rubric.md`):
faithfulness, coverage (recall of key points), coherence (order + completeness), selection
(precision of material *type*).

- **Coverage and selection are complementary**: recall of what must be said vs. precision
  of what is said. This lets a lead extract score 4 on faithfulness and still rank last.
- **Selection scores material TYPE, not topical relevance.** Learned the hard way — see §5.
- **Format compliance is a reported flag, not a dimension.** 2/250 does not earn billing.

**Lexicographic ranking**, not a weighted sum: faithfulness → coverage → coherence →
selection. A weighted sum cannot justify its own coefficients and lets fluent writing
offset a factual error. Lexicographic ordering is defensible in one sentence and makes
sensitivity analysis concrete.

**Key points extracted before any candidate is seen**, by a separate agent, with verbatim
excerpts and exactly one flagged `is_main_event`. Stops the judge anchoring "what matters"
on the candidate in front of it.

**Pre-registered per-arm predictions** (`runs/PREDICTIONS.md`) written before any scoring,
with an explicit list of which predictions the author was least confident in, and what
outcome would falsify the *design* rather than the judge.

---

## 4. Validating an evaluation in a language you do not read

The author does not read Japanese. This is a normal industrial condition, not a defect,
and the assignment says only that the validation approach is "yours to defend".

**Annotation** (read output, judge quality) needs the language. **Validation** (check the
evaluator against known answers) needs *known answers*. Four sources of those:

1. **Constructed ground truth.** Script a corruption; the answer is known because you made
   it. `runs/perturbations.jsonl` — 137 items: 40 number swaps, 40 entity swaps, 24
   polarity reversals, and 33 **meaning-preserving paraphrase controls the judge must NOT
   penalise** (the specificity half).
2. **Structurally guaranteed answers.** Byte-identical candidates must tie. A truncated
   prefix must be incomplete. A summary copied from another article must be irrelevant.
3. **Internal consistency.** Same input twice → same output. A permutation differs from its
   source only in order, so only coherence should move.
4. **Auditable reasoning.** Every claim verdict must cite a **verbatim** article excerpt.
   Whether that string exists is pure string matching — catches a judge fabricating its own
   evidence, in any language.

**What this cannot establish, and must be stated:** whether the judge's sense of a *good*
Japanese summary matches a native reader's; whether the extracted key points are the right
essential facts; and 3 of the 6 corruption types (fabricated quotation, fabricated event,
hallucinated status) cannot be produced by substitution and so have no constructed ground
truth.

A failed idea worth recording: adjudicating near-twin pairs by Ctrl-F (does the article
contain `ロシア` or `イラン`?) looked like language-free faithfulness validation. It covers
2 of 6 corruption types and **systematically misses polarity reversal**, the hardest one —
so it would have produced a flattering recall number by excluding the difficult cases.

---

## 5. What went wrong — the most transferable part

### 5.1 Every subagent reported success. Four had defects found only by measuring output.

| defect | how it was caught |
|---|---|
| key points returned as topic labels (`発表媒体`), not propositions — 75/100 under 8 chars, 0 with a verb | measured the length distribution |
| perturbations replaced one occurrence of a multi-occurrence span, leaving summaries that contradict *themselves* — catchable without the source, inflating the recall being measured | counted span occurrences |
| perturbations produced impossible values (`23月`, `2泊20日`) — rejectable on plausibility alone, same confound | scanned spans in compound numeric context |
| judge spliced two non-adjacent article spans with "…" and presented them as one quotation — 16 cases, ~8% of evidence strings | the agent's own verifier caught these; the clean final file would have hidden them |

Every one of those reports was confident, well-written prose claiming success. **Read the
output, not the report.** This is also the argument the whole validation architecture
rests on, applied to the pipeline that builds it.

### 5.2 Author errors, kept in the record

- **"16 misattached"** was wrong; it is 15. A detector flagged a candidate at copy=0.048
  where a rival article beat its own by 0.002 — but that candidate *is* its article's
  reference, which happens to be unusually abstractive. Fix: test reference-identity
  **before** copy rate. A cheap structural detector returning a confident wrong answer.
- **"A seventh arm I did not predict"** — off-topic summaries were item 7 on the original
  hypothesis list. Claimed novelty for something already predicted.
- **P1 was a bad prediction, not a judge failure.** Predicted lead extracts must score ≤2
  on coverage. BBC copy is an inverted pyramid — the opening paragraph often *is* the main
  event. The prediction was recorded as failed and **not amended**; editing a
  pre-registration after seeing data defeats its purpose.
- **P3 was partly an ill-posed test.** It assumed natural near-twin pairs are minimal and
  consist of one clean and one corrupted candidate. Neither holds: at J≈0.45 two candidates
  differ for legitimate reasons, and in one pair *both* were faulty. The sound instrument
  is the perturbation suite, where minimality is guaranteed by construction.

### 5.3 Two rubric defects the pilot caught before they propagated

- **v1 → v1.1**: the judge scored a misattached candidate 0 on *selection*, reading
  "summary-appropriate" as "appropriate for this article". Defensible — and it collapses
  selection into coverage, destroying the diagnostic that these candidates are fluent
  well-formed prose about the wrong story. Fixed by scoping selection to material type.
- **v1.1 → v1.2**: a candidate that invented an entire NHS regulatory mandate scored
  **2**, because the scale keyed severity on the supported/contradicted axis and a
  fabrication is *unsupported* rather than contradicted. A swapped digit scored 0–1. So
  inventing a government policy ranked as **less serious** than misstating a number, and
  three of the six corruption types sat in that under-penalised bucket. v1.2 keys severity
  on *invention*.

Both were found on development data, before freezing. Scoring all 250 first would have
propagated them silently through every result.

### 5.4 Process observation

Four rounds of plan review each produced roughly one real correction. Every *discovery* —
the template, the misattached arm, the corruption taxonomy, the baseline's blindness —
came from running code against the data. Plan review has sharply diminishing returns
against exploration.

---

## 6. Measured results so far

**Baselines** (`runs/baselines.jsonl`, frozen on development articles only):

- The **structural baseline assigns an identical score to all 101 abstractive candidates**
  and ties them in **50/50 articles** — zero ranking power on the only subset requiring
  judgement. It discriminates exactly the candidates already determined by string relations.
- The **reference-similarity baseline scores exactly 1.0 on all 58 references.**

**Judge, 50 development candidates under v1.1** (`runs/DEV_RESULTS.md`):

| arm | faith | cover | coher | select |
|---|---|---|---|---|
| misattached | **0.00** | **0.00** | 4.00 | 4.00 |
| lead extract | **4.00** | 1.80 | 2.90 | 2.50 |
| truncation | 2.33 | 1.33 | **1.00** | 4.00 |
| permutation | 3.50 | 2.00 | **2.50** | 4.00 |
| reference | 3.33 | 1.83 | 4.00 | 4.00 |
| abstractive | 2.85 | 2.10 | 4.00 | 4.00 |

Predictions: **P2, P4, P5, P6 pass. P1 fails (bad prediction). P3 fails (partly ill-posed
test, partly a real rubric defect, now fixed in v1.2).**

Notable: the **reference arm took first place in none** of the three pilot articles, from
a judge that never saw which candidate was the reference — independent corroboration of
the exploration finding about XL-Sum reference quality.

---

## 7. State and what remains

Done: exploration (10 articles read closely, evidence log), arm census, rubric v1.2,
pre-registered predictions, key points for 20 articles, 137 perturbations, two frozen
baselines, ranking utilities (tau-b + article-level cluster bootstrap), judge pilot and
full development run, blind review packet, provenance checking.

Remaining: freeze at v1.2 → score all 250 + run the 137 perturbations → validation
analysis (perturbation recall/precision, duplicate determinism, baseline comparison on the
abstractive-only subset, length/copy/reference-similarity bias regressions) → `scores.jsonl`
→ report sections 3–4 and README.

**Two standing rules for whoever continues:**
1. Resample **articles**, never summaries. The five candidates in an article are not
   independent — several are literal transformations of one another.
2. Report any baseline comparison **excluding structurally-determined candidates**, or the
   judge is being graded against a shortcut that works on candidates needing no judgement.
