const SQRT3 = Math.sqrt(3);
const spacing = 20;
const radius = 9;

const routes = {
  twoLayer9: [[0,0],[1.079,-19.223],[2.074,-21.84],[7.805,-29.963],[18.308,-52.191]],
  threeLayer27: [[0,0],[-1.233,6.358],[-1.768,10.909],[-0.158,20.09],[8.667,30.865],[10.791,37.25],[13.933,42.087],[18.671,48.053],[20.929,53.624],[24.652,64.975],[26.678,73.296]],
  threeLayerMidline: [[0,0],[10,spacing*SQRT3/6],[20,2*spacing*SQRT3/6],[30,spacing*SQRT3/6],[40,2*spacing*SQRT3/6],[40,4*spacing*SQRT3/6],[50,5*spacing*SQRT3/6],[60,4*spacing*SQRT3/6],[70,5*spacing*SQRT3/6]],
};

function obstacles(maxLayer) {
  const out = [];
  for (let i = -maxLayer; i <= maxLayer; i++) {
    for (let j = -maxLayer; j <= maxLayer; j++) {
      if (i === 0 && j === 0) continue;
      const layer = Math.max(Math.abs(i), Math.abs(j), Math.abs(i + j));
      if (layer <= maxLayer) out.push({i,j,layer,x:spacing*i+spacing*j/2,y:spacing*SQRT3*j/2});
    }
  }
  return out;
}

function segmentDistance(a,b,p) {
  const vx=b[0]-a[0], vy=b[1]-a[1], wx=p.x-a[0], wy=p.y-a[1];
  const denom=vx*vx+vy*vy;
  const t=Math.max(0,Math.min(1,denom ? (wx*vx+wy*vy)/denom : 0));
  const q=[a[0]+t*vx,a[1]+t*vy];
  return {distance:Math.hypot(q[0]-p.x,q[1]-p.y),t,q};
}

function turn(a,b,c) {
  const u=[b[0]-a[0],b[1]-a[1]], v=[c[0]-b[0],c[1]-b[1]];
  const dot=u[0]*v[0]+u[1]*v[1];
  const cross=u[0]*v[1]-u[1]*v[0];
  return Math.abs(Math.atan2(cross,dot)*180/Math.PI);
}

function verify(name,path,maxLayer) {
  let closest={distance:Infinity};
  const obs=obstacles(maxLayer);
  path.slice(0,-1).forEach((a,k)=>obs.forEach(o=>{
    const hit=segmentDistance(a,path[k+1],o);
    if(hit.distance<closest.distance) closest={...hit,segment:k,obstacle:o};
  }));
  const turns=path.slice(1,-1).map((b,k)=>turn(path[k],b,path[k+2]));
  const cards=turns.map(x=>Math.ceil((x-1e-10)/5));
  return {name,maxLayer,obstacleCount:obs.length,closest,turns,cards,totalCards:cards.reduce((a,b)=>a+b,0),safe:closest.distance+1e-9>=radius};
}

for (const result of [verify('twoLayer9',routes.twoLayer9,2),verify('threeLayer27',routes.threeLayer27,3),verify('threeLayerMidline',routes.threeLayerMidline,3)]) {
  console.log(JSON.stringify(result,null,2));
}
