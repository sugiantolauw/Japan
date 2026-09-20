# Evaluating a Japanese News Summarizer

**Status:** sections 1 and 2 complete; 3 and 4 pending the frozen scoring run.

---

## 1. Exploration

### 1.1 First contact

The surface statistics said little. 50 articles (459–3,637 chars, median 1,546), 250
summaries (22–302 chars, median 124), exactly five per article, no missing joins.
References run 41–164 chars.

The first useful check was for **leakage**: is a summary's position in the file a proxy for
its generation method? It is not. Mean length, sentence count and copy rate are flat across
positions k=0–4 (copy rate 0.343 / 0.371 / 0.356 / 0.386 / 0.397). The data README's claim
that the ID suffix carries no information holds in fact, not only in assertion. I report
this because position is the cheapest way to accidentally cheat, and ruling it out is
worth more than assuming it away.

### 1.2 The dataset is a 4+1 construction template

Three fingerprints are computable with no model at all:

- **58 summaries are byte-identical to their article's `reference_summary`.** All 50
  articles have at least one; 8 have two.
- **Exactly one summary per article has char-5-gram copy rate 1.00** against the article
  body — verbatim lead extraction, in 50/50 articles.
- **17 summaries are strict prefixes of their reference**, ending mid-sentence.

Classifying all 250 on these relations (`runs/arm_census.json`) exposes the generator:

| component | n | share |
|---|---|---|
| abstractive — clean or corrupted, needs judgement | 101 | 40.4% |
| reference verbatim | 58 | 23.2% |
| lead extract | 50 | 20.0% |
| truncation of reference | 17 | 6.8% |
| misattached — wrong article | 15 | 6.0% |
| permutation of reference | 9 | 3.6% |

Every article carries **one reference, one lead extract, two abstractive candidates, and
one variable degradation** drawn from {truncation, misattached, permutation, duplicate
reference}. 49 of 50 fit exactly; one substitutes a third abstractive.

This has a direct consequence for evaluation design: **only 2 of 5 candidates per article
require semantic judgement.** The other three are structurally determined. An evaluator
that got only those right would look strong while adding nothing — so baseline comparisons
must be reported *excluding* structurally-determined candidates, or the LLM judge is being
graded against a shortcut it cannot beat and does not need to.

### 1.3 The misattached arm

I had listed "off-topic or wrong-article summary" among my ten initial hypotheses, but
expected it as an occasional defect rather than a systematic arm. Reading the Brazil museum
fire article, one candidate turned out to be about **Uber's CEO pivoting to e-scooters**. A systematic search found **15 summaries attached to the wrong
article**: Finnish paternity leave under Iraqi Kurdish forces at Mosul, yoghurt sugar
content under the Academy Awards. Two are references lifted from other articles in this
same corpus.

These matter out of proportion to their 6%. They are fluent, well-formed, and faithful —
to some other article. **Any reference-free quality metric scores them highly.** This is
the strongest argument the dataset contains for grounding evaluation in the source text.

### 1.4 The references are not ground truth, and it is demonstrable

The assignment warns that XL-Sum reference quality is uneven. It matters more here than
usual, because **the reference is itself one of the five candidates**.

References carry a median **85% novel char-5-grams** against their own article; all 50
exceed 50%. Close reading of four:

- **37426493** (Jolie/Pitt). The reference gives the divorce reason as
  `「乗り越えがたい相違」` — absent from the article, which says only
  `家族の健康のための判断` — and dates the filing `20日` when the article says 19日. One
  **unsupported** claim and one **contradicted** claim, in the intended-gold candidate.
- **48116477** (LATE dementia). A 74-character single sentence that never names LATE and
  omits the "up to one third of patients" figure, while a clean abstractive sibling
  conveys both.
- **51145805**. The reference contains a typo (`だっだと`) which propagates into its
  permuted twin.

This is why the rubric separates **UNSUPPORTED** from **CONTRADICTED**. Collapsing them
would score the intended-gold candidate identically to a planted corruption.

### 1.5 Six corruption types

