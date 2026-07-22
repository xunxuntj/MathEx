// Enumerate honeycomb-center routes, then verify them in the rotating frame.
const SQRT3=Math.sqrt(3), H=10*SQRT3/3, OMEGA=Math.PI/30, SAFE=9;
const centers=[];
for(let i=-12;i<=12;i++)for(let j=-12;j<=12;j++){
  const x=20*i+10*j,y=10*SQRT3*j;
  centers.push([x+10,y+H],[x+10,y-H]);
}
const key=p=>`${Math.round(p[0]*1e6)},${Math.round(p[1]*1e6)}`;
const byKey=new Map(centers.map(p=>[key(p),p]));
function neighbors(p){
  const out=[];
  for(const q of centers) if(Math.abs(Math.hypot(q[0]-p[0],q[1]-p[1])-2*H)<1e-7) out.push(q);
  return out;
}
const adjacency=new Map([...byKey].map(([k,p])=>[k,neighbors(p)]));
function nearest(q){
  const jf=q[1]/(10*SQRT3),fi=(q[0]-10*jf)/20,i0=Math.round(fi),j0=Math.round(jf);
  let best=Infinity,site;
  for(let i=i0-2;i<=i0+2;i++)for(let j=j0-2;j<=j0+2;j++)if(i||j){
    const d=Math.hypot(q[0]-20*i-10*j,q[1]-10*SQRT3*j);if(d<best){best=d;site=[i,j];}
  }
  return [best,site];
}
function cardCount(path){
  let cards=0;
  for(let k=1;k<path.length-1;k++){
    const a=path[k-1],b=path[k],c=path[k+1],u=[b[0]-a[0],b[1]-a[1]],v=[c[0]-b[0],c[1]-b[1]];
    const angle=Math.abs(Math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1])*180/Math.PI);
    cards+=Math.ceil((angle-1e-8)/5);
  }
  return cards;
}
function verify(path,step=.02){
  const turns=cardCount(path);if(turns>100)return null;
  const acceleration=100-turns,speed=10*1.25**acceleration;
  let elapsed=0,s=0,bestRadius=0,minDistance=Infinity,collision=null;
  const extended=path.map(p=>[...p]);
  const a=extended.at(-2),b=extended.at(-1),len=Math.hypot(b[0]-a[0],b[1]-a[1]);
  extended.push([b[0]+500*(b[0]-a[0])/len,b[1]+500*(b[1]-a[1])/len]);
  for(let k=0;k<extended.length-1&&!collision;k++){
    const p=extended[k],q=extended[k+1],L=Math.hypot(q[0]-p[0],q[1]-p[1]),ux=(q[0]-p[0])/L,uy=(q[1]-p[1])/L;
    for(let z=step;z<=L+1e-9;z+=step){
      const d=Math.min(z,L),x=p[0]+ux*d,y=p[1]+uy*d,t=elapsed+d/speed,ang=-OMEGA*t,c=Math.cos(ang),sn=Math.sin(ang);
      const rotated=[c*x-sn*y,sn*x+c*y],[clearance,site]=nearest(rotated),radius=Math.hypot(x,y);
      minDistance=Math.min(minDistance,clearance);
      if(clearance<SAFE){collision={radius,time:t,site,clearance};break;}
      bestRadius=Math.max(bestRadius,radius);
    }
    elapsed+=L/speed;s+=L;
  }
  return {turns,acceleration,speed,bestRadius,minDistance,collision,path};
}

const start=[10,H], first=[20,2*H];
let frontier=[[ [0,0],start,first ]], best=null;
for(let depth=2;depth<=10;depth++){
  const next=[];
  for(const path of frontier){
    const result=verify(path);
    if(result&&(!best||result.bestRadius>best.bestRadius)){best=result;console.error('BEST',JSON.stringify({...best,path:best.path}));}
    const prev=path.at(-2),last=path.at(-1);
    for(const q of adjacency.get(key(last))??[]) if(key(q)!==key(prev)) next.push([...path,q]);
  }
  frontier=next;
}
console.log(JSON.stringify(best,null,2));
