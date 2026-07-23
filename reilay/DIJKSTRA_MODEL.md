# Dijkstra Model For Turn-Card Path Search

This note explains how Dijkstra's algorithm is used in the obstacle corridor
simulation.

## 1. Geometric Graph

After choosing a sampling precision, the safe corridor is discretized into
candidate points.

- Each candidate point is a graph node.
- Two candidate points are connected by an edge only if the straight segment
  between them is safe.
- A straight segment is safe if its distance to every obstacle center is at
  least `9`.

So the first graph is:

```text
sample point = node
safe straight segment = edge
```

## 2. Why Standard Node Dijkstra Is Not Enough

The cost is not attached to a single segment.  A turn card is spent at a bend.
For three consecutive points:

```text
A -> B -> C
```

the cost at `B` depends on the angle between segment `AB` and segment `BC`.

Therefore the current point `B` alone is not enough.  The algorithm must also
remember the previous point `A`.

## 3. State Graph

The Dijkstra state is:

```text
(previous_point, current_point)
```

For example:

```text
(A, B)
```

means the robot is currently at `B`, and it arrived from `A`, so its current
direction is known.

From state `(A, B)`, if `C` is a safe neighbor of `B`, the next state is:

```text
(B, C)
```

The transition cost is:

```text
ceil(angle(AB, BC) / 5 degrees)
```

The starting state is:

```text
(None, start)
```

The first segment costs no turn card because the initial direction can be
chosen freely.

## 4. Priority Order

The search primarily minimizes:

```text
total turn cards
```

Ties are broken by:

```text
total turn angle
path length
```

So the result is not simply the shortest geometric path.  It is the path with
the fewest turn cards in the sampled graph.

## 5. How The Next Point Is Chosen

At each Dijkstra step, the algorithm removes from the priority queue the state
with the best known cost so far.

For current state:

```text
(prev, current)
```

it enumerates every safe neighbor `next` of `current`.

For each candidate `next`, it computes:

```text
new_cost = old_cost + turn_cards(prev, current, next)
```

If this new cost is better than the best known cost for state:

```text
(current, next)
```

the state is updated and pushed into the priority queue.

Thus the algorithm does not greedily choose the locally smallest turn.  It
explores candidates in global best-cost order, which is the key Dijkstra
property.

## 6. Correctness Within The Sampled Graph

All transition costs are non-negative, so Dijkstra is valid on this state graph.
Therefore, once the target state is popped from the priority queue, the path is
optimal among all paths that use the sampled points and safe straight segments.

This is still a sampled-graph optimum, not a proof of global continuous
optimality.