| type | example | surface-detectable? |
|---|---|---|
| entity swap | トルコと**ロシア** → トルコと**イラン**; テキサス大学 → ハーバード大学 | no |
| number / date swap | 900万 → 500万クローナ; 19日 → 15日; 6人 → 4人 | no |
| fabricated quotation | Trump given `米国はもはや世界の警察ではない`, which appears nowhere | no |
| fabricated event | "police confirmed arson, two detained" — article says cause unknown | no |
| hallucinated status | a drug "in Phase 3 trials" when the article says trials **failed** | no |
| polarity reversal | airline `継続する` the tests it in fact `即時中断` | no |

**Polarity reversal is the hardest.** Its clean sibling differs in no entity and no number
— only the direction of the reported action. Every entity-overlap or number-matching check
passes it. This single finding killed a validation route I had planned, in which a
non-Japanese-reading reviewer would adjudicate near-twin pairs by string matching.

Separately, one failure has nothing to do with truth. `…fa255e70` is a verbatim mid-article
passage explaining *what Antifa is*: every claim supported, fluent, well-formed, and it
never mentions that Trump said he would designate it a terrorist organisation. A
faithfulness-only evaluator scores it near-perfect; it is arguably the worst summary in its
article. That candidate alone justifies keeping coverage separate from faithfulness.

### 1.6 Hypothesis ledger

Ten failure modes were hypothesised before looking at the data. **Five survived, five
died**, and the split is not arbitrary.

| hypothesis | outcome |
|---|---|
| verbatim lead extraction | **survived** — 50/50 articles |
| hallucinated numbers / dates / names | **survived** |
| entity swap | **survived** — predicted as the mode embedding similarity is blind to; it is |
| mid-sentence truncation | **survived** — 17/50 |
| off-topic / wrong-article summary | **survived** — 15/50 |
| >3 sentences | died — 2/250 |
| wrong or mixed language | died — 0/250 |
| degenerate repetition | died — 0/250 |
| meta-preamble (`以下が要約です:`) | died — 0/250 |
| vacuous genericity | died — not observed |

**Every hypothesis that survived concerns content being wrong; every one that died concerns
output being malformed.** That is the load-bearing result of the exploration: this
dataset's planted failures are semantic, so lexical and format checks cannot carry the
evaluation, and format compliance does not deserve to be a scored dimension.

What was *not* anticipated was structural rather than behavioural: the 4+1 slot template,
the reference being injected as a candidate, sentence-order permutation, duplicate
references, and polarity reversal. Those came from the data alone.

**Also survived.** The fixed slot template (49/50). References as comparison group rather
than ground truth (three independent failure types).

**Revised.**

- *Corrupted candidates are single-token swaps.* Wrong twice: the Jolie candidate carries
  **three** deltas, and polarity reversals change no token identity at all.
- *Lead extracts only ingest photo captions.* They ingest **journalist bylines** too.
- *High-similarity near-twins are factual variants.* Only partly — the most similar pairs
  are sentence-order **permutations**, which is how that arm was found.

**Died.**

| hypothesis | reality |
|---|---|
| wrong-language or mixed output | 0 / 250 |
| degenerate repetition | 0 / 250 |
| duplicate sentences | 0 / 250 |
| sentence-limit violations as a major mode | **2 / 250** |
| a second extractive mode | copy rate decays smoothly above the lead extracts |

Four of my initial guesses were crude surface phenomena and **none is present**. The
planted failures are semantic. That finding reoriented the design away from lexical
metrics entirely, and demoted format compliance from a scored dimension to a reported flag.

### 1.7 A correction I made to myself

I first reported **16** misattached summaries. It is 15. The detector flagged `…519dda6a`
because it scores copy=0.048 against its own article and a rival article beat it by 0.002 —
but that candidate *is* its article's reference, which happens to be unusually abstractive.
Fixed by testing reference-identity before copy rate.

It is kept in the evidence log deliberately: a cheap structural detector returning a
confident wrong answer, caught only because an independent classification disagreed. The
same reasoning is why every subagent output in this project was re-verified by measurement
rather than accepted from its report — a discipline that caught three further defects
(topic labels in place of propositions, partial span replacement, and impossible
perturbation values).

---

## 2. Design

