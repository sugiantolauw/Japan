# Validation results — constructed ground truth

137 perturbations, judged blind under frozen rubric v1.2. The judge saw only
`perturbation_id`, `article_id` and text; it was told some texts were altered and some
were not, and not told which. 607 claims, 508 evidence strings, **0 verbatim failures**.

Detection criterion (strict): the judge flagged a **CONTRADICTED** claim naming the
substituted value. This is stronger than "faithfulness dropped" — it requires the judge to
locate the specific corruption, not merely dislike the candidate.

## H1 — Sensitivity: **PASS**, 92/104

| corruption | detected | 95% CI |
|---|---|---|
| entity swap | **40/40 = 100%** | [91%, 100%] |
| quantity swap | **18/18 = 100%** | [82%, 100%] |
| polarity reversal | 20/24 = 83% | [64%, 93%] |
| **date swap** | **14/22 = 64%** | [43%, 80%] |

Mean faithfulness on the 104 corruptions: **0.73**.

## H2 — Specificity: **PASS**, 0/33 genuine false positives

Coherence and selection on the 104 corruptions: **3.99 and 3.96**. The corruptions altered
facts, not structure or material type, and those two dimensions did not move. Dimension
independence holds.

My first pass reported 3/33 specificity failures. **That was my detector's error, not the
judge's.** The rule — "a CONTRADICTED claim containing the paraphrase replacement" —
false-positives whenever the paraphrased word sits inside a sentence that was *already*
false. All three source candidates were corrupted before any paraphrase was applied:

| item | source already asserted | paraphrase touched |
|---|---|---|
| `pert_0106` | `放火と断定`, `容疑者2人をすでに拘束` (article: cause unknown) | `と発表した`→`と明らかにした` |
| `pert_0119` | `解散・総選挙は行わず` (article: Abe announced dissolution) | `表明した`→`明言した` |
| `pert_0122` | `15日`, `9月1日`, `4人` (article: 19日, 9月15日, 6人) | `親権を求め`→`親権を要請し` |

The judge penalised pre-existing falsity and left the paraphrase alone. Corrected: **0/33**.

Supporting evidence that does not depend on the strict rule: across the 29 source
candidates carrying both a control and a corruption, the control scored higher in
**25/29**, mean faithfulness advantage **+1.52**.

## H3 — "Polarity reversal is hardest": **FAILS. I named the wrong type.**

I predicted polarity reversal would have the lowest recall, reasoning that it changes no
token identity and so gives claim-level checking no anchor. The reasoning was plausible
and the prediction was wrong.

**Date swaps are the weak point: 64%, and all 8 missed number swaps are dates.** Quantity
swaps — counts, sums, prize money — are detected 18/18. The split is clean: every miss is
a `N日`, `N月` or `N年` span; not one is a quantity.

Polarity reversal at 83% sits between, with an interval overlapping dates', so those two
are not statistically distinguishable at this n. What *is* distinguishable is that entity
and quantity swaps are at ceiling while dates are not.

**Why dates, plausibly.** A Japanese news article carries many dates, and a date absent
from the body reads as unstated detail rather than as a conflict — the judge hedges to
UNSUPPORTED instead of committing to CONTRADICTED. Note this dataset makes that hedge
reasonable: the body is missing its own lead paragraph (see `runs/evidence_log.md`), so a
date genuinely may have been stated in text the judge was never shown. The judge may be
correctly calibrated to a source it knows is incomplete.

**This is the most actionable limitation found.** A reader should not trust this evaluator
to catch a wrong date at the rate it catches a wrong name or number.

## What still needs the 250-candidate run

The definitive paired test — each perturbed text against its own unperturbed original
under v1.2 — requires the originals scored under the frozen rubric. The results above use
the strict detection criterion and within-source pairing, which need no originals.

## Honest note on the instrument

Three times now my own measurement has been the thing at fault: the misattached count
(16→15), P3's assumption that natural near-twin pairs are minimal, and this specificity
detector. The judge has been wrong less often than my tests for it. That is worth stating
in a report about trusting evaluation signals.

---

# Full-corpus results — 250 candidates, frozen v1.2

## Mean score by arm (judge blind to arm throughout)

