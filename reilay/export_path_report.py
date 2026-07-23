#!/usr/bin/env python3
"""Export a human-readable and third-party-checkable path report."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from corridor_search import Point, cards_for_turn, dist_point_segment, obstacles, segment_clearance, turn_angle_deg
from draw_layers import labeled_channel_points


def nearest_axis_label(p: Point, labels: list[tuple[str, Point]]) -> str:
    label, _ = min(labels, key=lambda item: (p - item[1]).norm())
    return label


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("labeled_corridor_result_g1.json"))
    parser.add_argument("--layers", type=int, default=9)
    parser.add_argument("--prefix", type=Path, default=Path("labeled_corridor_g1"))
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    path = [Point(float(p["x"]), float(p["y"])) for p in data["path"]]
    obs = obstacles(args.layers)
    labels = [(label, Point(p.x, p.y)) for label, p, _, _ in labeled_channel_points(args.layers)]

    points_csv = args.prefix.with_suffix(".points.csv")
    segments_csv = args.prefix.with_suffix(".segments.csv")
    turns_csv = args.prefix.with_suffix(".turns.csv")
    report_md = args.prefix.with_suffix(".report.md")

    with points_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["point_index", "x", "y", "nearest_green_label"])
        for idx, p in enumerate(path):
            w.writerow([idx, f"{p.x:.9f}", f"{p.y:.9f}", nearest_axis_label(p, labels)])

    with segments_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["segment_index", "from_point", "to_point", "length", "min_clearance", "nearest_obstacle_i", "nearest_obstacle_j", "nearest_obstacle_layer"])
        for idx, (a, b) in enumerate(zip(path, path[1:])):
            best = (float("inf"), None)
            for o in obs:
                clearance = dist_point_segment(o.p, a, b) - 9.0
                if clearance < best[0]:
                    best = (clearance, o)
            o = best[1]
            w.writerow([
                idx,
                idx,
                idx + 1,
                f"{(b - a).norm():.9f}",
                f"{best[0]:.9f}",
                o.i,
                o.j,
                o.layer,
            ])

    total_cards = 0
    total_turn = 0.0
    with turns_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["turn_index", "at_point", "turn_deg", "cards"])
        for idx in range(1, len(path) - 1):
            turn = turn_angle_deg(path[idx - 1], path[idx], path[idx + 1])
            cards = cards_for_turn(turn)
            total_cards += cards
            total_turn += turn
            w.writerow([idx - 1, idx, f"{turn:.9f}", cards])

    total_length = sum((b - a).norm() for a, b in zip(path, path[1:]))
    min_clearance = min(segment_clearance(a, b, obs) for a, b in zip(path, path[1:]))

    report = f"""# Labeled Corridor Path Report

Source: `{args.input.name}`

Axis labels:

```text
{' -> '.join(data.get('axis_labels', []))}
```

## Summary

- Layers checked: `{args.layers}`
- Grid step: `{data.get('grid_step')}`
- Corridor width: `{data.get('corridor_width')}`
- Points: `{len(path)}`
- Segments: `{len(path) - 1}`
- Total cards: `{total_cards}`
- Total turn: `{total_turn:.9f}` degrees
- Total length: `{total_length:.9f}`
- Minimum clearance: `{min_clearance:.9f}` meters

The minimum clearance is measured as:

```text
distance(segment, obstacle_center) - 9
```

A non-negative value means the segment is collision-free with respect to the
expanded obstacle disks.

## Exported Files

- `{points_csv.name}`: all path point coordinates.
- `{segments_csv.name}`: every segment length, minimum clearance, and nearest obstacle.
- `{turns_csv.name}`: every turn angle and required card count.

## Sampling Note

This path is optimal only inside the sampled graph used by
`search_labeled_corridor.py`.  Increasing sampling precision may find a better
path, but the number of candidate points grows roughly like `1 / step^2`, and
the visibility-graph construction can grow close to quadratically in the number
of candidate points.  Therefore smaller grid steps can cost much more runtime.
"""
    report_md.write_text(report, encoding="utf-8")

    print(f"wrote {points_csv}")
    print(f"wrote {segments_csv}")
    print(f"wrote {turns_csv}")
    print(f"wrote {report_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
