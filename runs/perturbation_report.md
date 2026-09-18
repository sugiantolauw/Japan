# Perturbation suite report

Seed: 20260918. Source pool: arm in {abstractive_undetermined, reference}, articles in exploration+development splits only (never held-out).

Pool size: 66 source summaries across 20 articles.

Total perturbations generated: 137.

## Counts per type

| type | count | in [25,40]? |
|---|---|---|
| number_swap | 40 | yes |
| entity_swap | 40 | yes |
| polarity_reversal | 24 | NO |
| paraphrase_control | 33 | yes |

**Note on polarity_reversal (24 < 25):** this is a genuine data ceiling, not a selection-code artifact. Every antonym-pair direction in the table below was checked against every pool summary; 24 is the total count of (summary, antonym pair) matches where the ORIGINAL form is verbatim in both the summary and the article, and the REPLACEMENT is verbatim absent from the article -- i.e. it is literally every valid opportunity this pool contains under the rule the task specifies, not a sample of a larger set. Reaching 25+ would require either relaxing the verbatim-match rule (weakening ground truth) or fabricating less-grounded antonym pairs to force matches, both of which this suite avoids. This scarcity itself corroborates `runs/evidence_log.md`'s own observation that polarity reversal was the rarest corruption type found during exploration ('Two instances').

## Counts per split

| split | count |
|---|---|
| exploration | 72 |
| development | 65 |

## Counts per type x split

| type | exploration | development |
|---|---|---|
| number_swap | 19 | 21 |
| entity_swap | 19 | 21 |
| polarity_reversal | 13 | 11 |
| paraphrase_control | 21 | 12 |

## Verification results

- All checks passed: **True** (137 items checked)
- Distinct source summaries perturbed: 57
- Max perturbations from a single source summary: 3 (cap = 3)
- Held-out article present in output: **False** (must be False)
- [1] perturbed_text differs from original_text: 137/137
- [2] perturbed_text is EXACTLY original_text with EVERY occurrence of span_original replaced by span_replacement (global replace, not a first-occurrence-only edit): 137/137
- [3] no held-out article present: 137/137
- [4] drop-type items where span_original is verified PRESENT in the article: 104/104
- [5] drop-type items where span_replacement is verified ABSENT from the article: 104/104
- [6] drop-type items where span_original is verified ABSENT from perturbed_text, i.e. the corruption was applied to EVERY occurrence so the item cannot be caught by noticing it contradicts itself instead of the source: 104/104

**Multi-occurrence spans are replaced globally, not just at the first occurrence.** A span that occurs more than once in a summary (e.g. a count repeated in two sentences) was originally replaced at only one location, which could leave the original value still present elsewhere in the perturbed text -- e.g. 'he alone' in one clause and 'a group of 10' in another. Such an item is internally self-contradictory and can be flagged by noticing it disagrees with ITSELF, with no reference to the article at all. Since this suite exists specifically to measure whether a judge does SOURCE-grounded checking, an internally-inconsistent item would let a judge score well via a cheaper route than actually consulting the article, inflating the very recall metric the suite is meant to measure. `make_item()` therefore replaces every occurrence of `span_original` in one pass (`str.replace`, unbounded count) and check [6] above confirms none remain.

## Entity substitution table used

| category | original | replacement |
|---|---|---|
| country | ドイツ | フランス |
| country | カナダ | オーストラリア |
| country | スイス | ノルウェー |
| country | 中国 | インド |
| country | ベトナム | フィリピン |
| country | 北朝鮮 | イラン |
| country | ブラジル | アルゼンチン |
| country | 英国 | フランス |
| country | フィンランド | スウェーデン |
| country | イラン | イラク |
| country | インド | パキスタン |
| country | トルコ | ヨルダン |
| country | ロシア | イラン |
| place | ケルン | ミュンヘン |
| place | サンバーナディーノ | サクラメント |
| place | カリフォルニア州 | テキサス州 |
| place | ロサンゼルス | サンフランシスコ |
| place | リオデジャネイロ | サンパウロ |
| place | マシュハド | エスファハーン |
| place | テヘラン | アンカラ |
| place | ハル | リーズ |
| place | パークランド | オーランド |
| place | フロリダ州 | ジョージア州 |
| place | ノースカロライナ州 | サウスカロライナ州 |
| place | 北京 | 上海 |
| place | デリー | ムンバイ |
| place | サイパン | グアム |
| place | 香港 | 台湾 |
| org | マギル大学 | トロント大学 |
| org | ベルン大学 | チューリッヒ大学 |
| org | ハーバード大学 | プリンストン大学 |
| org | 京都大学 | 東京大学 |
| org | NHS | WHO |
| org | 香港エクスプレス | ジェットスター |
| org | ダブルツリー・ヒルトン | マリオット |
| org | ロイヤル・ホテル | プレミアインホテル |
| org | サイエンス誌 | ネイチャー誌 |
| person | アンジェリーナ・ジョリー | ジェニファー・アニストン |
| person | ブラッド・ピット | レオナルド・ディカプリオ |
| person | ドナルド・トランプ | ジョー・バイデン |
| person | 安倍晋三 | 麻生太郎 |
| person | ハッサン・ロウハニ | モハンマド・ハタミ |
| person | サンナ・マリン | エルナ・ソルベルグ |
| person | マシュー・ロブソン | ジェームズ・スミス |
| person | ジャスティン・ブラックマン | マイケル・ジョンソン |
| person | ジェイムズ・P・アリソン | デイヴィッド・ジュリアス |
| person | 本庶佑 | 山中伸弥 |
| brand | マッカラン | グレンフィディック |