See `code/prompts/rubric.md` (v1.1) for the frozen contract. Four scored dimensions, each
anchored to a candidate observed in the exploration split:

| dimension | what it catches | anchor |
|---|---|---|
| **Faithfulness** | six corruption types, none surface-detectable | reference asserting `「乗り越えがたい相違」` (unsupported) vs `20日` (contradicted) |
| **Coverage** (recall) | faithful-but-useless candidates | `…fa255e70`, the Antifa definition that never mentions the news |
| **Coherence** (order, completeness) | permutations, truncations | `…07d482c6` leads with subordinate detail; `…7b3a10b0` ends `逃走したが、` |
| **Selection** (precision of material *type*) | caption and byline ingestion | `…979831e4` opening with a journalist byline |

Format compliance is a reported flag, not a dimension: 2/250 violations do not earn equal
billing, and padding the rubric to five dimensions would misrepresent the data.

**Ranking is lexicographic** — faithfulness → coverage → coherence → selection — each
compared only when higher dimensions tie. A weighted sum was rejected: it cannot justify
its own coefficients, and it lets fluent writing offset a factual error. The lexicographic
rule is defensible in one sentence and makes sensitivity analysis concrete — does the
within-article ranking change if coherence and selection swap priority?

Ties are permitted and expected: 8 articles contain byte-identical candidates that **must**
tie.

---

## 3. Validation

Full results: `runs/VALIDATION_RESULTS.md`. Hypotheses were registered before any result
existed (`runs/PREDICTIONS_v2.md`).

### 3.1 Constructed ground truth

137 scripted perturbations judged blind under the frozen rubric — the judge was told some
texts were altered and some were not, and not told which. 607 claims, 508 evidence
strings, **0 verbatim failures**. Detection required the judge to flag a CONTRADICTED
claim *naming the substituted value*, not merely to score the candidate low.

| corruption | detected | 95% CI |
|---|---|---|
| entity swap | 40/40 = 100% | [91%, 100%] |
| quantity swap | 18/18 = 100% | [82%, 100%] |
| polarity reversal | 20/24 = 83% | [64%, 93%] |
| **date swap** | **14/22 = 64%** | [43%, 80%] |

**Specificity: 0/33.** The 33 meaning-preserving controls produced no false contradiction,
and coherence and selection on the 104 corruptions stayed at 3.99 and 3.96 — the
perturbations changed facts, and only the fact-sensitive dimension moved.

### 3.2 The prediction that failed

I predicted polarity reversal would be hardest, since it changes no token identity.
Wrong — **date swaps are the weak point, and every one of the eight missed number swaps is
a date**. Quantities are caught 18/18.

The likely reason is specific to this dataset: the article body is missing its own lead
paragraph, so a date absent from the body genuinely may have been stated in text the judge
was never shown. The judge hedges to UNSUPPORTED rather than committing to CONTRADICTED,
which may be correct calibration to a source it knows is incomplete. Either way, **this
evaluator should not be trusted to catch a wrong date at the rate it catches a wrong name
or number.**

### 3.3 Dimension independence, on natural data

Permutations differ from their own reference on coherence alone. Misattached candidates
score 0/0/4/4 — faithfulness and coverage floored, coherence and selection intact. Both
tested on real candidates, not constructed ones.

### 3.4 Full corpus: every arm signature reproduces

| arm | n | faith | cover | coher | select |
|---|---|---|---|---|---|
| abstractive | 101 | 2.02 | 2.10 | 4.00 | 3.92 |
| reference | 58 | 2.60 | 2.00 | 3.97 | 3.93 |
| lead extract | 50 | **4.00** | 1.82 | 2.82 | **2.14** |
| truncation | 17 | 2.76 | 1.06 | **1.00** | 3.76 |
| misattached | 15 | **0.00** | **0.00** | 4.00 | 4.00 |
| permutation | 9 | 2.00 | 1.89 | **2.11** | 4.00 |

**Determinism (H7): 8/8.** All duplicate-reference pairs received identical score vectors.

**The reference does not sweep (H6): first place in 2/50 articles.**

### 3.5 The ranking rule is broken, and the sensitivity analysis says so

