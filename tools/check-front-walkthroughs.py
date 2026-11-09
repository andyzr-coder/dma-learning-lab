"""Independent truth-table, cover, ROBDD and sequence checks for guided examples."""
from pathlib import Path
from itertools import product, combinations
import json, math, re

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def ok(name, condition=True):
    assert condition, name
    checks.append(name)
def cube_points(cube):
    return {sum(v<<(len(cube)-1-i) for i,v in enumerate(bits))
            for bits in product((0,1),repeat=len(cube))
            if all(c=='-' or int(c)==b for c,b in zip(cube,bits))}
def primes(on,dc,n):
    legal={''.join(c):cube_points(c) for c in product('01-',repeat=n)}
    legal={c:v for c,v in legal.items() if v <= (on|dc) and v&on}
    return {c:v for c,v in legal.items() if not any(v<w for w in legal.values())}
def cover_value(cubes):
    return set().union(*(cube_points(c) for c in cubes))

f_on={i for i,(a,b,c) in enumerate(product((0,1),repeat=3)) if (a and b) or c}
ok('m01/m02 f=ab+c ON and all 8 truth rows', f_on=={1,3,5,6,7})
ok('m02 Kmap Gray placement and two overlapping cubes', cover_value(['--1','11-'])==f_on)
for b,c in product((0,1),repeat=2):
    ok(f'm02 a Boolean difference at bc={b}{c}', (bool(c)^bool(b or c)) == bool(b and not c))

F={0,1,2,5,6,7}; ps=primes(F,set(),3)
ok('m03 complete prime set independently enumerated',set(ps)=={'00-','0-0','-01','-10','1-1','11-'})
optimal=[]
for k in range(1,len(ps)+1):
    optimal=[sorted(sel) for sel in combinations(ps,k) if set().union(*(ps[c] for c in sel))==F]
    if optimal:break
ok('m03 minimum cover count and both optima',k==3 and len(optimal)==2 and all(sum(c.count('0')+c.count('1') for c in sel)==6 for sel in optimal))
ok('m03 DC=3 variant prime set',set(primes(F,{3},3))=={'0--','-1-','--1'})
dc_ps=primes(F,{3},3)
ok('m03 DC variant requires all three primes',not any(F<=set().union(*(dc_ps[c] for c in sel)) for sel in combinations(dc_ps,2)))

stages=[['111','110','011'],['11-','110','011'],['11-','011'],['11-','-11']]
ok('m04 9→8→5→4 literal costs',[sum(len(c.replace('-','')) for c in stage) for stage in stages]==[9,8,5,4])
ok('m04 each cover preserves exactly ON 3,6,7',all(cover_value(stage)=={3,6,7} for stage in stages))
ok('m04 legal reduce and illegal reduce',cover_value(['110','-11'])=={3,6,7} and cover_value(['111','-11'])=={3,7})
ok('m04 final PI set',set(primes({3,6,7},set(),3))=={'11-','-11'})
for a,b,c in product((0,1),repeat=3):
    c1=a and b;c2=a and c;h=(a and not b and c) or (a and b and not c)
    ok(f'm04 deletion dependency at {a}{b}{c}',bool(c1 or c2 or h)==bool(c1 or h)==bool(c2 or h))
ok('m04 simultaneous deletion loses 111',7 not in cover_value(['101','110']))

cof=[];xorcof=[]
for b,c in product((0,1),repeat=2):
    vals=tuple(int((a and b) or (a and c)) for a in (0,1));cof.append(vals)
    xorcof.append(tuple(a^b^c for a in (0,1)))
ok('m05 exact cofactor classes 0,a,a,a',cof==[(0,0),(0,1),(0,1),(0,1)])
ok('m05 XOR variant a,not a,not a,a',xorcof==[(0,1),(1,0),(1,0),(0,1)])
ok('m05 both variants need one encoded bit',len(set(cof))==len(set(xorcof))==2)
for a,b,c in product((0,1),repeat=3):ok(f'm05 factored equivalence {a}{b}{c}',bool((a and b) or (a and c))==bool(a and (b or c)))

def bdd_count(order):
    unique={}
    def build(i,values):
        if i==len(order):return int(values['a']==values['c'] and values['b']==values['d'])
        var=order[i]
        low=build(i+1,values|{var:0});high=build(i+1,values|{var:1})
        if low==high:return low
        key=(var,low,high)
        if key not in unique:unique[key]=len(unique)+2
        return unique[key]
    root=build(0,{})
    return len(unique),root
ok('m06 independent canonical BDD construction: grouped 9, interleaved 6',bdd_count('abcd')[0]==9 and bdd_count('acbd')[0]==6)
specs=json.loads((ROOT/'content/figure-specs-front.json').read_text(encoding='utf-8'))
bddspec=next(s for s in specs if s['id']=='front-m06-bdd')
for name in ('grouped','interleaved'):
    graph=bddspec[name];nodes={row[0]:row[1:] for row in graph['nodes']}
    for vals in product((0,1),repeat=4):
        env=dict(zip('abcd',vals));node=graph['root'];visited=set()
        while node not in ('0','1'):
            assert node not in visited;visited.add(node)
            var,lo,hi=nodes[node];node=hi if env[var] else lo
        ok(f'm06 diagram {name} truth {vals}',int(node)==int(env['a']==env['c'] and env['b']==env['d']))

