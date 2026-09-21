# Evaluating a Japanese News Summarizer

**What this evaluation establishes.** The dataset is built on a fixed template that I
recovered from text relations alone, which means only 2 of 5 candidates per article need
semantic judgement. Against corruptions I scripted myself, on the subset whose labels survived a
semantic audit — the evaluator catches **100% of entity and quantity swaps**, raises no contradiction attributable to a
meaning-preserving edit, scores byte-identical candidates identically **8/8**,
and reproduces every structural failure signature while blind to which candidate is which.

**What it does not.** **My date-detection labels turned out to be invalid** and the 64% figure they produced is
withdrawn (§3.2). There is no ground truth for ranking the 101 candidates that genuinely
need judgement, so I can show my evaluator disagrees with a cheap baseline there but not
that it is right. And my own aggregation rule
is wrong: it ranks a verbatim copy of the article first in half the articles, because a
copy cannot be unfaithful. I measured which alternative fixes that and did not change the
frozen rule.

Detail behind every number is in `runs/`; this is the argument.

## 1. Exploration

**No positional leakage.** Copy rate is flat across summary positions k=0–4 (0.343 / 0.371
/ 0.356 / 0.386 / 0.397). The opaque ID suffix is honoured in fact. Worth ruling out —
position is the cheapest way to accidentally cheat.

### 1.1 The dataset is a fixed 4+1 template

Three relations are computable with no model (`runs/arm_census.json`):

| component | n | share |
|---|---|---|
| abstractive — clean or corrupted, undetermined | 101 | 40.4% |
| reference verbatim | 58 | 23.2% |
| lead extract (copy rate 1.00) | 50 | 20.0% |
| truncation of reference | 17 | 6.8% |
| misattached — a summary of a **different article** | 15 | 6.0% |
| permutation of reference | 9 | 3.6% |

Every article holds **one reference, one lead extract, two abstractive candidates, and one
variable degradation**. 49 of 50 fit exactly.

**Consequence that shapes everything: two candidates per article are structurally
undetermined.** The other three are *identifiable* from string relations — which gives a
diagnostic hypothesis about each, not a quality score; they still need semantic evaluation.
Either way, a baseline comparison over all candidates measures partly the wrong thing.

The misattached arm matters beyond its 6%: Finnish paternity leave filed under Iraqi
forces at Mosul, yoghurt sugar content under the Oscars. These are fluent, well-formed and
faithful — to some *other* article. Any **source-free** metric may score them highly. (My evaluator is reference-free but
source-grounded, which is the distinction that matters.)

### 1.2 The references are candidates, and they are not ground truth

All 50 articles contain a byte-identical copy of their `reference_summary`; 8 contain two.
References carry a median **84% novel char-5-grams** against their own body.

The mechanism: **45 of 50 articles have a title content-word absent from the body**, and
references supply ages, stated reasons and disclosure dates the body never contains.
XL-Sum takes the BBC lead paragraph as the reference and excludes it from `text`. So the
references are not badly written — they summarise a fuller article than the one supplied.
They are unsupported *relative to the evidence a summarizer sees*, which is the right
standard here but is not evidence they are poor. (An inference about construction, not a
measurement.)

**This makes reference similarity unsuitable as the sole metric on this dataset.**
Measured: a reference-similarity baseline
scores exactly 1.0 on all 58 reference candidates — an answer key, not a metric.

### 1.3 Six corruption types, none surface-detectable

entity swap (`ロシア`→`イラン`) · number/date swap (`900万`→`500万`) · fabricated quotation ·
fabricated event ("police confirmed arson" when the cause is unknown) · hallucinated status
(a drug "in Phase 3" when trials failed) · **polarity reversal** (`即時中断`→`継続`).

Polarity reversal is the hardest: its clean sibling differs in **no entity and no number** —
only the direction of the action.

One failure is not about truth at all. `…fa255e70` is a verbatim mid-article passage
defining *what Antifa is*: every claim supported, fluent, and it never mentions that Trump
said he would designate it a terrorist organisation. A faithfulness-only evaluator scores
it near-perfect. That candidate is why coverage is a separate dimension.

### 1.4 Hypotheses: five survived, five died

| survived | died |
|---|---|
| verbatim lead extraction (50/50) | >3 sentences — 2/250 |
| hallucinated numbers/dates/names | wrong or mixed language — 0/250 |
| entity swap | degenerate repetition — 0/250 |
| mid-sentence truncation (17/50) | meta-preamble — 0/250 |
| off-topic / wrong-article summary (15/50) | vacuous genericity — not observed |