A verbatim copy cannot be unfaithful. Lead extracts score faithfulness **4.00 in every
batch without exception**, while genuine abstractive candidates risk 0–2. Under a
lexicographic rule with faithfulness first, the copy wins before any other dimension is
read — lead extracts take first place in **24 of 50** articles, usually while scoring worse
on the other three.

| rule | first place |
|---|---|
| faith → cover → coher → select *(frozen)* | **lead extract 24**, abstractive 24, reference 2 |
| faith → cover → select → coher | lead extract 25, abstractive 23 |
| cover → faith → coher → select | abstractive **39**, lead extract 7 |
| unweighted sum | abstractive **42**, lead extract **2** |

**A dimension with a degenerate optimum must not be the primary sort key.** Faithfulness
is maximised at zero effort by copying. Selection was designed to catch that — it scores
lead extracts 2.14 against 3.9+ elsewhere — but lexicographic ordering never consults it
when faithfulness differs. I placed the exploitable dimension first and its antidote last.

I rejected a weighted sum because *"it lets polished writing offset a factual error."* The
real failure runs the other way, and the unweighted sum is the best of the four rules
tested. **The rule is frozen and was not changed** — swapping an aggregation rule after
seeing which one flatters the output is what a freeze prevents.

The same root cause explains the one structural ordering where the judge underperforms the
baselines (§3.6): **faithfulness-first rewards saying less.**

### 3.5b Measuring the fix

The defect is reported, so the obvious question is whether an alternative rule is
demonstrably better rather than merely different. Tested against the orderings that are
structurally guaranteed and need no human judgement:

| rule | ref > truncation | ref > permutation | anything > misattached | **all** | lead extract 1st |
|---|---|---|---|---|---|
| **frozen** (faith→cov→coh→sel) | 14/17 = 82% | 9/9 = 100% | 59/60 = 98% | **95%** | **25/50** |
| coverage-first (cov→faith→…) | 15/17 = 88% | 9/9 = 100% | 59/60 = 98% | 97% | 8/50 |
| faith double-weighted sum | 16/17 = 94% | 9/9 = 100% | 59/60 = 98% | 98% | 17/50 |
| **unweighted sum** | **17/17 = 100%** | 9/9 = 100% | 59/60 = 98% | **99%** | **4/50** |

Mean within-article rank by arm (1 = best of five):

| rule | abstractive | reference | lead extract | permutation | truncation | misattached |
|---|---|---|---|---|---|---|
| frozen | 3.01 | 2.79 | **1.76** | 4.11 | 3.82 | 4.93 |
| coverage-first | 2.60 | 2.57 | 2.76 | 4.00 | 4.12 | 4.93 |
| **unweighted sum** | 2.34 | **1.98** | 3.18 | 4.11 | 4.41 | 4.93 |

**The unweighted sum dominates on every criterion available.** It is the only rule that
respects all 17 reference-over-truncation orderings, it has the highest overall structural
compliance, and it cuts degenerate copies taking first place from 25/50 to 4/50. It also
produces a monotone severity ordering across arms, which no other rule does.

Two honest caveats. First, under the sum the **reference arm ranks best overall (1.98)**,
ahead of clean abstractive candidates — the opposite of what exploration suggested, and
there is no ground truth on that subset to adjudicate it. Second, the sum still places
**permutations (4.11) below lead extracts (3.18)**, which is questionable: a permuted
reference contains all the content in the wrong order, while a lead extract often misses
the main event entirely. No rule tested gets everything right.

`scores.jsonl` carries `within_article_rank` (frozen), `rank_coverage_first` and
`rank_unweighted_sum` so a reader can apply whichever they find defensible.

### 3.6 Against the baselines

On orderings that are structurally guaranteed and need no judgement:

| ordering | n | judge | structural baseline | reference-similarity |
|---|---|---|---|---|
| reference > its truncation | 17 | 82% | 100% | 100% |
| reference > its permutation | 9 | **100%** | **0%** | 100% |
| anything > misattached | 60 | **98%** | 67% | 93% |

And on discrimination within the 101 abstractive candidates — the only ones needing
semantic judgement:

| scorer | articles where it cannot separate its abstractive candidates |
|---|---|
| structural baseline | **50 / 50** |
| reference similarity | 1 / 50 |
| LLM judge | **0 / 50** |

