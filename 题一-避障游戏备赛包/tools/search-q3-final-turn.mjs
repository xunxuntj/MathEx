// Search the tradeoff between acceleration and one additional terminal turn.
const SQRT3=Math.sqrt(3),H=10*SQRT3/3,OMEGA=Math.PI/30,SAFE=9;
const base=[[0,0],[10,H],[20,2*H],[30,H],[40,2*H],[50,H],[60,2*H],[70,H],[80,2*H]];
function nearest(x,y){
  const jf=y/(10*SQRT3),fi=(x-10*jf)/20,i0=Math.round(fi),j0=Math.round(jf);let best=Infinity,site;
  for(let i=i0-2;i<=i0+2;i++)for(let j=j0-2;j<=j0+2;j++)if(i||j){const d=Math.hypot(x-20*i-10*j,y-10*SQRT3*j);if(d<best){best=d;site=[i,j];}}
  return [best,site];
}
function evaluate(acceleration,deltaDegrees,step=.05){
  const speed=10*1.25**acceleration,delta=deltaDegrees*Math.PI/180;
  const prev=base.at(-2),last=base.at(-1),heading=Math.atan2(last[1]-prev[1],last[0]-prev[0])+delta;
  const path=[...base,[last[0]+300*Math.cos(heading),last[1]+300*Math.sin(heading)]];
  let elapsed=0,bestRadius=0,hit=null,minDistance=Infinity;
  for(let k=0;k<path.length-1&&!hit;k++){
    const a=path[k],b=path[k+1],L=Math.hypot(b[0]-a[0],b[1]-a[1]),ux=(b[0]-a[0])/L,uy=(b[1]-a[1])/L;
    for(let z=step;z<=L+1e-9;z+=step){
      const d=Math.min(z,L),x=a[0]+ux*d,y=a[1]+uy*d,t=elapsed+d/speed,ang=-OMEGA*t,c=Math.cos(ang),s=Math.sin(ang);
      const [clearance,site]=nearest(c*x-s*y,s*x+c*y),radius=Math.hypot(x,y);minDistance=Math.min(minDistance,clearance);
      if(clearance<SAFE){hit={radius,time:t,site,clearance};break;}bestRadius=Math.max(bestRadius,radius);
    }
    elapsed+=L/speed;
  }
  return {acceleration,terminalTurnCards:Math.ceil((Math.abs(deltaDegrees)-1e-9)/5),deltaDegrees,speed,bestRadius,minDistance,hit};
}
let best=null;
for(let cards=1;cards<=20;cards++){
  const maxAcceleration=100-72-cards;
  for(let acceleration=Math.max(0,maxAcceleration-8);acceleration<=maxAcceleration;acceleration++){
    for(const sign of [-1,1])for(let mag=Math.max(0,(cards-1)*5)+.25;mag<=cards*5+1e-9;mag+=.25){
      const r=evaluate(acceleration,sign*mag);if(!best||r.bestRadius>best.bestRadius){best=r;console.error('BEST',JSON.stringify(best));}
    }
  }
}
console.log(JSON.stringify(best,null,2));
