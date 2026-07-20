import fs from 'node:fs';

const file = new URL('../../三层路径演示/index.html', import.meta.url);
const html = fs.readFileSync(file, 'utf8');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(m => m[1]);
const external = [...html.matchAll(/<(?:script|link|img)[^>]+(?:src|href)=["']([^"']+)["']/gi)]
  .map(m => m[1]).filter(x => /^(?:https?:)?\/\//i.test(x));

if (!scripts.length) throw new Error('未找到内嵌脚本');
for (const source of scripts) new Function(source);
if (external.length) throw new Error(`发现外部依赖：${external.join(', ')}`);

for (const id of ['board','playBtn','resetBtn','twoLayerRouteBtn','safeRouteBtn','betterRouteBtn','showGrid','showSafety','showLabels']) {
  if (!html.includes(`id="${id}"`)) throw new Error(`缺少控件：${id}`);
}

console.log(JSON.stringify({file:decodeURIComponent(file.pathname),inlineScripts:scripts.length,externalDependencies:external.length,syntax:'ok',requiredControls:'ok'},null,2));
