// Aim at the positions that honeycomb gap centers have when the robot arrives.
const SQRT3=Math.sqrt(3),H=10*SQRT3/3,OMEGA=Math.PI/30,SAFE=9;
function rotate(p,t){const a=OMEGA*t,c=Math.cos(a),s=Math.sin(a);return[c*p[0]-s*p[1],s*p[0]+c*p[1]];}
function intercept(from,t0,target,speed){
  let lo=t0,hi=t0+Math.hypot(target[0]-from[0],target[1]-from[1])/speed+1;
  const f=t=>Math.hypot(...rotate(target,t).map((v,i)=>v-from[i]))-speed*(t-t0);
  while(f(hi)>0)hi=2*hi-t0;
  for(let k=0;k<70;k++){const mid=(lo+hi)/2;if(f(mid)>0)lo=mid;else hi=mid;}
  return {time:hi,point:rotate(target,hi)};
}
function nearest(x,y){
  const jf=y/(10*SQRT3),fi=(x-10*jf)/20,i0=Math.round(fi),j0=Math.round(jf);let best=Infinity,site;
  for(let i=i0-2;i<=i0+2;i++)for(let j=j0-2;j<=j0+2;j++)if(i||j){const d=Math.hypot(x-20*i-10*j,y-10*SQRT3*j);if(d<best){best=d;site=[i,j];}}
  return[best,site];
}
function cards(path){let total=0,angles=[];for(let k=1;k<path.length-1;k++){
  const a=path[k-1],b=path[k],c=path[k+1],u=[b[0]-a[0],b[1]-a[1]],v=[c[0]-b[0],c[1]-b[1]];
  const angle=Math.abs(Math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1])*180/Math.PI);angles.push(angle);total+=Math.ceil((angle-1e-9)/5);
  }return{total,angles};}
function verify(path,speed,step=.02){
  let time=0,bestRadius=0,minDistance=Infinity,hit;
  const a=path.at(-2),b=path.at(-1),L=Math.hypot(b[0]-a[0],b[1]-a[1]),extended=[...path,[b[0]+400*(b[0]-a[0])/L,b[1]+400*(b[1]-a[1])/L]];
  for(let k=0;k<extended.length-1&&!hit;k++){
    const p=extended[k],q=extended[k+1],len=Math.hypot(q[0]-p[0],q[1]-p[1]),ux=(q[0]-p[0])/len,uy=(q[1]-p[1])/len;
    for(let z=step;z<=len+1e-9;z+=step){const d=Math.min(z,len),x=p[0]+ux*d,y=p[1]+uy*d,t=time+d/speed,ang=-OMEGA*t,c=Math.cos(ang),s=Math.sin(ang),[clearance,site]=nearest(c*x-s*y,s*x+c*y),radius=Math.hypot(x,y);
      minDistance=Math.min(minDistance,clearance);if(clearance<SAFE){hit={radius,time:t,site,clearance};break;}bestRadius=Math.max(bestRadius,radius);}
    time+=len/speed;
  }return{bestRadius,minDistance,hit};
}
function build(acceleration,count){
  const speed=10*1.25**acceleration,path=[[0,0]];let time=0,from=[0,0];
  for(let k=1;k<=count;k++){
    const target=[10*k,(k%2?1:2)*H],arrival=intercept(from,time,target,speed);path.push(arrival.point);from=arrival.point;time=arrival.time;
  }
  return{path,speed,...cards(path)};
}
let best=null;
for(let acceleration=0;acceleration<=30;acceleration++)for(let count=2;count<=16;count++){
  const route=build(acceleration,count);if(acceleration+route.total>100)continue;
  const result={acceleration,turns:route.total,unused:100-acceleration-route.total,speed:route.speed,angles:route.angles,path:route.path,...verify(route.path,route.speed)};
  if(!best||result.bestRadius>best.bestRadius){best=result;console.error('BEST',JSON.stringify(best));}
}
console.log(JSON.stringify(best,null,2));
