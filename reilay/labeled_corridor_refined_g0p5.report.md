# Labeled Corridor Path Report

Source: `labeled_corridor_result_refined_g0p5.json`

Axis labels:

```text

```

## Summary

- Layers checked: `9`
- Grid step: `0.5`
- Corridor width: `None`
- Points: `28`
- Segments: `27`
- Total cards: `48`
- Total turn: `201.691176575` degrees
- Total length: `161.923161021`
- Minimum clearance: `0.003521692` meters

The minimum clearance is measured as:

```text
distance(segment, obstacle_center) - 9
```

A non-negative value means the segment is collision-free with respect to the
expanded obstacle disks.

## Exported Files

- `labeled_corridor_refined_g0p5.points.csv`: all path point coordinates.
- `labeled_corridor_refined_g0p5.segments.csv`: every segment length, minimum clearance, and nearest obstacle.
- `labeled_corridor_refined_g0p5.turns.csv`: every turn angle and required card count.

## Sampling Note

This path is optimal only inside the sampled graph used by
`search_labeled_corridor.py`.  Increasing sampling precision may find a better
path, but the number of candidate points grows roughly like `1 / step^2`, and
the visibility-graph construction can grow close to quadratically in the number
of candidate points.  Therefore smaller grid steps can cost much more runtime.
