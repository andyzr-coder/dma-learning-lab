import test from 'node:test';
import assert from 'node:assert/strict';
import {freshState,normalizeState} from '../src/state.mjs';

const D={modules:[{id:'m08',exercises:[{id:'m08-q1',type:'numeric',expected:17,tolerance:0,maxScore:2},{id:'m08-q2',type:'text',maxScore:4}]}],labs:['qm','bdd','events','faults','lfsr','annealing'].map(id=>({id})),examGuide:{mock:{questions:[{id:'mock-01',points:6}]}}};

test('fresh state is detached, includes numeric, and round-trips',()=>{
  const a=freshState(),b=freshState();a.settings.intervals.push(20);assert.notDeepEqual(a,b);
  assert.deepEqual(normalizeState(JSON.parse(JSON.stringify(b)),D),b);
});
test('reject malformed root without mutating the previous state',()=>{
  const prior=freshState();prior.notes.m08='保留笔记';const snapshot=structuredClone(prior);
  for(const bad of [null,[],1,'text',{}, {version:2}, {version:'1'}])assert.throws(()=>normalizeState(bad,D),/version=1/);
  assert.deepEqual(prior,snapshot);
});
test('valid notes, numerical results, self grades, review and mock answers round-trip',()=>{
  const s=freshState();Object.assign(s,{read:['m08'],notes:{m08:'事件表'},answers:{'m08-q1':'7+4+6=17','mock-01':'独立推导'},numeric:{'m08-q1':{value:'17',correct:true,date:1000}},grades:{'m08-q1':{score:2,kind:'self',date:1000},'mock-01':{score:5,kind:'self',date:2000}},reviews:{'m08-q1':{level:2,due:999999},'mock-01':{level:0,due:100000}},labNotes:{faults:{predict:'先激活',explain:'再传播',transfer:'更换故障',params:{vectors:[0,6]}}},theme:'dark'});
  assert.deepEqual(normalizeState(JSON.parse(JSON.stringify(s)),D),s);
});
test('malicious HTML score is never imported as a grade',()=>{
  const out=normalizeState({version:1,answers:{'m08-q1':'test'},grades:{'m08-q1':{score:'<img src=x onerror=alert(1)>',kind:'self',date:0}}},D);
  assert.deepEqual(out.grades,{});
});
test('nested arrays, nulls, primitives, overlong strings and unknown IDs are discarded',()=>{
  const out=normalizeState({version:1,read:['m08','m08','bad',{}],notes:{m08:{html:'bad'},bad:'no'},answers:{'m08-q1':[], 'm08-q2':'x'.repeat(20001)},grades:{'m08-q1':null},reviews:{'m08-q1':2},numeric:{'m08-q1':null},labNotes:{faults:[],qm:'bad',bdd:null}},D);
  assert.deepEqual(out.read,['m08']);for(const k of ['notes','answers','grades','reviews','numeric','labNotes'])assert.deepEqual(out[k],{});
});
test('prototype-shaped keys do not enter state maps',()=>{
  const v=JSON.parse('{"version":1,"notes":{"__proto__":{"polluted":true},"constructor":"bad","m08":"ok"},"grades":{"prototype":{}}}');
  const out=normalizeState(v,D);assert.deepEqual(out.notes,{m08:'ok'});assert.equal({}.polluted,undefined);assert.deepEqual(out.grades,{});
});
test('score requires numeric bounds, a self label, a valid timestamp and an answer',()=>{
  for(const score of [-1,3,NaN,Infinity,'2',null])assert.deepEqual(normalizeState({version:1,answers:{'m08-q1':'work'},grades:{'m08-q1':{score,kind:'self',date:0}}},D).grades,{});
  for(const g of [{score:2,kind:'auto',date:0},{score:2,kind:'self',date:NaN},{score:2,kind:'self',date:-1}])assert.deepEqual(normalizeState({version:1,answers:{'m08-q1':'work'},grades:{'m08-q1':g}},D).grades,{});
  assert.deepEqual(normalizeState({version:1,grades:{'m08-q1':{score:2,kind:'self',date:0}}},D).grades,{});
});
test('numeric values are checked against the course rather than a supplied correct flag',()=>{
  const out=normalizeState({version:1,numeric:{'m08-q1':{value:'18',correct:true,date:1},'m08-q2':{value:'17',correct:true,date:1}}},D);
  assert.deepEqual(out.numeric,{'m08-q1':{value:'18',correct:false,date:1}});
  for(const value of ['', 'Infinity','NaN','0x11','<b>17</b>',{},17])assert.deepEqual(normalizeState({version:1,numeric:{'m08-q1':{value,correct:true,date:1}}},D).numeric,{});
});
test('review levels clamp after intervals change and invalid dates cannot poison scheduling',()=>{
  const out=normalizeState({version:1,settings:{intervals:[1]},reviews:{'m08-q1':{level:2,due:12345},'m08-q2':{level:0,due:null}}},D);
  assert.deepEqual(out.reviews,{'m08-q1':{level:0,due:12345}});
  for(const due of [Infinity,NaN,-1,'100',8640000000000001])assert.deepEqual(normalizeState({version:1,reviews:{'m08-q1':{level:0,due}}},D).reviews,{});
});
test('settings validate real calendar dates and bounded numeric intervals',()=>{
  assert.equal(normalizeState({version:1,settings:{startDate:'2026-02-30'}},D).settings.startDate,'2026-11-08');
  assert.equal(normalizeState({version:1,settings:{startDate:'2028-02-29'}},D).settings.startDate,'2028-02-29');
  assert.deepEqual(normalizeState({version:1,settings:{hours:'7',intervals:[0,-1,'3']}},D).settings,freshState().settings);
  assert.deepEqual(normalizeState({version:1,settings:{hours:7.5,intervals:[7,1,7,3]}},D).settings,{startDate:'2026-11-08',hours:7.5,intervals:[1,3,7]});
});
test('lab params use per-experiment whitelist; malformed vectors never reach includes',()=>{
  const out=normalizeState({version:1,labNotes:{faults:{predict:'ok',params:{vectors:{},html:'bad'}},qm:{params:{n:4,on:'0,1',dc:'2',unexpected:1}},events:{params:{width:'2',delay:'0',mode:'transport',vectors:[1]}},lfsr:{params:{seed:0,mask:3}},annealing:{params:{delta:'2',temperature:'0',random:'1'}}}},D);
  assert.deepEqual(out.labNotes.faults,{predict:'ok',params:{}});
  assert.deepEqual(out.labNotes.qm.params,{n:'4',on:'0,1',dc:'2'});
  assert.deepEqual(out.labNotes.events.params,{width:'2',delay:'0',mode:'transport'});
  assert.deepEqual(out.labNotes.lfsr.params,{seed:'0',mask:'3'});
  assert.deepEqual(out.labNotes.annealing.params,{delta:'2',temperature:'0'});
});
test('corrected merged backups cannot retain an out-of-range review level',()=>{
  const current=freshState();current.reviews['m08-q1']={level:2,due:Date.now()+10000};
  const incoming=normalizeState({version:1,settings:{intervals:[2]}},D);
  const merged=normalizeState({...current,settings:incoming.settings,reviews:{...current.reviews,...incoming.reviews}},D);
  assert.equal(merged.reviews['m08-q1'].level,0);
  assert.equal(merged.settings.intervals[merged.reviews['m08-q1'].level],2);
});
