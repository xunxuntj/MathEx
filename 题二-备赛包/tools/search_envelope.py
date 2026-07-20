"""Reproducible heuristic lower envelope; compare with clique-star upper bound.

If the found value equals the universal clique-star bound, the row is certified
exact. Rows with a gap remain explicitly labelled computational lower bounds.
"""
from __future__ import annotations
import argparse, itertools, json, math, random
from pathlib import Path

PATTERN={(0,1),(0,2),(0,3),(0,4),(5,6),(7,8)}

def tri_count(es,n):
    a=[[False]*n for _ in range(n)]
    for u,v in es:a[u][v]=a[v][u]=True
    return sum(a[i][j] and a[i][k] and a[j][k]
               for i in range(n) for j in range(i+1,n) for k in range(j+1,n))

def kk(m):
    r=1
    while (r+1)*r//2<=m:r+=1
    s=m-r*(r-1)//2
    return r*(r-1)*(r-2)//6+s*(s-1)//2

def search(n,m,restarts=3000,seed=20260720):
    rng=random.Random(seed+100*n+m)
    all_e=list(itertools.combinations(range(n),2)); free=[e for e in all_e if e not in PATTERN]
    q=m-len(PATTERN); best=set(PATTERN); bt=tri_count(best,n); target=kk(m)
    if q == 0:
        return bt,best,target
    if q == len(free):
        best=set(PATTERN)|set(free)
        return tri_count(best,n),best,target
    for z in range(restarts):
        cur=set(PATTERN)|set(rng.sample(free,q)); t=tri_count(cur,n)
        temp=2.0
        for it in range(1200):
            rem=rng.choice(tuple(cur-PATTERN)); add=rng.choice(tuple(set(free)-cur))
            nxt=(cur-{rem})|{add}; nt=tri_count(nxt,n); delta=nt-t
            if delta>=0 or rng.random()<math.exp(delta/max(temp,.03)):
                cur,t=nxt,nt
            temp*=.995
            if t>bt:
                best,bt=set(cur),t
                if bt==target:return bt,best,target
    return bt,best,target

def main():
    p=argparse.ArgumentParser();p.add_argument('n',type=int);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--restarts',type=int,default=3000);a=p.parse_args(); rows=[]
    for m in range(6,a.n*(a.n-1)//2+1):
        t,es,u=search(a.n,m,a.restarts)
        rows.append({'n':a.n,'m':m,'found_triangles':t,'universal_upper':u,
                     'certified':t==u,'edges':[list(e) for e in sorted(es)]})
        print(a.n,m,t,u,'exact' if t==u else 'gap',flush=True)
    a.out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