| arm | n | faithfulness | coverage | coherence | selection |
|---|---|---|---|---|---|
| abstractive | 101 | 2.02 | 2.10 | 4.00 | 3.92 |
| reference | 58 | 2.60 | 2.00 | 3.97 | 3.93 |
| lead extract | 50 | **4.00** | 1.82 | 2.82 | **2.14** |
| truncation | 17 | 2.76 | 1.06 | **1.00** | 3.76 |
| misattached | 15 | **0.00** | **0.00** | 4.00 | 4.00 |
| permutation | 9 | 2.00 | 1.89 | **2.11** | 4.00 |

Every arm signature predicted from structure is reproduced by a judge that never saw the
arms: misattached floored on both fact dimensions while fluent, truncation floored on
coherence, permutation depressed on coherence alone, lead extract maximal on faithfulness
and minimal on selection.

## H7 — Determinism: **PASS, 8/8**

All eight duplicate-reference pairs received **identical score vectors**. Byte-identical
input, independent judgements, no shared cache. Within-rater determinism is exact.

## H6 — The reference arm does not sweep: **PASS, but not for the predicted reason**

The reference takes first place in **2 of 50** articles (unchanged at 2/49 excluding the
E1-affected article). But it is crowded out by **lead extracts (24/50)**, not by clean
abstractive candidates (24/50) as I assumed. That leads directly to the next result.

## THE RANKING RULE IS BROKEN — and the sensitivity analysis says so

**A verbatim copy of the article cannot be unfaithful.** Lead extracts score faithfulness
**4.00 in every batch, without exception**. Genuinely abstractive candidates risk 0–2
because they restate rather than copy. Under a lexicographic rule with faithfulness as the
primary key, the copy wins before any other dimension is consulted.

Article `34991666`, ranked under the frozen rule:

| rank | arm | (faith, cover, coher, select) |
|---|---|---|
| **1** | **lead extract** | **(4, 2, 3, 3)** |
| 2 | reference | (2, **3**, **4**, **4**) |
| 3 | abstractive | (2, 2, **4**, **4**) |

The winner is worse on three of four dimensions. It wins on one, and that one sorts first.

### Sensitivity to the ordering (pre-registered)

| rule | first place |
|---|---|
| faith → cover → coher → select *(frozen)* | **lead extract 24**, abstractive 24, reference 2 |
| faith → cover → select → coher | lead extract 25, abstractive 23, reference 2 |
| **cover → faith** → coher → select | abstractive **39**, lead extract 7, reference 4 |
| **unweighted sum of all four** | abstractive **42**, reference 6, lead extract **2** |

Swapping the middle two changes nothing — the failure is entirely in which dimension sorts
first. Both alternatives produce far more defensible rankings.

### The diagnosis

**A dimension with a degenerate optimum must not be the primary sort key.** Faithfulness is
maximised at zero effort by copying the source. Selection was the dimension designed to
catch exactly that — it scores lead extracts 2.14 against 3.9+ everywhere else — but under
lexicographic ordering **selection is never consulted when faithfulness differs.** I put
the exploitable dimension first and its antidote last.

### I rejected the right rule for the wrong reason

I dismissed a weighted sum on the grounds that *"it lets polished writing offset a factual
error."* The real failure runs the other way: lexicographic faithfulness-first lets a
**trivial copy beat every genuine summary**. The unweighted sum I rejected produces the
most sensible ranking of the four rules tested — lead extracts drop from 24 first places
to 2.

The rule is frozen and is **not** being changed; the frozen result stands as the headline
number, with this sensitivity analysis reported beside it. Changing the aggregation rule
after seeing which one flatters the output is precisely what a freeze exists to prevent.

## Rater effect between batches

Arm-conditional mean faithfulness, by batch:

| arm | b0 | b1 | b2 | b3 | b4 | spread |
|---|---|---|---|---|---|---|
| lead extract | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | **0.0** |
| misattached | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** |
| abstractive | 1.6 | 2.2 | 2.4 | 1.8 | 2.0 | 0.8 |
| permutation | 1.5 | 2.0 | — | 2.0 | 2.2 | 0.8 |
| reference | 2.1 | 2.8 | 3.2 | 2.2 | 2.6 | 1.1 |
| truncation | 2.5 | 1.0 | 3.0 | 2.8 | 3.3 | **2.3** |

Raters agree **exactly** where the answer is forced — a copy is faithful, a wrong-article
summary is not — and diverge by up to 2.3 points on the graded middle, driven by the E4
anchor contradiction. Any cross-article aggregate above carries that spread; the
within-article rankings do not, since one rater scores all five candidates in an article.
