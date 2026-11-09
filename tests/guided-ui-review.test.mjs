import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {freshState,normalizeState} from '../src/state.mjs';
import {renderGuided,renderFigure} from '../src/guided.mjs';

const D=JSON.parse(fs.readFileSync('public/downloads/course-data.json','utf8'));

// This harness executes the real app module and event handlers without a browser.
// DOM layout is out of scope; the parent validates the rendered mobile/desktop UI.
function appHarness(initialHash='#/exam/a'){
  const elements=new Map();
  const element=key=>{
    if(!elements.has(key))elements.set(key,{key,innerHTML:'',textContent:'',value:'',dataset:{},events:{},classList:{add(){},remove(){},toggle(){}},setAttribute(){},scrollIntoView(){},focus(){},showModal(){},close(){},addEventListener(type,handler){this.events[type]=handler;}});
    return elements.get(key);
  };
  const location={hash:initialHash};
  const document={querySelector(s){if(s==='#timer'&&!element('#main').innerHTML.includes('id="timer"'))return null;return element(s);},querySelectorAll(){return [];},getElementById(id){return element('#'+id);},body:{classList:{add(){},remove(){},toggle(){},contains(){return false;}}},activeElement:{tagName:'BODY'},addEventListener(){}};
  let stored=null;
  // The production app has one realm. Clone across the VM boundary so this
  // harness does not reject VM object prototypes as if they were hostile input.
  const normalizeInHost=(value,data)=>normalizeState(JSON.parse(JSON.stringify(value)),data);
  const context=vm.createContext({D,freshState,normalizeState:normalizeInHost,renderGuided,renderFigure,renderLab:()=>'',bindLab(){},document,location,JSON,Date,Blob,URL,localStorage:{getItem:()=>stored,setItem:(key,value)=>{stored=value;}},window:{scrollTo(){},addEventListener(){}},requestAnimationFrame:fn=>fn(),setTimeout:()=>1,setInterval:()=>1,clearInterval(){}});
  const source=fs.readFileSync('src/app.mjs','utf8').replace(/^import.*$/gm,'');
  vm.runInContext(source+'\nglobalThis.reviewApi={render,state:()=>state,setState:s=>state=s,timerEnd:()=>mockEnd};',context);
  return {api:context.reviewApi,element,location,stored:()=>stored};
}

test('switching mock paper through the learning route cannot inherit the other paper countdown',()=>{
  const h=appHarness();
  h.element('#start-mock').events.click();
  assert.ok(h.api.timerEnd()>Date.now());
  h.location.hash='#/plan';h.api.render();
  h.location.hash='#/exam/b';h.api.render();
  assert.equal(h.api.timerEnd(),0,'Day 9 route retained the Day 8 paper deadline');
  assert.equal(h.element('#timer').textContent||'60:00','60:00');
});

test('returning to the same mock preserves its running countdown',()=>{
  const h=appHarness();h.element('#start-mock').events.click();const deadline=h.api.timerEnd();
  h.location.hash='#/plan';h.api.render();h.location.hash='#/exam/a';h.api.render();
  assert.equal(h.api.timerEnd(),deadline);
});

test('real import handler merges new guided drafts and paper B evidence without losing old records',async()=>{
  const h=appHarness('#/notes'),old=freshState();
  old.read=['m08'];old.notes.m08='原来的事件笔记';old.answers['m08-q1']='旧推导';
  old.coachAnswers['m08-step-1']='旧走读草稿';h.api.setState(old);
  const incoming=freshState();incoming.coachAnswers['m09-step-1']='新的delta草稿';
  incoming.answers['transfer-04']='排队4ns、7ns，先用旧signal值';
  incoming.grades['transfer-04']={score:8,kind:'self',date:1000};incoming.reviews['transfer-04']={level:0,due:12345};
  const file={size:1000,text:async()=>JSON.stringify(incoming)};
  await h.element('#import-state').events.change({target:{files:[file]}});
  const state=h.api.state();
  assert.equal(state.notes.m08,'原来的事件笔记');assert.equal(state.answers['m08-q1'],'旧推导');
  assert.equal(state.coachAnswers['m08-step-1'],'旧走读草稿');assert.equal(state.coachAnswers['m09-step-1'],'新的delta草稿');
  assert.equal(state.answers['transfer-04'],incoming.answers['transfer-04']);assert.equal(state.grades['transfer-04'].score,8);
  assert.equal(state.reviews['transfer-04'].due,12345);assert.deepEqual(state.read,['m08']);
  assert.deepEqual(JSON.parse(h.stored()),state);
});

test('invalid import leaves existing notes and guided drafts untouched',async()=>{
  const h=appHarness('#/notes'),old=freshState();old.notes.m08='保留';old.coachAnswers['m08-step-1']='不可丢失';h.api.setState(old);
  const before=JSON.stringify(old);
  await h.element('#import-state').events.change({target:{files:[{size:20,text:async()=>'null'}]}});
  assert.equal(JSON.stringify(h.api.state()),before);
});

test('built standalone HTML embeds every picture and its SVG has no external image dependency',()=>{
  const html=fs.readFileSync('public/downloads/dma-handbook.html','utf8');
  const images=[...html.matchAll(/<img[^>]+src="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(images.length,D.figures.length);
  for(const src of images){
    assert.ok(src.startsWith('data:image/svg+xml;base64,'));
    const svg=Buffer.from(src.split(',')[1],'base64').toString('utf8');
    assert.ok(svg.includes('<svg'));assert.ok(!/<image\b/.test(svg));
  }
  assert.ok(!/url\((?:"|')?(?:https?:|fonts\/)/.test(html),'offline math font depends on an external path');
  for(const q of D.examGuide.transferMock.questions)assert.ok(html.includes(q.id));
});
