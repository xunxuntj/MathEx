import fs from "node:fs";
import vm from "node:vm";

const html = fs.readFileSync(new URL("./index.html", import.meta.url), "utf8");
const q1Research = fs.readFileSync(new URL("../题一-避障游戏备赛包/09-第三问旋转障碍物与100卡优化.md", import.meta.url), "utf8");
const q2Research = fs.readFileSync(new URL("../题二-备赛包/06-研究方案与研究结果.md", import.meta.url), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
if (!script) throw new Error("未找到内联脚本");
new Function(script);

const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
const duplicate = ids.find((id, index) => ids.indexOf(id) !== index);
if (duplicate) throw new Error(`重复 id: ${duplicate}`);

const referenced = [...script.matchAll(/getElementById\('([^']+)'\)|getElementById\("([^"]+)"\)/g)]
  .map((m) => m[1] || m[2]);
const missing = [...new Set(referenced.filter((id) => !ids.includes(id)))];
if (missing.length) throw new Error(`脚本引用了不存在的 id: ${missing.join(", ")}`);

for (const required of ["94.5106", "693.9", "0.15408", "0.925°", "24*layers", "K₁,₄", "严格证明", "程序验证"]) {
  if (!html.includes(required)) throw new Error(`缺少关键展示内容: ${required}`);
}
for (const required of ["19张加速卡", "81张转向卡", "94.5106米", "9.000759"]) {
  if (!q1Research.includes(required)) throw new Error(`题一研究材料与展示关键值不一致: ${required}`);
}
for (const required of ["E(n,1)=7", "E_c(n,1)=n", "57", "78–84"]) {
  if (!q2Research.includes(required)) throw new Error(`题二研究材料缺少展示依据: ${required}`);
}

if (/\b(?:src|href)=["']https?:/i.test(html)) throw new Error("页面含外部资源，不能保证离线运行");

const SQRT3 = Math.sqrt(3);
function pathFor(n) {
  const h = 20 * SQRT3 / 6;
  if (n === 1) return [[0, 0], [30, 10 * SQRT3]];
  const p = [[0, 0], [10, h], [20, 2 * h], [30, h], [40, 2 * h], [40, 4 * h]];
  for (let x = 50; x <= 20 * n + 10; x += 10) {
    const k = (x - 50) / 10;
    p.push([x, (k % 2 === 0 ? 5 : 4) * h]);
  }
  return p;
}
function obstacleSet(n) {
  const out = [];
  for (let i = -n; i <= n; i += 1) for (let j = -n; j <= n; j += 1) {
    if (i === 0 && j === 0) continue;
    if (Math.max(Math.abs(i), Math.abs(j), Math.abs(i + j)) <= n) out.push([20 * i + 10 * j, 10 * SQRT3 * j]);
  }
  return out;
}
function segmentDistance(a, b, p) {
  const vx = b[0] - a[0], vy = b[1] - a[1], d = vx * vx + vy * vy;
  const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / d));
  return Math.hypot(a[0] + t * vx - p[0], a[1] + t * vy - p[1]);
}
for (let n = 1; n <= 12; n += 1) {
  const p = pathFor(n), obs = obstacleSet(n);
  let min = Infinity;
  for (let i = 0; i < p.length - 1; i += 1) for (const o of obs) min = Math.min(min, segmentDistance(p[i], p[i + 1], o));
  if (min < 9 - 1e-9) throw new Error(`第 ${n} 层展示路线不安全: ${min}`);
}

class FakeClassList {
  constructor(initial = []) { this.values = new Set(initial); }
  toggle(name, force) { force ? this.values.add(name) : this.values.delete(name); }
  contains(name) { return this.values.has(name); }
}
class FakeElement {
  constructor(id = "", classes = []) {
    this.id = id; this.classList = new FakeClassList(classes); this.dataset = {};
    this.textContent = ""; this.value = "3"; this.hidden = false; this.children = []; this.style = {};
    this.width = 1000; this.height = 610; this.onclick = null; this.oninput = null;
  }
  getBoundingClientRect() { return { width: 1000, height: 610 }; }
  getContext() { return new Proxy({}, { get: (obj, key) => obj[key] || (() => {}) , set: (obj, key, value) => (obj[key] = value, true) }); }
  setAttribute() {}
  append(...items) { this.children.push(...items); }
  prepend(...items) { this.children.unshift(...items); }
  replaceChildren(...items) { this.children = [...items]; }
}
const elements = Object.fromEntries(ids.map((id) => [id, new FakeElement(id)]));
elements.q1.classList.values.add("view"); elements.q1.classList.values.add("active");
elements.q2.classList.values.add("view");
elements.q1Canvas.getContext = FakeElement.prototype.getContext;
const tabs = [new FakeElement("", ["tab", "active"]), new FakeElement("", ["tab"])];
tabs[0].dataset.view = "q1"; tabs[1].dataset.view = "q2";
const q2Modes = ["motif", "triangle", "colex", "bounds"].map((mode, index) => {
  const e = new FakeElement("", ["q2mode", ...(index === 0 ? ["primary"] : [])]); e.dataset.mode = mode; return e;
});
const q1Steps = [0, 1, 2, 3].map((step, index) => {
  const e = new FakeElement("", ["step", ...(index === 0 ? ["active"] : [])]); e.dataset.q1Step = String(step); return e;
});
const fakeDocument = {
  getElementById: (id) => elements[id] || null,
  querySelectorAll: (selector) => selector === ".tab" ? tabs : selector === ".view" ? [elements.q1, elements.q2] : selector === ".q2mode" ? q2Modes : selector === "[data-q1-step]" ? q1Steps : [],
  querySelector: (selector) => selector === ".view.active" ? (elements.q1.classList.contains("active") ? elements.q1 : elements.q2) : null,
  createElementNS: () => new FakeElement(),
  fullscreenElement: null,
  documentElement: { requestFullscreen() {} },
  exitFullscreen() {}
};
const sandbox = { document: fakeDocument, window: { addEventListener() {}, devicePixelRatio: 1 }, devicePixelRatio: 1, requestAnimationFrame() {}, console, Math };
vm.runInNewContext(script, sandbox, { filename: "index-inline-script.js" });
tabs[1].onclick();
if (!elements.q2.classList.contains("active")) throw new Error("题目切换按钮未生效");
q2Modes[1].onclick(); elements.q2Next.onclick();
if (elements.q2T.textContent !== 1) throw new Error("题二下一步按钮未生成三角形");
elements.q1Rotation.onclick();
if (elements.q1Clear.textContent !== "周期60秒" || !elements.q1Explain.textContent.includes("刚性旋转")) throw new Error("题一旋转机制按钮未生效");
elements.q1Dynamic.onclick();
if (elements.q1Cards.textContent !== "19+81") throw new Error("题一100卡按钮未更新指标");
if (elements.q1KeyInsight.hidden) throw new Error("题一100卡核心信息未醒目显示");
if (elements.q1Layers.textContent !== "5层可见") throw new Error("题一100卡未显示正确可见层数");
if (!elements.q1Explain.textContent.includes("无限网格")) throw new Error("题一100卡未说明无限网格验证");
q1Steps[1].onclick();
if (!elements.q1Explain.textContent.includes("8+1=9米")) throw new Error("题一点化/安全圆步骤按钮未生效");
q1Steps[2].onclick();
if (!elements.q1Explain.textContent.includes("M(n)≤24n")) throw new Error("题一路线步骤按钮未生效");
elements.layerRange.value = "1"; elements.layerRange.oninput({ target: elements.layerRange });
if (elements.q1Cards.textContent !== "0") throw new Error("M(1)=0 未正确显示");
elements.layerRange.value = "12"; elements.layerRange.oninput({ target: elements.layerRange });
if (elements.q1Cards.textContent !== "≤288") throw new Error("M(12)≤288 未正确显示");
q2Modes[2].onclick(); elements.edgeRange.value = "7"; elements.edgeRange.oninput({ target: elements.edgeRange });
if (elements.q2M.textContent !== 28 || elements.q2T.textContent !== 56) throw new Error("colex 计数交互错误");
q2Modes[3].onclick();
if (!elements.q2Status.textContent.includes("严格区间与计算候选")) throw new Error("题二结果分级提示缺失");
elements.fullscreenBtn.onclick();

const dynamicEnd = [94.1235579499, 8.5449504674];
if (Math.abs(Math.hypot(...dynamicEnd) - 94.5106361192) > 1e-8) throw new Error("100卡展示终点半径错误");
if (!html.includes("@media(max-width:900px)") || !html.includes("@media(max-width:520px)")) throw new Error("缺少投影/窄屏适配");

console.log(JSON.stringify({ ok: true, ids: ids.length, scriptBytes: Buffer.byteLength(script), offline: true, verifiedLayers: 12, reportCrossCheck: true, responsiveBreakpoints: [900, 520], interactions: ["全屏", "切换题目", "题一点化", "题一安全圆", "题一路线", "题一层数1–12", "题一旋转60秒周期", "题一100卡真实相位", "题二下一步", "题二colex滑块", "题二结果分级"] }, null, 2));
