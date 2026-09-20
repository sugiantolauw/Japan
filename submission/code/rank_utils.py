"""Reusable ranking / agreement utilities for validating scorers against each other.

Pure Python (no numpy/scipy dependency) so it runs anywhere this repo's other
scripts run. Used by baselines.py at build time and by later validation code.
"""
from __future__ import annotations

import math
import random
from statistics import mean
from typing import Dict, Hashable, Iterable, List, Mapping, Sequence, Union


def _article_of(summary_id: str) -> str:
    """Derive article_id from a summary_id of the form '<article_id>_<suffix>'.

    article_ids in this dataset never contain underscores (verified against
    data/articles.jsonl), so a single rsplit is unambiguous.
    """
    return summary_id.rsplit("_", 1)[0]


def within_article_ranking(
    scores_by_summary_id: Mapping[str, float],
    article_of=None,
) -> Dict[str, List[List[str]]]:
    """Group summary_ids by article and order them best-to-worst by score.

    Returns {article_id: [group_1, group_2, ...]} where each group is a list
    of summary_ids tied at that rank (score-equal), ordered from the
    highest-scoring group to the lowest. Ties are preserved as multi-element
    groups rather than broken arbitrarily -- this dataset guarantees ties
    (byte-identical candidates sharing a reference), and collapsing them to a
    strict order would misrepresent the ranking.

    `article_of` may be supplied as a mapping summary_id -> article_id; if
    omitted, the article_id is derived from the summary_id prefix.
    """
    get_article = (lambda sid: article_of[sid]) if article_of is not None else _article_of

    by_article: Dict[str, List[str]] = {}
    for sid in scores_by_summary_id:
        by_article.setdefault(get_article(sid), []).append(sid)

    result: Dict[str, List[List[str]]] = {}
    for article_id, sids in by_article.items():
        sids_sorted = sorted(sids, key=lambda s: (-scores_by_summary_id[s], s))
        groups: List[List[str]] = []
        for sid in sids_sorted:
            score = scores_by_summary_id[sid]
            if groups and scores_by_summary_id[groups[-1][0]] == score:
                groups[-1].append(sid)
            else:
                groups.append([sid])
        result[article_id] = groups
    return result


def kendall_tau_b(ranking1: Sequence[float], ranking2: Sequence[float]) -> float:
    """Kendall's tau-b between two same-length, same-order sequences of scores.

    tau-a treats every non-strict-order pair as a plain discordance/concordance
    and has no correction for ties; with 8 articles in this dataset containing
    byte-identical candidates, ties are guaranteed on both the baseline side
    and (via the lexicographic rule) the judge side, so tau-a would understate
    agreement whenever both scorers correctly tie the same pair. tau-b removes
    pairs tied in either sequence from the denominator (the standard
    correction; see Kendall 1945), so a pair correctly tied by both scorers
    neither helps nor hurts the statistic.

    ranking1[i] and ranking2[i] must refer to the same item (e.g. two parallel
    lists of scores for the same summary_ids in the same order). Values can be
    raw scores or rank numbers -- only their relative order and ties matter.
    """
    n = len(ranking1)
    if len(ranking2) != n:
        raise ValueError("kendall_tau_b: sequences must be the same length")
    if n < 2:
        return float("nan")

    concordant = discordant = 0
    ties_only_1 = ties_only_2 = ties_both = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = ranking1[i] - ranking1[j]
            dy = ranking2[i] - ranking2[j]
            if dx == 0 and dy == 0:
                ties_both += 1
            elif dx == 0:
                ties_only_1 += 1
            elif dy == 0:
                ties_only_2 += 1
            elif (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1

    n0 = n * (n - 1) / 2
    n1 = n0 - ties_only_1 - ties_both  # pairs not tied in ranking1
    n2 = n0 - ties_only_2 - ties_both  # pairs not tied in ranking2
    denom = math.sqrt(n1 * n2)
    if denom == 0:
        return float("nan")
    return (concordant - discordant) / denom


def cluster_bootstrap_ci(
    per_article_values: Union[Mapping[Hashable, float], Iterable[float]],
    n: int = 10000,
    seed: int = 20260918,
) -> Dict[str, float]:
    """Mean and 95% percentile bootstrap CI, resampling ARTICLES.

    The five candidates within an article are not independent observations --
    several are literal transformations of one another (lead extract,
    truncation, permutation, misattached are all deterministic functions of
    the article or the reference). Resampling at the summary level would
    treat those as five independent draws and understate the interval.
    Resampling at the article level (with replacement, same number of
    articles each draw) respects the actual unit of independence.

    `per_article_values` is one already-aggregated number per article (e.g.
    a per-article mean score, or a per-article paired difference). Order does
    not matter; if a mapping is given its values are used.
    """
    vals = list(per_article_values.values()) if isinstance(per_article_values, Mapping) else list(per_article_values)
    m = len(vals)
    if m == 0:
        raise ValueError("cluster_bootstrap_ci: no article values given")

    point_mean = mean(vals)
    rng = random.Random(seed)
    boot_means = []
    for _ in range(n):
        sample = [vals[rng.randrange(m)] for _ in range(m)]
        boot_means.append(mean(sample))
    boot_means.sort()

    lo_idx = int(round(0.025 * (n - 1)))
    hi_idx = int(round(0.975 * (n - 1)))
    return {
        "mean": point_mean,
        "ci_lo": boot_means[lo_idx],
        "ci_hi": boot_means[hi_idx],
        "n_articles": m,
        "n_boot": n,
        "seed": seed,
    }
