# Labeled Corridor Path Report

Source: `labeled_corridor_result_refined_g0p3.json`

Axis labels:

```text

```

## Summary

- Layers checked: `9`
- Grid step: `0.3`
- Corridor width: `None`
- Points: `25`
- Segments: `24`
- Total cards: `42`
- Total turn: `177.931748808` degrees
- Total length: `161.755494667`
- Minimum clearance: `0.000201389` meters

The minimum clearance is measured as:

```text
distance(segment, obstacle_center) - 9
```

A non-negative value means the segment is collision-free with respect to the
expanded obstacle disks.

## Exported Files

- `labeled_corridor_refined_g0p3.points.csv`: all path point coordinates.
- `labeled_corridor_refined_g0p3.segments.csv`: every segment length, minimum clearance, and nearest obstacle.
- `labeled_corridor_refined_g0p3.turns.csv`: every turn angle and required card count.

## Sampling Note

This path is optimal only inside the sampled graph used by
`search_labeled_corridor.py`.  Increasing sampling precision may find a better
path, but the number of candidate points grows roughly like `1 / step^2`, and
the visibility-graph construction can grow close to quadratically in the number
of candidate points.  Therefore smaller grid steps can cost much more runtime.
