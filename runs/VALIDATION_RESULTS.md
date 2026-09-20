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