## Antonym table used (polarity_reversal)

Both directions of each pair were tried; a direction is used only when the ORIGINAL form appears in both the summary and the article, and the REPLACEMENT form is absent from the article.

| pair A | pair B |
|---|---|
| 中断 | 継続 |
| 解除 | 発動 |
| 上昇 | 下落 |
| 認めた | 否定した |
| 増加 | 減少 |
| 成功 | 失敗 |
| 可決 | 否決 |
| 拒否 | 受諾 |
| 下方修正 | 上方修正 |
| 残留する | 撤退する |
| 拘束した | 釈放した |
| 存続する | 中止する |
| 義務付ける | 免除する |
| 拡大している | 縮小している |
| 妨げられる | 促進される |
| 回復する | 悪化する |
| 非難している | 擁護している |
| 参加した | 欠席した |
| 逮捕された | 釈放された |
| 負傷した | 回復した |
| もたらした | もたらさなかった |
| 含まれている | 含まれていない |
| 精度の高い | 精度の低い |
| 指定する | 指定しない |
| 無料で | 有料で |
| 邪魔すると | 促進すると |
| 認めるよう | 拒むよう |
| 悲しい日 | 喜ばしい日 |

Several pairs from the task brief's suggested list (可決/否決, 成功/失敗, 上昇/下落, 認めた/否定した, 増加/減少, 解除/発動) did not occur in any pool summary's overlapping text and therefore produced zero items; they remain in the table for future pool growth. Pairs that DID fire came from actually-occurring text: 下方修正/上方修正, 拘束した/釈放した, 残留する/撤退する, 存続する/中止する, 拒否/受諾, 中断/継続, 義務付ける/免除する, 拡大している/縮小している, 妨げられる/促進される, 回復する/悪化する, 非難している/擁護している, 参加した/欠席した, 逮捕された/釈放された, 負傷した/回復した, もたらした/もたらさなかった, 指定する/指定しない, 精度の高い/精度の低い, 無料で/有料で, 邪魔すると/促進すると, 認めるよう/拒むよう, 悲しい日/喜ばしい日.

## Paraphrase-control table used

| original | meaning-preserving replacement |
|---|---|
| と発表した | と明らかにした |
| ことが明らかになった | ことが判明した |
| と述べた | と語った |
| 批判を浴びた | 非難を浴びた |
| 申し出た | 提案した |
| 表明した | 明言した |
| 分かった | 判明した |
| 発生した | 起きた |
| 参加した | 加わった |
| 親権を求め | 親権を要請し |
| 到着し、 | 到着して、 |
| 説明し、 | 述べ、 |

All pairs above were read individually and judged genuinely meaning-preserving before inclusion (conservative by design: per the task brief, a pair was skipped rather than included if it could not be made cleanly non-factual-altering). Two pairs were the mildest register shifts in the set and are flagged here explicitly so a reader knows they were considered rather than overlooked: **表明した→明言した** ("stated" -> "stated clearly/explicitly" -- adds emphasis, not a new claim) and **批判を浴びた→非難を浴びた** ("drew criticism" -> "drew condemnation" -- a stronger register, but reports the same underlying fact: negative public reaction occurred). Both were judged to preserve the truth-value of the claim, unlike the `polarity_reversal` pairs which invert it.

## Coverage of the observed corruption taxonomy

`runs/evidence_log.md` documents 6 observed corruption types. This suite covers **3 of 6** programmatically:

| taxonomy type | covered? | why |
|---|---|---|
| entity swap | yes | `entity_swap` — curated same-category substitution table, verified absent from article |
| number/date swap | yes | `number_swap` — regex-located numeral+unit token, replacement verified absent from article |
| polarity reversal | yes | `polarity_reversal` — curated antonym table, verified absent from article |
| fabricated quotation | **no** | requires GENERATING a novel quotation attributed to a speaker; there is no source span to substitute — a program can only rearrange or replace existing spans, not invent plausible false speech. Doing this mechanically-but-crudely (e.g. wrapping random text in quote marks) would not produce a genuinely plausible fabricated quote and risks being trivially detectable by surface form alone, defeating the purpose of the suite. |
| fabricated event | **no** | requires inventing a plausible but unstated event (e.g. "police confirmed arson, 2 detained") — there is no existing span in the source summary to substitute against; this is generation, not substitution, and would require a judgement call about what counts as 'plausible' that this deterministic tool cannot make. |
| hallucinated status | **no** | e.g. a drug "in Phase 3 trials" when trials failed — this requires synthesizing a specific false status claim consistent with the topic, again generation rather than substitution of an existing span. |

**Honest limitation:** this suite therefore measures faithfulness recall against 3 of 6 observed corruption types — the three that are expressible as a verified span substitution. The other three (fabricated quotation, fabricated event, hallucinated status) are qualitatively different: they require generating new false content rather than substituting a verifiable replacement for an existing span, which is exactly the property that let this suite avoid human/LLM judgement of quality. A judge that passes this suite has not been shown to catch fabrication or hallucination — only entity/number swaps and polarity reversal. `polarity_reversal` is the most load-bearing of the three covered types, since (per `evidence_log.md`) it is undetectable by symbol-matching (no entity or number changes) and was the corruption type found hardest to catch by structural detectors during exploration.

