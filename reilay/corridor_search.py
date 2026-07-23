#!/usr/bin/env python3
"""Search low-turn safe polylines through triangular-lattice obstacle layers.

This is an exploratory simulator for the obstacle-card problem.  It does not
prove optimality.  It builds candidate points from the geometric "corridor
center" structure, connects mutually visible safe segments, then searches for a
polyline minimizing the number of 5-degree turn cards.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SPACING = 20.0
SAFE_RADIUS = 9.0
SQRT3 = math.sqrt(3.0)
EPS = 1e-9


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)

    def scale(self, k: float) -> "Point":
        return Point(self.x * k, self.y * k)

    def norm(self) -> float:
        return math.hypot(self.x, self.y)


@dataclass(frozen=True)
class Obstacle:
    i: int
    j: int
    p: Point
    layer: int


@dataclass
class Node:
    id: int
    p: Point
    kind: str


@dataclass
class SearchResult:
    n: int
    cards: int
    total_turn_deg: float
    length: float
    min_clearance: float
    path: list[Point]


def lattice_point(i: int, j: int) -> Point:
    return Point(SPACING * i + 0.5 * SPACING * j, 0.5 * SPACING * SQRT3 * j)


def layer_of(i: int, j: int) -> int:
    return max(abs(i), abs(j), abs(i + j))


def obstacles(n: int) -> list[Obstacle]:
    out: list[Obstacle] = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            if i == 0 and j == 0:
                continue
            layer = layer_of(i, j)
            if 1 <= layer <= n:
                out.append(Obstacle(i, j, lattice_point(i, j), layer))
    return out


def dist_point_segment(p: Point, a: Point, b: Point) -> float:
    ab = b - a
    ap = p - a
    denom = ab.x * ab.x + ab.y * ab.y
    if denom <= EPS:
        return (p - a).norm()
    t = (ap.x * ab.x + ap.y * ab.y) / denom
    t = max(0.0, min(1.0, t))
    q = Point(a.x + t * ab.x, a.y + t * ab.y)
    return (p - q).norm()


def segment_clearance(a: Point, b: Point, obs: list[Obstacle]) -> float:
    return min(dist_point_segment(o.p, a, b) - SAFE_RADIUS for o in obs)


def path_clearance(path: list[Point], obs: list[Obstacle]) -> float:
    return min(segment_clearance(a, b, obs) for a, b in zip(path, path[1:]))


def visible(a: Point, b: Point, obs: list[Obstacle], margin: float = -1e-7) -> bool:
    return segment_clearance(a, b, obs) >= margin


def turn_angle_deg(a: Point, b: Point, c: Point) -> float:
    u = a - b
    v = c - b
    nu = u.norm()
    nv = v.norm()
    if nu <= EPS or nv <= EPS:
        return 0.0
    dot = (u.x * v.x + u.y * v.y) / (nu * nv)
    dot = max(-1.0, min(1.0, dot))
    # Interior angle at b; direction change is 180 - interior.
    interior = math.degrees(math.acos(dot))
    return abs(180.0 - interior)


def cards_for_turn(angle_deg: float) -> int:
    return int(math.ceil(max(0.0, angle_deg) / 5.0 - 1e-10))


def quant_key(p: Point, scale: int = 1_000_000) -> tuple[int, int]:
    return (round(p.x * scale), round(p.y * scale))


def add_node(nodes: list[Node], seen: dict[tuple[int, int], int], p: Point, kind: str) -> int:
    key = quant_key(p)
    if key in seen:
        return seen[key]
    idx = len(nodes)
    seen[key] = idx
    nodes.append(Node(idx, p, kind))
    return idx


def point_clearance(p: Point, obs: list[Obstacle]) -> float:
    return min((p - o.p).norm() - SAFE_RADIUS for o in obs)


def candidate_nodes(
    n: int,
    obs: list[Obstacle],
    buffer_layers: int = 2,
    grid_step: float = 0.0,
) -> list[Node]:
    """Build origin plus corridor-center candidates.

    Candidates:
    - midpoints between adjacent obstacle lattice sites (narrow gates)
    - centroids/circumcenters of elementary equilateral triangles (wide pockets)
    """
    nodes: list[Node] = []
    seen: dict[tuple[int, int], int] = {}
    add_node(nodes, seen, Point(0.0, 0.0), "origin")

    r = n + buffer_layers

    # Gate midpoints between adjacent lattice points.
    directions = [(1, 0), (0, 1), (1, -1)]
    for i in range(-r, r + 1):
        for j in range(-r, r + 1):
            p = lattice_point(i, j)
            for di, dj in directions:
                q = lattice_point(i + di, j + dj)
                mid = Point((p.x + q.x) / 2.0, (p.y + q.y) / 2.0)
                if mid.norm() <= SPACING * (n + 1.5):
                    add_node(nodes, seen, mid, "gate")

    # Circumcenters of elementary up/down triangles; for equilateral triangles,
    # the centroid is also the circumcenter.
    for i in range(-r, r + 1):
        for j in range(-r, r + 1):
            tris = [
                [(i, j), (i + 1, j), (i, j + 1)],
                [(i + 1, j + 1), (i + 1, j), (i, j + 1)],
            ]
            for tri in tris:
                ps = [lattice_point(a, b) for a, b in tri]
                c = Point(sum(p.x for p in ps) / 3.0, sum(p.y for p in ps) / 3.0)
                if c.norm() <= SPACING * (n + 1.5):
                    add_node(nodes, seen, c, "pocket")

    # Optional dense samples inside the safe region.  These let the path use the
    # width of a corridor instead of being locked to the Voronoi skeleton.
    if grid_step > 0:
        bound = SPACING * (n + 1.2)
        steps = int(math.ceil(2 * bound / grid_step))
        for ix in range(steps + 1):
            x = -bound + ix * grid_step
            for iy in range(steps + 1):
                y = -bound + iy * grid_step
                p = Point(x, y)
                if p.norm() > bound:
                    continue
                if point_clearance(p, obs) >= 0.05:
                    add_node(nodes, seen, p, "sample")

    return nodes


def build_visibility_graph(
    nodes: list[Node],
    obs: list[Obstacle],
    max_edge_len: float,
) -> list[list[tuple[int, float]]]:
    graph: list[list[tuple[int, float]]] = [[] for _ in nodes]
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a = nodes[i].p
            b = nodes[j].p
            length = (b - a).norm()
            if length <= max_edge_len and visible(a, b, obs):
                graph[i].append((j, length))
                graph[j].append((i, length))
    return graph


def is_goal(p: Point, n: int) -> bool:
    # A simple radial escape condition.  The final segment is still checked
    # against every obstacle in the first n layers.
    return p.norm() >= SPACING * n + 9.0


def reconstruct(
    parent: dict[tuple[int, int], tuple[int, int]],
    state: tuple[int, int],
    nodes: list[Node],
) -> list[Point]:
    ids = [state[1]]
    cur = state
    while cur in parent:
        cur = parent[cur]
        ids.append(cur[1])
    ids.reverse()
    return [nodes[i].p for i in ids]


def search(n: int, max_edge_len: float, grid_step: float) -> SearchResult:
    obs = obstacles(n)
    nodes = candidate_nodes(n, obs, grid_step=grid_step)
    graph = build_visibility_graph(nodes, obs, max_edge_len=max_edge_len)

    start = 0
    pq: list[tuple[int, float, float, tuple[int, int]]] = []
    parent: dict[tuple[int, int], tuple[int, int]] = {}
    best: dict[tuple[int, int], tuple[int, float, float]] = {}

    # State is (prev_node, current_node).  prev_node == -1 means no initial
    # direction has been fixed yet, so the first segment costs no card.
    initial = (-1, start)
    best[initial] = (0, 0.0, 0.0)
    heapq.heappush(pq, (0, 0.0, 0.0, initial))

    final_state: tuple[int, int] | None = None

    while pq:
        cards, angle_sum, length_sum, state = heapq.heappop(pq)
        if best.get(state) != (cards, angle_sum, length_sum):
            continue
        prev, cur = state
        if cur != start and is_goal(nodes[cur].p, n):
            final_state = state
            break
        for nxt, edge_len in graph[cur]:
            if nxt == prev:
                continue
            angle = 0.0 if prev < 0 else turn_angle_deg(nodes[prev].p, nodes[cur].p, nodes[nxt].p)
            new_cards = cards + cards_for_turn(angle)
            new_angle = angle_sum + angle
            new_len = length_sum + edge_len
            new_state = (cur, nxt)
            new_cost = (new_cards, new_angle, new_len)
            if new_cost < best.get(new_state, (10**9, float("inf"), float("inf"))):
                best[new_state] = new_cost
                parent[new_state] = state
                heapq.heappush(pq, (new_cards, new_angle, new_len, new_state))

    if final_state is None:
        raise RuntimeError(f"no safe path found for n={n}")

    cards, total_turn, length = best[final_state]
    path = reconstruct(parent, final_state, nodes)
    return SearchResult(
        n=n,
        cards=cards,
        total_turn_deg=total_turn,
        length=length,
        min_clearance=path_clearance(path, obs),
        path=path,
    )


def result_to_json(result: SearchResult) -> dict:
    return {
        "n": result.n,
        "cards": result.cards,
        "total_turn_deg": result.total_turn_deg,
        "length": result.length,
        "min_clearance": result.min_clearance,
        "path": [{"x": p.x, "y": p.y} for p in result.path],
    }


def write_svg(path: Path, result: SearchResult) -> None:
    n = result.n
    obs = obstacles(n)
    margin = 25
    coords = [o.p for o in obs] + result.path
    min_x = min(p.x for p in coords) - margin
    max_x = max(p.x for p in coords) + margin
    min_y = min(p.y for p in coords) - margin
    max_y = max(p.y for p in coords) + margin
    width = max_x - min_x
    height = max_y - min_y

    def sx(x: float) -> float:
        return x - min_x

    def sy(y: float) -> float:
        return max_y - y

    poly = " ".join(f"{sx(p.x):.3f},{sy(p.y):.3f}" for p in result.path)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" viewBox="0 0 {width:.1f} {height:.1f}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]
    for o in obs:
        lines.append(
            f'<circle cx="{sx(o.p.x):.3f}" cy="{sy(o.p.y):.3f}" r="{SAFE_RADIUS:.3f}" '
            'fill="#f8d7da" stroke="#b00020" stroke-width="0.5"/>'
        )
    lines.append(f'<polyline points="{poly}" fill="none" stroke="#0057b8" stroke-width="1.4"/>')
    for p in result.path:
        lines.append(f'<circle cx="{sx(p.x):.3f}" cy="{sy(p.y):.3f}" r="1.4" fill="#0057b8"/>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-n", type=int, default=5)
    parser.add_argument("--edge-len", type=float, default=70.0)
    parser.add_argument("--grid-step", type=float, default=0.0)
    parser.add_argument("--out", type=Path, default=Path("corridor_results.json"))
    parser.add_argument("--svg-n", type=int, default=0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    results = []
    for n in range(1, args.max_n + 1):
        r = search(n, max_edge_len=args.edge_len, grid_step=args.grid_step)
        results.append(result_to_json(r))
        print(
            f"n={n:2d} cards={r.cards:2d} turn={r.total_turn_deg:8.3f} "
            f"len={r.length:8.3f} clearance={r.min_clearance:7.4f} "
            f"points={len(r.path)}",
            flush=True,
        )
        if args.svg_n == n:
            write_svg(args.out.with_suffix(f".n{n}.svg"), r)

    args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
