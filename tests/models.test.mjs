import test from 'node:test';import assert from 'node:assert/strict';
import {minimize,matches,bdd,pulse,faultTable,lfsr,anneal} from '../src/models.mjs';
test('QM hand case and all 256 three-variable truth tables agree exhaustively',()=>{
  assert.equal(minimize(3,[1,3,5,7]).expression,'c');
  for(let truth=0;truth<256;truth++){let on=Array.from({length:8},(_,v)=>v).filter(v=>(truth>>v)&1);const r=minimize(3,on);for(let v=0;v<8;v++)assert.equal(r.covers[0].some(i=>matches(r.primes[i],v)),on.includes(v));}
  const dc=minimize(3,[1,3],[5,7]);assert.equal(dc.expression,'c');assert.throws(()=>minimize(3,[1],[1]));
  assert.equal(minimize(4,[]).expression,'0');assert.equal(minimize(4,Array.from({length:16},(_,i)=>i)).expression,'1');
});
test('BDD reduction, constants, variable order and evaluation',()=>{
  assert.equal(bdd(3,[],[0,1,2]).count,0);assert.equal(bdd(3,[1,3,5,7],[0,1,2]).count,1);
  const on=Array.from({length:16},(_,v)=>v).filter(v=>(((v>>3)&1)===((v>>1)&1))&&(((v>>2)&1)===(v&1)));
  assert.notEqual(bdd(4,on,[0,2,1,3]).count,bdd(4,on,[0,1,2,3]).count);
  for(const order of [[0,1,2,3],[0,2,1,3]]){const b=bdd(4,on,order);for(let v=0;v<16;v++){let id=b.root;while(id>1){const node=b.nodes.find(x=>x.id===id);id=((v>>(3-node.variable))&1)?node.high:node.low;}assert.equal(id,Number(on.includes(v)));}}
});
test('Pulse threshold and zero delay',()=>{
  assert.equal(pulse(2,3).outputs.length,0);assert.deepEqual(pulse(2,3,'transport').outputs.map(e=>e.t),[4,6]);assert.equal(pulse(3,3).outputs.length,2);assert.equal(pulse(1,0).outputs[0].delta,1);
});
test('Fault enumeration has ten declared faults and n SA0 detector 110',()=>{
  const r=faultTable([0,1,2,3,4,5,6,7]);assert.equal(r.coverage,1);assert.equal(r.faults.length,10);
  const n=r.faults.findIndex(f=>f.id==='n/0');assert.deepEqual(r.rows.filter(row=>row.detected[n]).map(row=>row.v),[6]);assert.equal(faultTable([]).coverage,0);
});
test('LFSR recurrence hand sequence, maximum period and zero lock',()=>{
  assert.deepEqual(lfsr(1,3).trace.slice(0,5).map(t=>t.state),[1,8,4,2,9]);assert.equal(lfsr(1,3).period,15);assert.equal(lfsr(0,3).period,1);assert.equal(lfsr(1,1).period,4);
});
test('Annealing boundaries and hand calculation',()=>{assert.equal(anneal(1,0,.2).accept,false);assert.equal(anneal(-1,0,.9).accept,true);assert.ok(Math.abs(anneal(2,2,.4).p-Math.exp(-1))<1e-12);assert.equal(anneal(2,2,.4).accept,false);});
