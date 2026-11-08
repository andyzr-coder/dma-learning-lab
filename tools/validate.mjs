import fs from 'node:fs';import assert from 'node:assert/strict';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const D=read('public/downloads/course-data.json'),ids=new Set(D.modules.map(m=>m.id)),sources=new Set(D.sources.map(s=>s.id));
assert.equal(D.modules.length,13);assert.equal(sources.size,D.sources.length,'duplicate source ID');
const refs=[];for(const m of D.modules){assert.ok(m.sections.length>=4);assert.ok(m.exercises.length>=6);for(const dep of [...m.prerequisites,...m.related])assert.ok(ids.has(dep),`${m.id}: missing module ${dep}`);refs.push(...m.sourceRefs.map(s=>s.id));for(const q of m.exercises){assert.ok(q.answer&&q.rubric.length);if(q.type==='numeric')assert.ok(Number.isFinite(q.expected));}}
for(const l of D.labs){assert.ok(ids.has(l.module));refs.push(...l.sources);for(const k of ['model','assumptions','predict','hand','boundary','variation','limits'])assert.ok(l[k]);}
for(const e of D.exams.exams){assert.equal(e.questions.reduce((s,q)=>s+q.points,0),e.totalPoints);refs.push(e.sourceId,e.answerSource);}
for(const id of refs)assert.ok(sources.has(id),`missing source ${id}`);
const visited=new Set(),stack=new Set();function visit(id){assert.ok(!stack.has(id),`prerequisite cycle ${id}`);if(visited.has(id))return;stack.add(id);D.modules.find(m=>m.id===id).prerequisites.forEach(visit);stack.delete(id);visited.add(id);}ids.forEach(visit);
assert.equal(D.plan.days.length,10);assert.equal(D.examGuide.mock.questions.reduce((s,q)=>s+q.points,0),60);
const json=JSON.stringify(D);assert.ok(!/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(json));
for(const p of ['index.html','app.mjs','models.mjs','labs-ui.mjs','content.mjs','style.css','vendor/katex.min.css','downloads/dma-handbook.html','downloads/dma-handbook.md','downloads/course-data.json','downloads/source-index.json'])assert.ok(fs.existsSync('dist/'+p),`missing output ${p}`);
const report={date:'2026-11-08',modules:D.modules.length,exercises:D.modules.reduce((s,m)=>s+m.exercises.length,0),mockQuestions:D.examGuide.mock.questions.length,labs:D.labs.length,sources:D.sources.length,checks:['module references','acyclic prerequisites','source references','exam sums','mock sum','content structure','required output files'],status:'pass'};fs.writeFileSync('qa/content-check.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
