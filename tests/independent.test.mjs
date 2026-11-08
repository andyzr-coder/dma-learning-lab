import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {minimize,bdd,pulse,faultTable,lfsr,anneal} from '../src/models.mjs';

// Independent oracle: enumerate all 3^n cubes, without Quine merging, then
// solve weighted set cover by memoizing the still-uncovered on-set bitmask.
function oracle(n,on,dc=[]){
  const target=on.reduce((m,v)=>m|(1<<v),0),allowed=[...on,...dc].reduce((m,v)=>m|(1<<v),0);
  const candidates=[];
  for(let code=0;code<3**n;code++){
    let temp=code,care=0,ones=0,cost=0;
    for(let bit=0;bit<n;bit++){
      const digit=temp%3;temp=Math.floor(temp/3);
      if(digit!==2){care|=1<<bit;if(digit===1)ones|=1<<bit;cost++;}
    }
    let full=0;for(let v=0;v<2**n;v++)if((v&care)===ones)full|=1<<v;
    const cover=full&target;
    if(cover&&(full&~allowed)===0)candidates.push({cover,cost});
  }
  const memo=new Map([[0,[0,0]]]);
  function solve(remaining){
    if(memo.has(remaining))return memo.get(remaining);
    const pivot=remaining&-remaining;let best=[Infinity,Infinity];
    for(const c of candidates)if(c.cover&pivot){
      const tail=solve(remaining&~c.cover),score=[c.cost+tail[0],tail[1]+1];
      if(score[0]<best[0]||(score[0]===best[0]&&score[1]<best[1]))best=score;
    }
    memo.set(remaining,best);return best;
  }
  return solve(target);
}
function checkMinimum(n,on,dc=[]){
  const actual=minimize(n,on,dc),expected=oracle(n,on,dc);
  assert.deepEqual([actual.cost,actual.count],expected,`n=${n};on=${on};dc=${dc}`);
  for(const solution of actual.covers){
    for(let v=0;v<2**n;v++){
      const value=solution.some(i=>[...actual.primes[i]].every((s,j)=>s==='-'||Number(s)===((v>>(n-1-j))&1)));
      if(!dc.includes(v))assert.equal(value,on.includes(v),`functional correctness v=${v}`);
    }
  }
}
test('independent cube/set-cover oracle: all 256 complete 3-variable functions',()=>{
  for(let truth=0;truth<256;truth++)checkMinimum(3,Array.from({length:8},(_,v)=>v).filter(v=>(truth>>v)&1));
});
test('independent oracle: all 6561 on/off/DC assignments for 3 variables',()=>{
  for(let specification=0;specification<3**8;specification++){
    let x=specification;const on=[],dc=[];
    for(let v=0;v<8;v++){const digit=x%3;x=Math.floor(x/3);if(digit===1)on.push(v);if(digit===2)dc.push(v);}
    checkMinimum(3,on,dc);
  }
});
test('independent oracle: deterministic 4-variable complete and incomplete samples',()=>{
  let seed=0x12345678;
  for(let sample=0;sample<160;sample++){
    const on=[],dc=[];
    for(let v=0;v<16;v++){
      seed=(Math.imul(seed,1664525)+1013904223)>>>0;
      const category=(seed>>>16)%(sample%2?3:2);
      if(category===1)on.push(v);if(category===2)dc.push(v);
    }
    checkMinimum(4,on,dc);
  }
});

const permutations=a=>a.length?a.flatMap((x,i)=>permutations(a.filter((_,j)=>j!==i)).map(p=>[x,...p])):[[]];
test('BDD evaluation and reduction invariants for all 3-variable functions and orders',()=>{
  for(let mask=0;mask<256;mask++)for(const order of permutations([0,1,2])){
    const on=Array.from({length:8},(_,v)=>v).filter(v=>(mask>>v)&1),r=bdd(3,on,order),byId=new Map(r.nodes.map(x=>[x.id,x]));
    assert.equal(new Set(r.nodes.map(x=>`${x.variable},${x.low},${x.high}`)).size,r.count);
    for(const node of r.nodes){
      assert.notEqual(node.low,node.high);
      for(const child of [node.low,node.high])if(child>1)assert.ok(order.indexOf(byId.get(child).variable)>order.indexOf(node.variable));
    }
    for(let v=0;v<8;v++){
      let id=r.root,steps=0;
      while(id>1){const node=byId.get(id);id=((v>>(2-node.variable))&1)?node.high:node.low;assert.ok(++steps<=3);}
      assert.equal(id,(mask>>v)&1);
    }
  }
  assert.equal(bdd(4,[0,5,10,15],[0,2,1,3]).count,6);
  assert.equal(bdd(4,[0,5,10,15],[0,1,2,3]).count,9);
  assert.equal(bdd(3,[1,3,6,7],[0,1,2]).count,3);
  assert.equal(bdd(3,[1,3,6,7],[1,2,0]).count,5);
});