**Every survivor concerns content being wrong; every casualty concerns output being
malformed.** That single division moved the design off lexical metrics and demoted format
compliance from a dimension to a flag.

Not anticipated, and structural rather than behavioural: the slot template, the reference
injected as a candidate, sentence permutation, duplicate references, polarity reversal.

**A correction I made to myself.** I first reported 16 misattached summaries; it is 15. My
detector flagged a candidate at copy=0.048 that *is* its article's reference, unusually
abstractive. Fixed by testing reference-identity before copy rate. Kept in the log: a cheap
detector returning a confident wrong answer, caught only because an independent
classification disagreed.

## 2. Design

Four dimensions, each anchored to a candidate observed in exploration
(`code/prompts/rubric.md`, frozen v1.2):

| dimension | catches | anchor |
|---|---|---|
| **Faithfulness** | six corruption types | reference asserting `「乗り越えがたい相違」` (absent from body) |
| **Coverage** (recall) | faithful-but-useless | `…fa255e70`, the Antifa definition |
| **Coherence** (order, completeness) | permutations, truncations | `…7b3a10b0` ends `逃走したが、` |
| **Selection** (precision of material *type*) | caption/byline ingestion | `…979831e4` opening with a byline |

Coverage and selection are complementary — recall of what must be said versus precision of
what is said. Format compliance is a reported flag: 2/250 violations do not earn a
dimension.

Claim status separates **UNSUPPORTED** from **CONTRADICTED**, because the reference arm is
unsupported while the corrupted arm is contradicted, and collapsing them would score them
alike.

**Ranking is lexicographic** — faithfulness → coverage → coherence → selection. I rejected
a weighted sum because it cannot justify its coefficients and lets polish offset a factual
error. **That reasoning was wrong** (§3.5).

## 3. Validation

### 3.1 One article, end to end

`34991666` contains all five arms. The judge saw the article, its key points, and one
candidate at a time, blind to arms.

| candidate | arm | F | C | Co | S | sum |
|---|---|---|---|---|---|---|
| `…c1f887ae` | lead extract | **4** | 2 | 3 | 3 | 12 |
| `…eb217fa8` | reference | 2 | **3** | **4** | **4** | **13** |
| `…52f88088` | abstractive (clean) | 2 | 2 | **4** | **4** | 12 |
| `…f6f8e339` | abstractive (corrupted) | **1** | 2 | 4 | 4 | 11 |
| `…7b3a10b0` | truncation | 2 | 2 | **1** | 4 | 9 |

**The evaluator works**: it catches the polarity reversal in `…f6f8e339` (says the pair
fled interstate; the article says they died) without being told one exists, floors
coherence on the truncation, and gives the verbatim extract full faithfulness while docking
selection for the caption.

**The unsupported dates are real, not judge error.** Both the reference and the clean
abstractive lose faithfulness for `2日` and `17人`, which genuinely are not in the supplied
body — because the lead paragraph is stripped (§1.2).

**And the frozen rule picks the wrong winner.** The lead extract sorts first because
faithfulness sorts first and a copy cannot be unfaithful, though the reference beats it on
the other three dimensions and on the total.

### 3.2 Constructed ground truth

137 scripted perturbations, judged blind — the judge was told some texts were altered and
some were not, and not told which. 607 claims, 508 evidence strings, **0 verbatim
failures**. Detection required flagging a CONTRADICTED claim *naming the substituted value*,
not merely scoring low.

| corruption | detected | 95% CI |
|---|---|---|
| entity swap | 40/40 = 100% | [91%, 100%] |
| quantity swap | 18/18 = 100% | [82%, 100%] |
| polarity reversal | 20/24 = 83% | [64%, 93%] |
| **all of the above** | **78/82 = 95%** | [88%, 98%] |
| ~~date swap~~ | ~~14/22 = 64%~~ | **withdrawn — see below** |

**The date labels are invalid and I withdraw that figure.** My generator verified that the
original date appeared *somewhere* in the article — not that it supported the event the
summary attributed it to. Auditing the misses: a summary asserts `警察は10日、被害件数を
516件に上方修正し…発表` while the article's only uses of `10日` are a justice minister's
newspaper interview and a street protest. The original date was already unsupported for
that event, so swapping it creates no contradiction, and the judge declining to call one
**may be correct**. By a conservative proxy, **12 of 22 date items** have no article
sentence sharing even two content words with the clause asserting the date.

