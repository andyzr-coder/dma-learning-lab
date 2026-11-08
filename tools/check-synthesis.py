"""Independent exhaustive checks for authored synthesis examples (no external EDA tool)."""
from itertools import product,combinations
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
bits=list(product([0,1],repeat=3))
F={0,1,2,5,6,7}
for i,(a,b,c) in enumerate(bits):
    f1=(not a and not b) or (b and not c) or (a and c)
    f2=(not a and not c) or (not b and c) or (a and b)
    assert f1==f2==(i in F)
P=['00-','0-0','-01','-10','1-1','11-']
def cover(pattern):return {i for i,t in enumerate(bits) if all(p=='-' or int(p)==b for p,b in zip(pattern,t))}
assert all(cover(p)<=F for p in P)
assert not any(set.union(*(cover(p) for p in sel))==F for sel in combinations(P,2))
assert sum(set.union(*(cover(p) for p in sel))==F for sel in combinations(P,3))==2
for a,b,c in bits:
    old=(a and b and c) or (a and b and not c) or (not a and b and c)
    optimized=(a and b) or (b and c)
    reduced=(a and b and not c) or (b and c)
    assert old==optimized==reduced
    c1=a and b;c2=a and c;h=(a and not b and c) or (a and b and not c)
    assert (c1 or c2 or h)==(c1 or h)==(c2 or h)
    if (a,b,c)==(1,1,1):assert not h
for a,b,c,d in product([0,1],repeat=4):
    f=(a and b) or (a and c) or (b and c) or (d and (a or b or c))
    z1=(a and b) or (a and c) or (b and c);z0=a or b or c
    assert f==(z1 or (z0 and d))

def bdd(order):
    unique={}
    def go(k,values):
        if k==3:return int((values['a'] and values['b']) or (not values['a'] and values['c']))
        v=order[k]
        lo=go(k+1,{**values,v:0});hi=go(k+1,{**values,v:1})
        if lo==hi:return lo
        key=(v,lo,hi)
        if key not in unique:unique[key]=len(unique)+2
        return unique[key]
    go(0,{})
    return len(unique)
assert bdd('abc')==3 and bdd('bca')==5

fsm={'A':[('B',0),('C',1)],'B':[('A',0),('C',1)],'C':[('D',0),('A',0)],'D':[('D',0),('B',1)]}
q={'X':[('X',0),('Y',1)],'Y':[('Z',0),('X',0)],'Z':[('Z',0),('X',1)]}
for n in range(1,11):
    for seq in product([0,1],repeat=n):
        a='A';b='X'
        for x in seq:
            a,ya=fsm[a][x];b,yb=q[b][x]
            assert ya==yb
enc={'X':(0,0),'Y':(0,1),'Z':(1,0)}
for s in q:
    q1,q0=enc[s]
    for x in [0,1]:
        d1=(not x) and (q1!=q0);d0=(not q1) and (not q0) and x;y=(not q0) and x
        target,expected_y=q[s][x]
        assert (int(d1),int(d0))==enc[target] and y==expected_y
for x in [0,1]:
    q1=q0=1
    assert not((not x) and(q1!=q0)) and not((not q1)and(not q0)and x) and not((not q0)and x)
modules=[]
for p in sorted((root/'content/modules').glob('0[1-7]-*.json')):
    m=json.loads(p.read_text(encoding='utf-8'));modules.append(m)
    assert len(m['sections'])>=5 and len(m['exercises'])==6
    assert len({s['id'] for s in m['sections']})==len(m['sections'])
    for e in m['exercises']:assert e['maxScore']==len(e['rubric'])
assert len(modules)==7
report={'status':'passed','checkedDate':'2026-11-08','scope':'Authored synthesis examples m01–m07; not original exam OCR correctness',
        'modules':7,'exercises':42,'checks':['QM six-PI example: exhaustive truth table, no two-row cover, exactly two three-row covers','Expand/reduce/remove examples: exhaustive 3-bit truth table; simultaneous-removal counterexample','Functional decomposition: all 16 original inputs agree','ROBDD MUX counts: 3 and 5 nonterminal nodes under stated variable orders, no complement edges','FSM original versus quotient: all sequences of length 1 through 10 agree','Encoded FSM: all legal state/input rows and unused-code recovery','JSON schema essentials, section identifiers, rubric point totals'],
        'command':'python tools/check-synthesis.py'}
(root/'qa').mkdir(exist_ok=True)
(root/'qa/synthesis-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: seven modules, 42 exercises, exhaustive QM/heuristic/decomposition checks, BDD counts 3/5, FSM traces through length 10 and all encoded transitions.')
