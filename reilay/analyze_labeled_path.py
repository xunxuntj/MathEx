#!/usr/bin/env python3
"""Analyze a path described by green pocket labels such as 1-6,2-16,3-26."""

from __future__ import annotations

import argparse
import math

from corridor_search import Point, cards_for_turn, obstacles, path_clearance, turn_angle_deg
from draw_layers import labeled_channel_points


def label_map(n: int) -> dict[str, Point]:
    return {label: Point(p.x, p.y) for label, p, _, _ in labeled_channel_points(n)}


def parse_path(raw: str) -> list[str]:
    return [item.strip() for item in raw.replace("->", ",").split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers", type=int, default=9)
    parser.add_argument("--path", default="1-6,2-16,3-26,4-36,5-46,6-56,7-66,8-76,9-86")
    args = parser.parse_args()

    labels = parse_path(args.path)
    points_by_label = label_map(args.layers)
    missing = [label for label in labels if label not in points_by_label]
    if missing:
        raise SystemExit(f"missing labels: {missing}")

    path = [Point(0.0, 0.0)] + [points_by_label[label] for label in labels]
    obs = obstacles(args.layers)

    print("label,x,y,segment_len,segment_angle_deg")
    prev = path[0]
    print(f"start,{prev.x:.6f},{prev.y:.6f},,")
    angles: list[float] = []
    for label, p in zip(labels, path[1:]):
        v = p - prev
        angle = math.degrees(math.atan2(v.y, v.x))
        length = v.norm()
        angles.append(angle)
        print(f"{label},{p.x:.6f},{p.y:.6f},{length:.6f},{angle:.6f}")
        prev = p

    print("\nturns:")
    total_cards = 0
    total_turn = 0.0
    for idx in range(1, len(path) - 1):
        angle = turn_angle_deg(path[idx - 1], path[idx], path[idx + 1])
        cards = cards_for_turn(angle)
        total_cards += cards
        total_turn += angle
        print(f"at {labels[idx-1]}: turn={angle:.6f} deg cards={cards}")

    print("\nsummary:")
    print(f"points={len(path)}")
    print(f"total_turn_deg={total_turn:.6f}")
    print(f"total_cards={total_cards}")
    print(f"min_clearance={path_clearance(path, obs):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
