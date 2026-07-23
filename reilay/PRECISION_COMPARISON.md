# Sampling Precision Comparison

Corridor axis:

```text
1-6 -> 2-16 -> 3-26 -> 4-36 -> 5-46 -> 6-56 -> 7-66 -> 8-76 -> 9-86
```

| sampling precision | method | cards | total turn | min clearance | path points | runtime | conclusion |
|---:|---|---:|---:|---:|---:|---:|---|
| 2.0m | full corridor-band search | 80 | 336.377 deg | 0.0035m | 22 | not recorded | coarse sampling, overestimates card count |
| 1.5m | full corridor-band search | 66 | 279.682 deg | 0.0031m | 24 | about 55s | finer sampling improves path |
| 1.0m | full corridor-band search | 57 | 236.227 deg | 0.0035m | 24 | about 5m47s | clear improvement; used as seed for refinement |
| 0.5m | full corridor-band search | 48 | 201.691 deg | 0.0035m | 28 | about 3h11m | best completed full search |
| 0.5m | local refinement around 1.0m path | 48 | 201.691 deg | 0.0035m | 28 | about 12m57s | same result as full search, about 14.8x faster |
| 0.3m | local refinement around 0.5m path | 42 | 177.932 deg | 0.0002m | 25 | about 2h32m | best current result, but very small clearance |

## Current Conclusion

The best completed result is the `0.3m` local-refinement search:

```text
42 cards
```

The observed estimate along this corridor is about:

```text
42 / 8 = 5.25 cards per layer crossing
```

The local-refinement strategy is effective: it found the same `0.5m` result as
the full search while using only about `6.8%` of the runtime, and it allowed the
finer `0.3m` run to complete with 42 cards.

## Caveat

All rows are sampled-graph upper bounds.  They prove that a path with the listed
card count exists in the sampled graph and passes segment-safety verification,
but they do not prove global continuous optimality.
