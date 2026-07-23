# Exploratory Results

These results are upper-bound candidates from the simulator.  They are not
optimality proofs.

## Centerline-only candidates

Command:

```bash
python3 corridor_search.py --max-n 5 --out corridor_results.json --svg-n 3
```

| n | cards | total turn | min clearance | notes |
|---:|---:|---:|---:|---|
| 1 | 0 | 0.000 deg | 1.0000 | straight through a first-layer gap |
| 2 | 24 | 120.000 deg | 1.0000 | too conservative |
| 3 | 48 | 240.000 deg | 1.0000 | repeats the corridor skeleton |
| 4 | 72 | 360.000 deg | 1.0000 | too rigid |
| 5 | 95 | 474.182 deg | 0.3633 | still skeleton-biased |

This confirms that staying only on the corridor centerline is wasteful.

## Dense safe-region samples

Command:

```bash
python3 corridor_search.py --max-n 3 --grid-step 3.0 --edge-len 70 --out corridor_results_grid3.json --svg-n 2
```

| n | cards | total turn | min clearance |
|---:|---:|---:|---:|
| 1 | 0 | 0.000 deg | 0.3972 |
| 2 | 13 | 57.780 deg | 0.0693 |
| 3 | 30 | 139.421 deg | 0.0000 |

Command:

```bash
python3 corridor_search.py --max-n 2 --grid-step 2.0 --edge-len 80 --out corridor_results_grid2.json --svg-n 2
```

| n | cards | total turn | min clearance |
|---:|---:|---:|---:|
| 1 | 0 | 0.000 deg | 0.4820 |
| 2 | 11 | 49.296 deg | 0.0039 |

Command:

```bash
python3 corridor_search.py --max-n 2 --grid-step 1.5 --edge-len 80 --out corridor_results_grid1p5.json --svg-n 2
```

| n | cards | total turn | min clearance |
|---:|---:|---:|---:|
| 1 | 0 | 0.000 deg | 0.6999 |
| 2 | 10 | 44.320 deg | 0.0301 |

The denser model already improves the two-layer candidate from 24 cards to 10
cards.  This supports the idea that the path should use the whole safe corridor,
not just the centerline skeleton.

## Current interpretation

- The triangular-lattice safe corridors are periodic.
- The same local corridor cells repeat from layer to layer.
- A good general construction should probably have an entrance pattern followed
  by a repeated crossing pattern.
- The present graph search is still discretized, so it can miss better
  continuous paths.

## Next improvements

1. Add continuous local optimization after a discrete path is found.
2. Penalize near-tangent paths so candidates keep a stable safety margin.
3. Search for one repeatable layer-crossing unit and tile it outward.
4. Add a lower-bound verifier only after good candidates are found.

## Local Refinement Comparison

Full `0.5m` search:

```text
cards=48
runtime ~= 11483.5s ~= 3h11m
output=labeled_corridor_result_g0p5.json
```

Local refinement `0.5m` search around the previous `1.0m` path:

```text
cards=48
nodes=2619
edge_checks=1230697
edges=392582
runtime ~= 776.9s ~= 12m57s
output=labeled_corridor_result_refined_g0p5.json
```

The optimized local search found the same 48-card result while using only about:

```text
776.9 / 11483.5 ~= 6.8%
```

of the full-search runtime.  Equivalently, it was about `14.8x` faster in this
run.  This supports using coarse-to-fine local refinement for further precision
improvements.

## Labeled corridor experiment

User-selected green-pocket axis:

```text
1-6 -> 2-16 -> 3-26 -> 4-36 -> 5-46 -> 6-56 -> 7-66 -> 8-76 -> 9-86
```

Directly connecting these green points is not safe, but the axis is highly
periodic: from `2-16` onward, each step translates by the same vector
`(-10, 17.3205)`.

Command:

```bash
python3 search_labeled_corridor.py --layers 9 --labels '1-6,2-16,3-26,4-36,5-46,6-56,7-66,8-76,9-86' --grid-step 2.0 --corridor-width 18 --edge-len 35 --out labeled_corridor_result_g2.json
```

Result:

| axis | cards | total turn | min clearance | points |
|---|---:|---:|---:|---:|
| `1-6` to `9-86` | 80 | 336.377 deg | 0.0035 | 22 |

Finer sampling:

| grid step | cards | total turn | min clearance | points | output |
|---:|---:|---:|---:|---:|---|
| 2.0 | 80 | 336.377 deg | 0.0035 | 22 | `labeled_corridor_result_g2.json` |
| 1.5 | 66 | 279.682 deg | 0.0031 | 24 | `labeled_corridor_result_g1p5.json` |
| 1.0 | 57 | 236.227 deg | 0.0035 | 24 | `labeled_corridor_result_g1.json` |
| 0.5 | 48 | 201.691 deg | 0.0035 | 28 | `labeled_corridor_result_g0p5.json` |
| 0.3 | 42 | 177.932 deg | 0.0002 | 25 | `labeled_corridor_result_refined_g0p3.json` |

This is a rough estimate, not a proof.  The best current run suggests roughly
`42 / 8 = 5.25` cards per layer crossing along this corridor, with endpoint
effects and a very small safety margin.  The turn sequence shows repeated
blocks, which supports the hypothesis that this corridor can be modeled by a
repeatable geometric unit.