I first reported this as "the judge is weak on dates" and speculated that hedging might be
correct calibration. The audit turns that speculation into a mechanism — and shifts the
fault from the judge to my test. The corruption types with sound labels are detected at
**95%**.

**Specificity, stated precisely.** Three of 33 controls carry a contradicted claim whose text contains the edited token, but
in all three the falsity **predates the edit** (fabricated arson; a reversed dissolution
announcement; three wrong figures) — so **no contradiction is attributable to the
paraphrase**. Coherence and selection on the
corruptions stayed at **3.99 and 3.96**. But that is a claim-label test, not score
stability. Comparing each control against its own original, faithfulness is **unchanged in
only 15/33** — 12 up, 6 down. Two caveats pull in opposite directions: the two runs used
different rater instances, and the direction of the shift tracks rater strictness (originals
from the strict batches shift **+0.75**, from the lenient batch **−0.17**), so most of the
movement is the E4 rater effect rather than paraphrase sensitivity. But not all of it —
`到着し、`→`到着して、`, a particle change that cannot alter meaning, still moved a score
from 4 to 3. **Score stability under paraphrase is not established**, and the design could
not establish it, because I never scored a control and its original with the same rater.

### 3.3 Full corpus, and dimension independence

| arm | n | faith | cover | coher | select |
|---|---|---|---|---|---|
| abstractive | 101 | 2.02 | 2.10 | 4.00 | 3.92 |
| reference | 58 | 2.60 | 2.00 | 3.97 | 3.93 |
| lead extract | 50 | **4.00** | 1.82 | 2.82 | **2.14** |
| truncation | 17 | 2.76 | 1.06 | **1.00** | 3.76 |
| misattached | 15 | **0.00** | **0.00** | 4.00 | 4.00 |
| permutation | 9 | 2.00 | 1.89 | **2.11** | 4.00 |

Every arm signature is reproduced by a judge blind to arms. Permutations differ from their
own reference on coherence alone; misattached candidates floor both fact dimensions while
staying fluent — dimension independence on natural data.

**Determinism: 8/8.** All duplicate-reference pairs received identical score vectors.
**The reference does not sweep: first in 2/50 articles.**

### 3.4 The ranking rule is broken — and here is which fix works

A verbatim copy cannot be unfaithful. Lead extracts score faithfulness **4.00 in every
batch without exception**. Under faithfulness-first ordering they take first place in
**25 of 50** articles, usually while scoring worse on the other three.

Tested against **expected** structural orderings — a reference should beat its own
truncation and its own permutation, and anything should beat a summary of another article.
These are strong priors, not guarantees: a truncation is not automatically worse in every
semantic respect.

| rule | ref > truncation | ref > permutation | any > misattached | **all** | lead extract 1st |
|---|---|---|---|---|---|
| **frozen** faith→cov→coh→sel | 14/17 = 82% | 9/9 | 59/60 | **95%** | **25** (sole 24) |
| coverage-first | 15/17 = 88% | 9/9 | 59/60 | 97% | 8 (sole 7) |
| **unweighted sum** | **17/17 = 100%** | 9/9 | 59/60 | **99%** | **4** (sole 2) |

Last column: articles where a lead extract is ranked first, counting ties; sole-winner
counts in brackets. The sum also produces far more ties at first place (11 articles vs 3),
which is part of why it looks tidier and is itself a reason not to treat it as definitive.

Mean within-article rank by arm under the sum: reference 1.98, abstractive 2.34, lead
extract 3.18, permutation 4.11, truncation 4.41, misattached 4.93 — a monotone severity
ordering no other rule produces.

**A dimension with a degenerate optimum must not be the primary sort key.** Faithfulness is
maximised at zero effort by copying. Selection was designed to catch that — 2.14 for lead
extracts against 3.9+ elsewhere — but lexicographic ordering never consults it. I placed
the exploitable dimension first and its antidote last, and I rejected the unweighted sum
for a failure mode that runs the opposite way.

**The rule was not changed.** Swapping an aggregation rule after seeing which one flatters
the output is what a freeze prevents. `scores.jsonl` carries all three orderings.

