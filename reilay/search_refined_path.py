#!/usr/bin/env python3
"""Refine a previous path by sampling only near that path."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import time
from pathlib import Path

from corridor_search import Point, cards_for_turn, obstacles, path_clearance, segment_clearance, turn_angle_deg


def dist_to_segment(p: Point, a: Point, b: Point) -> float:
    ab = b - a
    ap = p - a
    denom = ab.x * ab.x + ab.y * ab.y
    t = 0.0 if denom == 0 else (ap.x * ab.x + ap.y * ab.y) / denom
    t = max(0.0, min(1.0, t))
    q = Point(a.x + t * ab.x, a.y + t * ab.y)
    return (p - q).norm()


def dist_to_path(p: Point, path: list[Point]) -> float:
    return min(dist_to_segment(p, a, b) for a, b in zip(path, path[1:]))


def load_path(path: Path) -> list[Point]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Point(float(p["x"]), float(p["y"])) for p in data["path"]]


def build_samples(seed_path: list[Point], obs, grid_step: float, band: float) -> list[Point]:
    xs = [p.x for p in seed_path]
    ys = [p.y for p in seed_path]
    min_x, max_x = min(xs) - band - 3, max(xs) + band + 3
    min_y, max_y = min(ys) - band - 3, max(ys) + band + 3
    nodes: list[Point] = [seed_path[0], seed_path[-1]]
    seen = {(round(seed_path[0].x, 6), round(seed_path[0].y, 6)), (round(seed_path[-1].x, 6), round(seed_path[-1].y, 6))}
    # Keep old path points so the refined search is at least as feasible as the seed.
    for p in seed_path[1:-1]:
        key = (round(p.x, 6), round(p.y, 6))
        if key not in seen:
            seen.add(key)
            nodes.append(p)
    nx = int(math.ceil((max_x - min_x) / grid_step))
    ny = int(math.ceil((max_y - min_y) / grid_step))
    for ix in range(nx + 1):
        x = min_x + ix * grid_step
        for iy in range(ny + 1):
            y = min_y + iy * grid_step
            p = Point(x, y)
            if dist_to_path(p, seed_path) > band:
                continue
            if min((p - o.p).norm() - 9.0 for o in obs) < 0.05:
                continue
            key = (round(p.x, 6), round(p.y, 6))
            if key not in seen:
                seen.add(key)
                nodes.append(p)
    return nodes


def visible(a: Point, b: Point, obs, seed_path: list[Point], band: float) -> bool:
    if segment_clearance(a, b, obs) < -1e-7:
        return False
    for t in (0.25, 0.5, 0.75):
        p = Point(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)
        if dist_to_path(p, seed_path) > band:
            return False
    return True


def search(seed_path: list[Point], obs, grid_step: float, band: float, edge_len: float):
    t0 = time.perf_counter()
    nodes = build_samples(seed_path, obs, grid_step, band)
    sample_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    graph: list[list[tuple[int, float]]] = [[] for _ in nodes]
    edge_checks = 0
    edge_count = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            length = (nodes[j] - nodes[i]).norm()
            if length > edge_len:
                continue
            edge_checks += 1
            if visible(nodes[i], nodes[j], obs, seed_path, band):
                graph[i].append((j, length))
                graph[j].append((i, length))
                edge_count += 1
    graph_time = time.perf_counter() - t1

    t2 = time.perf_counter()
    start, goal = 0, 1
    init = (-1, start)
    pq = [(0, 0.0, 0.0, init)]
    best = {init: (0, 0.0, 0.0)}
    parent = {}
    expanded = 0
    final = None
    while pq:
        cards, turn_sum, length_sum, state = heapq.heappop(pq)
        if best.get(state) != (cards, turn_sum, length_sum):
            continue
        expanded += 1
        prev, cur = state
        if cur == goal:
            final = state
            break
        for nxt, edge_len2 in graph[cur]:
            if nxt == prev:
                continue
            turn = 0.0 if prev < 0 else turn_angle_deg(nodes[prev], nodes[cur], nodes[nxt])
            new = (cards + cards_for_turn(turn), turn_sum + turn, length_sum + edge_len2)
            ns = (cur, nxt)
            if new < best.get(ns, (10**9, float("inf"), float("inf"))):
                best[ns] = new
                parent[ns] = state
                heapq.heappush(pq, (*new, ns))
    search_time = time.perf_counter() - t2

    if final is None:
        raise RuntimeError("no path found")

    ids = [final[1]]
    cur = final
    while cur in parent:
        cur = parent[cur]
        ids.append(cur[1])
    ids.reverse()
    path = [nodes[i] for i in ids]
    stats = {
        "sample_time_sec": sample_time,
        "graph_time_sec": graph_time,
        "search_time_sec": search_time,
        "total_time_sec": sample_time + graph_time + search_time,
        "node_count": len(nodes),
        "edge_checks": edge_checks,
        "edge_count": edge_count,
        "expanded_states": expanded,
        "cards": best[final][0],
        "total_turn_deg": best[final][1],
        "length": best[final][2],
        "min_clearance": path_clearance(path, obs),
        "points": len(path),
    }
    return path, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=Path("labeled_corridor_result_g1.json"))
    parser.add_argument("--layers", type=int, default=9)
    parser.add_argument("--grid-step", type=float, default=0.5)
    parser.add_argument("--band", type=float, default=5.0)
    parser.add_argument("--edge-len", type=float, default=35.0)
    parser.add_argument("--out", type=Path, default=Path("labeled_corridor_result_refined_g0p5.json"))
    args = parser.parse_args()

    seed_path = load_path(args.seed)
    obs = obstacles(args.layers)
    path, stats = search(seed_path, obs, args.grid_step, args.band, args.edge_len)
    data = {
        "seed": str(args.seed),
        "grid_step": args.grid_step,
        "band": args.band,
        "edge_len": args.edge_len,
        **stats,
        "path": [{"x": p.x, "y": p.y} for p in path],
    }
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"cards={stats['cards']} nodes={stats['node_count']} edge_checks={stats['edge_checks']} "
        f"edges={stats['edge_count']} total_time={stats['total_time_sec']:.3f}s "
        f"clearance={stats['min_clearance']:.4f}"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
