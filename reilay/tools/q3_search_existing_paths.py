#!/usr/bin/env python3
"""Evaluate existing static-corridor paths as Q3 rotating-obstacle candidates.

For a fixed polyline, the heuristic schedule is:
1. spend all unused cards as acceleration cards at the origin;
2. follow the polyline, using the required turn cards at its vertices;
3. continue along the final segment direction until the first collision.

The script reports a feasible lower-bound candidate after backing up by a
small distance from the detected collision boundary. It is a numerical search,
not a proof of global optimality.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SQRT3 = math.sqrt(3.0)
OMEGA = math.pi / 30.0
SAFETY_RADIUS = 9.0
BASE_SPEED = 10.0
TOTAL_CARDS = 100


Point = tuple[float, float]


@dataclass
class Candidate:
    source: str
    label: str
    path: list[Point]


def point_from_obj(obj: object) -> Point:
    if isinstance(obj, dict):
        return float(obj["x"]), float(obj["y"])
    if isinstance(obj, (list, tuple)) and len(obj) >= 2:
        return float(obj[0]), float(obj[1])
    raise TypeError(f"cannot parse point: {obj!r}")


def ensure_origin(path: list[Point]) -> list[Point]:
    if not path:
        return [(0.0, 0.0)]
    if math.hypot(path[0][0], path[0][1]) < 1e-9:
        return path
    return [(0.0, 0.0), *path]


def load_candidates(path: Path) -> Iterable[Candidate]:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "path" in data:
        yield Candidate(path.name, data.get("label", "path"), [point_from_obj(p) for p in data["path"]])
        return
    if isinstance(data, list):
        for k, obj in enumerate(data):
            if isinstance(obj, dict) and "path" in obj:
                label = f"n={obj.get('n', k)}"
                yield Candidate(path.name, label, [point_from_obj(p) for p in obj["path"]])


def turn_angle_deg(a: Point, b: Point, c: Point) -> float:
    ux, uy = b[0] - a[0], b[1] - a[1]
    vx, vy = c[0] - b[0], c[1] - b[1]
    return abs(math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)))


def turn_cards(path: list[Point]) -> tuple[int, float, list[float]]:
    angles: list[float] = []
    cards = 0
    for k in range(1, len(path) - 1):
        angle = turn_angle_deg(path[k - 1], path[k], path[k + 1])
        if angle > 1e-8:
            angles.append(angle)
            cards += math.ceil((angle - 1e-10) / 5.0)
    return cards, sum(angles), angles


def nearest_lattice_distance(x: float, y: float) -> tuple[float, tuple[int, int, float, float]]:
    jf = y / (10.0 * SQRT3)
    ifloat = (x - 10.0 * jf) / 20.0
    i0, j0 = round(ifloat), round(jf)
    best = float("inf")
    best_site = (0, 0, 0.0, 0.0)
    for i in range(i0 - 3, i0 + 4):
        for j in range(j0 - 3, j0 + 4):
            if i == 0 and j == 0:
                continue
            px = 20.0 * i + 10.0 * j
            py = 10.0 * SQRT3 * j
            d = math.hypot(x - px, y - py)
            if d < best:
                best = d
                best_site = (i, j, px, py)
    return best, best_site


def build_segments(path: list[Point], speed: float):
    segments = []
    elapsed = 0.0
    total_s = 0.0
    for a, b in zip(path, path[1:]):
        length = math.dist(a, b)
        if length < 1e-12:
            continue
        segments.append((a, b, length, elapsed, total_s))
        elapsed += length / speed
        total_s += length
    if not segments:
        raise ValueError("path has no non-zero segment")
    return segments, elapsed, total_s


def evaluate(path: list[Point], source: str, label: str, step: float, backup: float, extend: float):
    cards, total_turn, angles = turn_cards(path)
    if cards > TOTAL_CARDS:
        return None
    acceleration = TOTAL_CARDS - cards
    speed = BASE_SPEED * (1.25 ** acceleration)
    segments, elapsed, total_s = build_segments(path, speed)
    last_a, last_b, last_len, _, _ = segments[-1]
    direction = ((last_b[0] - last_a[0]) / last_len, (last_b[1] - last_a[1]) / last_len)

    def state_at_s(s: float):
        if s <= total_s:
            seg = next((z for z in segments if s <= z[4] + z[2] + 1e-12), segments[-1])
            a, b, length, start_t, start_s = seg
            u = max(0.0, min(1.0, (s - start_s) / length))
            p = (a[0] + u * (b[0] - a[0]), a[1] + u * (b[1] - a[1]))
            t = start_t + (s - start_s) / speed
        else:
            extra = s - total_s
            p = (path[-1][0] + extra * direction[0], path[-1][1] + extra * direction[1])
            t = elapsed + extra / speed
        ca = math.cos(-OMEGA * t)
        sa = math.sin(-OMEGA * t)
        q = (ca * p[0] - sa * p[1], sa * p[0] + ca * p[1])
        distance, site = nearest_lattice_distance(q[0], q[1])
        return {
            "s": s,
            "time": t,
            "p": p,
            "q": q,
            "distance": distance,
            "site": site,
            "radius": math.hypot(p[0], p[1]),
        }

    hit = None
    min_state = {"distance": float("inf")}
    max_s = total_s + extend
    n_steps = int(max_s / step) + 1
    for k in range(1, n_steps + 1):
        s = k * step
        now = state_at_s(s)
        if now["distance"] < min_state["distance"]:
            min_state = now
        if now["distance"] < SAFETY_RADIUS:
            lo, hi = max(0.0, s - step), s
            for _ in range(70):
                mid = (lo + hi) / 2.0
                if state_at_s(mid)["distance"] >= SAFETY_RADIUS:
                    lo = mid
                else:
                    hi = mid
            hit = state_at_s(lo)
            break
    if hit is None:
        return None
    conservative = state_at_s(max(0.0, hit["s"] - backup))
    return {
        "source": source,
        "label": label,
        "points": len(path),
        "turn_cards": cards,
        "acceleration_cards": acceleration,
        "deceleration_cards": 0,
        "total_turn_deg": total_turn,
        "speed_mps": speed,
        "path_length": total_s,
        "path_end_radius": math.hypot(path[-1][0], path[-1][1]),
        "collision_boundary_radius": hit["radius"],
        "collision_boundary_s": hit["s"],
        "collision_site": hit["site"],
        "conservative_radius": conservative["radius"],
        "conservative_clearance": conservative["distance"],
        "conservative_margin": conservative["distance"] - SAFETY_RADIUS,
        "conservative_time_sec": conservative["time"],
        "minimum_sampled_distance": min_state["distance"],
        "backup_m": backup,
        "step_m": step,
        "path": [{"x": x, "y": y} for x, y in path],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--step", type=float, default=0.01)
    parser.add_argument("--backup", type=float, default=0.02)
    parser.add_argument("--extend", type=float, default=600.0)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    json_files = sorted(args.root.glob("*.json"))
    results = []
    for json_file in json_files:
        if json_file.name.startswith("q3_"):
            continue
        for candidate in load_candidates(json_file):
            full_path = ensure_origin(candidate.path)
            # Test every prefix with at least one direction-defining segment.
            for end in range(2, len(full_path) + 1):
                prefix = full_path[:end]
                result = evaluate(
                    prefix,
                    candidate.source,
                    f"{candidate.label}:prefix={end}/{len(full_path)}",
                    args.step,
                    args.backup,
                    args.extend,
                )
                if result is not None:
                    results.append(result)

    results.sort(key=lambda r: r["conservative_radius"], reverse=True)
    payload = {
        "model": "existing static paths, all remaining cards spent as accelerations at t=0",
        "step_m": args.step,
        "backup_m": args.backup,
        "results": results,
    }
    if args.out:
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    for item in results[: args.top]:
        print(
            f"{item['conservative_radius']:.6f}m "
            f"(boundary {item['collision_boundary_radius']:.6f}m), "
            f"turn={item['turn_cards']}, accel={item['acceleration_cards']}, "
            f"points={item['points']}, src={item['source']} {item['label']}, "
            f"margin={item['conservative_margin']:.6f}m"
        )


if __name__ == "__main__":
    main()
