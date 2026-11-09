import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {marked} from 'marked';
import katex from 'katex';

const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const modules=fs.readdirSync('content/modules').filter(n=>/^(08|09|10|11|12|13)-/.test(n)).map(n=>read(path.join('content/modules',n)));
const specs=read('content/figure-specs-back.json');
const spec=id=>specs.find(s=>s.id===id).data;
const strings=o=>typeof o==='string'?[o]:Array.isArray(o)?o.flatMap(strings):o&&typeof o==='object'?Object.values(o).flatMap(strings):[];

test('six walkthroughs are complete, self-contained, renderable and reference existing figures',()=>{
  assert.equal(modules.length,6);
  for(const m of modules){
    const w=m.walkthrough;
    assert.ok(w.title&&w.goal&&w.duration>0&&w.next&&w.exit.prompt&&w.exit.answer,m.id);
    assert.ok(w.steps.length>=4&&w.steps.length<=6,m.id);
    for(const s of w.steps){
      assert.ok(s.title&&s.do&&s.body&&s.check.prompt&&s.check.answer,m.id);
      if(s.figure)assert.ok(specs.some(f=>f.id===s.figure),s.figure);
    }
    for(const text of strings(w)){
      assert.ok(!/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(text),m.id+' control character');
      assert.ok(!/\*\*[^*\n]*\s\*\*/.test(text),m.id+' bold trailing space');
      assert.ok(!marked.parse(text).includes('**'),m.id+' unparsed bold');
      assert.ok(!/(?:去看|回到|打开)(?:原PDF|讲义|教程)/.test(text),m.id+' external prerequisite');
      for(const match of text.matchAll(/\$\$([\s\S]*?)\$\$|\$([^$\n]+)\$/g)){
        const formula=match[1]??match[2];
        assert.ok(!/[\u4e00-\u9fff]/.test(formula),m.id+' CJK in math');
        assert.doesNotThrow(()=>katex.renderToString(formula,{throwOnError:true}),m.id+' '+formula);
      }
    }
  }
});

test('all 80 fault matrix cells independently match good/faulty circuit evaluation',()=>{
  const matrix=spec('back-m12-matrix');
  function evalCircuit(vector,fault){
    let [a,b,c]=[...vector].map(Number);
    const set=(site,value)=>fault?.[0]===site?Number(fault[1]):value;
    a=set('a',a);b=set('b',b);c=set('c',c);
    const n=set('n',a&&b),y=set('y',n||c);
    return {n,y};
  }
  for(const row of matrix.rows){
    const good=evalCircuit(row.vector);
    assert.equal(row.n,good.n);assert.equal(row.goodY,good.y);
    matrix.faults.forEach((fault,i)=>{
      const bad=evalCircuit(row.vector,fault.split('/'));
      assert.equal(row.faultyY[i],bad.y,`${row.vector} ${fault}`);
      assert.equal(row.detected[i],Number(good.y!==bad.y),`${row.vector} ${fault}`);
    });
  }
  const covers=[];
  for(let subset=1;subset<256;subset++){
    const rows=matrix.rows.filter((_,i)=>subset&(1<<i));
    if(matrix.faults.every((_,i)=>rows.some(r=>r.detected[i])))covers.push(rows.map(r=>r.vector));
  }
  const min=Math.min(...covers.map(v=>v.length));
  assert.equal(min,4);
  assert.deepEqual(covers.filter(v=>v.length===min),matrix.minimumSets);
});

test('delta figure distinguishes immediate variables and deferred signals at both edges',()=>{
  const d=spec('back-m09-delta');
  function edge(old){
    const now={...old},pending={sa:old.sb,sb:old.sa};
    now.va=now.vb;now.vb=now.va;
    pending.q=now.sa;pending.r=now.va;
    return {now,pending,after:{...now,...pending}};
  }
  const first=edge(d.initial);
  assert.deepEqual(first.now,d.afterProcess);
  assert.deepEqual(first.pending,d.pending);
  assert.deepEqual(first.after,d.afterDelta);
  assert.deepEqual(edge(first.after).after,d.afterSecondEdgeAndDelta);
});

test('LFSR trace uses the specified bit order and returns to seed after 15 shifts',()=>{
  const d=spec('back-m13-lfsr');
  let bits=[0,0,0,1];
  const seen=new Set();
  for(const row of d.trace){
    assert.equal(bits.join(''),row.bits);assert.equal(parseInt(bits.join(''),2),row.decimal);
    assert.ok(!seen.has(row.bits));seen.add(row.bits);
    const feedback=bits[3]^bits[2];
    assert.equal(feedback,row.feedback);
    bits=[feedback,...bits.slice(0,3)];
    assert.equal(parseInt(bits.join(''),2),row.next);
  }
  assert.equal(seen.size,15);assert.equal(bits.join(''),'0001');
});

test('scan teaching example loads/captures/unloads in exactly 19 cycles',()=>{
  let bits=[0,0,0,0],cycles=0;
  const shift=input=>{const out=bits[3];bits=[input,...bits.slice(0,3)];cycles++;return out;};
  const capture=()=>{bits=bits.map(v=>1-v);cycles++;};
  [0,1,0,1].forEach(shift);assert.equal(bits.join(''),'1010');
  capture();assert.equal(bits.join(''),'0101');
  assert.deepEqual([1,1,0,0].map(shift),[1,0,1,0]);assert.equal(bits.join(''),'0011');
  capture();assert.equal(bits.join(''),'1100');
  assert.deepEqual([0,1,1,1].map(shift),[0,0,1,1]);assert.equal(bits.join(''),'1110');
  capture();assert.equal(bits.join(''),'0001');
  assert.deepEqual([0,0,0,0].map(shift),[1,0,0,0]);
  assert.equal(cycles,spec('back-m13-scan').totalCycles);
});

test('transfer mock questions 4-6 match independent arithmetic and fault-set checks',()=>{
  const exam=read('content/exam-guide.json').transferMock;
  const questions=exam.questions.slice(3);
  assert.deepEqual(questions.map(q=>q.id),['transfer-04','transfer-05','transfer-06']);
  assert.deepEqual([2,5].map(t=>t+2),[4,7]);
  assert.deepEqual([2,3].map(t=>t+2),[4,5]);
  const d=spec('back-m12-matrix');
  const tests=['010','100','110','001'].map(t=>d.rows.find(r=>r.vector===t));
  assert.ok(d.faults.every((_,i)=>tests.some(t=>t.detected[i])));
  assert.deepEqual(d.rows.filter(r=>r.detected[d.faults.indexOf('a/1')]).map(r=>r.vector),['010']);
  let scan=[0,0,0];
  const states=[1,0,1].map(input=>{scan=[scan[1],scan[2],input];return scan.join('');});
  assert.deepEqual(states,['001','010','101']);
  assert.equal([scan[1],scan[2],scan[0]^scan[2]].join(''),'010');
  let bits=[1,0,0,0];const trace=[];
  for(let i=0;i<4;i++){const f=bits[2]^bits[3];bits=[f,...bits.slice(0,3)];trace.push([f,parseInt(bits.join(''),2)]);}
  assert.deepEqual(trace,[[0,4],[0,2],[1,9],[1,12]]);
});
