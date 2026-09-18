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

*Pending the frozen run. Design and interim results: `runs/PILOT_RESULTS.md`,
`runs/PREDICTIONS.md`, `runs/perturbation_report.md`.*

## 4. Limitations

*Pending.* Known entries: no native-speaker validation was performed (see README);
constructed ground truth covers 3 of the 6 observed corruption types; the structural
detectors were derived before the split existed and are therefore not held out.
