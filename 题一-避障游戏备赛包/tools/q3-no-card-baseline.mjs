// 第三问“完全不用卡”的可复算基线。障碍物逆时针公转。
const SQRT3=Math.sqrt(3), omega=Math.PI/30, speed=10, safety=9;

function nearestDistance(x,y){
  const jf=y/(10*SQRT3), ifloat=(x-10*jf)/20;
  const i0=Math.round(ifloat), j0=Math.round(jf);
  let best=Infinity, site=null;
  for(let i=i0-2;i<=i0+2;i++) for(let j=j0-2;j<=j0+2;j++){
    if(i===0&&j===0) continue;
    const px=20*i+10*j, py=10*SQRT3*j;
    const d=Math.hypot(x-px,y-py);
    if(d<best){best=d;site=[i,j,px,py];}
  }
  return {distance:best,site};
}

function clearance(phi,t){
  // 固定系机器人沿phi直行；旋转系位置的极角为phi-omega*t。
  const r=speed*t, a=phi-omega*t;
  return {...nearestDistance(r*Math.cos(a),r*Math.sin(a)),r,t};
}

function firstCollision(phi,dt=0.001,tMax=120){
  let prev=clearance(phi,0);
  for(let t=dt;t<=tMax;t+=dt){
    const now=clearance(phi,t);
    if(now.distance<safety){
      let lo=t-dt,hi=t;
      for(let k=0;k<50;k++){
        const mid=(lo+hi)/2;
        if(clearance(phi,mid).distance>=safety)lo=mid;else hi=mid;
      }
      return clearance(phi,lo);
    }
    prev=now;
  }
  return prev;
}

let best=null;
for(let k=0;k<=1200;k++){
  const phi=(Math.PI/3)*k/1200;
  const hit=firstCollision(phi,0.002,60);
  if(!best||hit.r>best.r)best={...hit,phi};
}
// 在最佳粗角附近细化。
let refined=best;
for(let k=-1000;k<=1000;k++){
  const phi=best.phi+k*(Math.PI/3/1200)/1000;
  const hit=firstCollision(phi,0.0002,60);
  if(hit.r>refined.r)refined={...hit,phi};
}
console.log(JSON.stringify({
  model:'no cards, speed 10 m/s, obstacles rotate CCW with period 60 s',
  initialDirectionDegrees:refined.phi*180/Math.PI,
  firstCollisionTimeSeconds:refined.t,
  straightLineDistanceMeters:refined.r,
  limitingSite:refined.site,
  clearanceMeters:refined.distance,
  status:'numerical lower-bound baseline; grid/time refinement required for publication'
},null,2));