Two honest caveats on the sum: the reference arm ranks best under it, contradicting what
exploration suggested, with no ground truth to settle it; and it still places permutations
below lead extracts, which is questionable. No rule tested gets everything right.

### 3.5 Against the baselines, and length bias

Articles where each scorer **cannot separate** its abstractive candidates — the only ones
needing judgement:

| structural baseline | reference similarity | LLM judge |
|---|---|---|
| **50 / 50** | 1 / 50 | **0 / 50** |

The structural baseline has zero ranking power where judgement is required and is blind to
sentence reordering (0% on reference-over-permutation). **H5 is only half-answered:**
reference similarity discriminates well, but by scoring 1.0 on 58 references by
construction. On the abstractive subset there is **no ground truth**, so I can report that
judge and baseline rank differently, not which ranks better.

**Length bias, correlation with each dimension** (all 250 / abstractive only):
faithfulness +0.24 / +0.13 · **coverage +0.31 / +0.43** · coherence +0.01 / 0.00 ·
selection −0.47 / −0.10. Coverage correlates with length *within* a single arm. Some is
legitimate — a longer summary can convey more — but coverage scores cannot be read as
independent of length.

## 4. Limitations

Ordered by how much each should change a reader's confidence.

1. **The ranking rule is wrong and I know it is** (§3.4). Use the dimension vector or
   `rank_unweighted_sum`, not `within_article_rank`.
2. **Faithfulness is effectively a four-point scale.** The frozen score-2 anchor's own
   example (*an unstated date, a descriptor*) is precisely the immaterial case defining
   score 3, so raters route everything to one side. Two judge batches produced zero 3s; one
   produced eleven 3s and zero 2s — the same candidate class scored ~1 point apart.
   (`runs/KNOWN_ERRORS.md` E4.)
3. **Cross-article aggregates carry a rater effect up to 2.3 points**, and I cannot show
   within-article rankings are safe from it. Five judge instances scored ten articles each.
   They agree *exactly* where the answer is forced (lead extract 4.0, misattached 0.0, zero
   spread) and diverge on the graded middle. I claimed within-article rankings were
   **immune** because one rater scores all five candidates; that was asserted, not tested.
   Simulating the boundary shift changes no ranking (0/50), but that only covers a uniform
   monotone shift — raters differing *non-uniformly* between two candidates would merge or
   split a tie and reorder them. Testing it needs the same article scored twice by
   different raters, which this design never did. The honest claim is **attenuated, not
   eliminated, and unvalidated.**
4. **No native-speaker validation.** I do not read Japanese. Validation rests on constructed
   ground truth, structurally guaranteed relations, internal consistency, and mechanical
   auditing of cited evidence. None of it establishes whether the judge's sense of a *good*
   Japanese summary matches a native reader's.
5. **Constructed ground truth covers 3 of 6 corruption types.** Fabrication requires
   generating false content, not substituting a verified span.
6. **The date-perturbation labels are invalid** and that figure is withdrawn (§3.2). Date
   corruption detection is simply unmeasured.
7. **Coverage is length-correlated** (+0.43 within arm).
8. **Three articles have a coverage yardstick that misses their main event**, because the
   key-point prompt required body-verbatim excerpts while the evidence boundary is title
   *plus* body. (E2.)
9. **The frozen rubric contains a factual error that changed two scores** — a compatible
   date pair labelled contradicted, depressing two candidates in the direction that
   flatters H6. (E1.)
10. **Structural detectors are not held out**, having been derived before the split existed.
    Only the semantic judge is.

### Next, in order

1. Re-run with coverage as the primary sort key — one hour, addresses the largest defect.
2. Fix the faithfulness anchor contradiction and measure how much of the 2.3-point rater
   spread it was causing.
3. Have 3–5 articles reviewed by a Japanese reader — not as ground truth, but to check
   whether the evaluator is confidently wrong in a way all four automated lines miss.
4. Extend constructed ground truth to fabrication using a generator, not a substituter.

### A note on method

Four defects in my own frozen artifacts were found by the subagents executing against them,
not by me: key points returned as topic labels, perturbations that left summaries
contradicting themselves, perturbations with impossible values, and a self-contradictory
scale anchor. Three of my own measurement instruments were also wrong before the judge was
— the misattached count, the paired-sensitivity test, and the specificity detector. In a
report about trusting evaluation signals, that belongs in the open: **the judge was wrong
less often than my tests for it.**
