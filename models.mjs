// Deterministic teaching models. No evaluation of user-supplied code.
export function integers(text,n){
  if(!text.trim())return [];
  const a=text.trim().split(/[\s,，]+/).map(Number);
  if(a.some(x=>!Number.isInteger(x)||x<0||x>=2**n))throw Error(`最小项必须是 0 到 ${2**n-1} 的整数。`);
  return [...new Set(a)].sort((a,b)=>a-b);
}
export const bits=(v,n)=>v.toString(2).padStart(n,'0');
export const matches=(cube,v)=>[...cube].every((c,i)=>c==='-'||c===bits(v,cube.length)[i]);
export const literals=cube=>[...cube].filter(c=>c!=='-').length;
export function cubeExpression(cube){return [...cube].map((v,i)=>v==='-'?'':String.fromCharCode(97+i)+(v==='0'?"′":'')).join('')||'1';}
export function minimize(n,on,dc=[]){
  if(n<1||n>4)throw Error('教学模型支持 1–4 个变量。');
  if(on.some(x=>dc.includes(x)))throw Error('On-set 与 don’t-care 不能重叠。');
  const valid=[...new Set([...on,...dc])];
  if(valid.some(x=>!Number.isInteger(x)||x<0||x>=2**n))throw Error('最小项超出范围。');
  let current=valid.map(v=>bits(v,n)),rounds=[],allPrimes=new Set();
  while(current.length){
    const used=new Set(),next=new Set();
    for(let i=0;i<current.length;i++)for(let j=i+1;j<current.length;j++){
      let diff=-1,ok=true;
      for(let k=0;k<n;k++)if(current[i][k]!==current[j][k]){
        if(current[i][k]==='-'||current[j][k]==='-'||diff!==-1){ok=false;break;}diff=k;
      }
      if(ok&&diff!==-1){used.add(current[i]);used.add(current[j]);next.add(current[i].slice(0,diff)+'-'+current[i].slice(diff+1));}
    }
    rounds.push(current.map(c=>({cube:c,combined:used.has(c)})));
    current.filter(c=>!used.has(c)).forEach(c=>allPrimes.add(c));current=[...next].sort();
  }
  const primes=[...allPrimes].filter(c=>on.some(v=>matches(c,v))).sort();
  const chart=on.map(v=>({minterm:v,indices:primes.flatMap((p,i)=>matches(p,v)?[i]:[])}));
  const essential=[...new Set(chart.filter(x=>x.indices.length===1).map(x=>x.indices[0]))];
  let bestCost=Infinity,bestCount=Infinity,covers=[],visited=new Set();
  function search(selected){
    const key=[...selected].sort((a,b)=>a-b).join(',');if(visited.has(key))return;visited.add(key);
    const cost=[...selected].reduce((s,i)=>s+literals(primes[i]),0);
    if(cost>bestCost)return;
    const remaining=chart.filter(x=>!x.indices.some(i=>selected.has(i)));
    if(!remaining.length){
      if(cost<bestCost||(cost===bestCost&&selected.size<bestCount)){bestCost=cost;bestCount=selected.size;covers=[];}
      if(cost===bestCost&&selected.size===bestCount&&covers.length<32)covers.push([...selected].sort((a,b)=>a-b));return;
    }
    remaining.sort((a,b)=>a.indices.length-b.indices.length);
    for(const i of remaining[0].indices)search(new Set([...selected,i]));
  }
  search(new Set(essential));
  return {rounds,primes,chart,essential,covers,cost:bestCost,count:bestCount,expression:covers[0]?.map(i=>cubeExpression(primes[i])).join(' + ')||'0'};
}
export function bdd(n,on,order){
  if(order.length!==n||new Set(order).size!==n||order.some(x=>x<0||x>=n))throw Error('变量顺序必须是每个变量恰好出现一次。');
  const set=new Set(on),nodes=[],unique=new Map();
  function build(depth,assignment){
    if(depth===n)return set.has(assignment)?1:0;
    const variable=order[depth],mask=1<<(n-1-variable);
    const low=build(depth+1,assignment&~mask),high=build(depth+1,assignment|mask);
    if(low===high)return low;
    const key=[variable,low,high].join(':');if(unique.has(key))return unique.get(key);
    const id=nodes.length+2;nodes.push({id,variable,depth,low,high});unique.set(key,id);return id;
  }
  const root=build(0,0);return {root,nodes,count:nodes.length};
}
export function pulse(width,delay,mode='inertial'){
  if(!Number.isFinite(width)||!Number.isFinite(delay)||width<=0||delay<0)throw Error('脉宽必须 >0，延迟必须 ≥0。');
  const start=1,end=1+width,pass=mode==='transport'||width>=delay;
  const outputs=pass?[{t:start+delay,delta:delay===0?1:0,value:1},{t:end+delay,delta:delay===0?1:0,value:0}]:[];
  const events=[{t:start,delta:0,kind:'input',value:1},{t:end,delta:0,kind:'input',value:0},...outputs.map(e=>({...e,kind:'output'}))].sort((a,b)=>a.t-b.t||a.delta-b.delta||(a.kind==='output'?-1:1));
  let input=0,output=0,pending=[];
  const trace=events.map(e=>{if(e.kind==='input')input=e.value;else output=e.value;
    if(e.kind==='input'){
      if(!pass&&e.value===0)pending=[];
      else pending.push({t:e.t+delay,delta:delay===0?1:0,value:e.value});
    }else pending=pending.filter(o=>!(o.t===e.t&&o.delta===e.delta&&o.value===e.value));
    const action=!pass&&e.kind==='input'&&e.value===0?'短脉冲：撤销原定上升事务':`${e.kind==='input'?'输入':'输出'} ← ${e.value}`;
    return {...e,input,output,action,pending:pending.map(o=>`${o.t}ns/δ${o.delta}→${o.value}`),occupancy:pending.length};});
  return {outputs,trace,pass,horizon:end+delay+2,width,delay,mode};
}
export const faultSites=['a','b','c','n','y'];
export function circuit(v,fault=null){
  let a=(v>>2)&1,b=(v>>1)&1,c=v&1;
  const force=(site,x)=>fault&&fault.site===site?fault.value:x;
  a=force('a',a);b=force('b',b);c=force('c',c);const n=force('n',a&b);return {a,b,c,n,y:force('y',n|c)};
}
export function faultTable(selected=[]){
  const faults=faultSites.flatMap(site=>[0,1].map(value=>({id:`${site}/${value}`,site,value})));
  const rows=Array.from({length:8},(_,v)=>({v,good:circuit(v),detected:faults.map(f=>circuit(v).y!==circuit(v,f).y)}));
  const covered=faults.filter((f,i)=>selected.some(v=>rows[v]?.detected[i]));
  const groups=[];faults.forEach((f,i)=>{const signature=rows.map(r=>Number(r.detected[i])).join('');const g=groups.find(g=>g.signature===signature);if(g)g.faults.push(f.id);else groups.push({signature,faults:[f.id]});});
  return {faults,rows,covered,coverage:covered.length/faults.length,groups};
}
export function lfsr(seed,mask,n=4){
  if(!Number.isInteger(seed)||seed<0||seed>=2**n||!Number.isInteger(mask)||mask<0||mask>=2**n)throw Error('种子和抽头掩码必须是 0–15 的整数。');
  const seen=new Map(),trace=[];let state=seed;
  while(!seen.has(state)){seen.set(state,trace.length);let parity=0;for(let i=0;i<n;i++)parity^=((state&mask)>>i)&1;trace.push({step:trace.length,state,bits:bits(state,n),feedback:parity,output:state&1});state=(state>>1)|(parity<<(n-1));}
  return {trace,repeated:state,transient:seen.get(state),period:trace.length-seen.get(state)};
}
export function anneal(delta,T,r){
  if(![delta,T,r].every(Number.isFinite)||T<0||r<0||r>=1)throw Error('T ≥ 0，随机数 r 的范围是 [0,1)。');
  const p=delta<=0?1:T===0?0:Math.exp(-delta/T);return {p,accept:delta<=0||r<p};
}
