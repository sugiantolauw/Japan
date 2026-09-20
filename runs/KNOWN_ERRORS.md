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