**H4 holds:** the structural baseline has literally zero ranking power where judgement is
required, and is blind to sentence reordering (0%). **H5 is only half-answered.** Reference
similarity discriminates and tracks the structural orderings well — but it does so by
scoring exactly 1.0 on all 58 reference candidates by construction, which is an answer key,
not a metric. On the abstractive subset there is **no ground truth**, so I can report that
the judge and the similarity baseline rank differently, not which ranks better.

### 3.7 Length bias (H8): partially fails, as suspected

| dimension | all 250 | abstractive only |
|---|---|---|
| faithfulness | +0.24 | +0.13 |
| **coverage** | **+0.31** | **+0.43** |
| coherence | +0.01 | 0.00 |
| selection | −0.47 | −0.10 |

Coverage correlates with length even within a single arm. Some of that is legitimate — a
longer summary genuinely can convey more units — but the size of it means **coverage
scores cannot be read as independent of length**, and I cannot separate the legitimate part
from the bias with this design.

## 4. Limitations

Ordered by how much they should change a reader's confidence.

**1. The ranking rule is wrong, and I know it is.** §3.5. Lead extracts win 24/50 articles
under the frozen rule because copying maximises faithfulness. The per-dimension scores are
sound; the aggregation into a single order is not. A reader should use the dimension
vector, not `within_article_rank`. The fix is to sort on coverage first or to use the
unweighted sum, both of which are shown.

**2. Faithfulness is a four-point scale, not five.** The frozen score-2 anchor's own
example (*an unstated date, a descriptor*) is precisely the immaterial case that defines
score 3, so raters route everything to one side. Two batches produced zero 3s; one produced
eleven 3s and zero 2s. The same candidate class is scored ~1 point apart depending on which
batch it landed in. Details: `runs/KNOWN_ERRORS.md` E4.

**3. Cross-article aggregates carry a rater effect of up to 2.3 points.** Five independent
judge instances scored ten articles each. They agree *exactly* where the answer is forced
(lead extract 4.0, misattached 0.0, zero spread in all five batches) and diverge on the
graded middle. Within-article rankings are immune — one rater scores all five candidates —
but every per-arm mean in §3.4 mixes rater variance with signal.

**4. No native-speaker validation.** I do not read Japanese. Validation rests on
constructed ground truth, structurally guaranteed relations, internal consistency, and
mechanical auditing of cited evidence. None of it establishes whether the judge's sense of
a *good* Japanese summary matches a native reader's, or whether the extracted key points
are the right essential facts. See README.

**5. Constructed ground truth covers 3 of 6 corruption types.** Fabricated quotation,
fabricated event and hallucinated status require generating false content rather than
substituting a verified span, so they have no scripted ground truth and rest on the
natural pairs and structural anchors.

**6. Date corruptions are detected at 64% against 100% for entities and quantities.** The
most actionable operational limit. Plausibly correct calibration to a source whose lead
paragraph is missing — but a user should not trust this evaluator on dates.

**7. Coverage is length-correlated (+0.43 within arm).** §3.7.

**8. Three articles have a coverage yardstick that misses their main event**, because the
key-point prompt required body-verbatim excerpts while the rubric's evidence boundary is
title *plus* body. `runs/KNOWN_ERRORS.md` E2.

**9. The frozen rubric contains a factual error that changed two scores.** The worked
example labels a compatible date pair as contradicted; two candidates in one article are
depressed by one faithfulness point, in the direction that flatters H6. E1.

**10. Structural detectors are not held out.** They were derived from full-dataset
inspection before the split existed. Only the semantic judge is genuinely held out.

### What I would do next, in order

1. Re-run with coverage as the primary sort key and compare rankings — one hour, and it
   addresses the largest defect.
2. Fix the faithfulness anchor contradiction and re-score; measure how much of the 2.3-point
   rater spread it was causing.
3. Get 3–5 articles reviewed by a Japanese reader — not as ground truth, but to check
   whether the evaluator is confidently wrong in a way all four automated lines miss
   together.
4. Extend constructed ground truth to fabrication types using a generator rather than a
   substituter.
