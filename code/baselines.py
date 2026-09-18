"""Two deterministic, model-free baseline scorers for the 250 candidate summaries.

Purpose: answer "does the expensive semantic judge add anything over cheap
signals?" Both baselines are pure surface-feature arithmetic -- no model call,
no fitting, no access to the arm labels. Baseline B is explicitly allowed to
read `reference_summary` (that is its point); Baseline A never looks at it.

Tuning discipline: every threshold and weight below was chosen by inspecting
ONLY the 10 development articles (runs/split.json -> splits.development).
The held-out and exploration articles were never used to pick a parameter.
Each constant's comment records the development-only evidence that produced
it (see runs/baselines_report.md for the full derivation and tables).

Usage:
    python3 code/baselines.py
writes runs/baselines.jsonl (250 rows, one per summary_id).
"""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_PATH = os.path.join(ROOT, "data", "articles.jsonl")
SUMMARIES_PATH = os.path.join(ROOT, "data", "summaries.jsonl")
OUT_PATH = os.path.join(ROOT, "runs", "baselines.jsonl")

PRODUCER = {"role": "builder", "model": "claude-sonnet-5", "agent": "builder", "run_kind": "primary"}

N_GRAM = 5
TERMINAL_PUNCT = set("。！？.!?」』")
SENTENCE_END_RE = re.compile(r"[。！？]")

# ---------------------------------------------------------------------------
# FROZEN PARAMETERS -- fixed on the 10 development articles, never touched
# after that. Development stats (n=50 candidates: 20 abstractive_undetermined,
# 12 reference, 10 lead_extract, 3 truncation, 3 misattached, 2 permutation):
#
#   copy_rate  abstractive_undetermined: 0.03-0.53   reference: 0.07-0.24
#              lead_extract: 0.95-1.00               truncation: 0.10-0.28
#              misattached: 0.00-0.01                permutation: 0.10
#   length     abstractive: 73-181   reference: 44-143   lead_extract: 126-252
#              truncation: 50-78     permutation: 56-101
#   terminal punctuation missing: truncation 3/3, every other arm 0/50-of-that-arm
# ---------------------------------------------------------------------------

# Baseline A -- copy-rate penalty band. lead_extract's dev minimum (0.95) sits
# far above the highest legitimate abstractive candidate (0.53), so 0.90 is a
# threshold with margin on both sides, not a boundary fit to the data.
COPY_HIGH = 0.90
# misattached dev max (0.01) sits just under the lowest legitimate abstractive
# candidate (0.03); 0.02 is the midpoint, again with margin on both sides.
COPY_LOW = 0.02

# Baseline A -- length band. Dev legitimate-length range across all non-degenerate
# arms is [44, 252] chars; padded by ~10% to avoid penalising the observed
# extremes themselves.
LEN_MIN = 40
LEN_MAX = 260

# Baseline A -- sentence-count band, same logic: dev legitimate range is [1, 4]
# sentences (lead_extract's 4-sentence outlier is the top of the legitimate
# range, truncation's 0-sentence candidates are the degenerate case this is
# meant to catch).
SENT_MIN = 1
SENT_MAX = 4

# Baseline A -- "front-loaded copy" rule (uses the position feature). On dev,
# every lead_extract candidate has mean matched-ngram position <= 0.116 with
# copy_rate >= 0.95; the highest copy_rate among legitimate (non-lead-extract)
# candidates with a front-loaded mean position was 0.42 (mean_pos 0.144-0.567
# for those). 0.85 / 0.15 sit strictly between the two groups with margin, and
# a minimum-match count avoids firing off 1-2 coincidental n-gram hits.
LEADPOS_COPY_THRESH = 0.85
LEAD_POS_THRESH = 0.15
MIN_MATCHES_FOR_POSITION = 5

# Baseline A -- additive penalty weights. Each is a fraction of the max score
# (1.0) and they sum to 1.0, so a candidate triggering every penalty at full
# severity bottoms out at 0. Relative sizes reflect how severe/reliable each
# dev-observed failure mode is: copy-rate extremes (lead_extract in full,
# misattached in full) are the strongest and cleanest dev signal, missing
# terminal punctuation is a clean deterministic truncation marker, length and
# front-loading are softer, secondary signals.
W_COPY = 0.40
W_PUNCT = 0.25
W_LEN = 0.15
W_LEADPOS = 0.20


# ---------------------------------------------------------------------------
# Shared n-gram machinery
# ---------------------------------------------------------------------------

def char_ngrams(s: str, n: int = N_GRAM):
    s = s.strip()
    if len(s) < n:
        return []
    return [s[i:i + n] for i in range(len(s) - n + 1)]


def article_ngram_index(article_text: str, n: int = N_GRAM):
    """First-occurrence position (0-1 normalised) of every distinct n-gram."""
    text = article_text.strip()
    alen = max(1, len(text))
    index = {}
    for i in range(len(text) - n + 1):
        g = text[i:i + n]
        if g not in index:
            index[g] = i / alen
    return index


def copy_rate_and_position(candidate: str, article_index: dict, n: int = N_GRAM):
    """Set-based precision of candidate n-grams found in the article, plus the
    mean normalised article-position of the matched n-grams (None if too few
    matches to be meaningful)."""
    cgrams = char_ngrams(candidate, n)
    if not cgrams:
        return 0.0, None, 0
    distinct = set(cgrams)
    matched_positions = [article_index[g] for g in distinct if g in article_index]
    cr = len(matched_positions) / len(distinct)
    n_match = len(matched_positions)
    mean_pos = sum(matched_positions) / n_match if n_match else None
    return cr, mean_pos, n_match


