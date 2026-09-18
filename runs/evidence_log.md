# Evidence Log — exploration split (10 articles)

Verbatim observations from close reading. Each entry: what I saw, the summary_id,
and the hypothesis it supports or kills. Written as I read, before rubric design.

---

## Article 37426493 — Jolie/Pitt divorce

All five arms are visible in one article, which makes this the clearest worked example
in the dataset.

| summary_id | reading |
|---|---|
| `…12ba3116` | **== reference.** |
| `…9d69dc21` | Clean abstractive. Filing 19日 ✓, separation 9月15日 ✓, 6人の子ども ✓. |
| `…6baeebc9` | **Corrupted twin of the above — THREE deltas.** Filing "15日" (article: 19日), separation "9月1日" (article: 9月15日), "4人の子ども" (article: 6人). |
| `…e6062236` | Lead extract, copy=1.00. Opens with the photo caption `ジョリーさんとピットさんは2014年、フランスで結婚した`. |
| `…f0038832` | **Reference with its three sentences reversed** (3-2-1). Opens on "ブランジェリーナ" trivia, states the reason, and only reaches the main event — that she filed for divorce — in the final sentence. |

**FINDING — the reference is not clean.** The reference asserts two things the supplied
article does not contain: the stated reason `「乗り越えがたい相違」` (irreconcilable
differences — the article gives only `家族の健康のための判断`) and the date `20日`
(the article gives 19日 for the filing). This is *unsupported*, not *contradicted*, and
it is exactly why that distinction must be in the rubric. It also means the
intended-gold arm will legitimately lose faithfulness points.

**FINDING — the corrupted arm is not a single-token swap.** Three independent factual
edits in one candidate. My earlier "one identified token" framing was too narrow; the
paired annotation task is "check each delta", not "check the delta".

---

## Article 48116477 — LATE dementia

| summary_id | reading |
|---|---|
| `…4d229e3c` | == reference. 1 sentence, 74 chars. |
| `…b3855ba6` | **== reference, byte-identical duplicate** of the above under a different id. One of the 8 duplicate-reference articles, confirmed by reading. |
| `…833a6901` | Clean abstractive, 3 sentences. 最大3分の1 ✓, LATE ✓, TDP-43 ✓, 80歳以上 ✓, 診断法未確立 ✓. |
| `…f5fe4b35` | **Hallucination.** Asserts `現在は特効薬の臨床試験が第3相に入っている` (a drug is in Phase 3 trials). The article states the opposite: the amyloid-reduction trials **failed**, and pharma companies are **withdrawing** from dementia drug development. This is CONTRADICTED, not merely unsupported. |
| `…291f4b8f` | Lead extract, copy=1.00. Opens with the **journalist byline** `ミシェル・ロバーツ、BBCニュースオンライン、保健編集長`. |

**FINDING — source contamination is bylines too, not only photo captions.** My earlier
caption detector (30/50) keyed on a space-delimited opening fragment; a byline matches the
same shape but is a different artifact. The evidence boundary decision must cover both.

**FINDING — the reference is materially worse than the clean abstractive here.** The
reference never names LATE, omits the 3分の1 figure, and runs one sentence. `…833a6901`
covers all of it. Any evaluator faithful to the rubric *should* rank the clean abstractive
above the reference on coverage. This is a prediction to test, not a bug to suppress.

---

## Hypotheses status after 2 articles

- **SURVIVES** — six-arm construction (reference / clean abstractive / corrupted abstractive
  / lead extract / truncation / permuted reference), drawn 5-at-a-time per article.
- **SURVIVES** — references are a comparison group, not gold. Two independent failures in
  two articles (unsupported claims; thin coverage).
- **REVISED** — corrupted candidates carry *multiple* factual deltas, not one.
- **REVISED** — lead-extract contamination includes bylines, not just captions.
- **DEAD** (from full-dataset structural pass) — wrong-language output 0/250,
  degenerate repetition 0/250, sentence-limit violations 2/250.

---

## Article 41875333 — Trump Japan visit

| summary_id | reading |
|---|---|
| `…398f4a38` / `…beaac925` | **Both == reference**, byte-identical, different ids. Second confirmed duplicate-reference article. |
| `…06c27e30` | Clean abstractive. Quote `どの独裁者も米国の決意を軽視してはならない` ✓ matches article. |
| `…aa36a21a` | **Fabricated quotation.** Same summary but the quote becomes `米国はもはや世界の警察ではない` — a sentence that appears nowhere in the article. A new corruption type: not an entity swap but an invented quote attributed to a named speaker. |
| `…d558c42b` | Lead extract, copy=1.00, opens with photo caption (ゴルフ場…（5日）). |

## Article 45392795 — Brazil National Museum fire

