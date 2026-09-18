#!/usr/bin/env python3
"""
build_perturbations.py

Deterministic (seed=20260918) programmatic perturbation suite.

Purpose: produce corrupted summaries with MECHANICAL ground truth (no human
judgement, no LLM judgement) so that a judge's faithfulness RECALL (does it
catch known-bad claims?) can be measured without human annotation.

Source pool restriction (contamination guard):
  - only candidates whose arm (runs/arm_census.json) is
    'abstractive_undetermined' or 'reference'
  - only articles in the EXPLORATION or DEVELOPMENT splits (runs/split.json)
  - HELD-OUT articles are never touched, at any point, by this script.

Perturbation types produced:
  1. number_swap        - drop  - a number in the summary that also occurs
                                   in the article is replaced by a value
                                   verified ABSENT from the article.
  2. entity_swap        - drop  - a proper noun shared with the article is
                                   replaced by a same-category entity
                                   verified ABSENT from the article.
  3. polarity_reversal  - drop  - a curated antonym substitution inverts the
                                   direction of a reported action; the
                                   original form must appear in both summary
                                   and article, the replacement must be
                                   ABSENT from the article.
  4. paraphrase_control - unchanged - a meaning-preserving lexical
                                   substitution. No article-absence check
                                   applies (that would be the wrong test for
                                   a control that must NOT trip the judge).

Every drop-type item is verified programmatically before being written out.
Nothing here is judged for "quality" -- only mechanically checked.
"""

import json
import random
import re
import sys
from collections import Counter, defaultdict

ROOT = "/home/user/japan"
DATA_DIR = f"{ROOT}/data"
RUNS_DIR = f"{ROOT}/runs"

SEED = 20260918
MAX_PER_SUMMARY = 3
TARGET_MIN = 25
TARGET_MAX = 40

PRODUCER = {
    "role": "builder",
    "model": "claude-sonnet-5",
    "agent": "builder",
    "run_kind": "primary",
}

# --------------------------------------------------------------------------
# Load inputs
# --------------------------------------------------------------------------

