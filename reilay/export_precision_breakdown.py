#!/usr/bin/env python3
"""Export per-precision, per-layer, and per-point card breakdown tables."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from corridor_search import Point, cards_for_turn, turn_angle_deg
from draw_layers import labeled_channel_points


RESULTS = [
    ("2.0m", "full", "labeled_corridor_result_g2.json"),
    ("1.5m", "full", "labeled_corridor_result_g1p5.json"),
    ("1.0m", "full", "labeled_corridor_result_g1.json"),
    ("0.5m", "full", "labeled_corridor_result_g0p5.json"),
    ("0.5m", "refined", "labeled_corridor_result_refined_g0p5.json"),
    ("0.3m", "refined", "labeled_corridor_result_refined_g0p3.json"),
]


def label_points(n: int) -> list[tuple[str, Point]]:
    return [(label, Point(p.x, p.y)) for label, p, _, _ in labeled_channel_points(n)]


def nearest_label(p: Point, labels: list[tuple[str, Point]]) -> str:
    label, _ = min(labels, key=lambda item: (p - item[1]).norm())
    return label


def load_path(path: Path) -> list[Point]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Point(float(p["x"]), float(p["y"])) for p in data["path"]]


def analyze(path: list[Point], labels: list[tuple[str, Point]]):
    point_rows = []
    for idx, p in enumerate(path):
        label = nearest_label(p, labels)
        layer = int(label.split("-")[0])
        point_rows.append({
            "point_index": idx,
            "x": p.x,
            "y": p.y,
            "nearest_green_label": label,
            "nearest_layer": layer,
            "turn_deg": "",
            "cards_at_point": "",
        })

    total_cards = 0
    total_turn = 0.0
    for idx in range(1, len(path) - 1):
        turn = turn_angle_deg(path[idx - 1], path[idx], path[idx + 1])
        cards = cards_for_turn(turn)
        total_cards += cards
        total_turn += turn
        point_rows[idx]["turn_deg"] = turn
        point_rows[idx]["cards_at_point"] = cards

    by_layer: dict[int, dict] = {}
    for row in point_rows:
        layer = row["nearest_layer"]
        by_layer.setdefault(layer, {"path_points": 0, "turn_points": 0, "cards": 0, "turn_deg": 0.0})
        by_layer[layer]["path_points"] += 1
        if row["cards_at_point"] != "":
            by_layer[layer]["turn_points"] += 1
            by_layer[layer]["cards"] += int(row["cards_at_point"])
            by_layer[layer]["turn_deg"] += float(row["turn_deg"])

    return point_rows, by_layer, total_cards, total_turn


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers", type=int, default=9)
    parser.add_argument("--out-prefix", type=Path, default=Path("precision_breakdown"))
    args = parser.parse_args()

    labels = label_points(args.layers)
    layer_csv = args.out_prefix.with_suffix(".layers.csv")
    point_csv = args.out_prefix.with_suffix(".points.csv")
    md_path = args.out_prefix.with_suffix(".md")

    layer_rows = []
    all_point_rows = []
    summaries = []

    for precision, method, filename in RESULTS:
        path_file = Path(filename)
        if not path_file.exists():
            summaries.append({
                "precision": precision,
                "method": method,
                "file": filename,
                "status": "missing_or_running",
            })
            continue
        path = load_path(path_file)
        point_rows, by_layer, total_cards, total_turn = analyze(path, labels)
        summaries.append({
            "precision": precision,
            "method": method,
            "file": filename,
            "status": "done",
            "points": len(path),
            "cards": total_cards,
            "turn_deg": total_turn,
        })
        for layer in sorted(by_layer):
            data = by_layer[layer]
            layer_rows.append({
                "precision": precision,
                "method": method,
                "source_file": filename,
                "layer": layer,
                "path_points_near_layer": data["path_points"],
                "turn_points_near_layer": data["turn_points"],
                "cards_near_layer": data["cards"],
                "turn_deg_near_layer": data["turn_deg"],
            })
        for row in point_rows:
            all_point_rows.append({
                "precision": precision,
                "method": method,
                "source_file": filename,
                **row,
            })

    with layer_csv.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "precision",
            "method",
            "source_file",
            "layer",
            "path_points_near_layer",
            "turn_points_near_layer",
            "cards_near_layer",
            "turn_deg_near_layer",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(layer_rows)

    with point_csv.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "precision",
            "method",
            "source_file",
            "point_index",
            "x",
            "y",
            "nearest_green_label",
            "nearest_layer",
            "turn_deg",
            "cards_at_point",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_point_rows)

    lines = [
        "# Precision Breakdown",
        "",
        "This file summarizes card counts by sampling precision, approximate layer, and path point.",
        "",
        "Layer assignment is based on the nearest labeled green pocket point.  Therefore the layer table is a practical diagnostic for the sampled path, not a new geometric theorem.",
        "",
        "## Summary",
        "",
        "| precision | method | status | cards | path points | total turn | source |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for s in summaries:
        if s["status"] != "done":
            lines.append(f"| {s['precision']} | {s['method']} | {s['status']} |  |  |  | `{s['file']}` |")
        else:
            lines.append(
                f"| {s['precision']} | {s['method']} | done | {s['cards']} | {s['points']} | "
                f"{s['turn_deg']:.3f} deg | `{s['file']}` |"
            )

    lines += [
        "",
        "## Per-Layer Cards",
        "",
        "| precision | method | layer | path points near layer | turn points | cards | turn |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in layer_rows:
        lines.append(
            f"| {row['precision']} | {row['method']} | {row['layer']} | "
            f"{row['path_points_near_layer']} | {row['turn_points_near_layer']} | "
            f"{row['cards_near_layer']} | {row['turn_deg_near_layer']:.3f} deg |"
        )

    lines += [
        "",
        "## CSV Files",
        "",
        f"- `{layer_csv.name}`: per-precision layer summary.",
        f"- `{point_csv.name}`: every path point, nearest green label, turn angle, and card count.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {layer_csv}")
    print(f"wrote {point_csv}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
