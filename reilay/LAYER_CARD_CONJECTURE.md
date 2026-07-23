# Layer Card Estimate And Conjecture

This note summarizes the current `0.5m` sampling result along the green-pocket
axis:

```text
1-6 -> 2-16 -> 3-26 -> 4-36 -> 5-46 -> 6-56 -> 7-66 -> 8-76 -> 9-86
```

Source path report:

```text
labeled_corridor_g0p5.report.md
```

## Current Per-Layer Estimate

| layer crossing | estimated cards |
|---|---:|
| `1-6 -> 2-16` | 9 |
| `2-16 -> 3-26` | 5 |
| `3-26 -> 4-36` | 5 |
| `4-36 -> 5-46` | 6 |
| `5-46 -> 6-56` | 6 |
| `6-56 -> 7-66` | 5 |
| `7-66 -> 8-76` | 6 |
| `8-76 -> 9-86` | 6 |

Total:

```text
9 + 5 + 5 + 6 + 6 + 5 + 6 + 6 = 48 cards
```

## Pattern

The first crossing appears to include entrance adjustment.  After that, the
observed pattern is approximately in the `5` to `6` card range:

```text
5, 5, 6, 6, 5, 6, 6, ...
```

The current 8 crossings cost `48` cards total, so the average is:

```text
48 / 8 = 6 cards per layer crossing
```

The internal non-entrance crossings cost:

```text
48 - 9 = 39 cards across 7 crossings ~= 5.57 cards per crossing
```

## Candidate Upper-Bound Formula Along This Corridor

For `n >= 2`, define `A(n)` as the current estimated number of cards to follow
this corridor from layer 1 to layer `n`.

Let:

```text
q = floor((n - 2) / 3)
s = (n - 2) mod 3
```

Then the current simplified estimate suggests:

```text
A(n) ~= 9 + 6(n - 2)
```

for `n >= 2`, with possible small periodic savings because many internal
crossings cost `5` instead of `6`.

An optimistic pattern-based estimate based on the current internal crossings is:

```text
A(n) ~= 9 + about 5.5 to 6 cards per additional layer
```

The exact periodic formula is not stable yet and should wait for more refined
sampling or continuous optimization.

## Important Caveats

- This is a sampled-path upper-bound estimate, not an optimality proof.
- The current best path uses `0.5m` sampling and has a very small minimum
  clearance, about `0.0035m`.
- Finer sampling may find a lower-card path.
- A final route that fully exits the first `n` obstacle layers may require an
  additional exit segment beyond the layer-`n` green point.