def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    rng = random.Random(SEED)

    articles = {a["article_id"]: a for a in load_jsonl(f"{DATA_DIR}/articles.jsonl")}
    summaries = load_jsonl(f"{DATA_DIR}/summaries.jsonl")
    with open(f"{RUNS_DIR}/arm_census.json", encoding="utf-8") as f:
        arm_census = json.load(f)
    with open(f"{RUNS_DIR}/split.json", encoding="utf-8") as f:
        split = json.load(f)

    heldout_articles = set(split["splits"]["heldout"])
    allowed_articles = set(split["splits"]["exploration"]) | set(split["splits"]["development"])
    assert allowed_articles.isdisjoint(heldout_articles)

    pool = [
        s for s in summaries
        if arm_census.get(s["summary_id"]) in ("abstractive_undetermined", "reference")
        and s["article_id"] in allowed_articles
        and s["article_id"] not in heldout_articles
    ]

    # article_id -> split name, for the output record
    article_split = {}
    for sp_name, ids in split["splits"].items():
        for aid in ids:
            article_split[aid] = sp_name

    print(f"[pool] {len(pool)} source candidates across "
          f"{len({s['article_id'] for s in pool})} articles "
          f"(exploration+development only, arm in "
          f"{{abstractive_undetermined, reference}})")

    # ----------------------------------------------------------------
    # Curated substitution tables
    # ----------------------------------------------------------------

    # (category, original, replacement) -- replacement must be verified
    # absent from the specific article at runtime; this table is just the
    # candidate pool of same-category swaps.
    ENTITY_TABLE = [
        ("country", "ドイツ", "フランス"),
        ("country", "カナダ", "オーストラリア"),
        ("country", "スイス", "ノルウェー"),
        ("country", "中国", "インド"),
        ("country", "ベトナム", "フィリピン"),
        ("country", "北朝鮮", "イラン"),
        ("country", "ブラジル", "アルゼンチン"),
        ("country", "英国", "フランス"),
        ("country", "フィンランド", "スウェーデン"),
        ("country", "イラン", "イラク"),
        ("country", "インド", "パキスタン"),
        ("country", "トルコ", "ヨルダン"),
        ("country", "ロシア", "イラン"),
        ("place", "ケルン", "ミュンヘン"),
        ("place", "サンバーナディーノ", "サクラメント"),
        ("place", "カリフォルニア州", "テキサス州"),
        ("place", "ロサンゼルス", "サンフランシスコ"),
        ("place", "リオデジャネイロ", "サンパウロ"),
        ("place", "マシュハド", "エスファハーン"),
        ("place", "テヘラン", "アンカラ"),
        ("place", "ハル", "リーズ"),
        ("place", "パークランド", "オーランド"),
        ("place", "フロリダ州", "ジョージア州"),
        ("place", "ノースカロライナ州", "サウスカロライナ州"),
        ("place", "北京", "上海"),
        ("place", "デリー", "ムンバイ"),
        ("place", "サイパン", "グアム"),
        ("place", "香港", "台湾"),
        ("org", "マギル大学", "トロント大学"),
        ("org", "ベルン大学", "チューリッヒ大学"),
        ("org", "ハーバード大学", "プリンストン大学"),
        ("org", "京都大学", "東京大学"),
        ("org", "NHS", "WHO"),
        ("org", "香港エクスプレス", "ジェットスター"),
        ("org", "ダブルツリー・ヒルトン", "マリオット"),
        ("org", "ロイヤル・ホテル", "プレミアインホテル"),
        ("org", "サイエンス誌", "ネイチャー誌"),
        ("person", "アンジェリーナ・ジョリー", "ジェニファー・アニストン"),
        ("person", "ブラッド・ピット", "レオナルド・ディカプリオ"),
        ("person", "ドナルド・トランプ", "ジョー・バイデン"),
        ("person", "安倍晋三", "麻生太郎"),
        ("person", "ハッサン・ロウハニ", "モハンマド・ハタミ"),
        ("person", "サンナ・マリン", "エルナ・ソルベルグ"),
        ("person", "マシュー・ロブソン", "ジェームズ・スミス"),
        ("person", "ジャスティン・ブラックマン", "マイケル・ジョンソン"),
        ("person", "ジェイムズ・P・アリソン", "デイヴィッド・ジュリアス"),
        ("person", "本庶佑", "山中伸弥"),
        ("brand", "マッカラン", "グレンフィディック"),
    ]

    # (original, replacement) -- both directions of each pair are tried;
    # applied only where 'original' occurs in both summary and article, and
    # 'replacement' is verified absent from the article.
    ANTONYM_PAIRS = [
        ("中断", "継続"),
        ("解除", "発動"),
        ("上昇", "下落"),
        ("認めた", "否定した"),
        ("増加", "減少"),
        ("成功", "失敗"),
        ("可決", "否決"),
        ("拒否", "受諾"),
        ("下方修正", "上方修正"),
        ("残留する", "撤退する"),
        ("拘束した", "釈放した"),
        ("存続する", "中止する"),
        ("義務付ける", "免除する"),
        ("拡大している", "縮小している"),
        ("妨げられる", "促進される"),
        ("回復する", "悪化する"),
        ("非難している", "擁護している"),
        ("参加した", "欠席した"),
        ("逮捕された", "釈放された"),
        ("負傷した", "回復した"),
        ("もたらした", "もたらさなかった"),
        ("含まれている", "含まれていない"),
        ("精度の高い", "精度の低い"),
        ("指定する", "指定しない"),
        ("無料で", "有料で"),
        ("邪魔すると", "促進すると"),
        ("認めるよう", "拒むよう"),
        ("悲しい日", "喜ばしい日"),
    ]

    # (original, replacement) -- meaning-preserving lexical swaps. No
    # article-absence check applies: these are the "must not move the
    # faithfulness score" control arm.
    PARAPHRASE_PAIRS = [
        ("と発表した", "と明らかにした"),
        ("ことが明らかになった", "ことが判明した"),
        ("と述べた", "と語った"),
        ("批判を浴びた", "非難を浴びた"),
        ("申し出た", "提案した"),
        ("表明した", "明言した"),
        ("分かった", "判明した"),
        ("発生した", "起きた"),
        ("参加した", "加わった"),
        ("親権を求め", "親権を要請し"),
        ("到着し、", "到着して、"),
        ("説明し、", "述べ、"),
    ]

    # ----------------------------------------------------------------
    # Number-swap machinery
    # ----------------------------------------------------------------

    NUM_SUFFIXES = ("万", "億", "ドル", "円", "ポンド", "クローナ", "人",
                     "日", "年", "月", "時", "分", "カ所", "か所", "%",
                     "パーセント", "件", "倍", "回", "冊", "点", "カ国")

    SUFFIXED_NUM_RE = re.compile(
        r"\d[\d,]*(?:\.\d+)?(?:万|億)?(?:" + "|".join(NUM_SUFFIXES) + r")"
    )
    AGE_NUM_RE = re.compile(r"(?<=（)\d+(?=）)")

    def find_number_spans(text):
        spans = []
        for m in SUFFIXED_NUM_RE.finditer(text):
            spans.append((m.start(), m.end(), m.group()))
        for m in AGE_NUM_RE.finditer(text):
            spans.append((m.start(), m.end(), m.group()))
        # de-dup by span
        seen = set()
        out = []
        for s in spans:
            key = (s[0], s[1])
            if key not in seen:
                seen.add(key)
                out.append(s)
        return out

    def split_number(tok):
        """Split a matched number token into (numeric_core, suffix)."""
        m = re.match(r"(\d[\d,]*(?:\.\d+)?)(.*)$", tok)
        return m.group(1), m.group(2)

    # Plausibility bounds for suffixes where an out-of-range value is
    # detectable as wrong WITHOUT consulting the article at all (there is no
    # 23rd month; a day-of-month above 31 does not exist). Restricting the
    # replacement to a value that is still *possible* on its face keeps the
    # corruption source-groundable rather than surface-rejectable.
    PLAUSIBLE_RANGE = {
        "月": (1, 12),
        "日": (1, 31),
    }

    def is_coupled_numeric_idiom(text, tok):
        """True if ANY occurrence of `tok` in `text` sits inside a fixed
        numeral+counter compound where two numerals are grammatically
        locked together -- e.g. N-泊-M-日 ("N nights, M days"), where M is
        conventionally N+1 and cannot be edited independently without
        producing a self-contradictory idiom (2泊20日). Since a global
        replace touches every occurrence of `tok`, if even one occurrence
        is coupled this way the whole opportunity is rejected rather than
        edited around."""
        for m in re.finditer(re.escape(tok), text):
            if m.start() > 0 and text[m.start() - 1] == "泊":
                return True
        return False

    def gen_number_replacement(tok, article_text, summary_text, rng):
        core, suffix = split_number(tok)
        if is_coupled_numeric_idiom(summary_text, tok):
            return None
        core_clean = core.replace(",", "")
        is_decimal = "." in core_clean
        deltas = [3, -3, 5, -5, 7, -7, 11, -2, 9, -9, 13, -4, 17, -6, 21]
        rng.shuffle(deltas)
        lo_hi = PLAUSIBLE_RANGE.get(suffix)
        if is_decimal:
            base = float(core_clean)
            candidates = [round(base + d * 0.1, 1) for d in deltas]
        else:
            base = int(core_clean)
            candidates = [base + d for d in deltas]
        for cand in candidates:
            if is_decimal:
                if cand <= 0:
                    continue
                cand_str = f"{cand:.1f}"
            else:
                if cand <= 0:
                    continue
                if lo_hi is not None and not (lo_hi[0] <= cand <= lo_hi[1]):
                    continue
                cand_str = str(cand)
            new_tok = cand_str + suffix
            if new_tok == tok:
                continue
            if new_tok not in article_text:
                return new_tok
        return None

    # ----------------------------------------------------------------
    # Opportunity collection
    # ----------------------------------------------------------------

    def make_item(kind, s, article_text, orig, repl, direction, meta):
        """Build one perturbation candidate, replacing EVERY occurrence of
        `orig` in the summary with `repl` (not just the first). A span that
        occurs more than once must be replaced consistently everywhere, or
        the perturbed text becomes internally self-contradictory (e.g. "he
        alone" ... "10 people") and is then detectable by noticing it
        contradicts ITSELF, with no reference to the article at all -- which
        defeats the purpose of a suite meant to measure SOURCE-grounded
        checking. Returns None if the pair cannot be safely applied (e.g.
        replacement text would itself reintroduce the original span)."""
        summary_text = s["summary"]
        assert orig in summary_text
        perturbed = summary_text.replace(orig, repl)
        if perturbed == summary_text:
            return None
        # global-replace correctness: every occurrence replaced, nothing missed
        assert perturbed == summary_text.replace(orig, repl)
        if orig in perturbed:
            # repl itself re-introduced orig as a substring (or orig was
            # left over some other way) -- reject rather than emit a
            # partially/self-inconsistently corrupted item.
            return None
        if direction == "drop":
            assert orig in article_text, f"{kind}: span_original not in article for {s['summary_id']}"
            assert repl not in article_text, f"{kind}: span_replacement leaked into article for {s['summary_id']}"
        return {
            "source_summary_id": s["summary_id"],
            "article_id": s["article_id"],
            "split": article_split[s["article_id"]],
            "type": kind,
            "original_text": summary_text,
            "perturbed_text": perturbed,
            "span_original": orig,
            "span_replacement": repl,
            "expected_faithfulness_direction": direction,
            "meta": meta,
        }

    number_opps = []
    entity_opps = []
    polarity_opps = []
    paraphrase_opps = []

    for s in pool:
        summary_text = s["summary"]
        article_text = articles[s["article_id"]]["text"]

        # --- number_swap ---
        seen_tokens = set()
        for (start, end, tok) in find_number_spans(summary_text):
            if tok in seen_tokens:
                continue
            seen_tokens.add(tok)
            if tok not in article_text:
                continue
            repl = gen_number_replacement(tok, article_text, summary_text, rng)
            if repl is None:
                continue
            item = make_item("number_swap", s, article_text, tok, repl,
                              "drop", {"note": "numeric token replaced (all occurrences); verified absent from article"})
            if item is not None:
                number_opps.append(item)

        # --- entity_swap ---
        for (category, orig, repl) in ENTITY_TABLE:
            if orig not in summary_text:
                continue
            if orig not in article_text:
                continue
            if repl in article_text:
                continue
            if repl in summary_text:
                continue
            item = make_item("entity_swap", s, article_text, orig, repl,
                              "drop", {"category": category})
            if item is not None:
                entity_opps.append(item)

        # --- polarity_reversal ---
        for (a, b) in ANTONYM_PAIRS:
            for (orig, repl) in ((a, b), (b, a)):
                if orig not in summary_text:
                    continue
                if orig not in article_text:
                    continue
                if repl in article_text:
                    continue
                item = make_item("polarity_reversal", s, article_text, orig, repl,
                                  "drop", {"antonym_pair": [a, b]})
                if item is not None:
                    polarity_opps.append(item)

        # --- paraphrase_control ---
        for (orig, repl) in PARAPHRASE_PAIRS:
            if orig not in summary_text:
                continue
            item = make_item("paraphrase_control", s, article_text, orig, repl,
                              "unchanged", {"note": "meaning-preserving lexical substitution (all occurrences)"})
            if item is not None:
                paraphrase_opps.append(item)

    print(f"[opportunities found] number_swap={len(number_opps)} "
          f"entity_swap={len(entity_opps)} polarity_reversal={len(polarity_opps)} "
          f"paraphrase_control={len(paraphrase_opps)}")

    # ----------------------------------------------------------------
    # Selection: balance across articles, cap 3 perturbations / source summary
    # (cap applies across ALL types combined), target 25-40 per type.
    # ----------------------------------------------------------------

    def interleave_by_article(opps, rng):
        by_article = defaultdict(list)
        for o in opps:
            by_article[o["article_id"]].append(o)
        for lst in by_article.values():
            rng.shuffle(lst)
        article_ids = sorted(by_article.keys())
        rng.shuffle(article_ids)
        out = []
        i = 0
        remaining = True
        while remaining:
            remaining = False
            for aid in article_ids:
                lst = by_article[aid]
                if i < len(lst):
                    out.append(lst[i])
                    remaining = True
            i += 1
        return out

    summary_used = Counter()  # per-source-summary total across all types

    def select(opps, target_max, rng):
        ordered = interleave_by_article(opps, rng)
        chosen = []
        for o in ordered:
            sid = o["source_summary_id"]
            if summary_used[sid] >= MAX_PER_SUMMARY:
                continue
            chosen.append(o)
            summary_used[sid] += 1
            if len(chosen) >= target_max:
                break
        return chosen

    # Process types in an order that gives the SCARCE types (polarity_reversal,
    # paraphrase_control -- few genuine opportunities exist in the pool) first
    # claim on the per-summary budget. number_swap and entity_swap have a
    # large surplus of opportunities (88 and 91 respectively, versus a target
    # of at most 40), so they can route around whichever source summaries the
    # scarce types already consumed.
    selected_polarity = select(polarity_opps, TARGET_MAX, rng)
    selected_paraphrase = select(paraphrase_opps, TARGET_MAX, rng)
    selected_entity = select(entity_opps, TARGET_MAX, rng)
    selected_number = select(number_opps, TARGET_MAX, rng)

    all_selected = {
        "polarity_reversal": selected_polarity,
        "entity_swap": selected_entity,
        "number_swap": selected_number,
        "paraphrase_control": selected_paraphrase,
    }

    # ----------------------------------------------------------------
    # Verification pass
    # ----------------------------------------------------------------

    print("\n[verification]")
    all_ok = True
    n_checked = 0
    check_counts = Counter()  # per-check pass counts, for reporting
    for kind, items in all_selected.items():
        for it in items:
            n_checked += 1
            article_text = articles[it["article_id"]]["text"]
            orig = it["span_original"]
            repl = it["span_replacement"]
            ot, pt = it["original_text"], it["perturbed_text"]
            is_drop = it["expected_faithfulness_direction"] == "drop"

            # check: perturbed_text differs from original_text
            if ot != pt:
                check_counts["differs_from_original"] += 1
            else:
                print(f"  FAIL {kind} {it['source_summary_id']}: perturbed_text == original_text")
                all_ok = False

            # check: perturbed_text is EXACTLY original_text with every
            # occurrence of span_original replaced by span_replacement
            # (global replace, not a partial/first-occurrence edit)
            if pt == ot.replace(orig, repl):
                check_counts["global_replace_exact"] += 1
            else:
                print(f"  FAIL {kind} {it['source_summary_id']}: perturbed_text is not "
                      f"exactly original_text with every occurrence of span_original replaced")
                all_ok = False

            # check: no held-out article leaked in
            if it["article_id"] not in heldout_articles:
                check_counts["no_heldout"] += 1
            else:
                print(f"  FAIL {kind} {it['source_summary_id']}: held-out article leaked in")
                all_ok = False

            if is_drop:
                # check: span_original DOES appear in the article
                if orig in article_text:
                    check_counts["drop_orig_in_article"] += 1
                else:
                    print(f"  FAIL {kind} {it['source_summary_id']}: span_original not in article")
                    all_ok = False

                # check: span_replacement does NOT appear anywhere in the article
                if repl not in article_text:
                    check_counts["drop_repl_absent_from_article"] += 1
                else:
                    print(f"  FAIL {kind} {it['source_summary_id']}: span_replacement found in article")
                    all_ok = False

                # check: span_original does NOT appear anywhere in perturbed_text
                # -- i.e. the corruption is applied consistently everywhere it
                # occurs, so the item cannot be caught by noticing it
                # contradicts ITSELF instead of the source.
                if orig not in pt:
                    check_counts["drop_orig_absent_from_perturbed"] += 1
                else:
                    print(f"  FAIL {kind} {it['source_summary_id']}: span_original still "
                          f"present in perturbed_text (partial/self-inconsistent replacement)")
                    all_ok = False

                # check: the replacement value is semantically POSSIBLE on
                # its face (there is no 23rd month; a day-of-month above 31
                # does not exist), and the edited numeral is not part of a
                # fixed numeral+counter idiom (N-泊-M-日) that a reader can
                # reject as self-contradictory without ever consulting the
                # article. This is the same confound as check [6] --
                # "detectable as wrong without source-grounded checking" --
                # arriving via surface plausibility instead of internal
                # self-contradiction.
                if kind == "number_swap":
                    plausible = True
                    m = re.match(r"^(\d+)(月|日)$", repl)
                    if m:
                        val, suf = int(m.group(1)), m.group(2)
                        lo, hi = PLAUSIBLE_RANGE[suf]
                        if not (lo <= val <= hi):
                            plausible = False
                    if is_coupled_numeric_idiom(ot, orig):
                        plausible = False
                    if plausible:
                        check_counts["number_plausible"] += 1
                    else:
                        print(f"  FAIL {kind} {it['source_summary_id']}: replacement "
                              f"'{repl}' is not a semantically possible value "
                              f"(out-of-range month/day, or a coupled numeral+counter "
                              f"idiom such as N泊M日)")
                        all_ok = False

    print(f"  items checked: {n_checked}")
    print(f"  [1] differs_from_original: {check_counts['differs_from_original']}/{n_checked}")
    print(f"  [2] global_replace_exact (perturbed == original.replace(orig, repl)): "
          f"{check_counts['global_replace_exact']}/{n_checked}")
    print(f"  [3] no_heldout_article: {check_counts['no_heldout']}/{n_checked}")
    n_drop = sum(1 for items in all_selected.values() for it in items
                 if it["expected_faithfulness_direction"] == "drop")
    print(f"  [4] drop-type: span_original present in article: "
          f"{check_counts['drop_orig_in_article']}/{n_drop}")
    print(f"  [5] drop-type: span_replacement absent from article: "
          f"{check_counts['drop_repl_absent_from_article']}/{n_drop}")
    print(f"  [6] drop-type: span_original absent from perturbed_text "
          f"(no self-contradiction): {check_counts['drop_orig_absent_from_perturbed']}/{n_drop}")
    n_number_drop = sum(1 for items in all_selected.values() for it in items
                        if it["type"] == "number_swap"
                        and it["expected_faithfulness_direction"] == "drop")
    print(f"  [7] number_swap: replacement is a semantically possible value "
          f"(month in 1-12, day in 1-31, not inside a N泊M日 idiom): "
          f"{check_counts['number_plausible']}/{n_number_drop}")
    print(f"  all checks passed: {all_ok}")

    # ----------------------------------------------------------------
    # Assemble output rows
    # ----------------------------------------------------------------

    rows = []
    counters = {"type": Counter(), "split": Counter(), "type_split": Counter()}
    pid_counter = 0
    for kind in ("number_swap", "entity_swap", "polarity_reversal", "paraphrase_control"):
        for it in all_selected[kind]:
            pid_counter += 1
            pid = f"pert_{pid_counter:04d}_{kind}"
            row = {
                "perturbation_id": pid,
                "source_summary_id": it["source_summary_id"],
                "article_id": it["article_id"],
                "split": it["split"],
                "type": it["type"],
                "original_text": it["original_text"],
                "perturbed_text": it["perturbed_text"],
                "span_original": it["span_original"],
                "span_replacement": it["span_replacement"],
                "expected_faithfulness_direction": it["expected_faithfulness_direction"],
                "producer": PRODUCER,
            }
            rows.append(row)
            counters["type"][kind] += 1
            counters["split"][it["split"]] += 1
            counters["type_split"][(kind, it["split"])] += 1

    out_path = f"{RUNS_DIR}/perturbations.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\n[output] wrote {len(rows)} rows to {out_path}")
    print("\n[counts per type]")
    for kind in ("number_swap", "entity_swap", "polarity_reversal", "paraphrase_control"):
        n = counters["type"][kind]
        flag = "" if TARGET_MIN <= n <= TARGET_MAX else "  <-- outside 25-40 target"
        print(f"  {kind}: {n}{flag}")
    print("\n[counts per split]")
    for sp in ("exploration", "development"):
        print(f"  {sp}: {counters['split'][sp]}")
    print("\n[counts per type x split]")
    for kind in ("number_swap", "entity_swap", "polarity_reversal", "paraphrase_control"):
        for sp in ("exploration", "development"):
            print(f"  {kind} / {sp}: {counters['type_split'][(kind, sp)]}")

    n_distinct_summaries = len({r["source_summary_id"] for r in rows})
    max_per_summary_actual = max(Counter(r["source_summary_id"] for r in rows).values()) if rows else 0
    print(f"\n[cap check] distinct source summaries perturbed: {n_distinct_summaries}; "
          f"max perturbations from one source summary: {max_per_summary_actual} "
          f"(cap={MAX_PER_SUMMARY})")

    held_out_present = any(r["article_id"] in heldout_articles for r in rows)
    print(f"[held-out check] any held-out article present: {held_out_present}")

    # ----------------------------------------------------------------
    # Report
    # ----------------------------------------------------------------

    report_lines = []
    report_lines.append("# Perturbation suite report\n")
    report_lines.append(f"Seed: {SEED}. Source pool: arm in "
                         "{abstractive_undetermined, reference}, articles in "
                         "exploration+development splits only (never held-out).\n")
    report_lines.append(f"Pool size: {len(pool)} source summaries across "
                         f"{len({s['article_id'] for s in pool})} articles.\n")
    report_lines.append(f"Total perturbations generated: {len(rows)}.\n")

    report_lines.append("## Counts per type\n")
    report_lines.append("| type | count | in [25,40]? |")
    report_lines.append("|---|---|---|")
    for kind in ("number_swap", "entity_swap", "polarity_reversal", "paraphrase_control"):
        n = counters["type"][kind]
        ok = "yes" if TARGET_MIN <= n <= TARGET_MAX else "NO"
        report_lines.append(f"| {kind} | {n} | {ok} |")
    report_lines.append("")
    n_pol = counters["type"]["polarity_reversal"]
    if n_pol < TARGET_MIN:
        report_lines.append(
            f"**Note on polarity_reversal ({n_pol} < {TARGET_MIN}):** this is a genuine "
            "data ceiling, not a selection-code artifact. Every antonym-pair direction "
            "in the table below was checked against every pool summary; "
            f"{n_pol} is the total count of (summary, antonym pair) matches where the "
            "ORIGINAL form is verbatim in both the summary and the article, and the "
            "REPLACEMENT is verbatim absent from the article -- i.e. it is literally "
            "every valid opportunity this pool contains under the rule the task "
            "specifies, not a sample of a larger set. Reaching 25+ would require either "
            "relaxing the verbatim-match rule (weakening ground truth) or fabricating "
            "less-grounded antonym pairs to force matches, both of which this suite "
            "avoids. This scarcity itself corroborates `runs/evidence_log.md`'s own "
            "observation that polarity reversal was the rarest corruption type found "
            "during exploration ('Two instances').")
        report_lines.append("")

    report_lines.append("## Counts per split\n")
    report_lines.append("| split | count |")
    report_lines.append("|---|---|")
    for sp in ("exploration", "development"):
        report_lines.append(f"| {sp} | {counters['split'][sp]} |")
    report_lines.append("")

    report_lines.append("## Counts per type x split\n")
    report_lines.append("| type | exploration | development |")
    report_lines.append("|---|---|---|")
    for kind in ("number_swap", "entity_swap", "polarity_reversal", "paraphrase_control"):
        e = counters["type_split"][(kind, "exploration")]
        d = counters["type_split"][(kind, "development")]
        report_lines.append(f"| {kind} | {e} | {d} |")
    report_lines.append("")

    report_lines.append("## Verification results\n")
    report_lines.append(f"- All checks passed: **{all_ok}** ({n_checked} items checked)")
    report_lines.append(f"- Distinct source summaries perturbed: {n_distinct_summaries}")
    report_lines.append(f"- Max perturbations from a single source summary: "
                         f"{max_per_summary_actual} (cap = {MAX_PER_SUMMARY})")
    report_lines.append(f"- Held-out article present in output: **{held_out_present}** "
                         "(must be False)")
    report_lines.append(f"- [1] perturbed_text differs from original_text: "
                         f"{check_counts['differs_from_original']}/{n_checked}")
    report_lines.append(f"- [2] perturbed_text is EXACTLY original_text with EVERY "
                         f"occurrence of span_original replaced by span_replacement "
                         f"(global replace, not a first-occurrence-only edit): "
                         f"{check_counts['global_replace_exact']}/{n_checked}")
    report_lines.append(f"- [3] no held-out article present: "
                         f"{check_counts['no_heldout']}/{n_checked}")
    report_lines.append(f"- [4] drop-type items where span_original is verified PRESENT "
                         f"in the article: {check_counts['drop_orig_in_article']}/{n_drop}")
    report_lines.append(f"- [5] drop-type items where span_replacement is verified "
                         f"ABSENT from the article: "
                         f"{check_counts['drop_repl_absent_from_article']}/{n_drop}")
    report_lines.append(f"- [6] drop-type items where span_original is verified ABSENT "
                         f"from perturbed_text, i.e. the corruption was applied to EVERY "
                         f"occurrence so the item cannot be caught by noticing it "
                         f"contradicts itself instead of the source: "
                         f"{check_counts['drop_orig_absent_from_perturbed']}/{n_drop}")
    report_lines.append(f"- [7] number_swap items where the replacement is a "
                         f"semantically POSSIBLE value on its face (month in 1-12, "
                         f"day-of-month in 1-31, and not inside a fixed N泊M日 "
                         f"numeral+counter idiom): "
                         f"{check_counts['number_plausible']}/{n_number_drop}")
    report_lines.append("")
    report_lines.append("**Plausibility constraint on number_swap replacements.** Two "
                         "items in an earlier run were detectable as wrong WITHOUT "
                         "consulting the article at all: `2泊3日` -> `2泊20日` (the "
                         "night/day counts in this fixed idiom are grammatically "
                         "coupled, so 20 days after 2 nights is self-evidently wrong) "
                         "and `2月14日` -> `23月14日` (there is no 23rd month). Both are "
                         "the same confound as the multi-occurrence issue above, arriving "
                         "by a different route: a judge could reject either on surface "
                         "plausibility alone and never do source-grounded checking, which "
                         "would inflate recall on exactly the metric this suite exists to "
                         "measure. `gen_number_replacement()` now (a) restricts any "
                         "`月`-suffixed replacement to 1-12 and any `日`-suffixed "
                         "replacement to 1-31, and (b) rejects the opportunity outright "
                         "(`is_coupled_numeric_idiom()`) if the numeral sits immediately "
                         "after `泊`, rather than trying to compute a jointly-consistent "
                         "replacement. Check [7] confirms every number_swap item in the "
                         "final output satisfies both constraints.")
    report_lines.append("")
    report_lines.append("**Multi-occurrence spans are replaced globally, not just at "
                         "the first occurrence.** A span that occurs more than once in a "
                         "summary (e.g. a count repeated in two sentences) was originally "
                         "replaced at only one location, which could leave the original "
                         "value still present elsewhere in the perturbed text -- e.g. "
                         "'he alone' in one clause and 'a group of 10' in another. Such "
                         "an item is internally self-contradictory and can be flagged by "
                         "noticing it disagrees with ITSELF, with no reference to the "
                         "article at all. Since this suite exists specifically to measure "
                         "whether a judge does SOURCE-grounded checking, an "
                         "internally-inconsistent item would let a judge score well via a "
                         "cheaper route than actually consulting the article, inflating "
                         "the very recall metric the suite is meant to measure. "
                         "`make_item()` therefore replaces every occurrence of "
                         "`span_original` in one pass (`str.replace`, unbounded count) "
                         "and check [6] above confirms none remain.")
    report_lines.append("")

    report_lines.append("## Entity substitution table used\n")
    report_lines.append("| category | original | replacement |")
    report_lines.append("|---|---|---|")
    for (cat, orig, repl) in ENTITY_TABLE:
        report_lines.append(f"| {cat} | {orig} | {repl} |")
    report_lines.append("")

    report_lines.append("## Antonym table used (polarity_reversal)\n")
    report_lines.append("Both directions of each pair were tried; a direction is used "
                         "only when the ORIGINAL form appears in both the summary and "
                         "the article, and the REPLACEMENT form is absent from the "
                         "article.\n")
    report_lines.append("| pair A | pair B |")
    report_lines.append("|---|---|")
    for (a, b) in ANTONYM_PAIRS:
        report_lines.append(f"| {a} | {b} |")
    report_lines.append("")
    report_lines.append("Several pairs from the task brief's suggested list "
                         "(可決/否決, 成功/失敗, 上昇/下落, 認めた/否定した, 増加/減少, "
                         "解除/発動) did not occur in any pool summary's overlapping "
                         "text and therefore produced zero items; they remain in the "
                         "table for future pool growth. Pairs that DID fire came from "
                         "actually-occurring text: 下方修正/上方修正, 拘束した/釈放した, "
                         "残留する/撤退する, 存続する/中止する, 拒否/受諾, 中断/継続, "
                         "義務付ける/免除する, 拡大している/縮小している, "
                         "妨げられる/促進される, 回復する/悪化する, "
                         "非難している/擁護している, 参加した/欠席した, "
                         "逮捕された/釈放された, 負傷した/回復した, "
                         "もたらした/もたらさなかった, 指定する/指定しない, "
                         "精度の高い/精度の低い, 無料で/有料で, "
                         "邪魔すると/促進すると, 認めるよう/拒むよう, "
                         "悲しい日/喜ばしい日.\n")

    report_lines.append("## Paraphrase-control table used\n")
    report_lines.append("| original | meaning-preserving replacement |")
    report_lines.append("|---|---|")
    for (orig, repl) in PARAPHRASE_PAIRS:
        report_lines.append(f"| {orig} | {repl} |")
    report_lines.append("")
    report_lines.append("All pairs above were read individually and judged genuinely "
                         "meaning-preserving before inclusion (conservative by design: "
                         "per the task brief, a pair was skipped rather than included if "
                         "it could not be made cleanly non-factual-altering). Two pairs "
                         "were the mildest register shifts in the set and are flagged "
                         "here explicitly so a reader knows they were considered rather "
                         "than overlooked: **表明した→明言した** (\"stated\" -> \"stated "
                         "clearly/explicitly\" -- adds emphasis, not a new claim) and "
                         "**批判を浴びた→非難を浴びた** (\"drew criticism\" -> \"drew "
                         "condemnation\" -- a stronger register, but reports the same "
                         "underlying fact: negative public reaction occurred). Both were "
                         "judged to preserve the truth-value of the claim, unlike the "
                         "`polarity_reversal` pairs which invert it.")
    report_lines.append("")

    report_lines.append("## Coverage of the observed corruption taxonomy\n")
    report_lines.append("`runs/evidence_log.md` documents 6 observed corruption types. "
                         "This suite covers **3 of 6** programmatically:\n")
    report_lines.append("| taxonomy type | covered? | why |")
    report_lines.append("|---|---|---|")
    report_lines.append("| entity swap | yes | `entity_swap` — curated same-category "
                         "substitution table, verified absent from article |")
    report_lines.append("| number/date swap | yes | `number_swap` — regex-located "
                         "numeral+unit token, replacement verified absent from article |")
    report_lines.append("| polarity reversal | yes | `polarity_reversal` — curated "
                         "antonym table, verified absent from article |")
    report_lines.append("| fabricated quotation | **no** | requires GENERATING a novel "
                         "quotation attributed to a speaker; there is no source span to "
                         "substitute — a program can only rearrange or replace existing "
                         "spans, not invent plausible false speech. Doing this "
                         "mechanically-but-crudely (e.g. wrapping random text in "
                         "quote marks) would not produce a genuinely plausible fabricated "
                         "quote and risks being trivially detectable by surface form "
                         "alone, defeating the purpose of the suite. |")
    report_lines.append("| fabricated event | **no** | requires inventing a plausible "
                         "but unstated event (e.g. \"police confirmed arson, 2 "
                         "detained\") — there is no existing span in the source summary "
                         "to substitute against; this is generation, not substitution, "
                         "and would require a judgement call about what counts as "
                         "'plausible' that this deterministic tool cannot make. |")
    report_lines.append("| hallucinated status | **no** | e.g. a drug \"in Phase 3 "
                         "trials\" when trials failed — this requires synthesizing a "
                         "specific false status claim consistent with the topic, again "
                         "generation rather than substitution of an existing span. |")
    report_lines.append("")
    report_lines.append("**Honest limitation:** this suite therefore measures faithfulness "
                         "recall against 3 of 6 observed corruption types — the three "
                         "that are expressible as a verified span substitution. The "
                         "other three (fabricated quotation, fabricated event, "
                         "hallucinated status) are qualitatively different: they require "
                         "generating new false content rather than substituting a "
                         "verifiable replacement for an existing span, which is exactly "
                         "the property that let this suite avoid human/LLM judgement "
                         "of quality. A judge that passes this suite has not been shown "
                         "to catch fabrication or hallucination — only entity/number "
                         "swaps and polarity reversal. `polarity_reversal` is the most "
                         "load-bearing of the three covered types, since (per "
                         "`evidence_log.md`) it is undetectable by symbol-matching "
                         "(no entity or number changes) and was the corruption type "
                         "found hardest to catch by structural detectors during "
                         "exploration.")
    report_lines.append("")

    with open(f"{RUNS_DIR}/perturbation_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"\n[output] wrote report to {RUNS_DIR}/perturbation_report.md")

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
