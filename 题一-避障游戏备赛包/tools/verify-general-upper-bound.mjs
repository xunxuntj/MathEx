const SQRT3=Math.sqrt(3),spacing=20,radius=9,h=spacing*SQRT3/6;
function pathFor(n){
  if(n===1)return [[0,0],[30,Math.sqrt(3)*10]];
  const p=[[0,0],[10,h],[20,2*h],[30,h],[40,2*h],[40,4*h]];
  for(let x=50;x<=20*n+10;x+=10){
    const k=(x-50)/10;p.push([x,(k%2===0?5:4)*h]);
  }
  return p;
}
function obstacles(n){const o=[];for(let i=-n;i<=n;i++)for(let j=-n;j<=n;j++){
  if(i===0&&j===0)continue;const layer=Math.max(Math.abs(i),Math.abs(j),Math.abs(i+j));
  if(layer<=n)o.push({i,j,x:20*i+10*j,y:10*SQRT3*j});
}return o;}
function segDist(a,b,p){const vx=b[0]-a[0],vy=b[1]-a[1],d=vx*vx+vy*vy;
  const t=Math.max(0,Math.min(1,((p.x-a[0])*vx+(p.y-a[1])*vy)/d));
  return Math.hypot(a[0]+t*vx-p.x,a[1]+t*vy-p.y);}
function angle(a,b,c){const u=[b[0]-a[0],b[1]-a[1]],v=[c[0]-b[0],c[1]-b[1]];
  return Math.abs(Math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1])*180/Math.PI);}
function verify(n){const p=pathFor(n),obs=obstacles(n);let min=Infinity;
  for(let k=0;k<p.length-1;k++)for(const o of obs)min=Math.min(min,segDist(p[k],p[k+1],o));
  const turns=p.slice(1,-1).map((b,k)=>angle(p[k],b,p[k+2])).filter(x=>x>1e-8);
  const cards=turns.reduce((s,x)=>s+Math.ceil((x-1e-10)/5),0);
  return {n,points:p.length,turns:turns.length,cards,minDistance:min,safe:min+1e-9>=radius,endpoint:p.at(-1)};
}
const results=[];for(let n=1;n<=20;n++)results.push(verify(n));
if(results.some(x=>!x.safe))throw new Error('通用构造在n<=20验证中失败');
console.log(JSON.stringify(results,null,2));
