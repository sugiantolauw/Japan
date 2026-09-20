#!/usr/bin/env python3
"""Validate judge output rows against the rubric's schema and evidence contract.

Checks, for every row in a judge jsonl file:
  - required fields are present
  - faithfulness/coverage/coherence/selection are integers in [0, 4]
  - every claim's `status` is one of the allowed labels
  - every non-null claim `evidence` string occurs verbatim (whitespace-normalised)
    in the article text (title + text) of the article that candidate belongs to

Usage:
    python3 verify_judge.py [path/to/judge_output.jsonl]

Default path: runs/judge/pilot.jsonl (relative to the repo root, i.e.
/home/user/japan).
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_PATH = REPO_ROOT / "data" / "articles.jsonl"
SUMMARIES_PATH = REPO_ROOT / "data" / "summaries.jsonl"
PERTURBATIONS_BLIND_PATH = REPO_ROOT / "runs" / "perturbations_blind.jsonl"
DEFAULT_JUDGE_PATH = REPO_ROOT / "runs" / "judge" / "pilot.jsonl"

# A row identifies its candidate with either 'summary_id' (resolved via
# data/summaries.jsonl) or 'perturbation_id' (resolved via
# runs/perturbations_blind.jsonl). Exactly one of the two id fields is
# required; the rest of REQUIRED_TOP_FIELDS is always required.
REQUIRED_TOP_FIELDS = [
    "claims", "faithfulness", "coverage",
    "coherence", "selection", "rationale", "producer",
]
ID_FIELDS = ("summary_id", "perturbation_id")
REQUIRED_CLAIM_FIELDS = ["claim", "status", "evidence"]
ALLOWED_STATUSES = {"SUPPORTED", "CONTRADICTED", "UNSUPPORTED", "AMBIGUOUS"}
SCORE_DIMS = ["faithfulness", "coverage", "coherence", "selection"]


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def load_article_text_by_id():
    articles = {}
    with open(ARTICLES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            aid = str(d["article_id"])
            combined = (d.get("title") or "") + "\n" + (d.get("text") or "")
            articles[aid] = normalize_ws(combined)
    return articles


def load_summary_to_article():
    mapping = {}
    with open(SUMMARIES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            mapping[d["summary_id"]] = str(d["article_id"])
    return mapping


def load_perturbation_to_article():
    mapping = {}
    if not PERTURBATIONS_BLIND_PATH.exists():
        return mapping
    with open(PERTURBATIONS_BLIND_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            mapping[d["perturbation_id"]] = str(d["article_id"])
    return mapping


def main():
    judge_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JUDGE_PATH

    articles = load_article_text_by_id()
    summary_to_article = load_summary_to_article()
    perturbation_to_article = load_perturbation_to_article()

    failures = []
    n_rows = 0
    n_claims = 0
    n_evidence_checked = 0

    with open(judge_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            n_rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                failures.append(f"line {line_no}: invalid JSON ({e})")
                continue

            # candidate id: exactly one of summary_id / perturbation_id required
            id_field = next((f for f in ID_FIELDS if row.get(f)), None)
            summary_id = row.get("summary_id")
            perturbation_id = row.get("perturbation_id")
            row_id = summary_id or perturbation_id

            if id_field is None:
                failures.append(f"line {line_no} (?): missing one of {ID_FIELDS}")

            # required top-level fields (id fields checked separately above)
            for field in REQUIRED_TOP_FIELDS:
                if field not in row:
                    failures.append(f"line {line_no} ({row_id or '?'}): missing field '{field}'")

            # score fields: integers 0-4
            for dim in SCORE_DIMS:
                if dim not in row:
                    continue
                val = row[dim]
                if not isinstance(val, int) or isinstance(val, bool):
                    failures.append(f"line {line_no} ({row_id}): {dim}={val!r} is not an integer")
                elif not (0 <= val <= 4):
                    failures.append(f"line {line_no} ({row_id}): {dim}={val} out of range [0,4]")

            # producer sanity (present, has expected keys) -- not over-strict
            producer = row.get("producer")
            if not isinstance(producer, dict):
                failures.append(f"line {line_no} ({row_id}): 'producer' is not an object")

            # resolve article text for this candidate, via whichever id field is present
            article_id = None
            if summary_id is not None:
                article_id = summary_to_article.get(summary_id)
                if article_id is None:
                    failures.append(f"line {line_no} ({row_id}): summary_id not found in {SUMMARIES_PATH.name}")
            elif perturbation_id is not None:
                article_id = perturbation_to_article.get(perturbation_id)
                if article_id is None:
                    failures.append(f"line {line_no} ({row_id}): perturbation_id not found in {PERTURBATIONS_BLIND_PATH.name}")

            if article_id is not None:
                article_text = articles.get(article_id)
                if article_text is None:
                    failures.append(f"line {line_no} ({row_id}): article_id {article_id} not found in {ARTICLES_PATH.name}")
            else:
                article_text = None

            claims = row.get("claims")
            if not isinstance(claims, list) or len(claims) == 0:
                failures.append(f"line {line_no} ({row_id}): 'claims' missing or empty")
                claims = []

            for ci, claim in enumerate(claims):
                n_claims += 1
                if not isinstance(claim, dict):
                    failures.append(f"line {line_no} ({row_id}): claim[{ci}] is not an object")
                    continue
                for field in REQUIRED_CLAIM_FIELDS:
                    if field not in claim:
                        failures.append(f"line {line_no} ({row_id}): claim[{ci}] missing field '{field}'")

                status = claim.get("status")
                if status not in ALLOWED_STATUSES:
                    failures.append(f"line {line_no} ({row_id}): claim[{ci}] status '{status}' not in {sorted(ALLOWED_STATUSES)}")

                evidence = claim.get("evidence")
                if evidence is not None:
                    n_evidence_checked += 1
                    if not isinstance(evidence, str):
                        failures.append(f"line {line_no} ({row_id}): claim[{ci}] evidence is not a string or null")
                    elif article_text is not None:
                        norm_ev = normalize_ws(evidence)
                        if norm_ev == "" or norm_ev not in article_text:
                            failures.append(
                                f"line {line_no} ({row_id}): claim[{ci}] evidence NOT FOUND verbatim in article "
                                f"{article_id}: {evidence!r}"
                            )

    print(f"Checked {n_rows} rows, {n_claims} claims, {n_evidence_checked} non-null evidence strings.")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for msg in failures:
            print(" -", msg)
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
