// Continuous differential-evolution search for low-card routes through two layers.
const SQRT3 = Math.sqrt(3), SAFE = 9;
const obstacles = [];
for (let i=-2;i<=2;i++) for (let j=-2;j<=2;j++) {
  if (!i && !j) continue;
  if (Math.max(Math.abs(i),Math.abs(j),Math.abs(i+j)) <= 2)
    obstacles.push([20*i+10*j,10*SQRT3*j]);
}

let seed = (Number(process.argv[2] ?? 0x5eed1234) >>> 0);
function random(){ seed=(1664525*seed+1013904223)>>>0; return seed/2**32; }
function segmentDistance(a,b,p){
  const vx=b[0]-a[0],vy=b[1]-a[1],wx=p[0]-a[0],wy=p[1]-a[1];
  const t=Math.max(0,Math.min(1,(wx*vx+wy*vy)/(vx*vx+vy*vy)));
  return Math.hypot(a[0]+t*vx-p[0],a[1]+t*vy-p[1]);
}
function route(x, allocation){
  let p=[0,0], heading=x[0], points=[[...p]];
  for(let k=0;k<allocation.length;k++){
    const length=x[1+k];
    p=[p[0]+length*Math.cos(heading),p[1]+length*Math.sin(heading)];
    points.push(p); heading+=x[1+allocation.length+k];
  }
  p=[p[0]+180*Math.cos(heading),p[1]+180*Math.sin(heading)]; points.push(p);
  return points;
}
function score(x,allocation){
  const points=route(x,allocation); let clearance=Infinity;
  for(let k=0;k<points.length-1;k++) for(const p of obstacles)
    clearance=Math.min(clearance,segmentDistance(points[k],points[k+1],p));
  const exit=Math.hypot(...points.at(-2));
  return Math.min(clearance, SAFE+(exit-48)*0.08);
}
function search(allocation,generations=1800,population=180){
  const m=allocation.length;
  const bounds=[[-Math.PI,Math.PI],...Array.from({length:m},()=>[0.2,65]),...allocation.map(c=>[-c*5*Math.PI/180,c*5*Math.PI/180])];
  const pop=Array.from({length:population},()=>bounds.map(([a,b])=>a+random()*(b-a)));
  const values=pop.map(x=>score(x,allocation));
  for(let g=0;g<generations;g++) for(let i=0;i<population;i++){
    let a,b,c; do a=Math.floor(random()*population);while(a===i); do b=Math.floor(random()*population);while(b===i||b===a); do c=Math.floor(random()*population);while(c===i||c===a||c===b);
    const trial=pop[i].slice(), forced=Math.floor(random()*trial.length), F=0.55+0.35*random();
    for(let d=0;d<trial.length;d++) if(random()<0.82||d===forced){
      const [lo,hi]=bounds[d]; trial[d]=Math.max(lo,Math.min(hi,pop[a][d]+F*(pop[b][d]-pop[c][d])));
    }
    const v=score(trial,allocation); if(v>values[i]){pop[i]=trial;values[i]=v;}
  }
  const best=values.indexOf(Math.max(...values)), x=pop[best], points=route(x,allocation);
  return {allocation,cards:allocation.reduce((a,b)=>a+b,0),minimumDistance:values[best],safe:values[best]>=SAFE,
    initialHeadingDegrees:x[0]*180/Math.PI,lengths:x.slice(1,1+m),turnsDegrees:x.slice(1+m).map(v=>v*180/Math.PI),points};
}

const allocations=process.argv.length>3
  ? [process.argv.slice(3).map(Number)]
  : [[3,3,2],[3,2,3],[2,3,3],[4,2,2],[2,4,2],[2,2,4],[2,2,2,2],[3,2,2,1],[2,3,2,1],[2,2,3,1]];
let best=null;
for(const allocation of allocations){
  const result=search(allocation);
  console.log(JSON.stringify(result));
  if(!best||result.minimumDistance>best.minimumDistance)best=result;
  if(result.safe) break;
}
console.error('BEST',JSON.stringify(best,null,2));
console.log('BEST_ONELINE',JSON.stringify(best));