def ngram_f1(a: str, b: str, n: int = N_GRAM):
    """Set-based F1 between two texts' char n-grams. See report for why F1
    (not raw Jaccard) was chosen for Baseline B."""
    ga, gb = set(char_ngrams(a, n)), set(char_ngrams(b, n))
    if not ga and not gb:
        return 1.0
    if not ga or not gb:
        return 0.0
    inter = len(ga & gb)
    precision = inter / len(ga)
    recall = inter / len(gb)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def has_terminal_punct(s: str) -> bool:
    s = s.strip()
    return bool(s) and s[-1] in TERMINAL_PUNCT


def sentence_count(s: str) -> int:
    return len(SENTENCE_END_RE.findall(s))


# ---------------------------------------------------------------------------
# Baseline A -- structural heuristic
# ---------------------------------------------------------------------------

def _band_penalty(value, lo, hi):
    """0 inside [lo, hi]; ramps to 1 outside, scaled by distance relative to
    the nearer bound (so going twice as far below `lo` roughly doubles the
    penalty, capped at 1)."""
    if lo <= value <= hi:
        return 0.0
    if value < lo:
        return min(1.0, (lo - value) / max(1, lo))
    return min(1.0, (value - hi) / max(1, hi))


def baseline_a_score(candidate: str, article_index: dict):
    cr, mean_pos, n_match = copy_rate_and_position(candidate, article_index)
    term = has_terminal_punct(candidate)
    nsent = sentence_count(candidate)
    length = len(candidate.strip())

    # copy-rate extremes (near 1.0 = naive lead/verbatim copy, near 0 = no
    # textual relationship to the article at all, i.e. misattachment)
    if cr >= COPY_HIGH:
        copy_penalty = W_COPY * min(1.0, (cr - COPY_HIGH) / (1 - COPY_HIGH))
    elif cr <= COPY_LOW:
        copy_penalty = W_COPY * min(1.0, (COPY_LOW - cr) / COPY_LOW) if COPY_LOW > 0 else W_COPY
    else:
        copy_penalty = 0.0

    punct_penalty = 0.0 if term else W_PUNCT

    len_extremity = _band_penalty(length, LEN_MIN, LEN_MAX)
    sent_extremity = _band_penalty(nsent, SENT_MIN, SENT_MAX)
    length_penalty = W_LEN * max(len_extremity, sent_extremity)

    front_loaded = (
        n_match >= MIN_MATCHES_FOR_POSITION
        and cr >= LEADPOS_COPY_THRESH
        and mean_pos is not None
        and mean_pos <= LEAD_POS_THRESH
    )
    leadpos_penalty = W_LEADPOS if front_loaded else 0.0

    total_penalty = copy_penalty + punct_penalty + length_penalty + leadpos_penalty
    score = max(0.0, 1.0 - total_penalty)

    features = {
        "copy_rate": round(cr, 4),
        "mean_match_position": None if mean_pos is None else round(mean_pos, 4),
        "n_matched_ngrams": n_match,
        "has_terminal_punct": term,
        "n_sentences": nsent,
        "char_length": length,
        "front_loaded_flag": front_loaded,
        "penalty_copy": round(copy_penalty, 4),
        "penalty_punct": round(punct_penalty, 4),
        "penalty_length": round(length_penalty, 4),
        "penalty_leadpos": round(leadpos_penalty, 4),
    }
    return round(score, 4), features


# ---------------------------------------------------------------------------
# Baseline B -- reference similarity
# ---------------------------------------------------------------------------

def baseline_b_score(candidate: str, reference_summary: str):
    score = ngram_f1(candidate, reference_summary)
    return round(score, 4), {"ref_ngram_f1": round(score, 4)}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_split():
    with open(os.path.join(ROOT, "runs", "split.json"), encoding="utf-8") as f:
        split = json.load(f)
    article_to_split = {}
    for split_name, article_ids in split["splits"].items():
        for aid in article_ids:
            article_to_split[aid] = split_name
    return article_to_split


def main():
    articles = {a["article_id"]: a for a in load_jsonl(ARTICLES_PATH)}
    summaries = load_jsonl(SUMMARIES_PATH)
    article_to_split = load_split()

    article_index_cache = {}
    rows = []
    for s in summaries:
        aid = s["article_id"]
        article = articles[aid]
        if aid not in article_index_cache:
            article_index_cache[aid] = article_ngram_index(article["text"])
        a_score, a_features = baseline_a_score(s["summary"], article_index_cache[aid])
        b_score, b_features = baseline_b_score(s["summary"], article["reference_summary"])
        features = {**a_features, **b_features}
        rows.append({
            "summary_id": s["summary_id"],
            "article_id": aid,
            "split": article_to_split.get(aid, "unknown"),
            "baseline_a_score": a_score,
            "baseline_b_score": b_score,
            "features": features,
            "producer": PRODUCER,
        })

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"wrote {len(rows)} rows to {OUT_PATH}")
    unknown = [r["summary_id"] for r in rows if r["split"] == "unknown"]
    if unknown:
        print(f"WARNING: {len(unknown)} rows had no split assignment: {unknown[:5]}...")


if __name__ == "__main__":
    main()
