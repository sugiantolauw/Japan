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

### Did it affect any score? — **CORRECTED: yes, it did**

I first concluded it was inert, based only on the perturbation run. **That conclusion was
wrong.** The full scoring run shows it propagating: batch 0 reported applying "the rubric's
own worked example (reason = UNSUPPORTED, date 20日 vs actual 19日 = CONTRADICTED)" to both
candidates of article 37426493 that contain the reference text.

| candidate | arm | faithfulness | claim the judge marked CONTRADICTED |
|---|---|---|---|
| `…12ba3116` | reference | **1** | `弁護士は20日にこれを明らかにした` |
| `…f0038832` | permutation | **1** | `弁護士は20日にこれを明らかにした` |

Under a correct reading both should be **2** (material unsupported detail, nothing
contradicted). Two of 250 candidates are depressed by one faithfulness point.

**The bias runs in the direction that flatters my own hypothesis.** H6 predicts the
reference arm does not sweep first place; depressing the reference in this article makes
H6 easier to pass. The H6 analysis will therefore be reported with and without article
37426493.

The judge also generalised the pattern to `39776572`, marking `生後1週間を過ぎた` against
the article's `生後3日` as contradicted. **That generalisation is correct** — same event,
incompatible timing — so the rule transferred soundly even though the example that taught
it was wrong.

### Original assessment — OBSOLETE, retained only to show what was corrected

Everything in this subsection was written before the full scoring run and is **wrong**;
the corrected finding is above. A judge agent scoring the perturbation set reported applying "the
rubric's own worked example (date=CONTRADICTED)" as precedent for article 37426493, which
is what prompted this check. The three perturbation rows for that article derive from
source candidates `…6baeebc9` and `…9d69dc21`; neither contains `20日`, so the erroneous
precedent was never applied to the claim it concerns.

The rule the example was illustrating is sound in principle: a candidate asserting a date
incompatible with the article's date **for the same event** is contradicted.

**SUPERSEDED:** I then wrote that all 26 CONTRADICTED date-bearing claims in batch A were
same-event swaps and therefore correctly labelled. **E6 shows that is wrong** — the
generator never checked same-event support, so an unknown share of those date labels are
invalid.

### Why it is not being fixed

The rubric is frozen and the error was found after freezing. Editing a frozen input post
hoc — even to correct a real mistake — makes every other frozen artifact's status
negotiable. The error stands, documented, with its measured effect recorded above.

*(An earlier version of this section said the error "demonstrably changed no score" and
"was inert". That was written before the full scoring run and is wrong: it depressed two
candidates by one faithfulness point each, as the corrected section above records.)*

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
in one context, so a rater's threshold shifts all five together. I claimed this **cancels
in the within-article ranking**; E7 below corrects that — it is attenuated, not
eliminated, and was never tested — which is what the lexicographic rule produces and what the task
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

## E6 — The date-perturbation labels are invalid (external review finding)

The generator verified that `span_original` appeared **somewhere** in the article. It never
verified that the date **supported the event the summary attributed it to**.

Example: a summary asserts `警察は10日、被害件数を516件に上方修正し…発表した`. The article's
only occurrences of `10日` are a justice minister's newspaper interview and a street
protest. The original date was already unsupported for that event, so substituting it
creates no contradiction — and the judge declining to mark one **may be correct**.

Conservative proxy: **12 of 22** date items have no article sentence sharing even two
content words with the clause asserting the date.

**The 64% date-detection figure is withdrawn.** Detection on the corruption types whose
labels survive the audit is **78/82 = 95%** [88%, 98%]. Date corruption detection is
unmeasured, not poor.

This is the fourth time a measurement instrument of mine was at fault rather than the
judge, and the second where I had already written down the correct explanation as
speculation without testing it.

## E7 — "Within-article rankings are immune to rater effects" was asserted, not tested

Simulating the E4 boundary shift changes no ranking (0/50), but that only covers a
*uniform monotone* shift. Raters differing **non-uniformly** between two candidates in the
same article would merge or split a tie and reorder them. Testing this requires the same
article scored twice by different raters, which the design never did. Corrected claim:
**attenuated, not eliminated, and unvalidated.**

## E8 — Specificity was stated more broadly than measured

"0/33 false positives" is a claim-label result: no control produced a CONTRADICTED claim
naming the paraphrase. It is **not** score stability. Against their own originals,
faithfulness is unchanged in only **15/33** controls (12 up, 6 down). The direction tracks
rater strictness (+0.75 from strict batches, −0.17 from the lenient one), so most movement
is the E4 rater effect — but not all: `到着し、`→`到着して、` moved a score from 4 to 3.
Score stability under paraphrase is **not established**, and could not be, because controls
and originals were never scored by the same rater.

## E9 — A hardcoded path broke three scripts in the packaged submission

`build_perturbations.py` set `ROOT = "/home/user/japan"`. My reproducibility check was run
from the repo root, so it passed while the packaged submission was broken — **I verified
the wrong thing.** Fixed to resolve from `__file__`; `arm_census.json` and `split.json`
moved into `runs/`. All five scripts now run from `submission/` and reproduce
byte-identical output.

## E10 — Rank counts mixed two incompatible definitions (second review)

The report quoted 24, 25, 2 and 3 for "first place" across sections. Those came from
`argmax`, which returns one winner even when several tie — so they were neither
"rank-1 including ties" nor "sole winner", but an incoherent third thing.

Correct counts, both definitions, from `code/analyze_results.py`:

| rule | rank-1 incl. ties | sole winner | articles tied at first |
|---|---|---|---|
| frozen | extract 25, abstractive 25, reference 3 | extract 24, abstractive 22, reference 1 | 3 |
| coverage-first | abstractive 40, extract 8, reference 7 | abstractive 35, extract 7, reference 3 | 5 |
| unweighted sum | abstractive 47, reference 11, extract 4 | abstractive 34, reference 3, extract 2 | 11 |

The sum produces far more ties at first place (11 vs 3), which is part of why it looks
tidier — and a further reason not to treat it as the definitive ordering.

## E11 — Superseded results were left in place

`runs/VALIDATION_RESULTS.md` still carried the withdrawn date figure, an H1 total computed
over invalid labels, and the "immune to rater effects" claim, all contradicting the revised
report. Now carries a supersession banner naming each. `runs/KNOWN_ERRORS.md` carried both
an obsolete "the error was inert" conclusion and the superseded "rater effects cancel"
claim; both are now marked obsolete in place rather than deleted, so the correction is
visible.

## E12 — The README claimed code that did not exist

It said `code/` contained "everything used to produce the scores and the validation".
`scores.jsonl` was assembled, and every report table computed, in ad-hoc shell sessions
that were never committed. Added `assemble_scores.py`, `validate_submission.py` and
`analyze_results.py`; all three run from either the repo root or the packaged submission
and regenerate the deliverable and every reported figure.

## E13 — provenance_check.py was described as more than it is

Described as enforcing "each output came from its assigned model". It checks the
**declared** producer metadata. It detects misrouted or unstamped output; it cannot verify
which model actually ran. Description corrected.
