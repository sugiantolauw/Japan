# Live hypotheses — registered before the frozen-run results exist

The original ten hypotheses were about **the data**. Exploration settled them (5 survived,
5 died) and they are now findings, not hypotheses. What remains open is about **the
evaluator**. Registered now, while the perturbation and held-out runs are still executing
and no result has been seen.

## Settled from the first round (`runs/PILOT_RESULTS.md`, `runs/DEV_RESULTS.md`)

| # | prediction | status |
|---|---|---|
| P1 | lead extracts: faithfulness 4, coverage ≤2 | **failed** — the prediction was wrong (inverted-pyramid news often puts the main event first). Faithfulness half held 3/3. Not amended. |
| P2 | misattached: 0 / 0 / 4 / 4 | **passes** after the v1.1 selection fix |
| P3 | corrupted/clean siblings separate ≥3 on faithfulness, ≤1 elsewhere | **failed** — partly an ill-posed test (natural pairs are not minimal), partly a real rubric defect now fixed in v1.2. Superseded by H1/H2 below. |
| P4 | permutation differs from its reference on coherence only | **passes** 2/2 |
| P5 | the reference arm does not sweep first place | **passes** on 3 pilot articles — restated as H6 for all 50 |
| P6 | duplicate references score identically | **passes** on 1 pair — restated as H7 for all 8 |

## Open hypotheses

### H1 — Sensitivity. The judge detects scripted corruptions.
Faithfulness drops on the 104 drop-type perturbations relative to their unperturbed
originals. **This is the measurement P3 was trying and failing to make**, now with
certain ground truth and guaranteed minimality.
*Confidence: moderate-high.* Entity and number swaps are the kind of thing claim-level
checking exists for.

### H2 — Specificity. The judge does NOT penalise meaning-preserving paraphrase.
Faithfulness is unchanged on the 33 paraphrase controls (`発生した→起きた`,
`と発表した→と明らかにした`). Without this, H1 is worthless — a judge that lowers the
score on any edit would "pass" H1 by being uniformly suspicious.
*Confidence: moderate.* This is where I expect trouble: two controls
(`表明した→明言した`, `批判を浴びた→非難を浴びた`) are mild register shifts.

### H3 — Polarity reversal is the judge's hardest corruption type.
Recall on the 24 polarity reversals is **lower** than on the 80 entity/number swaps.
Reasoning: entity and number swaps leave a token that is absent from the source, so
claim-level checking has an anchor. A polarity reversal changes no token identity — both
`中断` and `継続` are ordinary words, and detecting the error requires understanding
direction, not matching strings.
*Confidence: moderate-high. This is the most interesting prediction in the set,* because
it is the one type no cheaper method could ever catch, so it is where an LLM judge has to
earn its cost.

### H4 — The judge beats both baselines on the abstractive-only subset.
Measured already: the structural baseline assigns an identical score to all 101 abstractive
candidates, so it has literally zero ranking power there. The real contest is against
reference similarity.
*Confidence: high vs. Baseline A (arithmetically certain), genuinely uncertain vs. B.*

### H5 — Baseline B wins on all candidates and loses on the abstractive subset.
Reference similarity scores exactly 1.0 on the 58 reference candidates by construction, so
including them flatters it. Restricting to candidates that need judgement should reverse
the result. **If this fails — if reference similarity also wins on the abstractive subset —
that is a serious finding against the whole design**, and it must be reported as such.

### H6 — The reference arm does not sweep first place across all 50 articles.
Held on 3 pilot articles. Exploration found references with unsupported claims and
one-sentence coverage losing to three-sentence abstractive candidates.
*Confidence: high.*

### H7 — All 8 duplicate-reference pairs score identically.
Byte-identical input, independent judgements, no shared cache. Any difference is pure
judge variance and quantifies it for free.
*Confidence: moderate.* One pair held; eight is a harder test.

### H8 — Judge scores are not strongly length-biased.
Regressing each dimension on candidate length should show no large positive coefficient
once arm is controlled for. **Stated as a null I expect to survive, which means it is weak
evidence if it does and strong evidence if it does not.**
*Confidence: low.* Length bias is among the best-documented LLM-judge failure modes and I
would not be surprised to be wrong.

### H9 — The judge's raw evidence-verbatim error rate replicates near 8%.
Measured once: 16 non-verbatim evidence strings in the development run, all spliced
non-adjacent spans, self-corrected before the file was finalised. If the frozen runs show a
similar raw rate, it is a stable property worth reporting as a judge limitation rather than
a one-off.
*Confidence: low — a single observation.*

## What would falsify the design rather than the judge

- **H1 fails**: claim-level checking does not detect scripted single-fact corruptions. The
  rubric's central mechanism does not work and the design needs rework, not prompt-tuning.
- **H2 fails**: the judge penalises harmless paraphrase, so any apparent sensitivity in H1
  is indiscriminate suspicion rather than detection.
- **H5 fails**: a cheap reference-similarity metric matches the LLM judge even on
  candidates requiring semantic judgement — on a dataset where the reference is a
  candidate and is demonstrably flawed. That would undermine the case for the whole
  approach and must be reported prominently, not buried.
