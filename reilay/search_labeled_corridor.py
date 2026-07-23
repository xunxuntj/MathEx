#!/usr/bin/env python3
"""Search a safe polyline constrained near a labeled green-pocket corridor."""

from __future__ import annotations

import argparse
import heapq
import json
import math
from pathlib import Path

from corridor_search import (
    Point,
    cards_for_turn,
    obstacles,
    path_clearance,
    segment_clearance,
    turn_angle_deg,
)
from draw_layers import labeled_channel_points


def parse_labels(raw: str) -> list[str]:
    return [item.strip() for item in raw.replace("->", ",").split(",") if item.strip()]


def label_points(n: int) -> dict[str, Point]:
    return {label: Point(p.x, p.y) for label, p, _, _ in labeled_channel_points(n)}


def nearest_dist_to_polyline(p: Point, axis: list[Point]) -> float:
    best = float("inf")
    for a, b in zip(axis, axis[1:]):
        ab = b - a
        ap = p - a
        denom = ab.x * ab.x + ab.y * ab.y
        t = 0.0 if denom == 0 else (ap.x * ab.x + ap.y * ab.y) / denom
        t = max(0.0, min(1.0, t))
        q = Point(a.x + t * ab.x, a.y + t * ab.y)
        best = min(best, (p - q).norm())
    return best


def build_samples(axis: list[Point], obs, grid_step: float, corridor_width: float, extra: float) -> list[Point]:
    xs = [p.x for p in axis]
    ys = [p.y for p in axis]
    min_x, max_x = min(xs) - extra, max(xs) + extra
    min_y, max_y = min(ys) - extra, max(ys) + extra
    nodes: list[Point] = [axis[0], axis[-1]]
    seen = {(round(axis[0].x, 6), round(axis[0].y, 6)), (round(axis[-1].x, 6), round(axis[-1].y, 6))}
    nx = int(math.ceil((max_x - min_x) / grid_step))
    ny = int(math.ceil((max_y - min_y) / grid_step))
    for ix in range(nx + 1):
        x = min_x + ix * grid_step
        for iy in range(ny + 1):
            y = min_y + iy * grid_step
            p = Point(x, y)
            if nearest_dist_to_polyline(p, axis) > corridor_width:
                continue
            if min((p - o.p).norm() - 9.0 for o in obs) < 0.05:
                continue
            key = (round(p.x, 6), round(p.y, 6))
            if key not in seen:
                seen.add(key)
                nodes.append(p)
    return nodes


def visible(a: Point, b: Point, obs, axis: list[Point], corridor_width: float) -> bool:
    if segment_clearance(a, b, obs) < -1e-7:
        return False
    # Check midpoint and quarter points to keep long shortcuts near the intended corridor.
    for t in (0.25, 0.5, 0.75):
        p = Point(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)
        if nearest_dist_to_polyline(p, axis) > corridor_width:
            return False
    return True


def search(axis: list[Point], obs, grid_step: float, corridor_width: float, max_edge_len: float) -> list[Point]:
    nodes = build_samples(axis, obs, grid_step, corridor_width, extra=corridor_width + 3.0)
    graph: list[list[tuple[int, float]]] = [[] for _ in nodes]
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            length = (nodes[j] - nodes[i]).norm()
            if length <= max_edge_len and visible(nodes[i], nodes[j], obs, axis, corridor_width):
                graph[i].append((j, length))
                graph[j].append((i, length))

    start, goal = 0, 1
    pq: list[tuple[int, float, float, tuple[int, int]]] = []
    best: dict[tuple[int, int], tuple[int, float, float]] = {}
    parent: dict[tuple[int, int], tuple[int, int]] = {}
    init = (-1, start)
    best[init] = (0, 0.0, 0.0)
    heapq.heappush(pq, (0, 0.0, 0.0, init))

    final = None
    while pq:
        cards, turn_sum, length_sum, state = heapq.heappop(pq)
        if best.get(state) != (cards, turn_sum, length_sum):
            continue
        prev, cur = state
        if cur == goal:
            final = state
            break
        for nxt, edge_len in graph[cur]:
            if nxt == prev:
                continue
            turn = 0.0 if prev < 0 else turn_angle_deg(nodes[prev], nodes[cur], nodes[nxt])
            new = (cards + cards_for_turn(turn), turn_sum + turn, length_sum + edge_len)
            ns = (cur, nxt)
            if new < best.get(ns, (10**9, float("inf"), float("inf"))):
                best[ns] = new
                parent[ns] = state
                heapq.heappush(pq, (*new, ns))

    if final is None:
        raise RuntimeError("no path found")

    ids = [final[1]]
    cur = final
    while cur in parent:
        cur = parent[cur]
        ids.append(cur[1])
    ids.reverse()
    return [nodes[i] for i in ids]


def path_stats(path: list[Point], obs) -> dict:
    turns = [turn_angle_deg(path[i - 1], path[i], path[i + 1]) for i in range(1, len(path) - 1)]
    return {
        "points": len(path),
        "cards": sum(cards_for_turn(t) for t in turns),
        "total_turn_deg": sum(turns),
        "length": sum((b - a).norm() for a, b in zip(path, path[1:])),
        "min_clearance": path_clearance(path, obs),
        "turns_deg": turns,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers", type=int, default=9)
    parser.add_argument("--labels", default="1-6,2-16,3-26,4-36,5-46,6-56,7-66,8-76,9-86")
    parser.add_argument("--grid-step", type=float, default=1.5)
    parser.add_argument("--corridor-width", type=float, default=18.0)
    parser.add_argument("--edge-len", type=float, default=35.0)
    parser.add_argument("--out", type=Path, default=Path("labeled_corridor_result.json"))
    args = parser.parse_args()

    labels = parse_labels(args.labels)
    points_by_label = label_points(args.layers)
    axis = [points_by_label[label] for label in labels]
    obs = obstacles(args.layers)
    path = search(axis, obs, args.grid_step, args.corridor_width, args.edge_len)
    stats = path_stats(path, obs)
    result = {
        "axis_labels": labels,
        "grid_step": args.grid_step,
        "corridor_width": args.corridor_width,
        "edge_len": args.edge_len,
        **stats,
        "path": [{"x": p.x, "y": p.y} for p in path],
    }
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"cards={stats['cards']} turn={stats['total_turn_deg']:.3f} "
        f"len={stats['length']:.3f} clearance={stats['min_clearance']:.4f} "
        f"points={stats['points']}"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
