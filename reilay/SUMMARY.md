# Reilay Corridor Search Summary

This directory records an exploratory computation for the obstacle-game
problem.  The goal is to model the repeated safe corridor structure and
estimate turn-card consumption along one selected green-pocket corridor.

## Selected Corridor

The current corridor axis is:

```text
1-6 -> 2-16 -> 3-26 -> 4-36 -> 5-46 -> 6-56 -> 7-66 -> 8-76 -> 9-86
```

Directly connecting these green points is not safe, but they define a repeated
geometric corridor.  From `2-16` onward, the axis advances by the same vector:

```text
(-10, 17.3205)
```

## Best Current Result

Best current sampled result:

```text
grid step = 0.3m local refinement
cards = 42
total turn = 177.932 degrees
min clearance = 0.0002m
path points = 25
```

Best output:

```text
labeled_corridor_result_refined_g0p3.json
```

Third-party-checkable exports:

```text
labeled_corridor_refined_g0p3.points.csv
labeled_corridor_refined_g0p3.segments.csv
labeled_corridor_refined_g0p3.turns.csv
labeled_corridor_refined_g0p3.report.md
```

The path is a valid sampled candidate because every segment has non-negative
clearance against radius-9 obstacle disks, and every turn is converted to cards
by:

```text
ceil(turn_angle / 5 degrees)
```

## Sampling Results

| grid step | cards | total turn | min clearance | points | output |
|---:|---:|---:|---:|---:|---|
| 2.0 | 80 | 336.377 deg | 0.0035 | 22 | `labeled_corridor_result_g2.json` |
| 1.5 | 66 | 279.682 deg | 0.0031 | 24 | `labeled_corridor_result_g1p5.json` |
| 1.0 | 57 | 236.227 deg | 0.0035 | 24 | `labeled_corridor_result_g1.json` |
| 0.5 | 48 | 201.691 deg | 0.0035 | 28 | `labeled_corridor_result_g0p5.json` |
| 0.3 local | 42 | 177.932 deg | 0.0002 | 25 | `labeled_corridor_result_refined_g0p3.json` |

As sampling becomes finer, the found card count decreases.  This supports the
idea that the continuous optimum is better approximated by finer local samples.

## Per-Layer Estimate From 0.3m Path

Approximate card consumption by layer crossing:

The current `0.3m` layer-nearest diagnostic is recorded in
`precision_breakdown.md`.  The first crossing contains entrance adjustment.
Later crossings are mostly in the `4` to `6` card range.  A simple current
empirical estimate along this corridor is:

```text
A(n) ~= 5n - 2, for n >= 2
```

This is only a sampled upper-bound estimate, not a proof of optimality.

Detailed note:

```text
LAYER_CARD_CONJECTURE.md
```

## Dijkstra Model

The search uses Dijkstra on a state graph.

Basic geometric graph:

```text
sample point = node
safe straight segment = edge
```

Because turn cost depends on three points, the Dijkstra state is:

```text
(previous_point, current_point)
```

Transition:

```text
(A, B) -> (B, C)
```

Cost:

```text
ceil(angle(AB, BC) / 5 degrees)
```

Initial direction is free, so the first segment has no turn-card cost.

Detailed note:

```text
DIJKSTRA_MODEL.md
```

## Full 0.5m Search Vs Local Refinement

Full `0.5m` search:

```text
cards = 48
runtime ~= 11483.5s ~= 3h11m
output = labeled_corridor_result_g0p5.json
```

Local refinement `0.5m` search around previous `1.0m` path:

```text
cards = 48
nodes = 2619
edge_checks = 1230697
edges = 392582
runtime ~= 776.9s ~= 12m57s
output = labeled_corridor_result_refined_g0p5.json
```

Local refinement found the same 48-card result using about:

```text
776.9 / 11483.5 ~= 6.8%
```

of the runtime, or about `14.8x` faster.

Third-party-checkable local-refinement exports:

```text
labeled_corridor_refined_g0p5.points.csv
labeled_corridor_refined_g0p5.segments.csv
labeled_corridor_refined_g0p5.turns.csv
labeled_corridor_refined_g0p5.report.md
```

Optimization ideas are recorded in:

```text
OPTIMIZATION_IDEAS.md
```

## Visualization

Three-layer route demonstration:

```text
three_layer_demo_reilay.html
```

Interactive zoomable layer/corridor drawing:

```text
layers9_corridors.html
```

Static SVG:

```text
layers9_corridors.svg
```

Only green three-circle pocket points are labeled.  Layer counts are:

```text
layer 1: 6
layer 2: 18
layer 3: 30
...
layer 9: 102
```

## Important Caveats

- These results are sampled-graph upper bounds, not global continuous
  optimality proofs.
- The current best path has very small clearance, about `0.0002m`; a more robust
  route should target larger clearance.
- Finer sampling may find better paths but increases runtime sharply.
- To prove exact optimality, one would need lower-bound reasoning or complete
  continuous-state coverage, which has not been done here.

## Draft Written Answer

The current first-two-question written answer draft is:

```text
REILAY_REPORT_DRAFT.md
```
