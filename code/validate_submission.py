"""Validate the delivered scores.jsonl. Exit 1 on any failure."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=['faithfulness','coverage','coherence','selection']
def main():
    S={json.loads(l)['summary_id'] for l in open(f'{ROOT}/data/summaries.jsonl',encoding='utf-8')}
    sc=f'{ROOT}/submission/scores.jsonl'
    if not os.path.exists(sc): sc=f'{ROOT}/scores.jsonl'
    rows=[json.loads(l) for l in open(sc,encoding='utf-8')]
    bad=[]
    if len(rows)!=250: bad.append(f"expected 250 rows, got {len(rows)}")
    ids={r['summary_id'] for r in rows}
    if ids!=S: bad.append(f"summary_id set mismatch: {len(S-ids)} missing, {len(ids-S)} extra")
    if len(ids)!=len(rows): bad.append("duplicate summary_ids")
    for r in rows:
        for d in D:
            if not (isinstance(r[d],int) and 0<=r[d]<=4): bad.append(f"{r['summary_id']} {d}={r[d]} out of range")
        for f in ('within_article_rank','rank_coverage_first','rank_unweighted_sum'):
            if not (1<=r[f]<=5): bad.append(f"{r['summary_id']} {f}={r[f]} out of range")
        if r['score_sum']!=sum(r[d] for d in D): bad.append(f"{r['summary_id']} score_sum inconsistent")
    # guard against the stale-copy hazard: submission/runs must match runs/
    import glob, filecmp
    src=os.path.join(ROOT,'runs'); dst=os.path.join(ROOT,'submission','runs')
    if os.path.isdir(src) and os.path.isdir(dst):
        for f in glob.glob(os.path.join(src,'*.md')):
            b=os.path.join(dst,os.path.basename(f))
            if os.path.exists(b) and not filecmp.cmp(f,b,shallow=False):
                bad.append(f"stale copy: submission/runs/{os.path.basename(f)} differs from runs/")
    print(f"checked {len(rows)} rows")
    for b in bad[:10]: print("  FAIL:",b)
    print("OK — scores.jsonl valid" if not bad else f"{len(bad)} failure(s)")
    sys.exit(1 if bad else 0)
if __name__=='__main__': main()
