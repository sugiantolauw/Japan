#!/usr/bin/env python3
"""Build the blind human-review packet for the held-out set.

Deterministic tooling only — this script makes no evaluative judgement about
summary quality. It selects a subset of held-out articles, anonymizes the
five candidate summaries per article behind per-article shuffled letters
(A-E), and writes:

  - runs/human_review_selection.json        (which articles were chosen, + seed)
  - annotations/packets/human_review.md     (the blind packet itself)
  - annotations/packets/human_review_template.json  (answer skeleton)
  - runs/human_review_keymap.json           (UNBLINDING key: letter -> summary_id)

Usage: python3 code/build_human_packet.py
"""
import json
import os
import random

SEED = 20260918
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARTICLES_PATH = os.path.join(ROOT, "data", "articles.jsonl")
SUMMARIES_PATH = os.path.join(ROOT, "data", "summaries.jsonl")
SPLIT_PATH = os.path.join(ROOT, "runs", "split.json")

SELECTION_OUT = os.path.join(ROOT, "runs", "human_review_selection.json")
PACKET_OUT = os.path.join(ROOT, "annotations", "packets", "human_review.md")
TEMPLATE_OUT = os.path.join(ROOT, "annotations", "packets", "human_review_template.json")
KEYMAP_OUT = os.path.join(ROOT, "runs", "human_review_keymap.json")

LETTERS = ["A", "B", "C", "D", "E"]


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    articles = {r["article_id"]: r for r in load_jsonl(ARTICLES_PATH)}

    summaries_by_article = {}
    for r in load_jsonl(SUMMARIES_PATH):
        summaries_by_article.setdefault(r["article_id"], []).append(r)

    with open(SPLIT_PATH, encoding="utf-8") as f:
        split = json.load(f)
    heldout = split["splits"]["heldout"]

    # 1. Select 10 of the 30 held-out article_ids, deterministically.
    sorted_ids = sorted(heldout)
    rng = random.Random(SEED)
    selected = rng.sample(sorted_ids, 10)

    selection_record = {
        "seed": SEED,
        "method": "sorted(splits.heldout) then random.Random(seed).sample(ids, 10)",
        "selected_article_ids": selected,
    }
    with open(SELECTION_OUT, "w", encoding="utf-8") as f:
        json.dump(selection_record, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 2/3. Build the blind packet.
    instructions = """# Human Review Packet — Japanese News Summaries

## Instructions

You will read 10 short Japanese news articles. Each is followed by five
candidate summaries, labelled A through E in a different, randomized order
for each article. The letter order carries no information — do not assume
A is always "first" in any meaningful sense.

For **each** article, please:

1. **Rank the 5 candidates from best to worst** by overall summary quality
   (accuracy, completeness, clarity, and appropriateness of content for a
   summary). Ties are allowed and expected — write your ranking like this:

       B > A = D > C > E

2. **Optionally flag any candidate(s) that contain a factual error** not
   supported by the article (e.g., a wrong number, date, name, or an event
   the article does not describe). List the letter(s), or leave blank if
   none.

3. **Record roughly how many minutes** the article took you to review.

Please do **articles 1 and 2 first**, then decide whether you'd like to
continue with the rest. There is no promised total time — go at whatever
pace feels right, and stop whenever you like.

Record your answers in the accompanying template file (one entry per
article: ranking, optional factual-error letters, and minutes).

---
"""

    keymap = {}
    template_entries = []
    packet_parts = [instructions]

    for idx, aid in enumerate(selected, start=1):
        article = articles[aid]
        cands = summaries_by_article[aid]
        # per-article seeded shuffle of candidate order -> letter assignment
        article_rng = random.Random(f"{SEED}:{aid}")
        shuffled = list(cands)
        article_rng.shuffle(shuffled)

        letter_map = {}
        section = [f"## Article {idx} (id: {aid})\n"]
        section.append(f"### Title\n\n{article['title']}\n")
        section.append(f"### Full text\n\n{article['text']}\n")
        section.append("### Candidate summaries\n")
        for letter, cand in zip(LETTERS, shuffled):
            letter_map[letter] = cand["summary_id"]
            section.append(f"**Candidate {letter}:**\n\n{cand['summary']}\n")
        section.append(
            "### Your ranking\n\n"
            "Ranking (e.g. `B > A = D > C > E`): ______________________\n\n"
            "Factual-error letters (optional, comma-separated): ______________________\n\n"
            "Minutes spent: ______________________\n"
        )
        packet_parts.append("\n".join(section))

        keymap[str(idx)] = {"article_id": aid, "letters": letter_map}
        template_entries.append({
            "article_no": idx,
            "article_id": aid,
            "ranking": "",
            "factual_error_letters": [],
            "minutes": None,
        })

    packet_text = "\n---\n\n".join(packet_parts)

    os.makedirs(os.path.dirname(PACKET_OUT), exist_ok=True)
    with open(PACKET_OUT, "w", encoding="utf-8") as f:
        f.write(packet_text)

    template = {
        "annotator": "human",
        "fresh_session": True,
        "saw_orchestrator_context": False,
        "articles": template_entries,
    }
    with open(TEMPLATE_OUT, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(KEYMAP_OUT, "w", encoding="utf-8") as f:
        json.dump({"seed": SEED, "mapping": keymap}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Selected article_ids: {selected}")
    print(f"Packet written to {PACKET_OUT} ({len(packet_text)} chars)")
    print(f"Template written to {TEMPLATE_OUT}")
    print(f"Keymap written to {KEYMAP_OUT}")
    print(f"Selection written to {SELECTION_OUT}")


if __name__ == "__main__":
    main()
