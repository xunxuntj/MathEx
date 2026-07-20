// 可复算的100卡下界候选：28张加速卡 + 72张转向卡的安全中线构造。
const SQRT3=Math.sqrt(3), omega=Math.PI/30, safety=9;
const h=20*SQRT3/6;
const path=[[0,0],[10,h],[20,2*h],[30,h],[40,2*h],[40,4*h],[50,5*h],[60,4*h],[70,5*h]];
function angle(a,b,c){
  const u=[b[0]-a[0],b[1]-a[1]],v=[c[0]-b[0],c[1]-b[1]];
  return Math.abs(Math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1])*180/Math.PI);
}
const turnAngles=path.slice(1,-1).map((b,k)=>angle(path[k],b,path[k+2])).filter(x=>x>1e-8);
const turnCards=turnAngles.map(x=>Math.ceil((x-1e-10)/5));
const accelerationCards=100-turnCards.reduce((a,b)=>a+b,0);
const speed=10*1.25**accelerationCards;

function nearest(x,y){
  const jf=y/(10*SQRT3), ifloat=(x-10*jf)/20;
  const i0=Math.round(ifloat),j0=Math.round(jf);
  let best=Infinity,site=null;
  for(let i=i0-2;i<=i0+2;i++)for(let j=j0-2;j<=j0+2;j++){
    if(i===0&&j===0)continue;
    const px=20*i+10*j,py=10*SQRT3*j,d=Math.hypot(x-px,y-py);
    if(d<best){best=d;site=[i,j,px,py];}
  }
  return {distance:best,site};
}

function rotateBack(p,t){
  const a=-omega*t,c=Math.cos(a),s=Math.sin(a);
  return [c*p[0]-s*p[1],s*p[0]+c*p[1]];
}

const segments=[]; let elapsed=0,totalLength=0;
for(let k=0;k<path.length-1;k++){
  const a=path[k],b=path[k+1],len=Math.hypot(b[0]-a[0],b[1]-a[1]);
  segments.push({a,b,len,startTime:elapsed,startS:totalLength});
  elapsed+=len/speed; totalLength+=len;
}
const last=path.at(-1),before=path.at(-2),lastLen=Math.hypot(last[0]-before[0],last[1]-before[1]);
const direction=[(last[0]-before[0])/lastLen,(last[1]-before[1])/lastLen];

function stateAtS(s){
  let p,t;
  if(s<=totalLength){
    const seg=segments.find(z=>s<=z.startS+z.len+1e-12)??segments.at(-1);
    const u=Math.max(0,Math.min(1,(s-seg.startS)/seg.len));
    p=[seg.a[0]+u*(seg.b[0]-seg.a[0]),seg.a[1]+u*(seg.b[1]-seg.a[1])];
    t=seg.startTime+(s-seg.startS)/speed;
  }else{
    const extra=s-totalLength;p=[last[0]+extra*direction[0],last[1]+extra*direction[1]];t=elapsed+extra/speed;
  }
  const q=rotateBack(p,t),near=nearest(q[0],q[1]);
  return {s,p,q,t,...near,radius:Math.hypot(p[0],p[1])};
}

let minBefore={distance:Infinity},hit=null;
// 从起点开始检查首次碰撞；若折线路线走完仍安全，再沿末方向继续。
for(let s=0.002;s<=totalLength+500;s+=0.002){
  const now=stateAtS(s);
  if(now.distance<minBefore.distance)minBefore=now;
  if(now.distance<safety){
    let lo=s-0.002,hi=s;
    for(let k=0;k<60;k++){const mid=(lo+hi)/2;if(stateAtS(mid).distance>=safety)lo=mid;else hi=mid;}
    hit=stateAtS(lo);break;
  }
}
if(!hit)throw new Error('500米延长范围内未找到碰撞');
const conservative=stateAtS(Math.max(0,hit.s-0.02));
console.log(JSON.stringify({
  cards:{acceleration:accelerationCards,turn:turnCards.reduce((a,b)=>a+b,0),deceleration:0,total:100},
  speedMetersPerSecond:speed,
  turnAnglesDegrees:turnAngles,
  turnCardBreakdown:turnCards,
  waypointPath:path,
  minimumSampledClearanceBeforeDetectedCollisionMeters:minBefore.distance,
  firstCollisionTimeSeconds:hit.t,
  collisionBoundaryRadiusMeters:hit.radius,
  conservativeReachableRadiusMeters:conservative.radius,
  conservativeClearanceMeters:conservative.distance,
  conservativeSafetyMarginMeters:conservative.distance-safety,
  collisionSite:hit.site,
  numericalStepMeters:0.002,
  status:'explicit 100-card schedule; distance immediately before first collision is a feasible lower bound, not a global optimum'
},null,2));
