// 独立验收第三问100卡候选：把候选程序的 JSON 输出转成硬性证书断言。
import { execFileSync } from 'node:child_process';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const node = process.execPath;
const candidate = fileURLToPath(new URL('./q3-100card-candidate.mjs', import.meta.url));
const raw = execFileSync(node, [candidate], { encoding: 'utf8' });
const result = JSON.parse(raw);
const expected = {
  acceleration: 19,
  turn: 81,
  deceleration: 0,
  total: 100,
  radius: 94.51063611915748,
  margin: 0.0007594591366935077,
};

const close = (actual, target, tolerance) => Math.abs(actual - target) <= tolerance;
const errors = [];
if (JSON.stringify(result.cards) !== JSON.stringify({ acceleration: 19, turn: 81, deceleration: 0, total: 100 })) {
  errors.push(`卡片分配不符：${JSON.stringify(result.cards)}`);
}
if (!close(result.conservativeReachableRadiusMeters, expected.radius, 1e-9)) {
  errors.push(`保守终点半径不符：${result.conservativeReachableRadiusMeters}`);
}
if (result.certifiedContinuousSafetyMarginMeters < expected.margin - 1e-12) {
  errors.push(`连续安全余量不足：${result.certifiedContinuousSafetyMarginMeters}`);
}
if (result.certifiedContinuousClearanceLowerBoundMeters < 9) {
  errors.push(`连续安全下界小于9米：${result.certifiedContinuousClearanceLowerBoundMeters}`);
}
if (errors.length) throw new Error(errors.join('\n'));
console.log(JSON.stringify({
  ok: true,
  cards: result.cards,
  certifiedReachableRadiusMeters: result.conservativeReachableRadiusMeters,
  certifiedClearanceMeters: result.certifiedContinuousClearanceLowerBoundMeters,
  certifiedSafetyMarginMeters: result.certifiedContinuousSafetyMarginMeters,
  firstCollisionBoundaryRadiusMeters: result.collisionBoundaryRadiusMeters,
}, null, 2));
