# Known errors in frozen artifacts

Recorded rather than fixed. The freeze exists to stop post-hoc changes to inputs; that
applies to changes I would like to make for good reasons, not only to convenient ones.

## E1 — The frozen rubric contains an incorrect worked example

`code/prompts/rubric.md` v1.2, the UNSUPPORTED/CONTRADICTED section, states:

> the reference for article 37426493 asserts the divorce reason `「乗り越えがたい相違」`
> and the date `20日`; the article gives `家族の健康のための判断` and 19日. The reason is
> UNSUPPORTED (absent), the date is CONTRADICTED (incompatible).

**The date claim is wrong.** The body's 19日 is the *filing* date; the reference's 20日 is
the lawyer's *disclosure* date. Different events, mutually compatible. `20日` is absent
from the body, so it is UNSUPPORTED, not CONTRADICTED.

### Did it affect any score?

Checked, and **no**. A judge agent scoring the perturbation set reported applying "the
rubric's own worked example (date=CONTRADICTED)" as precedent for article 37426493, which
is what prompted this check. The three perturbation rows for that article derive from
source candidates `…6baeebc9` and `…9d69dc21`; neither contains `20日`, so the erroneous
precedent was never applied to the claim it concerns.

The rule the example was illustrating is sound and was applied correctly: a candidate
asserting a date incompatible with the article's date **for the same event** is
contradicted. All 26 CONTRADICTED date-bearing claims in batch A are perturbation-induced
swaps of a date for the same event — genuine contradictions, correctly labelled.

### Why it is not being fixed

The rubric is frozen, the error was found after freezing, and it demonstrably changed no
score. Editing a frozen input post hoc — even to correct a real mistake — makes every
other frozen artifact's status negotiable. The error stands, documented, with the evidence
that it was inert.

## E2 — Coverage yardstick misses title-only main events (3 articles)

The key-point prompt required excerpts verbatim from the article `text`, narrower than the
rubric's evidence boundary of title **plus** body. On `52000333`, `53274336` and
`features-and-analysis-40566272` the main event appears only in the title, so the frozen
main-event unit is not the actual main event. Coverage will be reported with and without
these three. Details in `runs/evidence_log.md`.

## E3 — Anomaly: all claims SUPPORTED but faithfulness scored 3, not 4

`pert_0112_paraphrase_control` carries six claims, every one SUPPORTED, and scored
faithfulness **3**. The v1.2 anchor for 4 is "every claim SUPPORTED". Either the judge
docked for something outside its own claim list, or it applied the scale conservatively.

Not corrected — it is a judge behaviour, not an artifact defect, and correcting individual
judgements post hoc would destroy the run's integrity. Flagged for the validation section:
if all-SUPPORTED candidates systematically score 3 rather than 4, the faithfulness scale
has a compression problem at the top end, which would weaken every paired comparison that
relies on distinguishing 3 from 4.

## E4 — The faithfulness score of 3 is unreachable as written

Frozen v1.2 anchors:

> **3** — all claims SUPPORTED except **immaterial** UNSUPPORTED detail that does not change meaning
> **2** — **material** UNSUPPORTED detail — a plausible fact absent from the source (**an unstated date, a descriptor**) that invents no event or attribution

The score-2 example — *an unstated date, a descriptor* — is exactly the kind of addition
that is **immaterial**, which is what defines score 3. The label and the example
contradict each other, so any unsupported detail can be routed to 2 by following the
example, and 3 becomes empty.

Two independent judge instances reached this conclusion unprompted. One wrote: *"score 3
is empty in this batch by construction of the rubric's own examples, not from a scoring
bug. Worth double-checking this matches the rubric authors' intent."* It did not.

Observed usage of faithfulness=3:

| run | n | 3s |
|---|---|---|
| pert_a | 69 | 9 (13%) |
| pert_b | 68 | 5 (7%) |
| all_b1 | 50 | **0** |
| all_b3 | 50 | **0** |

**Consequence:** faithfulness is effectively a **four-point scale (0, 1, 2, 4)**, not five.
It loses the distinction between "clean" and "clean apart from a trivial unstated detail".
Every reported faithfulness figure should be read on that basis.

Not fixed — frozen, and found after the freeze. Reported as the scale's real resolution.

## E5 — Selection is underspecified for partial contamination

The selection anchor cites a candidate that *opens* with a journalist byline as score 1. It
does not say whether a candidate that is otherwise clean but carries a short spliced
caption should be scored by **presence** (1) or **proportion** (3, "minor extraneous
detail").

Two batches read it differently on the same arm:

| batch | lead-extract selection | mean |
|---|---|---|
| all_b1 | 1 ×10 | **1.0** |
| all_b3 | 1 ×3, 2 ×4, 3 ×1, 4 ×2 | **2.2** |

One batch stated the choice explicitly: *"I chose consistency with the literal anchor over
proportionality; this is the single biggest judgment call in the batch and affects 10 of
50 rows."*

## Why E4 and E5 do not invalidate the deliverable

Both are **between-rater** effects. Each article's five candidates are scored by one agent
in one context, so a rater's threshold shifts all five together and **cancels in the
within-article ranking** — which is what the lexicographic rule produces and what the task
asks for.

They do contaminate **cross-article aggregates**: any "mean faithfulness by arm" computed
across batches mixes rater effect with real effect. The 4+1 template makes this measurable
— arm composition is near-identical in every article, so systematic differences in
arm-conditional means *between batches* are rater variance. That measurement will be
reported rather than assumed away, and per-arm means will carry a between-batch spread.

## Pattern worth stating plainly

Four defects in frozen or delivered artifacts have now been found by the agents executing
against them rather than by their author: topic labels for propositions, partial span
replacement, impossible perturbation values, and now a self-contradictory scale anchor. In
every case the agent reported it without being asked and declined to paper over it.
