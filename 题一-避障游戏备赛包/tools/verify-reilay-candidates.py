"""Independent checks for the collaborator's sampled Q2/Q3 candidates.

These checks certify the reported constructions and numerical margins only;
they do not claim continuous or global optimality of the sampled searches.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "reilay"
SQRT3 = math.sqrt(3.0)
SAFE = 9.0


def point(obj):
    return float(obj["x"]), float(obj["y"])


def dist_segment(a, b, p):
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    den = vx * vx + vy * vy
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / den)) if den else 0.0
    q = (a[0] + t * vx, a[1] + t * vy)
    return math.dist(q, p)


def centers(max_layer=12):
    out = []
    for i in range(-max_layer, max_layer + 1):
        for j in range(-max_layer, max_layer + 1):
            layer = max(abs(i), abs(j), abs(i + j))
            if 0 < layer <= max_layer:
                out.append((20 * i + 10 * j, 10 * SQRT3 * j))
    return out


def turn_cards(path):
    cards = 0
    for a, b, c in zip(path, path[1:], path[2:]):
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        angle = abs(math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)))
        cards += math.ceil((angle - 1e-10) / 5.0) if angle > 1e-8 else 0
    return cards


def verify_q2():
    data = json.loads((ROOT / "labeled_corridor_result_refined_g0p3.json").read_text())
    waypoints = [point(p) for p in data["path"]]
    path = [(0.0, 0.0)] + waypoints
    minimum = min(
        dist_segment(a, b, p)
        for a, b in zip(path, path[1:])
        for p in centers(9)
    )
    assert data["cards"] == 42
    # The first segment from the origin has freely chosen direction, so it
    # carries no turn-card cost; the collaborator's 42 counts turns among
    # the listed sampled waypoints.
    assert turn_cards(waypoints) == 42
    assert minimum >= SAFE - 1e-9
    assert data["min_clearance"] > 0
    return {"cards": 42, "minimumSegmentClearance": minimum, "sampledClearance": data["min_clearance"]}


def nearest(x, y):
    jf = y / (10 * SQRT3)
    ii = (x - 10 * jf) / 20
    best = float("inf")
    for i in range(round(ii) - 3, round(ii) + 4):
        for j in range(round(jf) - 3, round(jf) + 4):
            if i == 0 and j == 0:
                continue
            best = min(best, math.hypot(x - 20 * i - 10 * j, y - 10 * SQRT3 * j))
    return best


def verify_q3():
    data = json.loads((ROOT / "q3_best_existing_path_candidate.json").read_text())
    path = [point(p) for p in data["path"]]
    turns = turn_cards(path)
    assert turns == 47
    assert turns + data["acceleration_cards"] + data["deceleration_cards"] == 100
    assert data["conservative_radius"] >= 174.5
    assert data["conservative_clearance"] >= 9.0
    assert data["conservative_margin"] >= 0.014
    return {k: data[k] for k in ("turn_cards", "acceleration_cards", "conservative_radius", "conservative_clearance", "conservative_margin", "collision_boundary_radius")}


if __name__ == "__main__":
    print(json.dumps({"q2": verify_q2(), "q3": verify_q3()}, ensure_ascii=False, indent=2))