test('pulse hand traces, exact-width threshold, zero delay, and cancellation',()=>{
  for(const mode of ['transport','inertial'])for(const width of [1,2,3,4])for(const delay of [0,1,2,3]){
    const r=pulse(width,delay,mode),passes=mode==='transport'||width>=delay;
    assert.deepEqual(r.outputs.map(e=>[e.t,e.delta,e.value]),passes?[[1+delay,delay===0?1:0,1],[1+width+delay,delay===0?1:0,0]]:[]);
    assert.equal(r.trace.at(-1).output,0);
  }
  assert.deepEqual(pulse(2,3,'inertial').trace.map(t=>t.occupancy),[1,0]);
  assert.deepEqual(pulse(2,3,'transport').trace.map(t=>t.occupancy),[1,2,1,0]);
});
test('queue must not display a transaction before the triggering event has run',()=>{
  // At width=delay the first output transaction and second input event share
  // physical time. Whichever order is chosen, the queue must reflect that order.
  for(const mode of ['transport','inertial'])for(const delay of [1,2,3]){
    const r=pulse(delay,delay,mode);let riseSeen=false,fallSeen=false;
    for(const row of r.trace){
      if(row.kind==='input'){if(row.value===1)riseSeen=true;else fallSeen=true;}
      const scheduled=[...(riseSeen?[r.outputs[0]]:[]),...(fallSeen?[r.outputs[1]]:[])];
      const expected=scheduled.filter(e=>e.t>row.t||(e.t===row.t&&e.delta>row.delta)).length;
      assert.equal(row.occupancy,expected,`${mode},w=d=${delay},${row.kind} at ${row.t}: future transaction appeared before its input was processed`);
    }
  }
});

test('fault detection sets independently derived, including minimum test-set lower bound',()=>{
  const expected={'a/0':[6],'a/1':[2],'b/0':[6],'b/1':[4],'c/0':[1,3,5],'c/1':[0,2,4],'n/0':[6],'n/1':[0,2,4],'y/0':[1,3,5,6,7],'y/1':[0,2,4]};
  const r=faultTable();
  for(const [id,vectors] of Object.entries(expected)){
    const col=r.faults.findIndex(f=>f.id===id);
    assert.deepEqual(r.rows.filter(row=>row.detected[col]).map(row=>row.v),vectors,id);
  }
  assert.deepEqual(faultTable([6]).covered.map(f=>f.id),['a/0','b/0','n/0','y/0']);
  assert.deepEqual(faultTable([4]).covered.map(f=>f.id),['b/1','c/1','n/1','y/1']);
  let best=9,solutions=[];
  for(let mask=0;mask<256;mask++){
    const selected=Array.from({length:8},(_,v)=>v).filter(v=>(mask>>v)&1);
    const covered=Object.values(expected).every(detectors=>selected.some(v=>detectors.includes(v)));
    if(covered&&selected.length<best){best=selected.length;solutions=[];}
    if(covered&&selected.length===best)solutions.push(selected);
  }
  assert.equal(best,4);
  assert.deepEqual(solutions,[[1,2,4,6],[2,3,4,6],[2,4,5,6]]);
});

test('LFSR all 16 masks and seeds agree with independent bit-array recurrence',()=>{
  for(let mask=0;mask<16;mask++)for(let seed=0;seed<16;seed++){
    const result=lfsr(seed,mask),seen=new Map(),states=[];
    let bits=Array.from({length:4},(_,i)=>(seed>>i)&1),state=seed;
    while(!seen.has(state)){
      seen.set(state,states.length);states.push(state);
      let feedback=0;for(let i=0;i<4;i++)if((mask>>i)&1)feedback^=bits[i];
      bits=[bits[1],bits[2],bits[3],feedback];state=bits.reduce((v,b,i)=>v+b*2**i,0);
    }
    assert.deepEqual(result.trace.map(t=>t.state),states);
    assert.equal(result.transient,seen.get(state));assert.equal(result.period,states.length-seen.get(state));
    assert.ok(result.trace.length<=16);
  }
  for(let seed=1;seed<16;seed++){assert.equal(lfsr(seed,3).period,15);assert.equal(lfsr(seed,3).transient,0);}
  const output=lfsr(1,3).trace.map(x=>x.output);
  for(let i=0;i<11;i++)assert.equal(output[i+4],output[i+1]^output[i]);
});
test('annealing probability monotonicity and r=p boundary',()=>{
  const p=Math.exp(-1);
  assert.equal(anneal(2,2,p).accept,false);
  assert.equal(anneal(2,2,p-1e-10).accept,true);
  assert.ok(anneal(2,4,.4).p>anneal(2,2,.4).p);
  assert.equal(anneal(0,0,0).accept,true);
});

test('all supplied exercise scores are bounded, IDs unique, numeric expectations finite',()=>{
  const ids=new Set();
  for(const file of fs.readdirSync(new URL('../content/modules/',import.meta.url))){
    if(!file.endsWith('.json'))continue;
    const module=JSON.parse(fs.readFileSync(new URL('../content/modules/'+file,import.meta.url),'utf8'));
    for(const q of module.exercises){
      assert.ok(!ids.has(q.id),q.id);ids.add(q.id);
      assert.ok(Number.isInteger(q.maxScore)&&q.maxScore>0,q.id);
      assert.ok(q.rubric.length>0&&q.answer.length>0,q.id);
      if(q.type==='numeric'){assert.ok(Number.isFinite(q.expected),q.id);assert.ok((q.tolerance??0)>=0,q.id);}
    }
    for(const ref of module.sourceRefs)assert.ok(ref.locator?.length>0,`${module.id}: missing source locator`);
  }
  const mock=JSON.parse(fs.readFileSync(new URL('../content/exam-guide.json',import.meta.url),'utf8')).mock;
  assert.equal(mock.questions.reduce((sum,q)=>sum+q.points,0),mock.totalPoints);
});
