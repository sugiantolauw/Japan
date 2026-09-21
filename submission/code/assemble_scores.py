"""Rebuild submission/scores.jsonl from the saved judge verdicts. Deterministic."""
import json, os, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = ['faithfulness','coverage','coherence','selection']

def load():
    S={s['summary_id']:s for s in (json.loads(l) for l in open(f'{ROOT}/data/summaries.jsonl',encoding='utf-8'))}
    census=json.load(open(f'{ROOT}/runs/arm_census.json'))
    B={r['summary_id']:r for r in (json.loads(l) for l in open(f'{ROOT}/runs/baselines.jsonl',encoding='utf-8'))}
    J={};batch={}
    for i in range(5):
        for l in open(f'{ROOT}/runs/judge/all_b{i}.jsonl',encoding='utf-8'):
            r=json.loads(l); J[r['summary_id']]=r; batch[r['summary_id']]=i
    return S,census,B,J,batch

def ranks(J,arts,rule):
    """Competition ranking, ties share a rank."""
    out={}
    for aid,ks in arts.items():
        keyed=sorted(ks,key=rule,reverse=True); r=0; prev=None
        for i,k in enumerate(keyed):
            cur=rule(k)
            if cur!=prev: r=i+1; prev=cur
            out[k]=r
    return out

def main():
    S,census,B,J,batch=load()
    arts=defaultdict(list)
    for k in J: arts[S[k]['article_id']].append(k)
    frozen=ranks(J,arts,lambda k:tuple(J[k][d] for d in D))
    covf  =ranks(J,arts,lambda k:tuple(J[k][d] for d in ['coverage','faithfulness','coherence','selection']))
    summ  =ranks(J,arts,lambda k:(sum(J[k][d] for d in D),))
    rows=[]
    for sid in sorted(S):
        j=J[sid]
        rows.append({"summary_id":sid,"article_id":S[sid]['article_id'],
          **{d:j[d] for d in D},
          "within_article_rank":frozen[sid],"rank_coverage_first":covf[sid],
          "rank_unweighted_sum":summ[sid],"score_sum":sum(j[d] for d in D),
          "n_claims":len(j['claims']),
          "n_contradicted":sum(c['status']=='CONTRADICTED' for c in j['claims']),
          "n_unsupported":sum(c['status']=='UNSUPPORTED' for c in j['claims']),
          "structural_arm":census[sid],
          "baseline_a_score":B[sid]['baseline_a_score'],"baseline_b_score":B[sid]['baseline_b_score'],
          "judge_batch":batch[sid],"rationale":j['rationale']})
    out=f'{ROOT}/submission/scores.jsonl'
    if not os.path.isdir(f'{ROOT}/submission'): out=f'{ROOT}/scores.jsonl'
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,'w',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    print(f"wrote {out}: {len(rows)} rows")
if __name__=='__main__': main()
