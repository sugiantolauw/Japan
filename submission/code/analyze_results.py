"""Recompute every table reported in report.md. Run: python3 code/analyze_results.py"""
import json, os, re, math, statistics as st
from collections import defaultdict, Counter
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=['faithfulness','coverage','coherence','selection']
def wilson(k,n,z=1.96):
    if not n: return (0,1)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=(z/d)*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return max(0,c-h),min(1,c+h)
S={s['summary_id']:s for s in (json.loads(l) for l in open(f'{ROOT}/data/summaries.jsonl',encoding='utf-8'))}
census=json.load(open(f'{ROOT}/runs/arm_census.json'))
J={};batch={}
for i in range(5):
    for l in open(f'{ROOT}/runs/judge/all_b{i}.jsonl',encoding='utf-8'):
        r=json.loads(l);J[r['summary_id']]=r;batch[r['summary_id']]=i
P={r['perturbation_id']:r for r in (json.loads(l) for l in open(f'{ROOT}/runs/perturbations.jsonl',encoding='utf-8'))}
JP={}
for f in ('pert_a','pert_b'):
    for l in open(f'{ROOT}/runs/judge/{f}.jsonl',encoding='utf-8'):
        r=json.loads(l);JP[r['perturbation_id']]=r
arts=defaultdict(list)
for k in J: arts[S[k]['article_id']].append(k)
date_re=re.compile(r'^\d+(日|月|年)$')
def strict(p):
    r,q=JP[p],P[p]
    return any(c['status']=='CONTRADICTED' and q['span_replacement'] in c['claim'] for c in r['claims'])

print("\n== detection on labels surviving the semantic audit (dates excluded, see E6) ==")
groups={'entity swap':[k for k,v in P.items() if v['type']=='entity_swap'],
 'quantity swap':[k for k,v in P.items() if v['type']=='number_swap' and not date_re.match(v['span_original'])],
 'polarity reversal':[k for k,v in P.items() if v['type']=='polarity_reversal']}
tot=sum(groups.values(),[])
for g,ids in list(groups.items())+[('ALL (audited)',tot)]:
    k=sum(strict(i) for i in ids); lo,hi=wilson(k,len(ids))
    print(f"  {g:20s} {k:>3}/{len(ids):<3} = {k/len(ids):>4.0%}  CI [{lo:.0%},{hi:.0%}]")
dates=[k for k,v in P.items() if v['type']=='number_swap' and date_re.match(v['span_original'])]
print(f"  date swap            WITHDRAWN (n={len(dates)}, labels invalid - see KNOWN_ERRORS E6)")

print("\n== paraphrase controls: claim-label vs score stability ==")
ctl=[k for k,v in P.items() if v['type']=='paraphrase_control']
print(f"  controls raising a contradiction naming the edit: {sum(strict(k) for k in ctl)}/{len(ctl)}")
d=[JP[k]['faithfulness']-J[P[k]['source_summary_id']]['faithfulness'] for k in ctl if P[k]['source_summary_id'] in J]
print(f"  faithfulness unchanged vs own original: {sum(x==0 for x in d)}/{len(d)}  (up {sum(x>0 for x in d)}, down {sum(x<0 for x in d)})")

print("\n== mean score by arm (all 250) ==")
for a,rows in sorted(((a,[J[k] for k in J if census[k]==a]) for a in set(census.values())),key=lambda x:-len(x[1])):
    print(f"  {a:26s} n={len(rows):>3} " + " ".join(f"{d_[:5]}={st.mean(r[d_] for r in rows):.2f}" for d_ in D))

print("\n== first place by rule — BOTH definitions stated explicitly ==")
RU={'frozen (faith>cov>coh>sel)':lambda k:tuple(J[k][d] for d in D),
 'coverage-first':lambda k:tuple(J[k][d] for d in ['coverage','faithfulness','coherence','selection']),
 'unweighted sum':lambda k:(sum(J[k][d] for d in D),)}
for name,rule in RU.items():
    inc=Counter();sole=Counter();tied=0
    for aid,ks in arts.items():
        top=max(rule(k) for k in ks); win=[k for k in ks if rule(k)==top]
        for k in win: inc[census[k]]+=1
        if len(win)==1: sole[census[win[0]]]+=1
        else: tied+=1
    fmt=lambda c:", ".join(f"{a.replace('_undetermined','')}={n}" for a,n in c.most_common(3))
    print(f"  {name}\n     rank-1 incl. ties: {fmt(inc)}\n     sole winner      : {fmt(sole)}   (articles tied at first: {tied})")

print("\n== expected structural orderings (not guarantees - see report) ==")
def pairs(ks,a,b): return [(x,y) for x in ks if census[x]==a for y in ks if census[y]==b]
def anyvs(ks): return [(x,y) for x in ks if census[x]!='misattached' for y in ks if census[y]=='misattached']
for nm,pf in [("reference > its truncation",lambda ks:pairs(ks,'reference','truncation')),
              ("reference > its permutation",lambda ks:pairs(ks,'reference','permutation')),
              ("anything > misattached",anyvs)]:
    for rn,rule in RU.items():
        R={};
        for aid,ks in arts.items():
            for k in ks: R[k]=rule(k)
        t=o=0
        for aid,ks in arts.items():
            for x,y in pf(ks): t+=1; o+= R[x]>R[y]
        if t: print(f"  {nm:30s} {rn:26s} {o}/{t} = {o/t:.0%}")

print("\n== rater effect: arm-conditional mean faithfulness by batch ==")
for arm in ['reference','lead_extract','abstractive_undetermined','truncation','permutation','misattached']:
    ms=[st.mean([J[k]['faithfulness'] for k in J if census[k]==arm and batch[k]==i]) if
        [k for k in J if census[k]==arm and batch[k]==i] else None for i in range(5)]
    got=[m for m in ms if m is not None]
    print(f"  {arm:26s} " + " ".join(f"{m:>5.1f}" if m is not None else "    -" for m in ms) + f"   spread {max(got)-min(got):.1f}")

print("\n== length correlation ==")
def corr(x,y):
    mx,my=st.mean(x),st.mean(y)
    n=sum((a-mx)*(b-my) for a,b in zip(x,y))
    dd=(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))**.5
    return n/dd if dd else 0
absid=[k for k in J if census[k]=='abstractive_undetermined']
for d_ in D:
    print(f"  {d_:14s} all={corr([len(S[k]['summary']) for k in J],[J[k][d_] for k in J]):+.2f}  "
          f"abstractive-only={corr([len(S[k]['summary']) for k in absid],[J[k][d_] for k in absid]):+.2f}")
