// Import boundaries for browser-local learning records. Never trust nested JSON.
const TEXT_LIMIT=20000,DATE_LIMIT=8640000000000000;
const record=v=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&(Object.getPrototypeOf(v)===Object.prototype||Object.getPrototypeOf(v)===null);
const own=(v,k)=>record(v)&&Object.hasOwn(v,k);
const text=v=>typeof v==='string'&&v.length<=TEXT_LIMIT;
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const timestamp=v=>finite(v)&&v>=0&&v<=DATE_LIMIT;
const decimal=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i;
const validDate=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v+'T00:00:00Z'))&&new Date(v+'T00:00:00Z').toISOString().slice(0,10)===v;

export function freshState(){return {version:1,read:[],notes:{},answers:{},grades:{},reviews:{},labNotes:{},numeric:{},settings:{startDate:'2026-11-08',hours:5,intervals:[1,3,7]},theme:'light'};}

function normalizeParams(id,v){
  const p={};if(!record(v))return p;
  const string=(key,max=400)=>{if(typeof v[key]==='string'&&v[key].length<=max)p[key]=v[key];};
  const choice=(key,choices)=>{if((typeof v[key]==='string'||finite(v[key]))&&choices.includes(String(v[key])))p[key]=String(v[key]);};
  const number=(key,min,max,exclusiveMax=false)=>{
    const raw=v[key];if(!(finite(raw)||typeof raw==='string'&&raw.length<=64&&decimal.test(raw.trim())))return;
    const n=Number(raw);if(Number.isFinite(n)&&n>=min&&(exclusiveMax?n<max:n<=max))p[key]=String(n);
  };
  switch(id){
    case'qm':choice('n',['2','3','4']);string('on');string('dc');break;
    case'bdd':string('on');choice('order',['0,1,2,3','0,2,1,3','3,2,1,0','1,3,0,2']);break;
    case'events':number('width',Number.MIN_VALUE,20);number('delay',0,20);choice('mode',['inertial','transport']);break;
    case'faults':if(Array.isArray(v.vectors)&&v.vectors.length<=8&&v.vectors.every(x=>Number.isInteger(x)&&x>=0&&x<=7))p.vectors=[...new Set(v.vectors)];break;
    case'lfsr':choice('seed',Array.from({length:16},(_,i)=>String(i)));choice('mask',['0','1','3','5','9','15']);break;
    case'annealing':number('delta',-1e12,1e12);number('temperature',0,1e12);number('random',0,1,true);break;
  }
  return p;
}

/**
 * Invalid root/version throws, so an import must normalize before replacing state.
 * Invalid nested entries are discarded; known safe entries are preserved.
 * Normalize the fully merged state again after importing changed settings, so
 * retained review levels are clamped to the new interval array as well.
 */
export function normalizeState(value,D){
  if(!record(value)||value.version!==1)throw new TypeError('不是本课程 version=1 学习记录对象');
  const r=freshState();
  const modules=new Set((D.modules||[]).map(m=>m.id));
  const questions=new Map([
    ...(D.modules||[]).flatMap(m=>(m.exercises||[]).map(q=>[q.id,q])),
    ...(D.examGuide?.mock?.questions||[]).map(q=>[q.id,{...q,maxScore:q.maxScore??q.points}])
  ]);
  const labs=new Set((D.labs||[]).map(l=>l.id));

  if(record(value.settings)){
    const s=value.settings;
    if(validDate(s.startDate))r.settings.startDate=s.startDate;
    if(finite(s.hours)&&s.hours>=2&&s.hours<=10)r.settings.hours=s.hours;
    if(Array.isArray(s.intervals)&&s.intervals.length>0&&s.intervals.length<=32&&s.intervals.every(n=>Number.isInteger(n)&&n>0&&n<=365))r.settings.intervals=[...new Set(s.intervals)].sort((a,b)=>a-b);
  }
  if(Array.isArray(value.read))r.read=[...new Set(value.read.filter(id=>typeof id==='string'&&modules.has(id)))];
  if(value.theme==='dark')r.theme='dark';
  for(const id of modules)if(own(value.notes,id)&&text(value.notes[id]))r.notes[id]=value.notes[id];
  for(const [id,q] of questions){
    if(own(value.answers,id)&&text(value.answers[id]))r.answers[id]=value.answers[id];
    const g=own(value.grades,id)?value.grades[id]:null;
    if(record(g)&&g.kind==='self'&&finite(g.score)&&g.score>=0&&g.score<=q.maxScore&&timestamp(g.date)&&r.answers[id]?.trim())r.grades[id]={score:g.score,kind:'self',date:g.date};
    const n=own(value.numeric,id)?value.numeric[id]:null;
    if(q.type==='numeric'&&record(n)&&typeof n.value==='string'&&n.value.length<=64&&decimal.test(n.value.trim())&&Number.isFinite(Number(n.value))&&timestamp(n.date)&&typeof n.correct==='boolean'){
      const expected=Number(q.expected),tol=Number(q.tolerance||0);
      r.numeric[id]={value:n.value.trim(),correct:Number.isFinite(expected)&&Number.isFinite(tol)&&tol>=0&&Math.abs(Number(n.value)-expected)<=tol,date:n.date};
    }
    const review=own(value.reviews,id)?value.reviews[id]:null;
    if(record(review)&&Number.isInteger(review.level)&&review.level>=0&&timestamp(review.due))r.reviews[id]={level:Math.min(review.level,r.settings.intervals.length-1),due:review.due};
  }
  for(const id of labs){
    const note=own(value.labNotes,id)?value.labNotes[id]:null;if(!record(note))continue;
    const clean={};for(const key of ['predict','explain','transfer'])if(text(note[key]))clean[key]=note[key];
    if(record(note.params))clean.params=normalizeParams(id,note.params);
    r.labNotes[id]=clean;
  }
  return r;
}
