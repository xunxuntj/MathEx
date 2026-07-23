# Labeled Corridor Path Report

Source: `labeled_corridor_result_g1.json`

Axis labels:

```text
1-6 -> 2-16 -> 3-26 -> 4-36 -> 5-46 -> 6-56 -> 7-66 -> 8-76 -> 9-86
```

## Summary

- Layers checked: `9`
- Grid step: `1.0`
- Corridor width: `18.0`
- Points: `24`
- Segments: `23`
- Total cards: `57`
- Total turn: `236.226621135` degrees
- Total length: `162.322993174`
- Minimum clearance: `0.003521692` meters

The minimum clearance is measured as:

```text
distance(segment, obstacle_center) - 9
```

A non-negative value means the segment is collision-free with respect to the
expanded obstacle disks.

## Exported Files

- `labeled_corridor_g1.points.csv`: all path point coordinates.
- `labeled_corridor_g1.segments.csv`: every segment length, minimum clearance, and nearest obstacle.
- `labeled_corridor_g1.turns.csv`: every turn angle and required card count.

## Sampling Note

This path is optimal only inside the sampled graph used by
`search_labeled_corridor.py`.  Increasing sampling precision may find a better
path, but the number of candidate points grows roughly like `1 / step^2`, and
the visibility-graph construction can grow close to quadratically in the number
of candidate points.  Therefore smaller grid steps can cost much more runtime.
