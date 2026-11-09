import fs from 'node:fs';
import assert from 'node:assert/strict';
const D=JSON.parse(fs.readFileSync('public/downloads/course-data.json','utf8'));
const figures=new Map(D.figures.map(f=>[f.id,f]));
const used=new Set();let steps=0,checks=0;
for(const m of D.modules){const w=m.walkthrough;assert.ok(w&&w.steps.length>=4,`${m.id}: missing complete walkthrough`);assert.ok(w.goal&&w.next&&w.exit.prompt&&w.exit.answer);for(const s of w.steps){steps++;assert.ok(s.do&&s.body.length>=100,`${m.id}: thin step`);if(s.figure){assert.ok(figures.has(s.figure),`missing figure ${s.figure}`);used.add(s.figure);}if(s.check){checks++;assert.ok(s.check.prompt&&s.check.answer);}}for(const s of m.sections)if(s.figure){assert.ok(figures.has(s.figure));used.add(s.figure);}assert.ok(w.steps.some(s=>s.figure),`${m.id}: no illustration`);}
for(const f of D.figures){assert.ok(used.has(f.id),`unattached diagram ${f.id}`);assert.ok(f.alt&&f.caption);for(const k of ['svg','png'])assert.ok(fs.existsSync('public/'+f[k]),`missing ${f[k]}`);}
for(const mock of [D.examGuide.mock,D.examGuide.transferMock]){assert.equal(mock.questions.reduce((s,q)=>s+q.points,0),60);for(const q of mock.questions)assert.ok(q.prompt&&q.answer&&q.rubric.length);}
const known=new Set(D.modules.flatMap(m=>m.exercises.map(q=>q.id)));
for(const day of D.plan.days){assert.ok(!/\b(?:F\d{3}|L25|T25)\b/.test(day.tasks.join(' ')),'route depends on an external course file');for(const id of day.tasks.join(' ').match(/m\d{2}-q\d+/g)||[])assert.ok(known.has(id),`route points to unknown ${id}`);}
const html=fs.readFileSync('public/downloads/dma-handbook.html','utf8'),md=fs.readFileSync('public/downloads/dma-handbook.md','utf8');
const imageSources=[...html.matchAll(/<img[^>]+src="([^"]+)"/g)].map(x=>x[1]);assert.equal(imageSources.length,used.size);assert.ok(imageSources.every(x=>x.startsWith('data:image/svg+xml;base64,')),'standalone HTML requires external pictures');
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);assert.equal(new Set(ids).size,ids.length,'duplicate offline anchor');
assert.equal((md.match(/!\[/g)||[]).length,used.size);for(const m of D.modules)assert.ok(md.includes(m.id+'-exit'));
const report={date:D.date,status:'pass',modules:D.modules.length,figures:figures.size,steps,checkpoints:checks+D.modules.length,papers:2,standaloneImages:imageSources.length,checks:['all guides complete','all diagrams attached and present','self-contained daily tasks','two scored papers','offline embedded figures','unique anchors','shared PDF/HTML coverage']};fs.writeFileSync('qa/guided-check.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
