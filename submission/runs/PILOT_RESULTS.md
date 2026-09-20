# Judge pilot — 3 development articles, 15 candidates

Run before freezing. Scored blind: article + key points + one candidate. No reference
field, no arm census, no predictions file. Evidence verification: **43 claims, 31 non-null
evidence strings, 0 failed the verbatim check** — the judge is not fabricating its own
evidence.

## Scores by structural arm (judge was blind to arm)

| arm | n | faithfulness | coverage | coherence | selection |
|---|---|---|---|---|---|
| abstractive (undetermined) | 6 | 1,2,4,3,4,4 | 1,1,4,1,1,3 | 4,4,4,4,4,4 | 4,4,4,2,4,4 |
| lead extract | 3 | **4,4,4** | 2,2,3 | 3,2,2 | 2,1,1 |
| reference | 4 | 2,3,3,4 | 1,2,2,2 | 4,4,4,4 | 4,4,4,4 |
| truncation | 1 | 2 | 1 | **1** | 4 |
| misattached | 1 | **0** | **0** | 4 | **0** |

## Pre-registered predictions

| # | prediction | result |
|---|---|---|
| 1 | lead extract: faithfulness 4, coverage ≤2 | **FAIL** (faithfulness half passed 3/3; coverage 3 on one) |
| 2 | misattached: 0 / 0 / 4 / 4 | **FAIL** (selection scored 0, not 4) |
| 3 | corrupted/clean siblings separate by ≥3 on faithfulness | untestable — no identified pair in these 3 articles |
| 4 | permutation differs from its reference only on coherence | untestable — no permutation in these 3 articles |
| 5 | the reference arm does not sweep first place | **PASS** — first place went to lead_extract, abstractive, abstractive |
| 6 | duplicate references score identically | **PASS** — `…17e4f012` and `…b97582b2` both 3/2/4/4 |

## P1 — my prediction was wrong, not the judge

The load-bearing half **passed**: all three lead extracts scored faithfulness 4. The judge
does not conflate "bad summary" with "false", which is the whole reason faithfulness and
coverage are separate.

The coverage half was a bad prediction. I assumed a verbatim lead extract must miss the
main event. BBC news is written as an inverted pyramid — the opening paragraph frequently
*is* the main event. A lead extract only loses coverage when the article opens with a
caption or byline ahead of the substance, which is 30/50 articles, not all of them.

**I am not amending this prediction.** Editing a pre-registration after seeing the data
defeats its purpose. It is recorded as failed, with the reason: the prediction was wrong.

## P2 — a real rubric defect, fixed before freeze

The judge scored the misattached candidate **0 on selection**, reasoning that none of its
content serves a summary of *this* article. That is a defensible reading of
"summary-appropriate", and the rubric did not disambiguate.

But it collapses selection into coverage. Both go to 0 for the same reason, and the
dimensions stop being independent — which is exactly what P2 was written to detect. The
diagnostic that misattached candidates are *fluent, well-formed prose about the wrong
article* is lost.

Fixed in rubric v1.1: **selection scores the TYPE of material included (summary prose vs.
captions, bylines, definitional asides, quote attributions), not its topical relevance.**
Relevance is coverage's job. A misattached candidate is well-selected prose that is
comprehensively off-topic, and the score vector should say so.

This is a legitimate pre-freeze fix on development data, and it is disclosed here rather
than folded in silently.

## Third finding: claim decomposition is too shallow

43 claims over 15 candidates — **2.9 per candidate**, minimum 2. A three-sentence Japanese
news summary typically carries 5–8 checkable claims (actor, action, time, place, quantity,
attribution). Coarse decomposition is a direct threat to faithfulness recall: a corruption
inside an undecomposed claim is invisible. Tightened in v1.1.

## What the pilot established

- The judge does not fabricate evidence (0/31 failures) — the single most important check.
- Byte-identical candidates receive identical scores (P6) — no gratuitous variance.
- The reference arm is genuinely weak here: faithfulness 2,3,3,4 and coverage 1,2,2,2, and
  it took first place in none of the three articles. The exploration reading of XL-Sum
  reference quality is corroborated by a judge that never saw which candidate was the
  reference.