| summary_id | reading |
|---|---|
| `…a027bba1` | == reference. |
| `…74c007a5` | Clean abstractive, covers fire/collection size/reactions. |
| `…321915ee` | **Fabricated event.** Asserts `警察当局は出火原因を放火と断定し、容疑者2人をすでに拘束した` (arson confirmed, 2 suspects held). Article states `出火の原因は明らかになっていない`. CONTRADICTED. |
| `…7b0e7ddf` | Lead extract, copy=1.00, opens with caption. |
| `…35096e70` | **OFF-TOPIC — summary of a different article entirely** (Uber's CEO shifting to e-scooters and bikes). copy=0.00. |

---

## FINDING — seventh arm: misattached summaries

Systematic check across all 250 (copy-rate ≤ 0.05 vs own article, then best-matching
article in the corpus): **16 summaries across 15 articles are attached to the wrong
article.** Split: 1 exploration, 3 development, 11 held-out. Seven confirmed by reading:

| summary_id | attached to | actually about |
|---|---|---|
| `…35096e70` | Brazil museum fire | Uber CEO / e-scooters |
| `…dbc28b65` | Iraqi Kurdish forces, Mosul | Finnish paternity leave policy |
| `…d912de2c` | Vietnam oil drilling | Syria ceasefire |
| `…ab76c193` | Shape of Water at the Oscars | sugar content of yoghurt |
| `…cff3d43b` | Georgia jogger shooting | LATE dementia — *the reference from article 48116477* |
| `…bbe6c482` | Barr on election fraud | NYT publisher meeting Trump |
| `…31b57567` | childhood career aspirations | *the reference from article 40504740* |

Two candidates at copy ≤ 0.05 did **not** flag (`…b6028e64`, `…a3eb7364`) — their best
match is their own article. They are merely highly abstractive. The detector discriminates.

**Design consequences.**
1. These are fluent, well-formed, and faithful *to some article* — just not this one. Any
   reference-free fluency or quality metric scores them highly. This is the single
   strongest argument in the dataset for source-grounded evaluation.
2. Several misattached summaries are references *lifted from other articles in this corpus*,
   so a reference-similarity baseline sees a familiar-looking string. Its behaviour here is
   worth measuring rather than assuming.
3. **Caution for validation:** this arm is trivially detectable by copy rate, so it will
   inflate the structural baseline's apparent ranking performance. The baseline comparison
   must be reported with and without the misattached candidates, or the LLM judge is
   handicapped against a shortcut that only works on 6% of the data.

## Revised arm inventory (7)

| arm | prevalence | primary failure |
|---|---|---|
| reference verbatim | 50/50 articles (58 summaries) | (intended gold; not clean — see 37426493, 48116477) |
| lead extract, copy=1.00 | 50/50 | selection; ingests captions **and bylines** |
| clean abstractive | ~1 per article | — |
| corrupted abstractive | ≥26 pairs / 24 articles | faithfulness: entity swap, number swap, fabricated quote, fabricated event |
| reference truncated | 17/50 | completeness |
| reference permuted | 9/50 | coherence |
| **misattached (wrong article)** | **16 / 15 articles** | relevance — total coverage failure |

---

## CORRECTION — misattached count is 15, not 16

My first off-topic detector (copy-rate ≤ 0.05 vs own article, then best-matching article
in the corpus) false-positived on `…519dda6a`. That candidate **is** its article's
reference verbatim; the reference for `features-and-analysis-42940954` is so abstractive
that it scores copy=0.048 against its own article body, and a rival article beat it by
0.002 — noise, not signal.

The fix is ordering: test reference-identity **before** copy-rate. The census below does
that. Corrected figure: **15 misattached summaries in 15 articles** (one per affected
article, not two). The seven entries verified by reading in the table above are unaffected.

Worth keeping in the report: this is a concrete example of a cheap structural detector
producing a confident wrong answer, caught only because the arm census disagreed with it.

---

## FINDING — the construction is a fixed 4+1 template

Structural census over all 250 (`runs/arm_census.json`). Clean vs corrupted abstractive
cannot be separated structurally and is left as one bucket for the judge.

| arm | n | share |
|---|---|---|
| abstractive (clean or corrupted — undetermined) | 101 | 40.4% |
| reference verbatim | 58 | 23.2% |
| lead extract (copy=1.00) | 50 | 20.0% |
| truncation of reference | 17 | 6.8% |
| misattached (wrong article) | 15 | 6.0% |
| permutation of reference | 9 | 3.6% |

**Every article has exactly one lead extract and at least one reference (50/50 each).**
The per-article composition is almost perfectly regular:

| pattern | articles |
|---|---|
| reference + lead extract + 2 abstractive + **truncation** | 17 |
| reference + lead extract + 2 abstractive + **misattached** | 15 |
| reference + lead extract + 2 abstractive + **permutation** | 9 |
| reference + lead extract + 2 abstractive + **second reference** | 8 |
| reference + lead extract + 3 abstractive (no degradation slot) | 1 |

So the generator fills **five slots: reference, lead extract, two abstractive, and one
variable degradation** drawn from {truncation, misattached, permutation, duplicate
reference}. This is the single most useful structural fact in the dataset and it was not
disclosed.

**Consequences for the evaluation.**
1. Exactly 2 of 5 candidates per article require semantic judgement to separate. The other
   3 are structurally determined. An evaluator that only got the structural ones right
   would look deceptively good — reinforcing the need to report baseline comparisons
   *excluding* structurally-determined candidates.
2. The abstractive bucket is 101 summaries ≈ 2 per article, presumably ~half clean and
   ~half corrupted. Only 26 of those pairs are near-twins detectable by surface similarity,
   so roughly half the corrupted candidates differ from their clean sibling too much for a
   paired surface test to find. The paired sensitivity test therefore covers about half the
   faithfulness cases, not all of them — a sharper statement of the selection-bias caveat.
3. No second extractive mode: within the abstractive bucket, copy-rate decays smoothly and
   only 7 candidates exceed 0.50. One (`…9e82620f`, copy=0.76) is a genuine mid-article
   extract that opens on a quote attribution and never states the main finding — a
   selection failure distinct from lead extraction.
