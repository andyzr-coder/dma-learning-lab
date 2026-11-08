"""Independent exhaustive checks for the small examples in modules m08-m13.

These tests validate educational arithmetic and Boolean examples, not an HDL
simulator, silicon timing model, industrial ATPG, or manufacturing test flow.
"""
import itertools
import json
from pathlib import Path

checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)

def gate_outputs(a,b,kind='and',fault=None):
    loc,stuck=fault if fault else ('',0)
    aa=stuck if loc=='a' else a
    bb=stuck if loc=='b' else b
    y=(aa & bb) ^ (kind=='nand')
    return stuck if loc=='y' else int(y)

faults=list(itertools.product(['a','b','y'],[0,1]))
inputs=list(itertools.product([0,1],repeat=2))
for kind in ['and','nand']:
    got={''.join(map(str,t)):{f'{p}/{s}' for p,s in faults if gate_outputs(*t,kind,(p,s))!=gate_outputs(*t,kind)} for t in inputs}
    expected=({'00':{'y/1'},'01':{'a/1','y/1'},'10':{'b/1','y/1'},'11':{'a/0','b/0','y/0'}} if kind=='and' else {'00':{'y/0'},'01':{'a/1','y/0'},'10':{'b/1','y/0'},'11':{'a/0','b/0','y/1'}})
    check(f'{kind}: six fault dictionary',got==expected)
    universe={f'{p}/{s}' for p,s in faults}
    complete=[set(ts) for n in range(5) for ts in itertools.combinations(got,n) if set().union(*(got[t] for t in ts))==universe]
    check(f'{kind}: unique size-three minimum cover',len([s for s in complete if len(s)==3])==1 and {'01','10','11'} in complete and min(map(len,complete))==3)
    if kind=='and': check('AND: coverage of 01 and 11',len(got['01']|got['11'])==5)

def reconverge(a,b,c,fault=None):
    loc,stuck=fault if fault else ('',0)
    aa=stuck if loc=='a' else a
    bb=stuck if loc=='b' else b
    cc=stuck if loc=='c' else c
    u=stuck if loc=='u' else aa&bb
    v=stuck if loc=='v' else aa&cc
    y=stuck if loc=='y' else u^v
    return u,v,y

rfaults=list(itertools.product(['a','b','c','u','v','y'],[0,1]))
detected={f'{p}/{s}' for p,s in rfaults if reconverge(1,1,0,(p,s))[-1]!=reconverge(1,1,0)[-1]}
check('reconvergence: m12 worked six detected faults',detected=={'a/0','b/0','c/1','u/0','v/1','y/0'})
stemtests=[t for t in itertools.product([0,1],repeat=3) if reconverge(*t,('a',0))[-1]!=reconverge(*t)[-1]]
check('reconvergence: a/0 test set',stemtests==[(1,0,1),(1,1,0)])
check('reconvergence: 111 stem masked',reconverge(1,1,1,('a',0))[-1]==reconverge(1,1,1)[-1])
check('XOR deductive symmetric difference',({'f1','f2','f3'}^{'f2','f3','f4'})=={'f1','f4'})

for u,v,du,dv in itertools.product([0,1],repeat=4):
    direct=(u&v)^((u^du)&(v^dv))
    chain=(u&dv)^(v&du)^(du&dv)
    check(f'Boolean AND difference truth row {u}{v}{du}{dv}',direct==chain)

def mod(value,poly):
    while value.bit_length()>=poly.bit_length():
        value^=poly<<(value.bit_length()-poly.bit_length())
    return value

def orbit(seed,poly):
    states=[]
    s=seed
    while s not in states:
        states.append(s)
        s=mod(s<<1,poly)
    return states,s

seq,end=orbit(1,0b1011)
check('LFSR3: declared seven-state orbit',seq==[1,2,4,3,6,7,5] and end==1)
check('LFSR3: zero seed locks',orbit(0,0b1011)==([0],0))
check('degree4 nonprimitive: period five',orbit(1,0b11111)==([1,2,4,8,15],1))
check('degree4 example: no linear factor',mod(0b11111,0b10)!=0 and mod(0b11111,0b11)!=0)
check('degree4 example: no irreducible quadratic factor',mod(0b11111,0b111)!=0)
check('signature worked remainder',mod(0b1101,0b1011)==0b110)
check('signature collision',mod(0b0110,0b1011)==mod(0b1101,0b1011))
aliases=[e for e in range(1,16) if mod(e,0b1011)==0]
check('uniform 4-bit nonzero error alias fraction',aliases==[0b1011])
check('signature 4-to-3 linear mapping is balanced',all(sum(mod(a,0b1011)==r for a in range(16))==2 for r in range(8)))

def scan_cycles(n,p,c=1):
    return 0 if p==0 else n*(p+1)+p*c
check('single-chain example',scan_cycles(1000,10)==11010)
check('four-chain example',scan_cycles(250,10)==2760)
check('scan P=1 includes final unload',scan_cycles(100,1)==201)
check('scan P=0 special case',scan_cycles(100,0)==0)
check('scan N=0',scan_cycles(0,4)==4)
check('scan exercise',scan_cycles(100,5)==605)
check('event chain example',10+2+3==15)
check('event chain exercise',7+4+6==17)
check('hazard baseline width',(10+3+2+1)-(10+2+1)==3)
check('hazard changed inverter width',(10+5+2+1)-(10+2+1)==5)

root=Path(__file__).resolve().parents[1]
for file in sorted((root/'content'/'modules').glob('*.json')):
    if file.name[:2] not in ('08','09','10','11','12','13'): continue
    d=json.loads(file.read_text(encoding='utf-8'))
    check(f'{d["id"]}: six or more sections',len(d['sections'])>=6)
    check(f'{d["id"]}: six or more exercises',len(d['exercises'])>=6)
    check(f'{d["id"]}: valid unique exercise IDs',len({q['id'] for q in d['exercises']})==len(d['exercises']))
    def strings(x):
        if isinstance(x,str): yield x
        if isinstance(x,dict):
            for v in x.values(): yield from strings(v)
        if isinstance(x,list):
            for v in x: yield from strings(v)
    check(f'{d["id"]}: no escaped control characters',all(not any(ord(c)<32 and c not in '\n\r\t' for c in s) for s in strings(d)))
result={'status':'passed','checks':len(checks),'scope':'Independent educational arithmetic, Boolean truth-table, signature/LFSR and content-integrity checks. Not an HDL or hardware simulation.','items':checks}
(root/'qa').mkdir(exist_ok=True)
(root/'qa'/'testing-content-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'passed','checks':len(checks)},ensure_ascii=False))
