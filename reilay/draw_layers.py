#!/usr/bin/env python3
"""Draw triangular-lattice obstacle layers and their safe-corridor skeleton."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path


SPACING = 20.0
SAFE_RADIUS = 9.0
SQRT3 = math.sqrt(3.0)


@dataclass(frozen=True)
class Point:
    x: float
    y: float


def lattice_point(i: int, j: int) -> Point:
    return Point(SPACING * i + 0.5 * SPACING * j, 0.5 * SPACING * SQRT3 * j)


def layer_of(i: int, j: int) -> int:
    return max(abs(i), abs(j), abs(i + j))


def qkey(p: Point) -> tuple[int, int]:
    return (round(p.x * 1000), round(p.y * 1000))


def hex_boundary_vertices(layer: int) -> list[Point]:
    # Axial coordinate hex corners for layer r.
    coords = [
        (layer, 0),
        (layer, -layer),
        (0, -layer),
        (-layer, 0),
        (-layer, layer),
        (0, layer),
    ]
    return [lattice_point(i, j) for i, j in coords]


def collect_points(n: int) -> tuple[list[tuple[int, int, Point, int]], list[Point], list[Point], list[tuple[Point, Point]]]:
    obstacles: list[tuple[int, int, Point, int]] = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            if i == 0 and j == 0:
                continue
            layer = layer_of(i, j)
            if 1 <= layer <= n:
                obstacles.append((i, j, lattice_point(i, j), layer))

    gates: dict[tuple[int, int], Point] = {}
    pockets: dict[tuple[int, int], Point] = {}
    skeleton_edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    directions = [(1, 0), (0, 1), (1, -1)]
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            p = lattice_point(i, j)
            for di, dj in directions:
                if max(layer_of(i, j), layer_of(i + di, j + dj)) > n:
                    continue
                q = lattice_point(i + di, j + dj)
                mid = Point((p.x + q.x) / 2.0, (p.y + q.y) / 2.0)
                gates[qkey(mid)] = mid

    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            tris = [
                [(i, j), (i + 1, j), (i, j + 1)],
                [(i + 1, j + 1), (i + 1, j), (i, j + 1)],
            ]
            for tri in tris:
                if max(layer_of(a, b) for a, b in tri) > n:
                    continue
                ps = [lattice_point(a, b) for a, b in tri]
                c = Point(sum(p.x for p in ps) / 3.0, sum(p.y for p in ps) / 3.0)
                pockets[qkey(c)] = c
                for a, b in [(tri[0], tri[1]), (tri[0], tri[2]), (tri[1], tri[2])]:
                    mid = Point(
                        (lattice_point(*a).x + lattice_point(*b).x) / 2.0,
                        (lattice_point(*a).y + lattice_point(*b).y) / 2.0,
                    )
                    ka, kb = qkey(c), qkey(mid)
                    skeleton_edges.add(tuple(sorted((ka, kb))))

    all_points = [p for _, _, p, _ in obstacles] + list(gates.values()) + list(pockets.values())
    key_to_point = {qkey(p): p for p in list(gates.values()) + list(pockets.values())}
    edges = [(key_to_point[a], key_to_point[b]) for a, b in skeleton_edges if a in key_to_point and b in key_to_point]
    return obstacles, list(gates.values()), list(pockets.values()), edges


def labeled_channel_points(n: int) -> list[tuple[str, Point, str, int]]:
    """Label only green triangular-pocket points.

    A pocket belongs to layer r if the largest obstacle-layer index among the
    three triangle vertices is r.  This gives 6, 18, 30, ... pockets for layers
    1, 2, 3, ... .
    """
    grouped: dict[int, list[tuple[float, Point, str]]] = {r: [] for r in range(1, n + 1)}
    seen: set[tuple[int, int]] = set()
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            tris = [
                [(i, j), (i + 1, j), (i, j + 1)],
                [(i + 1, j + 1), (i + 1, j), (i, j + 1)],
            ]
            for tri in tris:
                layer = max(layer_of(a, b) for a, b in tri)
                if not (1 <= layer <= n):
                    continue
                ps = [lattice_point(a, b) for a, b in tri]
                p = Point(sum(q.x for q in ps) / 3.0, sum(q.y for q in ps) / 3.0)
                key = qkey(p)
                if key in seen:
                    continue
                seen.add(key)
                grouped.setdefault(layer, []).append((math.atan2(p.y, p.x), p, "pocket"))

    labeled: list[tuple[str, Point, str, int]] = []
    for layer in range(1, n + 1):
        pts = sorted(grouped.get(layer, []), key=lambda item: item[0])
        for idx, (_, p, kind) in enumerate(pts, start=1):
            labeled.append((f"{layer}-{idx}", p, kind, layer))
    return labeled


def svg_content(n: int) -> tuple[str, float, float]:
    obstacles, gates, pockets, edges = collect_points(n)
    labels = labeled_channel_points(n)
    all_points = [p for _, _, p, _ in obstacles] + gates + pockets
    margin = 30.0
    min_x = min(p.x for p in all_points) - margin
    max_x = max(p.x for p in all_points) + margin
    min_y = min(p.y for p in all_points) - margin
    max_y = max(p.y for p in all_points) + margin
    width = max_x - min_x
    height = max_y - min_y

    def sx(x: float) -> float:
        return x - min_x

    def sy(y: float) -> float:
        return max_y - y

    lines = [
        f'<svg id="mainSvg" xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" viewBox="0 0 {width:.1f} {height:.1f}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<defs><style>text{font-family:Arial,sans-serif;font-size:3px}</style></defs>',
        '<g id="viewport">',
    ]

    # Layer hexagons.
    for r in range(1, n + 1):
        verts = hex_boundary_vertices(r)
        pts = " ".join(f"{sx(p.x):.3f},{sy(p.y):.3f}" for p in verts)
        lines.append(f'<polygon points="{pts}" fill="none" stroke="#999" stroke-width="0.35" stroke-dasharray="2 2"/>')
        label = verts[0]
        lines.append(f'<text x="{sx(label.x)+2:.3f}" y="{sy(label.y)-2:.3f}" fill="#555">L{r}</text>')

    # Corridor skeleton.
    for a, b in edges:
        lines.append(
            f'<line x1="{sx(a.x):.3f}" y1="{sy(a.y):.3f}" x2="{sx(b.x):.3f}" y2="{sy(b.y):.3f}" '
            'stroke="#2f80ed" stroke-width="0.35" opacity="0.55"/>'
        )

    # Obstacles.
    palette = ["#f8d7da", "#fde2cf", "#fff3bf", "#d3f9d8", "#d0ebff", "#e5dbff"]
    for i, j, p, layer in obstacles:
        fill = palette[(layer - 1) % len(palette)]
        lines.append(
            f'<circle cx="{sx(p.x):.3f}" cy="{sy(p.y):.3f}" r="{SAFE_RADIUS:.3f}" '
            f'fill="{fill}" stroke="#8a1f1f" stroke-width="0.35" opacity="0.75"/>'
        )
        lines.append(f'<circle cx="{sx(p.x):.3f}" cy="{sy(p.y):.3f}" r="0.9" fill="#333"/>')

    for p in gates:
        lines.append(f'<circle cx="{sx(p.x):.3f}" cy="{sy(p.y):.3f}" r="0.75" fill="#0057b8" opacity="0.9"/>')
    for p in pockets:
        lines.append(f'<circle cx="{sx(p.x):.3f}" cy="{sy(p.y):.3f}" r="0.9" fill="#00843d" opacity="0.9"/>')

    for label, p, kind, layer in labels:
        lines.append(f'<text x="{sx(p.x)+0.9:.3f}" y="{sy(p.y)-0.9:.3f}" fill="#006b2e">{label}</text>')

    origin = Point(0.0, 0.0)
    lines.append(f'<circle cx="{sx(origin.x):.3f}" cy="{sy(origin.y):.3f}" r="2.2" fill="#111"/>')
    lines.append(f'<text x="{sx(origin.x)+3:.3f}" y="{sy(origin.y)-3:.3f}" fill="#111">start</text>')

    # Legend.
    lx, ly = 10.0, 14.0
    legend = [
        ("red disks", "radius-9 forbidden zones"),
        ("blue lines", "corridor skeleton"),
        ("blue dots", "two-circle gates"),
        ("green dots", "three-circle pockets, labeled only"),
        ("gray hexagons", "layer boundaries"),
    ]
    for idx, (name, desc) in enumerate(legend):
        lines.append(f'<text x="{lx:.1f}" y="{ly + 8 * idx:.1f}" fill="#222">{name}: {desc}</text>')

    lines.append("</g>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n", width, height


def write_svg(path: Path, n: int) -> None:
    content, _, _ = svg_content(n)
    path.write_text(content, encoding="utf-8")


def write_html(path: Path, n: int) -> None:
    svg, width, height = svg_content(n)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{n}层安全通道</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; }}
    #toolbar {{ position: fixed; left: 12px; top: 12px; background: rgba(255,255,255,.9); border: 1px solid #ccc; padding: 8px; z-index: 2; }}
    #wrap {{ width: 100vw; height: 100vh; overflow: hidden; background: #fafafa; }}
    svg {{ width: 100%; height: 100%; cursor: grab; }}
    svg:active {{ cursor: grabbing; }}
    button {{ margin-right: 4px; }}
  </style>
</head>
<body>
  <div id="toolbar">
    <button id="zoomIn">放大</button>
    <button id="zoomOut">缩小</button>
    <button id="reset">重置</button>
    <span>滚轮缩放，拖拽平移；只编号绿色三圆空隙点，如 1-1、2-3。</span>
  </div>
  <div id="wrap">
{svg}
  </div>
  <script>
    const svg = document.getElementById('mainSvg');
    let viewBox = [0, 0, {width:.6f}, {height:.6f}];
    const initial = viewBox.slice();
    function apply() {{ svg.setAttribute('viewBox', viewBox.join(' ')); }}
    function zoom(factor, cx, cy) {{
      const [x, y, w, h] = viewBox;
      const nx = x + (cx - x) * (1 - factor);
      const ny = y + (cy - y) * (1 - factor);
      viewBox = [nx, ny, w * factor, h * factor];
      apply();
    }}
    function clientToSvg(evt) {{
      const rect = svg.getBoundingClientRect();
      return [
        viewBox[0] + (evt.clientX - rect.left) / rect.width * viewBox[2],
        viewBox[1] + (evt.clientY - rect.top) / rect.height * viewBox[3],
      ];
    }}
    svg.addEventListener('wheel', (evt) => {{
      evt.preventDefault();
      const [cx, cy] = clientToSvg(evt);
      zoom(evt.deltaY < 0 ? 0.85 : 1.18, cx, cy);
    }}, {{ passive: false }});
    let dragging = false, last = null;
    svg.addEventListener('mousedown', (evt) => {{ dragging = true; last = [evt.clientX, evt.clientY]; }});
    window.addEventListener('mouseup', () => {{ dragging = false; }});
    window.addEventListener('mousemove', (evt) => {{
      if (!dragging) return;
      const rect = svg.getBoundingClientRect();
      const dx = (evt.clientX - last[0]) / rect.width * viewBox[2];
      const dy = (evt.clientY - last[1]) / rect.height * viewBox[3];
      viewBox[0] -= dx; viewBox[1] -= dy;
      last = [evt.clientX, evt.clientY];
      apply();
    }});
    document.getElementById('zoomIn').onclick = () => zoom(0.85, viewBox[0] + viewBox[2]/2, viewBox[1] + viewBox[3]/2);
    document.getElementById('zoomOut').onclick = () => zoom(1.18, viewBox[0] + viewBox[2]/2, viewBox[1] + viewBox[3]/2);
    document.getElementById('reset').onclick = () => {{ viewBox = initial.slice(); apply(); }};
    apply();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers", type=int, default=9)
    parser.add_argument("--out", type=Path, default=Path("layers9_corridors.svg"))
    parser.add_argument("--html", type=Path, default=None)
    args = parser.parse_args()
    write_svg(args.out, args.layers)
    if args.html is not None:
        write_html(args.html, args.layers)
    print(f"wrote {args.out}")
    if args.html is not None:
        print(f"wrote {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
