# Scoring Rubric v1.2

Frozen before any development or held-out scoring. Every anchor cites a candidate from
the **exploration split only**. The judge never sees this provenance — only the scale.

## Evidence boundary

The evidence is the supplied `title` + `text` of the article the candidate is attached to.
Nothing else.

- Photo captions and journalist bylines spliced into `text` **are** part of the source
  (30/50 articles open with one). A claim supported only by a caption is *faithful* but
  usually *badly selected* — that tension is resolved by scoring the two dimensions
  separately, never by excluding captions from the evidence.
- The `reference_summary` is **not** evidence and never establishes support. It is a
  comparison group. In exploration it was independently shown to contain unsupported
  claims, thin coverage, and a typo.
- External world knowledge never establishes support. A true statement absent from the
  article is UNSUPPORTED, not SUPPORTED.

## Claim status labels

Applied per claim, before dimension scoring:

| label | meaning |
|---|---|
| `SUPPORTED` | the article states or directly entails it |
| `CONTRADICTED` | the article states something incompatible with it |
| `UNSUPPORTED` | the article neither states nor contradicts it |
| `AMBIGUOUS` | genuinely cannot be resolved from the article |

The SUPPORTED/UNSUPPORTED/CONTRADICTED separation is load-bearing. The reference for
article 37426493 asserts the divorce reason `「乗り越えがたい相違」` and the date `20日`;
the article gives `家族の健康のための判断` and 19日. The reason is UNSUPPORTED (absent),
the date is CONTRADICTED (incompatible). Collapsing these would score an intended-gold
candidate the same as a planted corruption.

## Dimensions

Four scored dimensions, each 0–4. Coverage and Selection are deliberately complementary:
coverage is **recall** of what must be said, selection is **precision** of what is said.

### 1. Faithfulness — are the claims supported by the source?

| score | anchor |
|---|---|
| 4 | every claim SUPPORTED |
| 3 | all claims SUPPORTED except immaterial UNSUPPORTED detail that does not change meaning |
| 2 | material UNSUPPORTED **detail** — a plausible fact absent from the source (an unstated date, a descriptor) that invents no event or attribution |
| 1 | one CONTRADICTED claim, **or one fabricated event, action, policy or quotation** — content invented rather than merely absent |
| 0 | multiple CONTRADICTED or fabricated claims, or the candidate describes an event the article does not cover at all |

Severity keys on *invention*, not only on the supported/contradicted axis. A fabricated
government regulation is at least as harmful as a misstated number, and three of the six
corruption types observed in this data — fabricated quotation, fabricated event,
hallucinated status — are inventions that no source sentence contradicts.

Observed failure types, all requiring the source to detect: entity swap, number/date swap,
fabricated quotation, fabricated event, hallucinated status, and **polarity reversal** —
a candidate that inverts the direction of a reported action while changing no entity or
number (`…3f3f4b05`: the airline "will continue" tests the article says it suspended).
A candidate whose claims are all about a different news story scores 0 (wholly
UNSUPPORTED), not 1 — nothing in it is contradicted, but nothing is supported either.

### 2. Coverage — does it convey the article's essential information?

Scored against the information units extracted from the article *before* any candidate was
seen (`runs/keypoints/`).

| score | anchor |
|---|---|
| 4 | conveys all essential units |
| 3 | conveys the main event and most essential context; minor omission |
| 2 | conveys the main event but omits significant essential context |
| 1 | related to the article but does not convey the main event |
| 0 | conveys none of the essential units |

`…fa255e70` scores 1: a verbatim passage defining what Antifa is — every claim supported,
and it never mentions that Trump said he would designate it a terrorist organisation.

### 3. Coherence — is it ordered and complete as a piece of Japanese?

| score | anchor |
|---|---|
| 4 | well-ordered; main event first; complete sentences |
| 3 | minor awkwardness |
| 2 | subordinate detail placed before the main event |
| 1 | ends mid-sentence, or ordering obscures the meaning |
| 0 | incoherent |

Score 2 anchor: `…07d482c6` opens `トランプ氏は…非難している` and reaches the actual
announcement only in the second sentence. Score 1 anchor: `…7b3a10b0` ends `逃走したが、`.

### 4. Selection — is the included material of a kind that belongs in a summary?

**Scope: this dimension scores the TYPE of material, not its topical relevance.** Whether
the content is about the right article is Coverage's job. A candidate that is fluent,
well-formed summary prose about a completely different news story scores HIGH on selection
and 0 on coverage — that vector is the diagnostic, and collapsing both to 0 destroys it.
Penalise here only for material that does not belong in any summary: photo captions,
journalist bylines, definitional asides, quote attributions, navigational text.

| score | anchor |
|---|---|
| 4 | everything included belongs in a summary |
| 3 | minor extraneous detail |
| 2 | non-summary material crowds out essentials |
| 1 | substantially composed of non-summary material — photo caption, byline, definitional aside, quote attribution |
| 0 | almost entirely non-summary material |

Score 1 anchor: `…979831e4` opens with the byline
`ミシェル・ロバーツ、BBCニュースオンライン健康担当編集長`.

## Deterministic flags (computed without the model, not scored)

`n_sentences`, `exceeds_three_sentences` (2/250 — reported, never scored),
`ends_without_terminal_punctuation`, `copy_rate`, `identical_to_reference`,
`structural_arm`. These are recorded alongside every judgement for validation, and are
**never shown to the judge**.

## Ranking rule — lexicographic, frozen

Candidates within an article are ordered by:

    faithfulness → coverage → coherence → selection

strictly in that priority, each compared only when all higher dimensions tie. Ties are
permitted and expected — the 8 duplicate-reference articles contain byte-identical
candidates that **must** tie.

A weighted sum was rejected: it invites "why 0.4 and not 0.3?", which the report cannot
answer honestly, and it lets polished writing compensate for a factual error. Lexicographic
ordering is defensible in one sentence — a summary that says something false is worse than
one that is merely badly organised — and makes the sensitivity analysis concrete: *does
the within-article ranking change if coherence and selection swap priority?*

## Judge output schema

```json
{
  "summary_id": "...",
  "claims": [{"claim": "...", "status": "SUPPORTED|CONTRADICTED|UNSUPPORTED|AMBIGUOUS",
              "evidence": "verbatim excerpt from the article, or null"}],
  "faithfulness": 0, "coverage": 0, "coherence": 0, "selection": 0,
  "rationale": "<=2 sentences",
  "producer": {"role": "judge", "model": "...", "agent": "judge", "run_kind": "primary"}
}
```

Every non-null `evidence` string must occur verbatim in the article. A judgement citing
an excerpt that does not appear is itself a hallucination and is counted as a judge error
during validation.

## What the judge is not given

The reference summary, structural flags, the arm census, copy-rate, other candidates for
the same article, or any hint about generation method. The judge sees rubric + article +
key points + one candidate. Contaminated input must be refused, not scored.
