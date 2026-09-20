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

---

## Articles 51145805 / 52873099 / 54083932 — exploration complete (10/10)

### NEW corruption type: polarity reversal

Two instances, and it is the most dangerous type seen so far because the surface
form is untouched — same entities, same numbers, same register.

| summary_id | article says | candidate says |
|---|---|---|
| `…3f3f4b05` | Hong Kong Express **suspended** the pregnancy tests immediately and apologised (`この対応を即時中断し、見直しを行っている`) | `今後も米移民法を遵守するため妊娠検査を継続する方針` — the airline will **continue** the tests |
| `…438d80a5` | Collection bought for £5,000 is now worth **£40,000+**, with `すでに多くの引き合い` (much buyer interest) | sells `購入価格総額5000ポンドのまま`, and `バイヤーからの引き合いは少なく、思ったような収益は見込めない` — little interest, poor return |

Its clean sibling `…1639e27b` states `対応の即時中断と謝罪を表明した` ✓. So the pair differs
only in the *direction* of the reported action. No entity or number is wrong. Any check
based on entity overlap or number matching will pass this candidate.

### NEW failure type: faithful but irrelevant (coverage-only failure)

`…fa255e70` (copy=0.64) is a verbatim passage from deep inside the Antifa article
explaining **what Antifa is** (`「Anti-Fascist Action」の略語で…指導者のいないゆるやかに
連携する活動家集団`). Every claim is supported by the source. It is fluent and
well-formed. And it never mentions the news event — that Trump said he would designate
Antifa a terrorist organisation.

This is the cleanest possible demonstration that **faithfulness and coverage must be
separate dimensions**. A faithfulness-only evaluator scores this candidate near-perfect.
It is arguably the worst summary in its article.

### Permutations confirmed

`…0a1b1dc6`, `…07d482c6`, `…91d615a7` are all the reference with its two sentences
swapped. In each case the effect is the same: the summary opens on subordinate detail
(`同社は…釈明している` / `トランプ氏は…非難している` / `高値での取引が見込まれており`) and
delivers the main event second. Faithful, complete, and badly ordered — a discourse
failure that no claim-level check will detect.

---

# EXPLORATION SYNTHESIS

## Corruption taxonomy (6 types, all observed)

| type | example | detectable by surface means? |
|---|---|---|
| entity swap | ロシア→イラン; テキサス大学→ハーバード大学 | only against the source |
| number/date swap | 900万→500万クローナ; 19日→15日; 6人→4人 | only against the source |
| fabricated quotation | `米国はもはや世界の警察ではない` attributed to Trump | no |
| fabricated event | police confirmed arson, 2 detained | no |
| hallucinated status | drug "in Phase 3 trials" when trials failed | no |
| **polarity reversal** | suspended → continuing; high demand → low demand | **no** |

## Quality dimensions the data forces

1. **Faithfulness** — 6 corruption types, none detectable without the source.
2. **Coverage** — `…fa255e70` is perfectly faithful and useless; misattached candidates
   are perfectly fluent and about another article entirely.
3. **Completeness** — 17 truncations, deterministic.
4. **Selection** — 50 lead extracts carrying captions and bylines; 1 mid-article extract.
5. **Coherence/order** — 9 permutations, faithful and complete but wrongly ordered.

Format compliance is **not** a dimension: 2/250 violations. Reported as a flag.

## Hypotheses: final status

| hypothesis | status |
|---|---|
| dataset is a fixed 4+1 slot template | **CONFIRMED** (arm census, 49/50 articles) |
| references are a comparison group, not gold | **CONFIRMED** — unsupported claims (37426493), thin coverage (48116477, 45715110), a typo (51145805) |
| corrupted candidates are single-token swaps | **REFUTED** — up to 3 deltas, and polarity reversals change no token identity |
| wrong-language output | **DEAD** 0/250 |
| degenerate repetition | **DEAD** 0/250 |
| sentence-limit violations are a major mode | **DEAD** 2/250 |
| a second extractive mode exists | **DEAD** — copy-rate decays smoothly above lead extracts |

---

## CORRECTION 2 — `20日` is UNSUPPORTED, not CONTRADICTED

I claimed the reference for `37426493` contains one unsupported and one **contradicted**
claim. The contradiction claim is wrong.

- Reference: `「乗り越えがたい相違」が理由だと、ジョリーさんの弁護士が20日、明らかにした`
  — the lawyer disclosed the reason **on the 20th**.
- Body: `ジョリーさんは19日に「結婚解消」の申し立てを提出し` — the petition was **filed on
  the 19th**.

These are two different events: a filing on the 19th and a lawyer's statement on the 20th.
Both can be true simultaneously. `20日` does not appear in the body, so it is
**UNSUPPORTED** (absent), not CONTRADICTED (incompatible). I conflated "a different date
appears nearby" with "the dates conflict".

Consequence for the record: **I have no verified example of a CONTRADICTED claim in a
reference.** References demonstrably carry UNSUPPORTED claims; the contradictions in this
dataset live in the corrupted abstractive arm (entity swaps, number swaps, polarity
reversals). The UNSUPPORTED/CONTRADICTED distinction in the rubric is still necessary —
it is what separates the reference arm from the corrupted arm — but the reference arm
supplies only the unsupported half of that justification.

## FINDING — why references look unfaithful: the body is missing its own lead

45 of 50 articles contain at least one title content-word absent from the body. Reading
the cases, the reference for `37426493` supplies the subjects' ages (41), (52), the stated
divorce reason, and the disclosure date — none in the body — while the body opens with a
photo caption and then continues mid-narrative (`調べによると…`).

The consistent reading: **XL-Sum uses the BBC article's lead paragraph as the reference and
the `text` field excludes it.** The references are therefore not badly written. They
summarise material the supplied body omits.

This is an inference about dataset construction, not a measurement. A test I ran —
fraction of title 5-grams appearing in the reference — came back at median 0.13 and does
**not** corroborate it, though that test is weak: Japanese headlines are too telegraphic
to share 5-grams with prose describing the same fact.

**What changes, and what does not.** The evidence boundary stays the supplied title and
body: a summarizer given only that body cannot know the lead facts, so scoring reference
candidates as unsupported is the correct standard *for this application*. What changes is
the interpretation. "XL-Sum references are low quality" was too strong. The accurate
statement is that they are unsupported **relative to the evidence the summarizer sees**,
because they answer a question about a fuller article than the one supplied.

## LIMITATION — the coverage yardstick misses title-only main events

The key-point extraction prompt required excerpts verbatim from the article `text`, which
is narrower than the rubric's evidence boundary of title **plus** body. On articles whose
main event appears only in the title, the extracted main-event unit is therefore not the
actual main event:

| article | title states | frozen main-event unit instead covers |
|---|---|---|
| `52000333` | clubs and cinemas closed (`映画館` absent from body) | Morrison's stated reason for acting |
| `53274336` | the athlete's suicide (`自殺` absent from body) | the audio tapes corroborating abuse |
| `features-and-analysis-40566272` | a feature with no discrete news event | Medicaid cuts under consideration |

Coverage scores on these three articles are measured against a yardstick that omits the
headline fact. **This is not being fixed.** The key-point prompt is frozen, the defect was
discovered after the freeze, and changing a frozen input because a post-freeze reading
suggests it would be better is exactly what the freeze exists to prevent. Instead,
coverage results will be reported both including and excluding these three articles as a
sensitivity check, and the affected article ids are recorded here.
