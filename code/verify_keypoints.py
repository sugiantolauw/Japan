"""Verify runs/keypoints/<article_id>.json files.

Checks, for every keypoints file:
  - the article_id exists in data/articles.jsonl
  - there are 3-6 units
  - every excerpt occurs verbatim in that article's `text` field
    (exact substring match after normalising whitespace)
  - every unit's `unit` text is at least 15 characters long (a real
    proposition, not a bare topic label)
  - exactly one unit per article has `is_main_event: true`

Usage: python3 code/verify_keypoints.py
"""
import json
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_PATH = os.path.join(ROOT, "data", "articles.jsonl")
KEYPOINTS_DIR = os.path.join(ROOT, "runs", "keypoints")


def normalize(s: str) -> str:
    # Collapse all whitespace (including full-width spaces) to single spaces, strip ends.
    s = s.replace("　", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def load_articles():
    articles = {}
    with open(ARTICLES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            articles[obj["article_id"]] = obj
    return articles


def main():
    articles = load_articles()
    failures = []
    checked = 0

    paths = sorted(glob.glob(os.path.join(KEYPOINTS_DIR, "*.json")))
    for path in paths:
        with open(path, encoding="utf-8") as f:
            try:
                obj = json.load(f)
            except json.JSONDecodeError as e:
                failures.append(f"{path}: invalid JSON ({e})")
                continue

        checked += 1
        aid = obj.get("article_id")
        if not aid:
            failures.append(f"{path}: missing article_id")
            continue
        if aid not in articles:
            failures.append(f"{path}: article_id {aid!r} not found in articles.jsonl")
            continue

        units = obj.get("units")
        if not isinstance(units, list):
            failures.append(f"{path}: units is not a list")
            continue
        n = len(units)
        if not (3 <= n <= 6):
            failures.append(f"{path}: unit count {n} out of range [3,6]")

        text_norm = normalize(articles[aid]["text"])

        main_event_count = 0
        for i, unit in enumerate(units):
            excerpt = unit.get("excerpt", "")
            if not excerpt:
                failures.append(f"{path}: unit[{i}] has empty excerpt")
                continue
            excerpt_norm = normalize(excerpt)
            if excerpt_norm not in text_norm:
                failures.append(
                    f"{path}: unit[{i}] excerpt not verbatim in article text: {excerpt!r}"
                )

            unit_text = unit.get("unit", "")
            if len(normalize(unit_text)) < 15:
                failures.append(
                    f"{path}: unit[{i}] unit text shorter than 15 chars: {unit_text!r}"
                )

            if unit.get("is_main_event") is True:
                main_event_count += 1

        if main_event_count != 1:
            failures.append(
                f"{path}: expected exactly 1 unit with is_main_event=true, found {main_event_count}"
            )

    print(f"Checked {checked} keypoints files.")
    if failures:
        print(f"FAILURES: {len(failures)}")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
