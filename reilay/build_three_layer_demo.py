#!/usr/bin/env python3
"""Build an HTML demo for the first three obstacle layers."""

from __future__ import annotations

import json
import math
from pathlib import Path

from corridor_search import Point, cards_for_turn, obstacles, path_clearance, turn_angle_deg
from draw_layers import labeled_channel_points


OUT = Path("three_layer_demo_reilay.html")


def nearest_label(p: Point, labels):
    label, q = min(labels, key=lambda item: (p - item[1]).norm())
    return label


def main() -> int:
    data = json.loads(Path("labeled_corridor_result_refined_g0p3.json").read_text(encoding="utf-8"))
    full_path = [Point(float(p["x"]), float(p["y"])) for p in data["path"]]
    # origin -> first points, up to the first point near layer 4.  Reaching the
    # layer-4 channel indicates that the first 3 layers have been crossed.
    demo_path = [Point(0.0, 0.0)] + full_path[:7]
    obs = obstacles(3)
    labels = [(label, Point(p.x, p.y)) for label, p, _, _ in labeled_channel_points(4)]

    turns = []
    for idx in range(1, len(demo_path) - 1):
        turn = turn_angle_deg(demo_path[idx - 1], demo_path[idx], demo_path[idx + 1])
        turns.append({"point": idx, "turn": turn, "cards": cards_for_turn(turn)})

    coords = [o.p for o in obs] + demo_path
    margin = 24
    min_x = min(p.x for p in coords) - margin
    max_x = max(p.x for p in coords) + margin
    min_y = min(p.y for p in coords) - margin
    max_y = max(p.y for p in coords) + margin
    width = max_x - min_x
    height = max_y - min_y

    def sx(x):
        return x - min_x

    def sy(y):
        return max_y - y

    poly = " ".join(f"{sx(p.x):.3f},{sy(p.y):.3f}" for p in demo_path)
    obstacle_svg = []
    colors = ["#ffd6d6", "#ffe8c2", "#fff3bf"]
    for o in obs:
        obstacle_svg.append(
            f'<circle cx="{sx(o.p.x):.3f}" cy="{sy(o.p.y):.3f}" r="9" '
            f'fill="{colors[o.layer-1]}" stroke="#b43b3b" stroke-width="0.45"/>'
        )
        obstacle_svg.append(f'<circle cx="{sx(o.p.x):.3f}" cy="{sy(o.p.y):.3f}" r="0.9" fill="#333"/>')

    point_svg = []
    for idx, p in enumerate(demo_path):
        label = "start" if idx == 0 else nearest_label(p, labels)
        point_svg.append(f'<circle cx="{sx(p.x):.3f}" cy="{sy(p.y):.3f}" r="1.8" fill="#0057b8"/>')
        point_svg.append(f'<text x="{sx(p.x)+2.5:.3f}" y="{sy(p.y)-2.5:.3f}">P{idx} {label}</text>')

    turn_rows = "\n".join(
        f"<tr><td>P{t['point']}</td><td>{t['turn']:.3f}°</td><td>{t['cards']}</td></tr>" for t in turns
    )
    path_rows = "\n".join(
        f"<tr><td>P{idx}</td><td>{p.x:.3f}</td><td>{p.y:.3f}</td><td>{'start' if idx==0 else nearest_label(p, labels)}</td></tr>"
        for idx, p in enumerate(demo_path)
    )
    total_cards = sum(t["cards"] for t in turns)
    total_turn = sum(t["turn"] for t in turns)
    clearance = path_clearance(demo_path, obs)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>前三层避障路径演示（Reilay）</title>
  <style>
    body {{ margin: 0; font-family: 'Microsoft YaHei', Arial, sans-serif; color: #1f2933; background: #f6f8fb; }}
    .app {{ display: grid; grid-template-columns: minmax(520px, 1fr) 380px; min-height: 100vh; }}
    .stage {{ background: white; border-right: 1px solid #d8dee9; overflow: hidden; }}
    aside {{ padding: 22px; overflow: auto; background: #fff; }}
    svg {{ width: 100%; height: 100vh; cursor: grab; }}
    text {{ font-size: 4px; fill: #123; }}
    h1 {{ font-size: 22px; margin: 0 0 8px; }}
    h2 {{ font-size: 16px; margin-top: 22px; }}
    p, li {{ line-height: 1.65; color: #52616f; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 10px 0; }}
    th, td {{ border: 1px solid #d8dee9; padding: 6px 8px; text-align: right; }}
    th:first-child, td:first-child {{ text-align: left; }}
    .metric {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .card {{ border: 1px solid #d8dee9; border-radius: 8px; padding: 10px; background: #f9fbfd; }}
    .card b {{ display: block; font-size: 20px; }}
    button {{ margin: 4px 4px 10px 0; padding: 7px 10px; border: 1px solid #ccd4df; border-radius: 6px; background: white; cursor: pointer; }}
    @media (max-width: 900px) {{ .app {{ grid-template-columns: 1fr; }} svg {{ height: 65vh; }} }}
  </style>
</head>
<body>
<div class="app">
  <div class="stage">
    <svg id="mainSvg" viewBox="0 0 {width:.3f} {height:.3f}">
      <rect width="100%" height="100%" fill="#ffffff"/>
      {''.join(obstacle_svg)}
      <polyline points="{poly}" fill="none" stroke="#0057b8" stroke-width="1.2"/>
      {''.join(point_svg)}
    </svg>
  </div>
  <aside>
    <h1>前三层避障路径演示</h1>
    <p>本演示使用当前 `0.3m` 局部加密搜索路径的前段。到达第 4 层通道点附近，视为已经穿过前三层障碍物。</p>
    <div>
      <button onclick="zoom(0.85)">放大</button>
      <button onclick="zoom(1.18)">缩小</button>
      <button onclick="resetView()">重置</button>
    </div>
    <div class="metric">
      <div class="card"><b>{total_cards}</b><span>前三层演示段转向卡</span></div>
      <div class="card"><b>{total_turn:.2f}°</b><span>总转角</span></div>
      <div class="card"><b>{clearance:.4f}m</b><span>最小安全余量</span></div>
      <div class="card"><b>{len(demo_path)}</b><span>路径点数量</span></div>
    </div>
    <h2>折点转向</h2>
    <table><thead><tr><th>折点</th><th>转角</th><th>卡数</th></tr></thead><tbody>{turn_rows}</tbody></table>
    <h2>路径点</h2>
    <table><thead><tr><th>点</th><th>x</th><th>y</th><th>最近绿点</th></tr></thead><tbody>{path_rows}</tbody></table>
    <h2>说明</h2>
    <ul>
      <li>红/橙/黄圆为前三层障碍物扩大后的半径 9 米禁止圆。</li>
      <li>蓝色折线为当前搜索得到的安全路径前段。</li>
      <li>每个折点卡数按 <code>ceil(转角/5°)</code> 计算。</li>
      <li>该演示是采样路径上界，不是全局最优性证明。</li>
    </ul>
  </aside>
</div>
<script>
const svg = document.getElementById('mainSvg');
const initial = [0, 0, {width:.6f}, {height:.6f}];
let vb = initial.slice();
function apply() {{ svg.setAttribute('viewBox', vb.join(' ')); }}
function zoom(f) {{ const cx=vb[0]+vb[2]/2, cy=vb[1]+vb[3]/2; vb=[cx-(vb[2]*f)/2, cy-(vb[3]*f)/2, vb[2]*f, vb[3]*f]; apply(); }}
function resetView() {{ vb = initial.slice(); apply(); }}
svg.addEventListener('wheel', e => {{ e.preventDefault(); zoom(e.deltaY < 0 ? 0.85 : 1.18); }}, {{passive:false}});
let drag=false,last=null;
svg.addEventListener('mousedown', e => {{ drag=true; last=[e.clientX,e.clientY]; }});
window.addEventListener('mouseup', () => drag=false);
window.addEventListener('mousemove', e => {{
  if(!drag) return;
  const r=svg.getBoundingClientRect();
  vb[0]-=(e.clientX-last[0])/r.width*vb[2];
  vb[1]-=(e.clientY-last[1])/r.height*vb[3];
  last=[e.clientX,e.clientY];
  apply();
}});
apply();
</script>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"cards={total_cards} clearance={clearance:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
