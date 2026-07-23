# Search Optimization Ideas

The current full-grid search is expensive because it builds a visibility graph
over many sampled points:

```text
candidate points * candidate edges * obstacle checks
```

When the grid step is reduced from `1.0m` to `0.5m`, the point count in a
2D region can grow by about `4x`, while pairwise edge checks can grow close to
`16x`.

## 1. Coarse-To-Fine Local Refinement

Use a coarse result, such as `labeled_corridor_result_g1.json`, as the center
of a narrow search band.

Instead of sampling the whole corridor axis at `0.5m`, sample only points close
to the previous best path.

Expected benefit:

- far fewer candidate points;
- far fewer visibility checks;
- still explores the neighborhood where a better path is likely.

This is the first optimization to compare against the current full `0.5m`
search.

## 2. Search One Layer Or One Period Unit

The selected green-pocket axis appears periodic.  Instead of searching all 9
layers at once, search:

```text
layer k -> layer k+1
```

or a period block:

```text
layer k -> layer k+3
```

Then tile the unit outward.

Expected benefit:

- smaller graph;
- easier to infer a formula such as a repeated `7, 7, 6` pattern.

## 3. Limit Candidate Edges

Only try to connect points that are:

- within a maximum distance;
- not too far from the intended corridor;
- generally moving toward the target;
- not obvious backtracking.

Expected benefit:

- reduces graph density;
- fewer expensive segment-obstacle checks.

## 4. Check Only Nearby Obstacles

For a segment, far-away obstacles cannot collide with it.  Use a spatial index
or grid bucket to check only obstacles near the segment's bounding box expanded
by radius `9`.

Expected benefit:

- much faster safety checks per edge.

## 5. A* Instead Of Plain Dijkstra

Use an admissible heuristic, such as a lower bound on remaining turns or
remaining progress, to prioritize states closer to the goal.

Expected benefit:

- fewer expanded states.

Risk:

- if the heuristic overestimates, optimality in the sampled graph may be lost.

## Planned Comparison

After the current full `0.5m` run finishes:

1. Record full-search runtime and result.
2. Run a local-refinement `0.5m` search around `labeled_corridor_result_g1.json`.
3. Compare:
   - runtime;
   - candidate point count;
   - path cards;
   - total turn;
   - minimum clearance.
