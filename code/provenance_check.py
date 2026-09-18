"""Verify that every output row under runs/ and annotations/ was produced by the
actor assigned in DEFINITION_OF_DONE.md. Exit 1 on any violation.

Usage: python3 code/provenance_check.py
"""
import json, sys, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {                              # role -> allowed producer models
    "judge":     {"primary": {"claude-sonnet-5"},
                  "repeat":  {"claude-sonnet-5"},
                  "cross_tier": {"claude-opus-5"}},
    "keypoints": {"primary": {"claude-sonnet-5"}},
}
FORBIDDEN_MODELS = {"claude-fable-5-1", "claude-fable-5", "claude-opus-5"}  # the orchestrator tier
ANNOT_DIRS = {"annotations/gpt": "gpt", "annotations/human": "human"}

def rows(path):
    with open(path, encoding="utf-8") as f:
        if path.endswith(".jsonl"):
            for i, line in enumerate(f, 1):
                if line.strip(): yield i, json.loads(line)
        else:
            yield 1, json.load(f)

bad = 0
def fail(msg):
    global bad; bad += 1; print("FAIL", msg)

# Model-generated outputs only. Deterministic derived data under runs/ (arm census,
# selections, keymaps) is reproducible from its script and carries no producer stamp;
# requiring one there conflates "who ran a script" with "which model made a judgement".
MODEL_DIRS = ("runs/judge", "runs/judge_repeat", "runs/judge_crosstier", "runs/keypoints")
paths = [q for d in MODEL_DIRS
           for q in glob.glob(os.path.join(ROOT, d, "**", "*.json*"), recursive=True)]
for path in paths:
    for ln, r in rows(path):
        p = r.get("producer")
        if not p: fail(f"{path}:{ln} missing producer"); continue
        role, model, kind = p.get("role"), p.get("model"), p.get("run_kind", "primary")
        if role not in ALLOWED: fail(f"{path}:{ln} unknown role {role!r}"); continue
        ok = ALLOWED[role].get(kind, set())
        if model not in ok: fail(f"{path}:{ln} role={role} run_kind={kind} model={model!r} not in {sorted(ok)}")
        if model in FORBIDDEN_MODELS and kind != "cross_tier":
            fail(f"{path}:{ln} orchestrator-tier model produced a {role} row")

# external annotations
for sub, expect in ANNOT_DIRS.items():
    for path in glob.glob(os.path.join(ROOT, sub, "*.json*")):
        for ln, r in rows(path):
            a = str(r.get("annotator", ""))
            if not a.startswith(expect): fail(f"{path}:{ln} annotator={a!r}, expected prefix {expect!r}")
            if r.get("fresh_session") is not True: fail(f"{path}:{ln} fresh_session must be true")
            if r.get("saw_orchestrator_context") is not False: fail(f"{path}:{ln} saw_orchestrator_context must be false")

print("OK — no provenance violations" if not bad else f"{bad} violation(s)")
sys.exit(1 if bad else 0)
