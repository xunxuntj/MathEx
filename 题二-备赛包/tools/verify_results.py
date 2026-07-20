"""Structural verification of saved candidate envelopes."""
import itertools, json
from pathlib import Path

base=next(Path('.').glob('*/search-n9.json')).parent
F={(0,1),(0,2),(0,3),(0,4),(5,6),(7,8)}
for n in (9,10):
    rows=json.loads((base/f'search-n{n}.json').read_text(encoding='utf-8'))
    last=-1
    for row in rows:
        es={tuple(e) for e in row['edges']}
        assert F<=es and len(es)==row['m']
        t=sum(all(tuple(sorted(e)) in es for e in itertools.combinations(tri,2))
              for tri in itertools.combinations(range(n),3))
        assert t==row['found_triangles'] and t<=row['universal_upper'] and t>=last
        assert row['certified']==(t==row['universal_upper'])
        last=t
    assert rows[-1]['found_triangles']==n*(n-1)*(n-2)//6
    print(f'n={n}: {len(rows)} rows verified; final triangles={last}')