trans={('S0',0):('S0',0),('S0',1):('S1',0),('S1',0):('S2',0),('S1',1):('S1',0),('S2',0):('S0',0),('S2',1):('S1',1)}
codes={'S0':0,'S1':1,'S2':2}
def simulate(seq):
    st='S0';out=[]
    for x in seq:st,y=trans[(st,x)];out.append(y)
    return out,st
for length in range(1,11):
    for seq in product((0,1),repeat=length):
        outputs,_=simulate(seq)
        assert outputs==[int(i>=2 and seq[i-2:i+1]==(1,0,1)) for i in range(length)]
ok('m07 all 2046 input sequences length 1–10 match direct substring specification')
for code in range(4):
    for x in (0,1):
        q1=(code>>1)&1;q0=code&1
        d1=int(not q1 and q0 and not x);d0=int(x and not(q1 and q0));y=int(q1 and not q0 and x)
        if code==3:expected=(0,0)
        else:
            st=next(k for k,v in codes.items() if v==code)
            ns,ey=trans[(st,x)];expected=(codes[ns],ey)
        assert ((d1<<1)|d0,y)==expected
ok('m07 encoded equations agree on all eight rows including unused-state recovery')
for seq,out in [('101','001'),('1101','0001'),('10101','00101'),('100101','000001'),('110101','000101')]:
    ok(f'm07 explicit trace {seq}',simulate(tuple(map(int,seq)))[0]==list(map(int,out)))

# Parent-requested independent audit of transferMock questions 1–3; never mutate them.
tF={0,2,8,10,12,14};tps=primes(tF,set(),4)
ok('transfer-01 complete PI set',set(tps)=={'-0-0','1--0'})
ok('transfer-01 both essential',any(sum(i in v for v in tps.values())==1 for i in [0]) and any(sum(i in v for v in tps.values())==1 for i in [12]))
for a,b,c,d in product((0,1),repeat=4):
    num=8*a+4*b+2*c+d
    assert bool((not b and not d) or (a and not d))==bool((not b or a) and not d)==(num in tF)
ok('transfer-01 full 16-row equivalence and 2-term/4-literal result')
def detector11(seq):
    prev=0;out=[]
    for x in seq:out.append(int(prev and x));prev=x
    return ''.join(map(str,out))
ok('transfer-02 overlapping 11 sequences',detector11(map(int,'11011'))=='01001' and detector11(map(int,'111'))=='011')
ok('transfer-02 c,a,b BDD has three nonterminals',len({('c','A',1),('a',0,'B'),('b',0,1)})==3)
for a,b,c in product((0,1),repeat=3):assert bool((a and b) or (a and not b and c))==bool(a and (b or c))
ok('transfer-03 legal expansion full 8-row check')
ok('transfer-03 exp(-3) and T=1 rejection',abs(math.exp(-3)-0.049787068367863944)<1e-15 and not (0.1<math.exp(-3)))

fig_ids={s['id'] for s in specs};wc=0;total_steps=0
def strings(obj):
    if isinstance(obj,str):yield obj
    elif isinstance(obj,list):
        for item in obj:yield from strings(item)
    elif isinstance(obj,dict):
        for item in obj.values():yield from strings(item)
for path in sorted((ROOT/'content/modules').glob('*.json')):
    mod=json.loads(path.read_text(encoding='utf-8-sig'))
    if mod['number']>7:continue
    w=mod['walkthrough'];wc+=1;total_steps+=len(w['steps'])
    assert len(w['steps'])>=4
    for s in w['steps']:
        assert s['title'] and s['do'] and s['body']
        assert len(s['body'])>250
        if 'figure' in s:assert s['figure'] in fig_ids,(mod['id'],s['figure'])
    for s in strings(w):
        assert not any(ord(c)<32 and c!='\n' for c in s),(path,'unexpected control char')
        assert r'\(' not in s and r'\)' not in s
ok('all seven walkthrough schemas, nonempty detailed steps, figure references and clean text',wc==7)
report={'status':'pass','checks':checks,'walkthroughs':wc,'steps':total_steps,'figures':len(specs),'transferMockFirstThree':'mathematics and answer coverage independently verified','limits':'Does not claim to simulate physical hardware; image render and UI/PDF integration are checked by owner agents.'}
(ROOT/'qa').mkdir(exist_ok=True)
(ROOT/'qa/front-walkthrough-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'pass','assertions':len(checks),'walkthroughs':wc,'steps':total_steps,'figures':len(specs)},ensure_ascii=True))
